from django.contrib import admin
from .models import Customer, JobOrder


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'customer_type', 'credit_limit', 'is_active')
    list_filter = ('customer_type', 'is_active')
    search_fields = ('name', 'phone', 'email', 'tin')


@admin.register(JobOrder)
class JobOrderAdmin(admin.ModelAdmin):
    list_display = ('reference', 'date', 'customer', 'origin', 'destination', 'status', 'created_by')
    list_filter = ('status',)
    search_fields = ('reference', 'customer__name', 'origin', 'destination', 'cargo_description')
    readonly_fields = ('reference', 'created_by', 'created_at')
    date_hierarchy = 'date'
