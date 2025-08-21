from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from datetime import datetime
import json
import math
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Pooja, Subscription, Customer
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, date
from django.utils.dateparse import parse_date
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.utils import timezone
from datetime import date
from .models import Pooja, Bill, BillPooja, NAKSHATHRA_CHOICES, SubscriptionCycleHistory
from django.utils.dateparse import parse_date
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from .models import Bill
from datetime import datetime, timedelta
from django.core.paginator import Paginator

def dashboard(request):
    try:
        poojas = Pooja.objects.all().order_by("pooja_name")
    except Exception as e:
        poojas = []
        print("Error fetching poojas:", e)

    context = {
        "current_date": datetime.now().strftime("%d-%m-%Y"),
        "current_time": datetime.now().strftime("%H:%M:%S"),
        "poojas": poojas,
        "NAKSHATHRA_CHOICES": NAKSHATHRA_CHOICES,
    }
    return render(request, "billing/dashboard.html", context)


# ------------------------
# API: Generate Bill (AJAX)
# ------------------------
@csrf_exempt
def generate_bill(request):
    """Handles bill creation via AJAX safely with error handling"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        customer_name = data.get("customer_name")
        nakshathra = data.get("nakshathra")
        cart = data.get("cart", [])
        total_amount = data.get("total", 0)

        if not customer_name or not nakshathra or not cart:
            return JsonResponse({"success": False, "error": "Missing required fields"}, status=400)

        # ✅ Ensure nakshathra is valid
        if nakshathra not in dict(NAKSHATHRA_CHOICES):
            return JsonResponse({"success": False, "error": "Invalid Nakshathra"}, status=400)

        with transaction.atomic():  # ensures all or nothing
            bill = Bill.objects.create(
                customer_name=customer_name,
                nakshathra=nakshathra,
                total_amount=total_amount,
            )

            for item in cart:
                pooja_id = item.get("id")
                try:
                    pooja = Pooja.objects.get(id=pooja_id)
                    BillPooja.objects.create(bill=bill, pooja=pooja)
                except Pooja.DoesNotExist:
                    continue  # skip invalid products

        return JsonResponse({"success": True, "bill_id": bill.id})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    

def pooja_list(request):
    poojas = Pooja.objects.all().order_by("id")
    return render(request, "billing/poojas.html", {"poojas": poojas})


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
        
        if pooja_id:  # Edit
            pooja = get_object_or_404(Pooja, id=pooja_id)
            pooja.pooja_name = name
            pooja.price = price
            pooja.save()
        else:  # Add
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

    # Prepare subscriptions JSON for JS usage
    subs_json = []
    for sub in subscriptions:
        # Calculate total days
        total_days = (sub.end_date - sub.start_date).days + 1
        
        # Calculate total bill amount - convert Decimal to float
        total_pooja_amount = sum(float(p.price) for p in sub.poojas.all())
        cycles = max(1, total_days / 28)  # At least 1 cycle
        rounded_cycles = math.ceil(cycles)  # Use ceil for better billing
        total_bill_amount = total_pooja_amount * rounded_cycles
        
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
            "poojas": list(sub.poojas.values_list('id', flat=True)),
        })

    # Add calculated fields to subscription objects for template
    for sub in subscriptions:
        sub.total_days = (sub.end_date - sub.start_date).days + 1
        total_pooja_amount = sum(float(p.price) for p in sub.poojas.all())
        cycles = max(1, sub.total_days / 28)
        rounded_cycles = math.ceil(cycles)
        sub.total_bill_amount = round(total_pooja_amount * rounded_cycles, 2)

    # Prepare poojas JSON - convert Decimal prices to float
    poojas_json = []
    for pooja in Pooja.objects.all():
        poojas_json.append({
            'id': pooja.id,
            'pooja_name': pooja.pooja_name,
            'price': float(pooja.price)  # Convert Decimal to float
        })

    return render(request, "billing/subscription_list.html", {
        "subscriptions": subscriptions,
        "subscriptions_json": json.dumps(subs_json),
        "poojas_json": json.dumps(poojas_json),
        "nakshathras": dict(NAKSHATHRA_CHOICES),
        "selected_nakshathra": selected_nakshathra,
        "selected_status": selected_status,
        "poojas": Pooja.objects.all(),
        "customers": Customer.objects.all(),
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
                created_sub_id = subscription.id
            else:  # Create new subscription
                subscription = Subscription.objects.create(
                    customer=customer,
                    nakshathra=nakshathra,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True
                )
                created_sub_id = subscription.id

            # Update poojas
            if pooja_ids:
                subscription.poojas.set(Pooja.objects.filter(id__in=pooja_ids))
            else:
                subscription.poojas.clear()

            return JsonResponse({
                "success": True, 
                "subscription_id": created_sub_id,
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
    cycles = max(1, math.ceil(total_days / 28))  # Round up cycles
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
    total_days = (subscription.end_date - subscription.start_date).days + 1
    cycles = max(1, math.ceil(total_days / 28))

    # Get existing histories
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
            history.save()

            return JsonResponse({"success": True, "message": f"Cycle {cycle_number} marked done!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})


def report_view(request):
    filter_option = request.GET.get("filter")  # today, week, month, year, custom
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    page = int(request.GET.get("page", 1))

    today = timezone.now().date()
    bills_qs = Bill.objects.prefetch_related("poojas").all().order_by("-date")

    # Filtering
    if filter_option:
        if filter_option == "today":
            bills_qs = bills_qs.filter(date=today)
        elif filter_option == "week":
            start_week = today - timedelta(days=today.weekday())
            bills_qs = bills_qs.filter(date__gte=start_week, date__lte=today)
        elif filter_option == "month":
            bills_qs = bills_qs.filter(date__month=today.month, date__year=today.year)
        elif filter_option == "year":
            bills_qs = bills_qs.filter(date__year=today.year)
        elif filter_option == "custom" and start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                bills_qs = bills_qs.filter(date__gte=start, date__lte=end)
            except:
                pass
        bills = bills_qs  # Use full filtered queryset
        total_bills = bills.count()
        total_amount = bills.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        page_obj = None
    else:
        # Paginate only if no filter selected
        paginator = Paginator(bills_qs, 2)  # 20 bills per page
        page_obj = paginator.get_page(page)
        bills = page_obj.object_list
        total_bills = paginator.count
        total_amount = bills_qs.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
    print("Bill Count is",bills.count())
    context = {
        "bills": bills,
        "total_bills": total_bills,
        "total_amount": total_amount,
        "filter_option": filter_option or "",
        "start_date": start_date or "",
        "end_date": end_date or "",
        "page_obj": page_obj,
    }
    return render(request, "billing/report.html", context)


import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def transliterate(request):
    """
    Proxy to Google Input Tools (Malayalam transliteration).
    Avoids browser CORS issues.
    """
    q = (request.GET.get("q") or "").strip()
    print("Query: ",q)
    if not q:
        return JsonResponse({"suggestions": []})

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.google.com/inputtools/try/",
        }
        r = requests.get("https://www.google.com/inputtools/request", params={
            "text": q,
            "itc": "ml-t-i0-und",
            "num": 5,
            "ie": "utf-8",
            "oe": "utf-8",
        }, headers=headers, timeout=5)
        print(r.json())
        data = r.json()
        suggestions = data[1][0][1] if data and data[0] == "SUCCESS" else []
        print("suggestions :",suggestions)
        return JsonResponse({"suggestions": suggestions})
    except Exception as e:
        return JsonResponse({"suggestions": [], "error": str(e)}, status=502)