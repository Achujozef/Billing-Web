from django import forms
from .models import Event, Pooja, Bill

# Event
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["event_name"]

# Festival Pooja
class FestivalPoojaForm(forms.ModelForm):
    class Meta:
        model = Pooja
        fields = ["pooja_name", "price"]

class FestivalBillForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.all())
    poojas = forms.ModelMultipleChoiceField(
        queryset=Pooja.objects.filter(festival_pooja=True)
    )
    customer_name = forms.CharField(max_length=200)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    nakshathra = forms.ChoiceField(
        choices=[("", "----")] + Bill._meta.get_field("nakshathra").choices
    )
    payment_status = forms.BooleanField(required=False, initial=True)