from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db import transaction
from .models import Business, UserProfile, Account, JournalEntry, JournalLine, Employee, SalaryPayment

admin.site.site_header = 'TBC Accounting'
admin.site.site_title = 'TBC Accounting'
admin.site.index_title = 'Administration'


# ── Business ──────────────────────────────────────────────────────────────────

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Company Information', {'fields': ['name', 'tin', 'address', 'phone', 'email']}),
        ('Settings', {'fields': ['base_currency']}),
    ]

    def has_add_permission(self, request):
        return not Business.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ── Users ─────────────────────────────────────────────────────────────────────

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Role & Access'
    fields = ['role']


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'get_full_name', 'email', 'user_role', 'is_active', 'is_staff', 'last_login']
    list_filter = ['is_active', 'is_staff']

    @admin.display(description='Role')
    def user_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return '—'


# ── Chart of Accounts ─────────────────────────────────────────────────────────

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'type', 'parent', 'is_active']
    list_filter = ['type', 'is_active']
    search_fields = ['code', 'name']
    list_display_links = ['code', 'name']
    list_per_page = 50


# ── Journal (read-only) ───────────────────────────────────────────────────────

class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 0
    readonly_fields = ['account', 'debit', 'credit', 'description']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['reference', 'date', 'description', 'source_type', 'total_debit', 'balanced_badge', 'created_by']
    list_filter = ['source_type', 'date']
    search_fields = ['reference', 'description']
    date_hierarchy = 'date'
    readonly_fields = ['reference', 'date', 'description', 'source_type', 'source_id', 'created_by', 'created_at']
    inlines = [JournalLineInline]
    list_per_page = 30

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Balanced', boolean=True)
    def balanced_badge(self, obj):
        return obj.is_balanced


# ── Employees ─────────────────────────────────────────────────────────────────

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'monthly_salary', 'phone', 'hire_date', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'role']
    list_per_page = 25


# ── Salary Payments ───────────────────────────────────────────────────────────

@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month_display', 'amount', 'paid_date', 'posted_by']
    list_filter = ['employee', 'month']
    search_fields = ['employee__name']
    readonly_fields = ['posted_by']
    date_hierarchy = 'paid_date'
    list_per_page = 25

    @admin.display(description='Month', ordering='month')
    def month_display(self, obj):
        return obj.month.strftime('%B %Y')

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            obj.posted_by = request.user
            super().save_model(request, obj, form, change)
            obj.post_to_ledger(request.user)

    def has_delete_permission(self, request, obj=None):
        return False
