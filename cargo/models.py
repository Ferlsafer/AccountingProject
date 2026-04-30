from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from core.models import Account, JournalEntry, JournalLine


class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['plate_number']

    def __str__(self):
        return f"{self.plate_number} — {self.make} {self.model}"


class Driver(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CargoCustomer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Trip(models.Model):
    STATUS_CHOICES = [
        ('planned',     'Planned'),
        ('in_progress', 'In Progress'),
        ('completed',   'Completed'),
        ('cancelled',   'Cancelled'),
    ]
    vehicle           = models.ForeignKey(Vehicle,      on_delete=models.PROTECT, related_name='trips')
    driver            = models.ForeignKey(Driver,       on_delete=models.PROTECT, related_name='trips')
    customer          = models.ForeignKey(CargoCustomer,on_delete=models.PROTECT, related_name='trips')
    origin            = models.CharField(max_length=200)
    destination       = models.CharField(max_length=200)
    date              = models.DateField(help_text='Departure date')
    cargo_description = models.TextField(blank=True)
    freight_amount    = models.DecimalField(max_digits=15, decimal_places=2)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    notes             = models.TextField(blank=True)
    created_by        = models.ForeignKey(User, on_delete=models.PROTECT, related_name='trips')
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.origin} → {self.destination} ({self.date})"

    def total_expenses(self):
        return self.expenses.aggregate(t=Sum('amount'))['t'] or Decimal('0')

    def profit(self):
        return self.freight_amount - self.total_expenses()


class TripExpense(models.Model):
    CATEGORY_CHOICES = [
        ('fuel',             'Fuel'),
        ('toll',             'Toll / Weighbridge'),
        ('driver_allowance', 'Driver Allowance'),
        ('loading',          'Loading / Offloading'),
        ('other',            'Other'),
    ]
    trip        = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=15, decimal_places=2)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    date        = models.DateField()
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='trip_expenses')

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.trip} — {self.description}"

    def _reverse_ledger_entry(self):
        JournalEntry.objects.filter(source_type='trip_expense', source_id=self.pk).delete()

    def post_to_ledger(self, user):
        self._reverse_ledger_entry()
        exp_acct  = Account.objects.get(code='5130')
        cash_acct = Account.objects.get(code='1010')
        entry = JournalEntry.objects.create(
            date=self.date,
            reference=f"TE-{self.pk}-{self.date.strftime('%Y%m%d')}",
            description=f"Trip expense — {self.trip} — {self.description}",
            source_type='trip_expense', source_id=self.pk, created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=exp_acct,  debit=self.amount,        credit=Decimal('0')),
            JournalLine(entry=entry, account=cash_acct, debit=Decimal('0'), credit=self.amount),
        ])


class VehicleExpense(models.Model):
    CATEGORY_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('repair',      'Repair'),
        ('insurance',   'Insurance'),
        ('fuel',        'Fuel'),
        ('tyre',        'Tyre'),
        ('other',       'Other'),
    ]
    vehicle     = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='expenses')
    description = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=15, decimal_places=2)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    date        = models.DateField()
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='vehicle_expenses')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.vehicle} — {self.description}"

    def _reverse_ledger_entry(self):
        JournalEntry.objects.filter(source_type='vehicle_expense', source_id=self.pk).delete()

    def post_to_ledger(self, user):
        self._reverse_ledger_entry()
        exp_acct  = Account.objects.get(code='5120')
        cash_acct = Account.objects.get(code='1010')
        entry = JournalEntry.objects.create(
            date=self.date,
            reference=f"VE-{self.pk}-{self.date.strftime('%Y%m%d')}",
            description=f"Vehicle expense — {self.vehicle} — {self.description}",
            source_type='vehicle_expense', source_id=self.pk, created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=exp_acct,  debit=self.amount,        credit=Decimal('0')),
            JournalLine(entry=entry, account=cash_acct, debit=Decimal('0'), credit=self.amount),
        ])


class Invoice(models.Model):
    PAYMENT_CHOICES = [
        ('cash',   'Cash'),
        ('bank',   'Bank Transfer'),
        ('mobile', 'Mobile Money'),
    ]
    PAYMENT_ACCOUNT_MAP = {'cash': '1010', 'bank': '1020', 'mobile': '1025'}

    trip           = models.OneToOneField(Trip, on_delete=models.PROTECT, related_name='invoice')
    number         = models.CharField(max_length=50, unique=True)
    date           = models.DateField()
    amount         = models.DecimalField(max_digits=15, decimal_places=2)
    is_paid        = models.BooleanField(default=False)
    paid_date      = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, blank=True)
    paid_by        = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='paid_invoices')
    issued_by      = models.ForeignKey(User, on_delete=models.PROTECT, related_name='issued_invoices')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.number

    def _reverse_ledger_entry(self):
        JournalEntry.objects.filter(source_type='invoice_payment', source_id=self.pk).delete()

    def post_to_ledger(self, user):
        self._reverse_ledger_entry()
        cash_acct = Account.objects.get(code=self.PAYMENT_ACCOUNT_MAP[self.payment_method])
        rev_acct  = Account.objects.get(code='4040')
        entry = JournalEntry.objects.create(
            date=self.paid_date,
            reference=f"INVP-{self.pk}-{self.paid_date.strftime('%Y%m%d')}",
            description=f"Invoice payment — {self.number} — {self.trip.customer}",
            source_type='invoice_payment', source_id=self.pk, created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=cash_acct, debit=self.amount,        credit=Decimal('0')),
            JournalLine(entry=entry, account=rev_acct,  debit=Decimal('0'), credit=self.amount),
        ])
