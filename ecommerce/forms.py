import json
from django import forms
from django.contrib.auth.models import User
from ecommerce.models import UserProfile, Order, Address


class AddressForm(forms.ModelForm):
    country = forms.ChoiceField(choices=[('IN', 'India')], initial='IN') # Set India as the only choice
    existing_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        empty_label="(Click to Choose an existing address)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Address
        fields = ['first_name', 'last_name', 'email', 'phone', 'address_line_1', 'country', 'state', 'city', 'zipcode', 'existing_address']

    def __init__(self, user, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.fields['existing_address'].queryset = Address.objects.filter(user=user)
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['name','phone_number', 'address']
    
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = []  # Remove 'products' from here

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)