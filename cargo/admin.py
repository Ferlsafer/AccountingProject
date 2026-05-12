from django.contrib import admin
from .models import Vehicle, Driver, CargoCustomer, Trip, TripExpense, VehicleExpense, Invoice


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'make', 'model', 'year', 'is_active']
    list_filter = ['is_active', 'make']
    search_fields = ['plate_number', 'make', 'model']


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'license_number', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'license_number']


@admin.register(CargoCustomer)
class CargoCustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email']
    search_fields = ['name', 'phone']


class TripExpenseInline(admin.TabularInline):
    model = TripExpense
    extra = 0
    readonly_fields = ['date', 'category', 'description', 'amount', 'recorded_by']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'customer', 'vehicle', 'driver', 'status', 'freight_amount', 'date']
    list_filter = ['status', 'date']
    search_fields = ['origin', 'destination', 'customer__name', 'vehicle__plate_number', 'driver__name']
    date_hierarchy = 'date'
    list_per_page = 25
    inlines = [TripExpenseInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['number', 'trip', 'amount', 'is_paid', 'paid_date', 'payment_method']
    list_filter = ['is_paid', 'payment_method']
    search_fields = ['number', 'trip__customer__name']
    date_hierarchy = 'date'
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VehicleExpense)
class VehicleExpenseAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'description', 'category', 'amount', 'date']
    list_filter = ['category', 'vehicle']
    search_fields = ['vehicle__plate_number', 'description']
    date_hierarchy = 'date'
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
