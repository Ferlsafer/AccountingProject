from django import forms
from .models import Trip, TripExpense, VehicleExpense, Invoice, CargoCustomer

_date = {'type': 'date', 'class': 'form-control'}
_num  = {'class': 'form-control', 'step': '0.01', 'min': '0'}
_sel  = {'class': 'form-select'}
_text = {'class': 'form-control'}


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['date', 'customer', 'vehicle', 'driver', 'origin', 'destination',
                  'freight_amount', 'cargo_description', 'notes']
        widgets = {
            'date':              forms.DateInput(attrs=_date),
            'customer':          forms.Select(attrs=_sel),
            'vehicle':           forms.Select(attrs=_sel),
            'driver':            forms.Select(attrs=_sel),
            'origin':            forms.TextInput(attrs={**_text, 'placeholder': 'e.g. Mbeya'}),
            'destination':       forms.TextInput(attrs={**_text, 'placeholder': 'e.g. Dar es Salaam'}),
            'freight_amount':    forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'cargo_description': forms.Textarea(attrs={**_text, 'rows': 2, 'placeholder': 'What cargo?'}),
            'notes':             forms.Textarea(attrs={**_text, 'rows': 2, 'placeholder': 'Optional notes'}),
        }


class TripExpenseForm(forms.ModelForm):
    class Meta:
        model = TripExpense
        fields = ['date', 'category', 'description', 'amount']
        widgets = {
            'date':        forms.DateInput(attrs=_date),
            'category':    forms.Select(attrs=_sel),
            'description': forms.TextInput(attrs={**_text, 'placeholder': 'e.g. Fuel Dar road'}),
            'amount':      forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
        }


class VehicleExpenseForm(forms.ModelForm):
    class Meta:
        model = VehicleExpense
        fields = ['date', 'vehicle', 'category', 'description', 'amount']
        widgets = {
            'date':        forms.DateInput(attrs=_date),
            'vehicle':     forms.Select(attrs=_sel),
            'category':    forms.Select(attrs=_sel),
            'description': forms.TextInput(attrs={**_text, 'placeholder': 'e.g. Oil change'}),
            'amount':      forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
        }


class CargoCustomerForm(forms.ModelForm):
    class Meta:
        model = CargoCustomer
        fields = ['name', 'phone', 'email', 'address']
        widgets = {
            'name':    forms.TextInput(attrs={**_text, 'placeholder': 'e.g. ABC Traders Ltd'}),
            'phone':   forms.TextInput(attrs={**_text, 'placeholder': 'e.g. +255 712 000 000'}),
            'email':   forms.EmailInput(attrs={**_text, 'placeholder': 'optional'}),
            'address': forms.Textarea(attrs={**_text, 'rows': 2, 'placeholder': 'Optional address'}),
        }


class InvoicePayForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['paid_date', 'payment_method']
        widgets = {
            'paid_date':      forms.DateInput(attrs=_date),
            'payment_method': forms.Select(attrs=_sel),
        }
