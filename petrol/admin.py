from django.contrib import admin
from .models import FuelType, Tank, FuelSupplier, CreditCustomer, DailyFuelSale, FuelPurchase, CreditSale, CreditPayment, PetrolExpense


@admin.register(FuelType)
class FuelTypeAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Tank)
class TankAdmin(admin.ModelAdmin):
    list_display = ['name', 'fuel_type', 'capacity', 'current_stock', 'stock_pct', 'is_active']
    list_filter = ['fuel_type', 'is_active']

    @admin.display(description='Stock %')
    def stock_pct(self, obj):
        if obj.capacity:
            pct = (obj.current_stock / obj.capacity) * 100
            return f"{pct:.0f}%"
        return '—'


@admin.register(FuelSupplier)
class FuelSupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone']
    search_fields = ['name', 'contact_person']


@admin.register(CreditCustomer)
class CreditCustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'credit_limit', 'current_balance', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'phone']


@admin.register(DailyFuelSale)
class DailyFuelSaleAdmin(admin.ModelAdmin):
    list_display = ['date', 'tank', 'litres_sold', 'unit_price', 'total_amount', 'recorded_by']
    list_filter = ['tank__fuel_type', 'date']
    date_hierarchy = 'date'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(FuelPurchase)
class FuelPurchaseAdmin(admin.ModelAdmin):
    list_display = ['date', 'supplier', 'tank', 'litres', 'unit_price', 'total_amount']
    list_filter = ['tank__fuel_type', 'supplier']
    date_hierarchy = 'date'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = ['date', 'customer', 'tank', 'litres', 'total_amount']
    list_filter = ['customer', 'tank__fuel_type']
    date_hierarchy = 'date'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CreditPayment)
class CreditPaymentAdmin(admin.ModelAdmin):
    list_display = ['date', 'customer', 'amount', 'reference', 'recorded_by']
    list_filter = ['customer']
    date_hierarchy = 'date'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PetrolExpense)
class PetrolExpenseAdmin(admin.ModelAdmin):
    list_display = ['date', 'description', 'category', 'amount', 'recorded_by']
    list_filter = ['category', 'date']
    date_hierarchy = 'date'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
