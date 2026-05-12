from django import forms
from django.contrib.auth.models import User
from .models import Employee, SalaryPayment, UserProfile, PettyCashTransaction, Account, Business

_date = {'type': 'date', 'class': 'form-control'}
_num  = {'class': 'form-control', 'step': '0.01', 'min': '0'}
_sel  = {'class': 'form-select'}
_text = {'class': 'form-control'}


class UserCreateForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**_text, 'placeholder': 'First name'}))
    last_name  = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={**_text, 'placeholder': 'Last name'}))
    username   = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**_text, 'placeholder': 'e.g. juma.petrol'}))
    role       = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs=_sel))
    password1  = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={**_text, 'placeholder': 'Password'}))
    password2  = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={**_text, 'placeholder': 'Repeat password'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned


class UserEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=_text))
    last_name  = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs=_text))
    role       = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs=_sel))
    is_active  = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    password1  = forms.CharField(label='New password', required=False,
                                 widget=forms.PasswordInput(attrs={**_text, 'placeholder': 'Leave blank to keep current'}))
    password2  = forms.CharField(label='Confirm new password', required=False,
                                 widget=forms.PasswordInput(attrs={**_text, 'placeholder': 'Repeat new password'}))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'role', 'monthly_salary', 'phone', 'hire_date', 'is_active']
        widgets = {
            'name':           forms.TextInput(attrs={**_text, 'placeholder': 'Full name'}),
            'role':           forms.TextInput(attrs={**_text, 'placeholder': 'e.g. Driver, Cashier'}),
            'monthly_salary': forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'phone':          forms.TextInput(attrs={**_text, 'placeholder': '+255 ...'}),
            'hire_date':      forms.DateInput(attrs=_date),
            'is_active':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ['employee', 'month', 'amount', 'paid_date', 'notes']
        widgets = {
            'employee':  forms.Select(attrs=_sel),
            'month':     forms.DateInput(attrs={**_date, 'placeholder': 'YYYY-MM-01'}),
            'amount':    forms.NumberInput(attrs={**_num, 'placeholder': '0.00'}),
            'paid_date': forms.DateInput(attrs=_date),
            'notes':     forms.Textarea(attrs={**_text, 'rows': 2, 'placeholder': 'Optional notes'}),
        }
        help_texts = {
            'month': 'Enter the first day of the month being paid (e.g. 2024-04-01)',
        }


class PettyCashTransactionForm(forms.ModelForm):
    class Meta:
        model = PettyCashTransaction
        fields = ["date", "transaction_type", "amount", "expense_category", "expense_account", "description", "receipt_reference"]
        widgets = {
            "date":             forms.DateInput(attrs={**_date}),
            "transaction_type": forms.Select(attrs=_sel),
            "amount":           forms.NumberInput(attrs={**_num}),
            "expense_category": forms.TextInput(attrs={**_text, "placeholder": "e.g. Driver Allowance"}),
            "expense_account":  forms.Select(attrs=_sel),
            "description":      forms.Textarea(attrs={**_text, "rows": 3}),
            "receipt_reference":forms.TextInput(attrs={**_text, "placeholder": "e.g. RCP-001"}),
        }


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['code', 'name', 'type', 'parent', 'is_active']
        widgets = {
            'code':      forms.TextInput(attrs={**_text, 'placeholder': 'e.g. 5180'}),
            'name':      forms.TextInput(attrs={**_text, 'placeholder': 'e.g. Bank Charges'}),
            'type':      forms.Select(attrs=_sel),
            'parent':    forms.Select(attrs=_sel),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'code': 'Unique account code. Use 1xxx=Asset, 2xxx=Liability, 3xxx=Equity, 4xxx=Revenue, 5xxx=Expense.',
            'parent': 'Optional — select a parent account to group sub-accounts.',
        }


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'tin', 'phone', 'email', 'address', 'base_currency']
        widgets = {
            'name':          forms.TextInput(attrs={**_text, 'placeholder': 'e.g. TLC Business Ltd'}),
            'tin':           forms.TextInput(attrs={**_text, 'placeholder': 'e.g. 123-456-789'}),
            'phone':         forms.TextInput(attrs={**_text, 'placeholder': 'e.g. +255 712 000 000'}),
            'email':         forms.EmailInput(attrs={**_text, 'placeholder': 'e.g. info@tlc.co.tz'}),
            'address':       forms.Textarea(attrs={**_text, 'rows': 2, 'placeholder': 'Physical address'}),
            'base_currency': forms.Select(attrs=_sel),
        }
