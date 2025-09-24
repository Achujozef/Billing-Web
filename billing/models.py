from django.db import models
from django.utils import timezone
# ----------------------------
# Nakshathra Choices (Malayalam)
# ----------------------------
NAKSHATHRA_CHOICES = [
    ("", "------"),
    ("അശ്വതി", "അശ്വതി"),
    ("ഭരണി", "ഭരണി"),
    ("കാർത്തിക", "കാർത്തിക"),
    ("രോഹിണി", "രോഹിണി"),
    ("മകയിരം", "മകയിരം"),
    ("തിരുവാതിര", "തിരുവാതിര"),
    ("പുണർതം", "പുണർതം"),
    ("പൂയം", "പൂയം"),
    ("ആയില്യം", "ആയില്യം"),
    ("മകം", "മകം"),
    ("പൂരം", "പൂരം"),
    ("ഉത്രം", "ഉത്രം"),
    ("അത്തം", "അത്തം"),
    ("ചിത്തിര", "ചിത്തിര"),
    ("ചോതി", "ചോതി"),
    ("വിശാഖം", "വിശാഖം"),
    ("അനിഴം", "അനിഴം"),
    ("തൃക്കേട്ട", "തൃക്കേട്ട"),
    ("മൂലം", "മൂലം"),
    ("പൂരാടം", "പൂരാടം"),
    ("ഉത്രാടം", "ഉത്രാടം"),
    ("തിരുവോണം", "തിരുവോണം"),
    ("അവിട്ടം", "അവിട്ടം"),
    ("ചതയം", "ചതയം"),
    ("പൂരുരുട്ടാതി", "പൂരുരുട്ടാതി"),
    ("ഉത്രട്ടാതി", "ഉത്രട്ടാതി"),
    ("രേവതി", "രേവതി"),
]

# ----------------------------
# Customer
# ----------------------------
class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True) 
    def __str__(self):
        return f"{self.name} ({self.phone_number})"


# ----------------------------
# Pooja (Product)
# ----------------------------
class Pooja(models.Model):
    pooja_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    festival_pooja = models.BooleanField(default=False, blank=True, null=True)
    def __str__(self):
        return f"{self.pooja_name} - ₹{self.price}"


# ----------------------------
# Subscription
# ----------------------------
class Subscription(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="subscriptions")
    start_date = models.DateField()
    end_date = models.DateField()
    nakshathra = models.CharField(max_length=50, choices=NAKSHATHRA_CHOICES,default="",)
    poojas = models.ManyToManyField(Pooja, through="SubscriptionPooja")
    is_active = models.BooleanField(default=True) 
    def __str__(self):
        return f"Subscription: {self.customer.name} ({self.nakshathra})"
    @property
    def status(self):
        """Return 'Active' or 'Inactive' based on end_date & toggle"""
        today = timezone.now().date()
        if self.end_date and self.end_date < today:
            return "Inactive"
        return "Active" if self.is_active else "Inactive"
    
class SubscriptionPooja(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    pooja = models.ForeignKey(Pooja, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subscription.customer.name} → {self.pooja.pooja_name}"


# ----------------------------
# Bills
# ----------------------------
class Bill(models.Model):
    customer_name = models.CharField(max_length=200)
    nakshathra = models.CharField(max_length=50, choices=NAKSHATHRA_CHOICES,default="",)
    date = models.DateField(auto_now_add=True)
    poojas = models.ManyToManyField(Pooja, through="BillPooja")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_no = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.BooleanField(default=True, blank=True, null=True)
    def __str__(self):
        return f"Bill {self.id} - {self.customer_name} ({self.nakshathra})"


class BillPooja(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    pooja = models.ForeignKey(Pooja, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=True, blank=True, default=1)
    def __str__(self):
        return f"Bill {self.bill.id} → {self.pooja.pooja_name}"

class SubscriptionCycleHistory(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="cycle_histories")
    cycle_number = models.PositiveIntegerField()
    poojas_done = models.ManyToManyField(Pooja, blank=True)
    done_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subscription', 'cycle_number')
        ordering = ['cycle_number']

    def __str__(self):
        return f"{self.subscription.customer.name} - Cycle {self.cycle_number} ({self.done_at.strftime('%Y-%m-%d %H:%M')})"
    
class SubscriptionBill(models.Model):
    subscription = models.ForeignKey("Subscription", on_delete=models.CASCADE, related_name="subscription_bills")
    bill = models.ForeignKey("Bill", on_delete=models.CASCADE, related_name="subscription_bills")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Subscription {self.subscription.id} ↔ Bill {self.bill.id}"
    

# ----------------------------
# ✅ NEW: Festival Events
# ----------------------------
class Event(models.Model):   # ✅ NEW
    event_name = models.CharField(max_length=200)

    def __str__(self):
        return self.event_name


class EventBooking(models.Model):   # ✅ NEW
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bookings")
    pooja = models.ForeignKey(Pooja, on_delete=models.CASCADE, limit_choices_to={'festival_pooja': True})
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="event_bookings")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.event.event_name} → {self.pooja.pooja_name} (Bill {self.bill.id})"
    

class FamilyBillMember(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="family_members")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)   # in case customer record is not created
    nakshathra = models.CharField(max_length=50, choices=NAKSHATHRA_CHOICES, default="")

    def __str__(self):
        return f"Bill {self.bill.id} → {self.name} ({self.nakshathra})"
