from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum

from core.models import Business, JournalEntry, JournalLine, SalaryPayment, Employee


@login_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    # Cash position: sum of debits minus credits on account 1010
    cash_qs = JournalLine.objects.filter(account__code='1010')
    cash_debits = cash_qs.aggregate(t=Sum('debit'))['t'] or Decimal('0')
    cash_credits = cash_qs.aggregate(t=Sum('credit'))['t'] or Decimal('0')
    cash_position = cash_debits - cash_credits

    # This month revenue: credits to 4xxx accounts
    month_revenue = JournalLine.objects.filter(
        account__code__startswith='4',
        entry__date__gte=month_start,
        entry__date__lte=today,
    ).aggregate(t=Sum('credit'))['t'] or Decimal('0')

    # This month expenses: debits to 5xxx accounts
    month_expenses = JournalLine.objects.filter(
        account__code__startswith='5',
        entry__date__gte=month_start,
        entry__date__lte=today,
    ).aggregate(t=Sum('debit'))['t'] or Decimal('0')

    month_profit = month_revenue - month_expenses

    # Salary payments this month
    salary_this_month = SalaryPayment.objects.filter(
        paid_date__gte=month_start,
        paid_date__lte=today,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    # Recent journal entries
    recent_entries = JournalEntry.objects.select_related('created_by').prefetch_related('lines__account')[:10]

    business = Business.get_solo()

    context = {
        'business': business,
        'today': today,
        'cash_position': cash_position,
        'month_revenue': month_revenue,
        'month_expenses': month_expenses,
        'month_profit': month_profit,
        'salary_this_month': salary_this_month,
        'active_employees': Employee.objects.filter(is_active=True).count(),
        'recent_entries': recent_entries,
    }
    return render(request, 'reports/dashboard.html', context)
