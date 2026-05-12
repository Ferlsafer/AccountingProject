from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from core.models import Account, JournalEntry, JournalLine

FUEL_REVENUE_MAP  = {'Petrol': '4010', 'Diesel': '4020', 'Kerosene': '4030'}
FUEL_INVENTORY_MAP = {'Petrol': '1210', 'Diesel': '1220', 'Kerosene': '1230'}


class FuelType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Tank(models.Model):
    name = models.CharField(max_length=100)
    fuel_type = models.ForeignKey(FuelType, on_delete=models.PROTECT, related_name='tanks')
    capacity = models.DecimalField(max_digits=10, decimal_places=2, help_text='Litres')
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'), help_text='Current selling price per litre (set by management)')
    last_purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Cost per litre from last approved purchase (auto-updated)')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['fuel_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.fuel_type})"


class FuelSupplier(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DailyFuelSale(models.Model):
    date = models.DateField()
    tank = models.ForeignKey(Tank, on_delete=models.PROTECT, related_name='sales')
    litres_sold = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='fuel_sales')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} — {self.tank} — {self.litres_sold}L"

    def _reverse_ledger_entry(self):
        JournalEntry.objects.filter(source_type='daily_fuel_sale', source_id=self.pk).delete()

    def post_to_ledger(self, user):
        self._reverse_ledger_entry()
        fuel_name = self.tank.fuel_type.name
        cash_acct = Account.objects.get(code='1010')
        rev_acct  = Account.objects.get(code=FUEL_REVENUE_MAP.get(fuel_name, '4050'))
        entry = JournalEntry.objects.create(
            date=self.date,
            reference=f"FS-{self.pk}-{self.date.strftime('%Y%m%d')}",
            description=f"Fuel sale — {fuel_name} {self.litres_sold}L @ {self.unit_price}/L",
            source_type='daily_fuel_sale', source_id=self.pk, created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=cash_acct, debit=self.total_amount, credit=Decimal('0')),
            JournalLine(entry=entry, account=rev_acct,  debit=Decimal('0'), credit=self.total_amount),
        ])


class FuelPurchase(models.Model):
    PAYMENT_CHOICES = [
        ('cash',         'Cash'),
        ('bank',         'Bank Transfer'),
        ('mpesa',        'M-Pesa'),
        ('tigopesa',     'Yas (Tigo Pesa)'),
        ('halopesa',     'HaloPesa'),
        ('airtelmoney',  'Airtel Money'),
        ('credit',       'Credit (Supplier Account)'),
    ]
    PAYMENT_ACCOUNT_MAP = {
        'cash':        '1010',
        'bank':        '1020',
        'mpesa':       '1025',
        'tigopesa':    '1026',
        'halopesa':    '1027',
        'airtelmoney': '1028',
        'credit':      '2020',
    }
    STATUS_CHOICES = [
        ('pending',   'Pending Approval'),
        ('approved',  'Approved'),
        ('returned',  'Returned'),
        ('cancelled', 'Cancelled'),
    ]

    date = models.DateField()
    supplier = models.ForeignKey(FuelSupplier, on_delete=models.PROTECT, related_name='purchases')
    tank = models.ForeignKey(Tank, on_delete=models.PROTECT, related_name='purchases')
    litres = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    invoice_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_purchases')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='fuel_purchases')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} — {self.supplier} — {self.litres}L"

    def _reverse_ledger_entry(self):
        JournalEntry.objects.filter(source_type='fuel_purchase', source_id=self.pk).delete()

    def post_to_ledger(self, user):
        self._reverse_ledger_entry()
        fuel_name   = self.tank.fuel_type.name
        inv_acct    = Account.objects.get(code=FUEL_INVENTORY_MAP.get(fuel_name, '1200'))
        credit_code = self.PAYMENT_ACCOUNT_MAP[self.payment_method]
        credit_acct = Account.objects.get(code=credit_code)
        entry = JournalEntry.objects.create(
            date=self.date,
            reference=f"FP-{self.pk}-{self.date.strftime('%Y%m%d')}",
            description=f"Fuel purchase — {fuel_name} {self.litres}L from {self.supplier} ({self.get_payment_method_display()})",
            source_type='fuel_purchase', source_id=self.pk, created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=inv_acct,    debit=self.total_amount, credit=Decimal('0')),
            JournalLine(entry=entry, account=credit_acct, debit=Decimal('0'),      credit=self.total_amount),
        ])


class CreditCustomer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CreditSale(models.Model):
    date = models.DateField()
    customer = models.ForeignKey(CreditCustomer, on_delete=models.PROTECT, related_name='credit_sales')
    tank = models.ForeignKey(Tank, on_delete=models.PROTECT, related_name='credit_sales')
    litres = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='credit_sales')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} — {self.customer} — {self.litres}L"

    def _reverse_ledger_entry(self):
        JournalEntry.objects.filter(source_type='credit_sale', source_id=self.pk).delete()

    def post_to_ledger(self, user):
        self._reverse_ledger_entry()
        fuel_name = self.tank.fuel_type.name
        recv_acct = Account.objects.get(code='1110')
        rev_acct  = Account.objects.get(code=FUEL_REVENUE_MAP.get(fuel_name, '4050'))
        entry = JournalEntry.objects.create(
            date=self.date,
            reference=f"CS-{self.pk}-{self.date.strftime('%Y%m%d')}",
            description=f"Credit sale — {self.customer} — {fuel_name} {self.litres}L",
            source_type='credit_sale', source_id=self.pk, created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=recv_acct, debit=self.total_amount, credit=Decimal('0')),
            JournalLine(entry=entry, account=rev_acct,  debit=Decimal('0'), credit=self.total_amount),
        ])


class CreditPayment(models.Model):
    date = models.DateField()
    customer = models.ForeignKey(CreditCustomer, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, help_text='Receipt or reference number')
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='credit_payments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} — {self.customer} — {self.amount}"

    def _reverse_ledger_entry(self):
        JournalEntry.objects.filter(source_type='credit_payment', source_id=self.pk).delete()

    def post_to_ledger(self, user):
        self._reverse_ledger_entry()
        cash_acct = Account.objects.get(code='1010')
        recv_acct = Account.objects.get(code='1110')
        entry = JournalEntry.objects.create(
            date=self.date,
            reference=f"CP-{self.pk}-{self.date.strftime('%Y%m%d')}",
            description=f"Credit payment — {self.customer} ({self.reference or 'no ref'})",
            source_type='credit_payment', source_id=self.pk, created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=cash_acct, debit=self.amount,         credit=Decimal('0')),
            JournalLine(entry=entry, account=recv_acct, debit=Decimal('0'), credit=self.amount),
        ])


class PetrolExpense(models.Model):
    CATEGORY_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('utilities',   'Utilities'),
        ('supplies',    'Supplies'),
        ('other',       'Other'),
    ]
    date = models.DateField()
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='petrol_expenses')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} — {self.description}"

    def _reverse_ledger_entry(self):
        JournalEntry.objects.filter(source_type='petrol_expense', source_id=self.pk).delete()

    def post_to_ledger(self, user):
        self._reverse_ledger_entry()
        exp_acct  = Account.objects.get(code='5140')
        cash_acct = Account.objects.get(code='1010')
        entry = JournalEntry.objects.create(
            date=self.date,
            reference=f"PE-{self.pk}-{self.date.strftime('%Y%m%d')}",
            description=f"Petrol expense — {self.description}",
            source_type='petrol_expense', source_id=self.pk, created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=exp_acct,  debit=self.amount,         credit=Decimal('0')),
            JournalLine(entry=entry, account=cash_acct, debit=Decimal('0'), credit=self.amount),
        ])
