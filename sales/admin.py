from django.contrib import admin
from .models import Customer, JobOrder, Quotation, QuotationLine, DeliveryNote, Receipt


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


class QuotationLineInline(admin.TabularInline):
    model = QuotationLine
    extra = 0
    fields = ('description', 'quantity', 'unit_price')


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('reference', 'date', 'customer', 'status', 'valid_until', 'created_by')
    list_filter = ('status',)
    search_fields = ('reference', 'customer__name')
    readonly_fields = ('reference', 'created_by', 'created_at')
    date_hierarchy = 'date'
    inlines = [QuotationLineInline]


@admin.register(DeliveryNote)
class DeliveryNoteAdmin(admin.ModelAdmin):
    list_display = ('reference', 'date', 'customer', 'trip', 'origin', 'destination', 'recipient_signature_received')
    list_filter = ('recipient_signature_received',)
    search_fields = ('reference', 'customer__name', 'driver_name', 'vehicle_plate')
    readonly_fields = ('reference', 'created_by', 'created_at')
    date_hierarchy = 'date'


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('reference', 'date', 'customer', 'amount', 'payment_method', 'against_type', 'created_by')
    list_filter = ('payment_method', 'against_type')
    search_fields = ('reference', 'customer__name')
    readonly_fields = ('reference', 'created_by', 'created_at')
    date_hierarchy = 'date'
