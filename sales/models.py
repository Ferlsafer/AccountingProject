from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    CUSTOMER_TYPES = [
        ('petrol', 'Petrol'),
        ('cargo', 'Cargo'),
        ('both', 'Both'),
    ]
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    tin = models.CharField(max_length=20, blank=True)
    customer_type = models.CharField(max_length=10, choices=CUSTOMER_TYPES, default='cargo')
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class JobOrder(models.Model):
    STATUS_CHOICES = [
        ('draft',       'Draft'),
        ('quoted',      'Quoted'),
        ('accepted',    'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed',   'Completed'),
        ('cancelled',   'Cancelled'),
    ]
    reference = models.CharField(max_length=30, unique=True)
    date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='job_orders')
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    cargo_description = models.CharField(max_length=255)
    estimated_weight_tons = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='job_orders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.reference} — {self.customer}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from sales.utils import generate_reference
            self.reference = generate_reference('JOB')
        super().save(*args, **kwargs)


class Quotation(models.Model):
    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('sent',     'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired',  'Expired'),
    ]
    reference = models.CharField(max_length=30, unique=True)
    date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='quotations')
    job_order = models.ForeignKey(JobOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    valid_until = models.DateField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='quotations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.reference} — {self.customer}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from sales.utils import generate_reference
            self.reference = generate_reference('QUO')
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        from decimal import Decimal
        return sum((line.amount for line in self.lines.all()), Decimal('0'))

    @property
    def total(self):
        return self.subtotal + self.vat_amount


class QuotationLine(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    @property
    def amount(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.description} x {self.quantity} @ {self.unit_price}"


class DeliveryNote(models.Model):
    reference = models.CharField(max_length=30, unique=True)
    date = models.DateField()
    trip = models.ForeignKey('cargo.Trip', on_delete=models.PROTECT, related_name='delivery_notes')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='delivery_notes')
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    cargo_description = models.CharField(max_length=255)
    driver_name = models.CharField(max_length=200)
    vehicle_plate = models.CharField(max_length=20)
    recipient_name = models.CharField(max_length=200, blank=True)
    recipient_signature_received = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='delivery_notes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.reference} — {self.customer}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from sales.utils import generate_reference
            self.reference = generate_reference('DN')
        super().save(*args, **kwargs)


class Receipt(models.Model):
    PAYMENT_METHODS = [
        ('cash',         'Cash'),
        ('bank',         'Bank Transfer'),
        ('mpesa',        'M-Pesa'),
        ('tigopesa',     'Yas (Tigo Pesa)'),
        ('halopesa',     'HaloPesa'),
        ('airtelmoney',  'Airtel Money'),
    ]
    PAYMENT_ACCOUNT_MAP = {
        'cash':        '1010',
        'bank':        '1020',
        'mpesa':       '1025',
        'tigopesa':    '1026',
        'halopesa':    '1027',
        'airtelmoney': '1028',
    }
    AGAINST_TYPES = [
        ('cargo_invoice',        'Cargo Invoice'),
        ('petrol_credit_payment','Petrol Credit Payment'),
        ('other',                'Other'),
    ]
    reference = models.CharField(max_length=30, unique=True)
    date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='receipts')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    against_type = models.CharField(max_length=30, choices=AGAINST_TYPES)
    against_id = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='receipts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.reference} — {self.customer}"

    def save(self, *args, **kwargs):
        if not self.reference:
            from sales.utils import generate_reference
            self.reference = generate_reference('REC')
        super().save(*args, **kwargs)
