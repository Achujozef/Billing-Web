from django.contrib import admin
from .models import*
# Register your models here.
admin.site.register(Customer)
admin.site.register(Pooja)
admin.site.register(Subscription)
admin.site.register(SubscriptionPooja)
admin.site.register(Bill)
admin.site.register(BillPooja)
admin.site.register([SubscriptionCycleHistory,EventBooking])
admin.site.register(FamilyBillMember)
admin.site.register(Event)
admin.site.register(EventBooking)
admin.site.register(FamilyBillMember)
