from django import forms
from .models import DailyFuelSale, FuelPurchase, CreditSale, CreditPayment, PetrolExpense, Tank, FuelSupplier

_date  = {'type': 'date', 'class': 'form-control'}
_num   = {'class': 'form-control', 'step': '0.01', 'min': '0'}
_sel   = {'class': 'form-select'}
_text  = {'class': 'form-control'}


class DailyFuelSaleForm(forms.ModelForm):
    class Meta:
        model = DailyFuelSale
        fields = ['date', 'tank', 'litres_sold']
        widgets = {
            'date':        forms.DateInput(attrs=_date),
            'tank':        forms.Select(attrs=_sel),
            'litres_sold': forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
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
        fields = ['date', 'customer', 'tank', 'litres']
        widgets = {
            'date':     forms.DateInput(attrs=_date),
            'customer': forms.Select(attrs=_sel),
            'tank':     forms.Select(attrs=_sel),
            'litres':   forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
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


class TankForm(forms.ModelForm):
    class Meta:
        model = Tank
        fields = ['name', 'fuel_type', 'capacity', 'selling_price', 'is_active']
        widgets = {
            'name':          forms.TextInput(attrs={**_text, 'placeholder': 'e.g. Tank A — Petrol'}),
            'fuel_type':     forms.Select(attrs=_sel),
            'capacity':      forms.NumberInput(attrs={**_num, 'placeholder': 'Litres, e.g. 20000'}),
            'selling_price': forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'is_active':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'capacity':      'Total tank capacity in litres.',
            'selling_price': 'Selling price per litre charged to customers.',
        }


class TankEditForm(forms.ModelForm):
    class Meta:
        model = Tank
        fields = ['capacity', 'selling_price', 'is_active']
        widgets = {
            'capacity':      forms.NumberInput(attrs={**_num, 'placeholder': 'Litres, e.g. 20000'}),
            'selling_price': forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'is_active':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'capacity':      'Total tank capacity in litres.',
            'selling_price': 'Selling price per litre charged to customers.',
        }


class FuelSupplierForm(forms.ModelForm):
    class Meta:
        model = FuelSupplier
        fields = ['name', 'phone', 'contact_person', 'address']
        widgets = {
            'name':           forms.TextInput(attrs={**_text, 'placeholder': 'e.g. PUMA Energy Tanzania'}),
            'phone':          forms.TextInput(attrs={**_text, 'placeholder': 'e.g. +255 22 000 0000'}),
            'contact_person': forms.TextInput(attrs={**_text, 'placeholder': 'e.g. Ali Mwita'}),
            'address':        forms.Textarea(attrs={**_text, 'rows': 2, 'placeholder': 'Optional address'}),
        }
