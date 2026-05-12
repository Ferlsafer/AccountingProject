from django import forms
from .models import Customer, JobOrder


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address', 'tin', 'customer_type', 'credit_limit', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'tin': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_type': forms.Select(attrs={'class': 'form-select'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class JobOrderForm(forms.ModelForm):
    class Meta:
        model = JobOrder
        fields = ['date', 'customer', 'origin', 'destination', 'cargo_description',
                  'estimated_weight_tons', 'notes']
        widgets = {
            'date':                   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'customer':               forms.Select(attrs={'class': 'form-select'}),
            'origin':                 forms.TextInput(attrs={'class': 'form-control'}),
            'destination':            forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_description':      forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_weight_tons':  forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes':                  forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
