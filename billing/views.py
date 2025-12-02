# Standard Library
import json
import math
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Max, Min,F
from django.views.decorators.http import require_POST
# Third-Party
import requests
from dateutil.relativedelta import relativedelta

# Django Core
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone, dateparse
from django.db import transaction
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
# Local App Imports
from .models import *
from .forms import *

@login_required(login_url="login")
def dashboard(request):
    try:
        poojas = Pooja.objects.all().order_by("id")  # ascending (oldest first)
        # For newest first: .order_by("-id")
        # test = 1/0
        # print("test",test)
        
    except Exception as e:
        poojas = []
        print("Error fetching poojas:", e)
        # return show_error(request, str(e))

    context = {
        "current_date": datetime.now().strftime("%d-%m-%Y"),
        "current_time": datetime.now().strftime("%H:%M:%S"),
        "poojas": poojas,
        "NAKSHATHRA_CHOICES": NAKSHATHRA_CHOICES,
        "family_indices": list(range(8)),
    }
    return render(request, "billing/dashboard.html", context)


@csrf_exempt
def generate_bill(request):
    """Handles bill creation with quantities and price validation"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        customer_name = data.get("customer_name")
        nakshathra = data.get("nakshathra")
        bill_no = data.get("bill_no")
        cart = data.get("cart", [])

        if not customer_name or not nakshathra or not cart:
            return JsonResponse({"success": False, "error": "Missing required fields"}, status=400)

        #  Ensure nakshathra is valid
        if nakshathra not in dict(NAKSHATHRA_CHOICES):
            return JsonResponse({"success": False, "error": "Invalid Nakshathra"}, status=400)

        with transaction.atomic():  # ensures all or nothing
            bill = Bill.objects.create(
                customer_name=customer_name,
                nakshathra=nakshathra,
                total_amount=0,  # will update later
                bill_no=bill_no
            )

            total_amount = 0
            for item in cart:
                pooja_id = item.get("id")
                qty = int(item.get("qty", 1))

                if qty <= 0:
                    continue  # skip invalid qty

                try:
                    pooja = Pooja.objects.get(id=pooja_id)
                except Pooja.DoesNotExist:
                    continue  # skip invalid product

                # calculate subtotal
                subtotal = pooja.price * qty
                total_amount += subtotal

                # create relation with quantity
                BillPooja.objects.create(
                    bill=bill,
                    pooja=pooja,
                    quantity=qty
                )

            # update final total
            bill.total_amount = total_amount
            bill.save()

        return JsonResponse({"success": True, "bill_id": bill.id})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
def generate_family_bill(request):
    """
    Handles family bill creation with multiple poojas and multiple family members.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        bill_no = data.get("bill_no")
        cart = data.get("cart", [])  # list of poojas with qty
        members = data.get("members", [])  # list of family members: {name, nakshathra, customer_id(optional)}

        if not cart or not members:
            return JsonResponse({"success": False, "error": "Cart and members are required"}, status=400)

        # validate nakshathras
        valid_nakshathras = dict(NAKSHATHRA_CHOICES)
        for m in members:
            if m.get("nakshathra") not in valid_nakshathras:
                return JsonResponse({"success": False, "error": f"Invalid Nakshathra for member {m.get('name')}"}, status=400)

        with transaction.atomic():
            # create main bill (customer_name can be head-of-family or summary)
            bill = Bill.objects.create(
                customer_name=f"Family Bill - {members[0]['name']}",  # first member or any label
                nakshathra="",  # blank for family bill
                total_amount=0,
                bill_no=bill_no
            )

            total_amount = 0
            # create BillPooja entries
            for item in cart:
                pooja_id = item.get("id")
                qty = int(item.get("qty", 1))
                if qty <= 0:
                    continue
                try:
                    pooja = Pooja.objects.get(id=pooja_id)
                except Pooja.DoesNotExist:
                    continue
                final_qty = qty * len(members)
                subtotal = pooja.price * qty
                total_amount += subtotal
                BillPooja.objects.create(bill=bill, pooja=pooja, quantity=final_qty)

            # create FamilyBillMember entries
            for m in members:
                customer_obj = None
                customer_id = m.get("customer_id")
                if customer_id:
                    try:
                        customer_obj = Customer.objects.get(id=customer_id)
                    except Customer.DoesNotExist:
                        customer_obj = None

                FamilyBillMember.objects.create(
                    bill=bill,
                    customer=customer_obj,
                    name=m.get("name", "Unknown"),
                    nakshathra=m.get("nakshathra", "")
                )

            # update total_amount in Bill
            final_total = total_amount * len(members)
            bill.total_amount = final_total
            bill.save()

        return JsonResponse({"success": True, "bill_id": bill.id})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    

    
@login_required(login_url="login")
def pooja_list(request):
    poojas = Pooja.objects.all().order_by("id")
    return render(request, "billing/poojas.html", {"poojas": poojas,"current_date": datetime.now().strftime("%d-%m-%Y"),})


@csrf_exempt
def save_pooja(request):
    """Handles Add/Edit Pooja via AJAX"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        pooja_id = data.get("id")
        name = data.get("pooja_name")
        price = data.get("price")
        if not name or price is None:
            return JsonResponse({"success": False, "error": "Missing fields"}, status=400)
        existing_pooja = Pooja.objects.filter(pooja_name__iexact = name).exists()
        
        if pooja_id:  # Edit
            pooja = get_object_or_404(Pooja, id=pooja_id)
            # Check if the new name already exists in another pooja
            if existing_pooja and Pooja.objects.filter(pooja_name__iexact=name).exclude(id=pooja_id).exists():
                return JsonResponse({"success": False, "error": f"Pooja with name '{name}' already exists!"}, status=400)
            pooja.pooja_name = name
            pooja.price = price
            pooja.save()
        else:  # Add
            # Check if name already exists
            if existing_pooja:
                return JsonResponse({"success": False, "error": f"Pooja with name '{name}' already exists!"}, status=400)
            pooja = Pooja.objects.create(pooja_name=name, price=price)

        return JsonResponse({"success": True, "pooja": {"id": pooja.id, "pooja_name": pooja.pooja_name, "price": float(pooja.price)}})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
def delete_pooja(request, pk):
    try:
        pooja = get_object_or_404(Pooja, id=pk)
        pooja.delete()
        return JsonResponse({"success": True})
    
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def calculate_month_cycles(start_date, end_date):
    """Return number of whole months between start_date and end_date (inclusive)."""
    if not start_date or not end_date:
        return 0

    diff = relativedelta(end_date, start_date)
    months = diff.years * 12 + diff.months + 1  # +1 to include the starting month
    return max(1, months)


@login_required(login_url="login")
def subscription_list(request):
    selected_nakshathra = request.GET.get("nakshathra", "")
    selected_status = request.GET.get("status", "")
    
    subscriptions = Subscription.objects.all()
    
    if selected_nakshathra:
        subscriptions = subscriptions.filter(nakshathra=selected_nakshathra)
    
    if selected_status:
        if selected_status == "Active":
            subscriptions = subscriptions.filter(is_active=True)
        elif selected_status == "Inactive":
            subscriptions = subscriptions.filter(is_active=False)

    subs_json = []
    for sub in subscriptions:
        # Total days
        total_days = (sub.end_date - sub.start_date).days + 1

        # Bill calculations
        pooja_list = list(sub.poojas.all())
        total_pooja_amount = sum(float(p.price) for p in pooja_list)
        cycles = calculate_month_cycles(sub.start_date, sub.end_date)
        total_bill_amount = total_pooja_amount * cycles

        # Prepare bill breakdown rows
        bill_items = []
        for p in pooja_list:
            bill_items.append({
                "id": p.id,
                "name": p.pooja_name,
                "price": float(p.price),
                "qty": cycles,
                "amount": float(p.price) * cycles,
            })

        subs_json.append({
            "id": sub.id,
            "customer": {
                "name": sub.customer.name,
                "phone_number": sub.customer.phone_number or ""
            },
            "nakshathra": sub.nakshathra,
            "start_date": sub.start_date.isoformat(),
            "end_date": sub.end_date.isoformat(),
            "total_days": total_days,
            "total_bill_amount": round(total_bill_amount, 2),
            "poojas": [p.id for p in pooja_list],
            "bill": {
                "cycles": cycles,
                "items": bill_items,
                "total": round(total_bill_amount, 2),
            }
        })

    # Add annotated fields for template use
    for sub in subscriptions:
        sub.total_days = (sub.end_date - sub.start_date).days + 1
        total_pooja_amount = sum(float(p.price) for p in sub.poojas.all())
        cycles = max(1, sub.total_days / 28)
        rounded_cycles = math.floor(cycles)
        sub.total_bill_amount = round(total_pooja_amount * rounded_cycles, 2)

    # Prepare poojas JSON
    poojas_json = [
        {"id": p.id, "pooja_name": p.pooja_name, "price": float(p.price)}
        for p in Pooja.objects.all()
    ]

    return render(request, "billing/subscription_list.html", {
        "subscriptions": subscriptions,
        "subscriptions_json": json.dumps(subs_json),
        "poojas_json": json.dumps(poojas_json),
        "nakshathras": dict(NAKSHATHRA_CHOICES),
        "selected_nakshathra": selected_nakshathra,
        "selected_status": selected_status,
        "poojas": Pooja.objects.all(),
        "customers": Customer.objects.all(),
        "current_date": datetime.now().strftime("%d-%m-%Y"),
    })
@csrf_exempt
def subscription_save(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            sub_id = data.get("id")
            customer_name = data.get("customer_name", "").strip()
            customer_phone = data.get("customer_phone", "").strip()
            nakshathra = data.get("nakshathra")
            start_date = parse_date(data.get("start_date"))
            end_date = parse_date(data.get("end_date"))
            pooja_ids = data.get("poojas", [])

            if not customer_name or not nakshathra or not start_date or not end_date:
                return JsonResponse({"success": False, "error": "All required fields must be filled."})

            if start_date >= end_date:
                return JsonResponse({"success": False, "error": "End date must be after start date."})

            # Get or create customer
            customer, _ = Customer.objects.get_or_create(
                name=customer_name,
                defaults={"phone_number": customer_phone or ""}
            )
            
            # Update phone if provided and different
            if customer_phone and customer.phone_number != customer_phone:
                customer.phone_number = customer_phone
                customer.save()

            if sub_id:  # Edit existing subscription
                subscription = get_object_or_404(Subscription, id=sub_id)
                subscription.customer = customer
                subscription.nakshathra = nakshathra
                subscription.start_date = start_date
                subscription.end_date = end_date
                subscription.save()
                
                # Update poojas if provided
                if pooja_ids:
                    pooja_objs = Pooja.objects.filter(id__in=pooja_ids)
                    subscription.poojas.set(pooja_objs)
                
                return JsonResponse({
                    "success": True, 
                    "subscription_id": subscription.id,
                    "message": "Subscription updated successfully!"
                })
            else:  # Create new subscription
                subscription = Subscription.objects.create(
                    customer=customer,
                    nakshathra=nakshathra,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True
                )
                created_sub_id = subscription.id
                if not pooja_ids:
                    return JsonResponse({
                    "success": True, 
                    "subscription_id": created_sub_id,
                    "message": "Subscription saved successfully without poojas!"
                })
                # Update poojas
                pooja_objs = Pooja.objects.filter(id__in=pooja_ids)
                subscription.poojas.set(pooja_objs)

               # --- Calculate cycles ---
                cycles = calculate_month_cycles(start_date, end_date)

                # --- Calculate total amount ---
                total_pooja_amount = sum(float(p.price) for p in pooja_objs)
                total_amount = total_pooja_amount * cycles

                # --- Create Bill ---
                bill = Bill.objects.create(
                    customer_name=customer_name,
                    nakshathra=nakshathra,
                    total_amount=total_amount
                )

                # --- Create BillPooja with quantity = cycles ---
                for p in pooja_objs:
                    BillPooja.objects.create(
                        bill=bill,
                        pooja=p,
                        quantity=cycles
                    )

                # --- Link Subscription ↔ Bill ---
                SubscriptionBill.objects.create(subscription=subscription, bill=bill)

                return JsonResponse({
                    "success": True, 
                    "subscription_id": created_sub_id,
                    "bill_id": bill.id,
                    "message": "Subscription saved successfully!"
                })

        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error saving subscription: {str(e)}"})

    return JsonResponse({"success": False, "error": "Invalid request method."})

@csrf_exempt
def toggle_subscription(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            subscription_id = data.get("id")
            
            subscription = get_object_or_404(Subscription, id=subscription_id)
            subscription.is_active = not subscription.is_active
            subscription.save()
            
            status = "Active" if subscription.is_active else "Inactive"
            return JsonResponse({"success": True, "status": status})
            
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request method."})

@csrf_exempt
def delete_subscription(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            subscription_id = data.get("id")
            
            subscription = get_object_or_404(Subscription, id=subscription_id)
            customer_name = subscription.customer.name
            
            subscription.delete()
            
            return JsonResponse({
                "success": True, 
                "message": f"Subscription for {customer_name} deleted successfully!"
            })
            
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error deleting subscription: {str(e)}"})
    
    return JsonResponse({"success": False, "error": "Invalid request method."})

def view_subscription_bill(request, subscription_id):
    """View subscription bill details"""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    # Calculate bill details
    total_days = (subscription.end_date - subscription.start_date).days + 1
    total_pooja_amount = sum(float(p.price) for p in subscription.poojas.all())
    cycles = calculate_month_cycles(subscription.start_date, subscription.end_date)
    total_bill_amount = total_pooja_amount * cycles
    
    context = {
        'subscription': subscription,
        'total_days': total_days,
        'cycles': cycles,
        'total_pooja_amount': round(total_pooja_amount, 2),
        'total_bill_amount': round(total_bill_amount, 2),
        'selected_poojas': subscription.poojas.all(),
    }
    
    return render(request, "billing/subscription_bill.html", context)

# Alternative: Custom JSON Encoder (if you prefer this approach)
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# Fetch subscription cycle history
def subscription_history(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id)
    cycles = calculate_month_cycles(subscription.start_date, subscription.end_date)

    histories = subscription.cycle_histories.all()

    hist_data = []
    for i in range(1, cycles + 1):
        hist = histories.filter(cycle_number=i).first()
        hist_data.append({
            "cycle_number": i,
            "done": bool(hist),
            "poojas_done": list(hist.poojas_done.values_list('id', flat=True)) if hist else [],
            "done_at": hist.done_at.strftime("%Y-%m-%d %H:%M") if hist else None
        })

    poojas = list(subscription.poojas.values("id", "pooja_name"))
    return JsonResponse({"success": True, "cycles": hist_data, "poojas": poojas})


# Mark a cycle done
@csrf_exempt
def mark_cycle_done(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            sub_id = data.get("subscription_id")
            cycle_number = int(data.get("cycle_number"))
            pooja_ids = data.get("pooja_ids", [])

            subscription = get_object_or_404(Subscription, id=sub_id)

            history, created = SubscriptionCycleHistory.objects.get_or_create(
                subscription=subscription,
                cycle_number=cycle_number
            )
            history.poojas_done.set(Pooja.objects.filter(id__in=pooja_ids))
            print("Hostory: ",history)
            return JsonResponse({"success": True, "message": f"Cycle {cycle_number} marked done!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required(login_url="login")
def report_view(request):
    filter_option = request.GET.get("filter")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    view_mode = request.GET.get("view")  
    page = int(request.GET.get("page", 1))
    report_type = request.GET.get("report", "bill")  # default bill
    search_query = request.GET.get("search", "").strip()
    today = timezone.now().date()
    bills_qs = Bill.objects.prefetch_related("poojas").all().order_by("-id")

    if search_query:
        if search_query.isdigit():  
            bills_qs = bills_qs.filter(id=search_query)
        else:
            # fallback if someone searches non-numeric, ignore
            bills_qs = bills_qs.none()

    # Filtering
    if filter_option:
        if filter_option == "today":
            bills_qs = bills_qs.filter(date=today)
        elif filter_option == "week":
            start_week = today - timedelta(days=today.weekday())
            bills_qs = bills_qs.filter(date__gte=start_week, date__lte=today)
        elif filter_option == "month":
            bills_qs = bills_qs.filter(date__year=today.year, date__month=today.month)
        elif filter_option == "year":
            bills_qs = bills_qs.filter(date__year=today.year)
        elif filter_option == "custom" and start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                bills_qs = bills_qs.filter(date__gte=start, date__lte=end)
            except ValueError:
                pass

    # --- BILL REPORT ---
    # --- BILL REPORT ---
    if report_type == "bill":
        bills = bills_qs if view_mode == "all" else Paginator(bills_qs, 20).get_page(page).object_list
        page_obj = None if view_mode == "all" else Paginator(bills_qs, 20).get_page(page)

        # Preload family members to avoid N+1 queries
        bills = bills.prefetch_related("family_members__customer", "billpooja_set__pooja")

        total_bills = bills_qs.count()
        total_amount = bills_qs.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        total_poojas = sum(bill.poojas.count() for bill in bills_qs)

        # Prepare family members display
        for bill in bills:
            bill.is_family = bill.family_members.exists()
            family_list = []
            for member in bill.family_members.all():
                if member.customer:
                    name = member.customer.name
                    nak = member.customer.nakshathra or member.nakshathra
                else:
                    name = member.name
                    nak = member.nakshathra
                family_list.append({"name": name, "nakshathra": nak})
            bill.family_data = family_list
            bill.family_display = ", ".join([f"{m['name']} ({m['nakshathra']})" for m in family_list]) if family_list else f"{bill.customer_name} ({bill.nakshathra})"

        context = {
            "report_type": "bill",
            "bills": bills,
            "total_bills": total_bills,
            "total_amount": total_amount,
            "total_poojas": total_poojas,
            "filter_option": filter_option or "",
            "start_date": start_date or "",
            "end_date": end_date or "",
            "page_obj": page_obj,
            "view_mode": view_mode or "",
            "current_date": datetime.now().strftime("%d-%m-%Y"),
        }

    # --- PRODUCT REPORT ---
    else:
        product_data = (
            Pooja.objects.filter(billpooja__bill__in=bills_qs)
            .values("id", "pooja_name", "price")
            .annotate(
                quantity=Sum("billpooja__quantity"),   #  sum of quantities from BillPooja
                total=Sum(F("price") * F("billpooja__quantity"))  #  total = price × quantity
            )
            .order_by("pooja_name")
        )

        total_products = product_data.count()
        total_quantity = sum(p["quantity"] or 0 for p in product_data)
        total_amount = sum(p["total"] or 0 for p in product_data)

        context = {
            "report_type": "product",
            "products": product_data,
            "total_products": total_products,
            "total_quantity": total_quantity,
            "total_amount": total_amount,
            "filter_option": filter_option or "",
            "start_date": start_date or "",
            "end_date": end_date or "",
            "view_mode": view_mode or "",
        }

    return render(request, "billing/report.html", context)



def _normalize(s: str) -> str:
    # Malayalam is caseless, but casefold keeps behavior consistent across scripts.
    return unicodedata.normalize("NFC", (s or "").strip()).casefold()

def _is_malayalam(s: str) -> bool:
    return any('\u0D00' <= ch <= '\u0D7F' for ch in s or "")

@require_GET
def transliterate(request):
    """
    Google Input Tools proxy (Malayalam).
    Also surfaces DB names (Customer/Bill/Subscription.customer)
    that start with the typed/suggested Malayalam prefix.
    """
    q_raw = (request.GET.get("q") or "").strip()
    if not q_raw:
        return JsonResponse({"suggestions": []})

    try:
        # ---- 1) Get Google suggestions ----
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.google.com/inputtools/try/",
        }
        r = requests.get(
            "https://www.google.com/inputtools/request",
            params={
                "text": q_raw,
                "itc": "ml-t-i0-und",
                "num": 10,
                "ie": "utf-8",
                "oe": "utf-8",
            },
            headers=headers,
            timeout=5,
        )
        data = r.json()
        suggestions = data[1][0][1] if data and data[0] == "SUCCESS" else []

        # Build prefixes we’ll search DB with:
        # - If user typed Malayalam, include q_raw itself
        # - Always include Google's Malayalam suggestions
        prefixes = []
        seen_p = set()
        if _is_malayalam(q_raw):
            prefixes.append(q_raw); seen_p.add(_normalize(q_raw))
        for s in suggestions:
            ns = _normalize(s)
            if s and ns not in seen_p:
                prefixes.append(s); seen_p.add(ns)

        if not prefixes:
            # Nothing Malayalam to search by → just return Google’s output
            return JsonResponse({"suggestions": suggestions})

        # ---- 2) Query DB for names starting with any prefix ----
        def startswith_q(field: str) -> Q:
            qobj = Q()
            for p in prefixes:
                qobj |= Q(**{f"{field}__istartswith": p})
            return qobj

        cust_qs = Customer.objects.filter(startswith_q("name")) \
                                  .order_by("name") \
                                  .values_list("name", flat=True)[:20]
        bill_qs = Bill.objects.filter(startswith_q("customer_name")) \
                              .order_by("customer_name") \
                              .values_list("customer_name", flat=True)[:20]
        sub_qs  = Subscription.objects.filter(startswith_q("customer__name")) \
                                      .order_by("customer__name") \
                                      .values_list("customer__name", flat=True)[:20]

        # Keep DB order stable, dedupe while preserving order
        db_candidates = list(dict.fromkeys(list(cust_qs) + list(bill_qs) + list(sub_qs)))

        # ---- 3) Rank DB hits: exact > prefix ----
        s_norms = [_normalize(p) for p in prefixes]
        s_norms_set = set(s_norms)

        def db_rank(name: str):
            n = _normalize(name)
            if n in s_norms_set:                                 # exact
                return (0, name)
            if any(n.startswith(sn) or sn.startswith(n) for sn in s_norms):  # prefix either way
                return (1, name)
            return (2, name)

        db_hits = sorted(db_candidates, key=db_rank)

        # ---- 4) Merge DB hits (first) + Google (next) with dedupe ----
        final, seen = [], set()
        for n in db_hits:
            nn = _normalize(n)
            if nn not in seen:
                final.append(n); seen.add(nn)

        for s in suggestions:
            ns = _normalize(s)
            if ns not in seen:
                final.append(s); seen.add(ns)

        # Trim to a tidy list
        return JsonResponse({"suggestions": final[:10]})

    except Exception as e:
        # Fallback: if user typed Malayalam, at least return DB matches
        if _is_malayalam(q_raw):
            fallback_q = Q(name__istartswith=q_raw)
            cust = list(Customer.objects.filter(fallback_q).values_list("name", flat=True)[:10])
            bill = list(Bill.objects.filter(customer_name__istartswith=q_raw).values_list("customer_name", flat=True)[:10])
            sub  = list(Subscription.objects.filter(customer__name__istartswith=q_raw).values_list("customer__name", flat=True)[:10])
            merged = list(dict.fromkeys(cust + bill + sub))[:10]
            return JsonResponse({"suggestions": merged, "fallback": True}, status=200)
        return JsonResponse({"suggestions": [], "error": str(e)}, status=502)

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")  # or wherever you want to redirect after login

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")  # change "dashboard" to your main page
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ---------------- Festival Dashboard ----------------
from django.http import JsonResponse

def festival_dashboard(request):
    events = Event.objects.all()
    festival_poojas = Pooja.objects.filter(festival_pooja=True)
    bills = Bill.objects.filter(event_bookings__isnull=False).distinct()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        event_id = request.GET.get('event')
        pooja_id = request.GET.get('pooja')
        payment_status = request.GET.get('payment')

        filtered_bills = bills

        if event_id:
            filtered_bills = filtered_bills.filter(event_bookings__event__id=event_id)
        if pooja_id:
            filtered_bills = filtered_bills.filter(event_bookings__pooja__id=pooja_id).distinct()
        if payment_status:
            if payment_status == 'paid':
                filtered_bills = filtered_bills.filter(payment_status=True)
            elif payment_status == 'pending':
                filtered_bills = filtered_bills.filter(payment_status=False)

        data = []
        for bill in filtered_bills:
            pooja_list = [eb.pooja.pooja_name for eb in bill.event_bookings.all()]
            data.append({
                'id': bill.id,
                'customer_name': bill.customer_name,
                'event_name': bill.event_bookings.first().event.event_name if bill.event_bookings.first() else '',
                'total_amount': bill.total_amount,
                'payment_status': 'Paid' if bill.payment_status else 'Pending',
                'poojas': pooja_list
            })


        return JsonResponse({'bills': data})

    return render(request, "festival_dashboard.html", {
        "events": events,
        "festival_poojas": festival_poojas,
        "bills": bills,
        "nakshathra_choices": Bill._meta.get_field('nakshathra').choices,
        "current_date": datetime.now().strftime("%d-%m-%Y"),
    })


# ---------------- Event CRUD ----------------
def add_event(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Event.objects.create(event_name=name)
            messages.success(request, "Event added successfully!")
            return redirect("festival_dashboard")
    return JsonResponse({"error": "Invalid request"}, status=400)


def edit_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            event.event_name = name
            event.save()
            messages.success(request, "Event updated successfully!")
            return redirect("festival_dashboard")
    return JsonResponse({"error": "Invalid request"}, status=400)


def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    event.delete()
    messages.success(request, "Event deleted successfully!")
    return redirect("festival_dashboard")



# ---------------- Festival Pooja CRUD ----------------
def add_festival_pooja(request):
    if request.method == "POST":
        form = FestivalPoojaForm(request.POST)
        if form.is_valid():
            pooja = form.save(commit=False)
            pooja.festival_pooja = True
            pooja.save()
            messages.success(request, "Festival Pooja added successfully!")
            return redirect("festival_dashboard")
    return JsonResponse({"error": "Invalid request"}, status=400)


def edit_festival_pooja(request, pk):
    pooja = get_object_or_404(Pooja, pk=pk)
    if request.method == "POST":
        form = FestivalPoojaForm(request.POST, instance=pooja)
        if form.is_valid():
            pooja = form.save(commit=False)
            pooja.festival_pooja = True
            pooja.save()
            messages.success(request, "Festival Pooja updated successfully!")
            return redirect("festival_dashboard")
    return JsonResponse({"error": "Invalid request"}, status=400)


def delete_festival_pooja(request, pk):
    pooja = get_object_or_404(Pooja, pk=pk)
    pooja.delete()
    messages.success(request, "Festival Pooja deleted successfully!")
    return redirect("festival_dashboard")

def create_festival_bill(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = FestivalBillForm(request.POST)
        if form.is_valid():
            try:
                customer, _ = Customer.objects.get_or_create(
                    name=form.cleaned_data["customer_name"],
                    phone_number=form.cleaned_data.get("phone_number"),
                    defaults={"address": form.cleaned_data.get("address")},
                )
                bill = Bill.objects.create(
                    customer_name=customer.name,
                    nakshathra=form.cleaned_data["nakshathra"],
                    total_amount=0,
                    payment_status=form.cleaned_data.get("payment_status", False),
                )

                total = 0
                for pooja in form.cleaned_data["poojas"]:
                    BillPooja.objects.create(bill=bill, pooja=pooja, quantity=1)
                    total += float(pooja.price)

                    EventBooking.objects.create(
                        event=form.cleaned_data["event"],
                        pooja=pooja,
                        bill=bill,
                        customer=customer,
                    )

                bill.total_amount = total
                bill.save()

                return JsonResponse({
                    "success": True,
                    "created_at": timezone.now().isoformat()
                })

            except Exception as e:
                print("SERVER ERROR:", e)
                return JsonResponse({
                    "success": False,
                    "error": f"Server error: {str(e)}"
                }, status=500)

        else:
            # Print form errors to console for debugging
            print("FORM VALIDATION ERROR:", form.errors.as_json())
            errors = form.errors.as_json()
            return JsonResponse({"success": False, "error": "Invalid form data", "details": errors}, status=400)

    print("INVALID REQUEST METHOD OR NOT AJAX")
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


def print_festival_bill(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    return render(request, "print_festival_bill.html", {"bill": bill})

@require_POST
def toggle_payment_status(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    action = request.POST.get("action")

    if action == "mark_paid":
        bill.payment_status = True
    elif action == "mark_unpaid":
        bill.payment_status = False
    
    bill.save()
    return JsonResponse({"success": True, "status": "Paid" if bill.payment_status else "Pending"})



def bill_discrepancy_report(request):
    # Get all bills from EventBooking
    bills = Bill.objects.filter(event_bookings__isnull=False).distinct()

    discrepancies = []
    grand_expected = 0
    grand_actual = 0

    for bill in bills:
        # Expected total from BillPooja
        pooja_items = BillPooja.objects.filter(bill=bill).select_related("pooja")
        expected_total = sum([p.pooja.price * p.quantity for p in pooja_items])
        actual_total = bill.total_amount
        difference = expected_total - actual_total

        if difference != 0:  # Only show mismatches
            discrepancies.append({
                "bill": bill,
                "customer_name": bill.customer_name,
                "poojas": [
                    {
                        "name": p.pooja.pooja_name,
                        "price": p.pooja.price,
                        "quantity": p.quantity,
                        "subtotal": p.pooja.price * p.quantity
                    }
                    for p in pooja_items
                ],
                "expected_total": expected_total,
                "actual_total": actual_total,
                "difference": difference,
            })

            grand_expected += expected_total
            grand_actual += actual_total

    context = {
        "discrepancies": discrepancies,
        "grand_expected": grand_expected,
        "grand_actual": grand_actual,
        "grand_difference": grand_expected - grand_actual,
    }

    return render(request, "billing/bill_discrepancy_report.html", context)

def family_bill_discrepancy_report(request):
    bills = Bill.objects.filter(family_members__isnull=False).distinct()

    discrepancies = []
    grand_expected = 0
    grand_actual = 0

    for bill in bills:
        pooja_items = BillPooja.objects.filter(bill=bill).select_related("pooja")
        expected_total = sum([p.pooja.price * p.quantity for p in pooja_items])
        actual_total = bill.total_amount
        difference = expected_total - actual_total

        if difference != 0:
            discrepancies.append({
                "bill": bill,
                "customer_name": bill.customer_name,
                "family_members": [f"{m.name} ({m.nakshathra})" for m in bill.family_members.all()],
                "poojas": [
                    {
                        "name": p.pooja.pooja_name,
                        "price": p.pooja.price,
                        "quantity": p.quantity,
                        "subtotal": p.pooja.price * p.quantity
                    }
                    for p in pooja_items
                ],
                "expected_total": expected_total,
                "actual_total": actual_total,
                "difference": difference,
            })
            grand_expected += expected_total
            grand_actual += actual_total

    context = {
        "discrepancies": discrepancies,
        "grand_expected": grand_expected,
        "grand_actual": grand_actual,
        "grand_difference": grand_expected - grand_actual,
    }

    return render(request, "billing/family_bill_discrepancy_report.html", context)

def all_bill_discrepancy_report(request):
    bills = Bill.objects.all().distinct()

    discrepancies = []
    grand_expected = 0
    grand_actual = 0

    for bill in bills:
        pooja_items = BillPooja.objects.filter(bill=bill).select_related("pooja")
        expected_total = sum([p.pooja.price * p.quantity for p in pooja_items])
        actual_total = bill.total_amount
        difference = expected_total - actual_total

        # ✅ Find the origin of the bill
        bill_type = []
        if bill.event_bookings.exists():
            bill_type.append("Festival/Event")
        if bill.family_members.exists():
            bill_type.append("Family")
        if bill.subscription_bills.exists():
            bill_type.append("Subscription")
        if not bill_type:
            bill_type.append("Regular")

        bill_type_label = ", ".join(bill_type)

        if difference != 0:
            discrepancies.append({
                "bill": bill,
                "customer_name": bill.customer_name,
                "bill_type": bill_type_label,   # ✅ added
                "poojas": [
                    {
                        "bill_pooja_id": p.id,
                        "name": p.pooja.pooja_name,
                        "price": p.pooja.price,
                        "quantity": p.quantity,
                        "subtotal": p.pooja.price * p.quantity
                    }
                    for p in pooja_items
                ],
                "expected_total": expected_total,
                "actual_total": actual_total,
                "difference": difference,
            })
            grand_expected += expected_total
            grand_actual += actual_total

    context = {
        "discrepancies": discrepancies,
        "grand_expected": grand_expected,
        "grand_actual": grand_actual,
        "grand_difference": grand_expected - grand_actual,
    }

    return render(request, "billing/all_bill_discrepancy_report.html", context)



