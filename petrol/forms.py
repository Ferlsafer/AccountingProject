from django import forms
from .models import DailyFuelSale, FuelPurchase, CreditSale, CreditPayment, PetrolExpense

_date  = {'type': 'date', 'class': 'form-control'}
_num   = {'class': 'form-control', 'step': '0.01', 'min': '0'}
_sel   = {'class': 'form-select'}
_text  = {'class': 'form-control'}


class DailyFuelSaleForm(forms.ModelForm):
    class Meta:
        model = DailyFuelSale
        fields = ['date', 'tank', 'litres_sold', 'unit_price']
        widgets = {
            'date':        forms.DateInput(attrs=_date),
            'tank':        forms.Select(attrs=_sel),
            'litres_sold': forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'unit_price':  forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
        }


class FuelPurchaseForm(forms.ModelForm):
    class Meta:
        model = FuelPurchase
        fields = ['date', 'supplier', 'tank', 'litres', 'unit_price', 'payment_method', 'invoice_number']
        widgets = {
            'date':           forms.DateInput(attrs=_date),
            'supplier':       forms.Select(attrs=_sel),
            'tank':           forms.Select(attrs=_sel),
            'litres':         forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'unit_price':     forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'payment_method': forms.Select(attrs=_sel),
            'invoice_number': forms.TextInput(attrs={**_text, 'placeholder': 'Optional'}),
        }


class CreditSaleForm(forms.ModelForm):
    class Meta:
        model = CreditSale
        fields = ['date', 'customer', 'tank', 'litres', 'unit_price']
        widgets = {
            'date':       forms.DateInput(attrs=_date),
            'customer':   forms.Select(attrs=_sel),
            'tank':       forms.Select(attrs=_sel),
            'litres':     forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'unit_price': forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
        }


class CreditPaymentForm(forms.ModelForm):
    class Meta:
        model = CreditPayment
        fields = ['date', 'customer', 'amount', 'reference']
        widgets = {
            'date':      forms.DateInput(attrs=_date),
            'customer':  forms.Select(attrs=_sel),
            'amount':    forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'reference': forms.TextInput(attrs={**_text, 'placeholder': 'Receipt / ref no.'}),
        }


class PetrolExpenseForm(forms.ModelForm):
    class Meta:
        model = PetrolExpense
        fields = ['date', 'description', 'category', 'amount']
        widgets = {
            'date':        forms.DateInput(attrs=_date),
            'description': forms.TextInput(attrs={**_text, 'placeholder': 'e.g. Pump servicing'}),
            'category':    forms.Select(attrs=_sel),
            'amount':      forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
        }
