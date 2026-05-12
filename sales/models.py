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
