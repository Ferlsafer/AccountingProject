from django import forms
from django.forms import inlineformset_factory
from .models import Customer, JobOrder, Quotation, QuotationLine, DeliveryNote


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


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['date', 'customer', 'job_order', 'valid_until', 'notes']
        widgets = {
            'date':        forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'customer':    forms.Select(attrs={'class': 'form-select'}),
            'job_order':   forms.Select(attrs={'class': 'form-select'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class QuotationLineForm(forms.ModelForm):
    class Meta:
        model = QuotationLine
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'quantity':    forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'unit_price':  forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
        }


QuotationLineFormSet = inlineformset_factory(
    Quotation, QuotationLine,
    form=QuotationLineForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class DeliveryNoteForm(forms.ModelForm):
    class Meta:
        model = DeliveryNote
        fields = ['date', 'trip', 'customer', 'origin', 'destination',
                  'cargo_description', 'driver_name', 'vehicle_plate',
                  'recipient_name', 'recipient_signature_received', 'notes']
        widgets = {
            'date':             forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'trip':             forms.Select(attrs={'class': 'form-select'}),
            'customer':         forms.Select(attrs={'class': 'form-select'}),
            'origin':           forms.TextInput(attrs={'class': 'form-control'}),
            'destination':      forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_description':forms.TextInput(attrs={'class': 'form-control'}),
            'driver_name':      forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_plate':    forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_name':   forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_signature_received': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes':            forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
