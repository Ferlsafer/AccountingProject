from datetime import date
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum

from core.models import Business, Account, JournalEntry, JournalLine, SalaryPayment, Employee
from petrol.models import DailyFuelSale, CreditSale, PetrolExpense, FuelType, Tank, CreditCustomer
from cargo.models import Trip, Invoice, TripExpense, VehicleExpense


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

    # Today's fuel sales
    today_fuel_revenue = DailyFuelSale.objects.filter(date=today).aggregate(
        t=Sum('total_amount'))['t'] or Decimal('0')
    today_fuel_litres = DailyFuelSale.objects.filter(date=today).aggregate(
        t=Sum('litres_sold'))['t'] or Decimal('0')

    # Recent journal entries (6 most recent)
    recent_entries = JournalEntry.objects.select_related('created_by').prefetch_related('lines__account')[:6]

    # Recent invoices (6 most recent)
    recent_invoices = (Invoice.objects
                       .select_related('trip__customer')
                       .order_by('-date')[:6])

    # Active trips count
    active_trips = Trip.objects.filter(status='in_progress').count()

    business = Business.get_solo()

    # ── Petrol clerk context ──────────────────────────────────────────────────
    tank_list = [
        {
            'obj': t,
            'pct': int(t.current_stock / t.capacity * 100) if t.capacity else 0,
        }
        for t in Tank.objects.filter(is_active=True).select_related('fuel_type').order_by('name')
    ]
    today_sales = (DailyFuelSale.objects
                   .filter(date=today)
                   .select_related('tank__fuel_type', 'recorded_by')
                   .order_by('-created_at')[:10])
    credit_qs = CreditCustomer.objects.filter(is_active=True, current_balance__gt=0)
    total_credit_balance = credit_qs.aggregate(t=Sum('current_balance'))['t'] or Decimal('0')
    outstanding_credit = credit_qs.order_by('-current_balance')[:5]

    # ── Cargo clerk context ───────────────────────────────────────────────────
    pending_trips = (Trip.objects
                     .filter(status__in=['planned', 'in_progress'])
                     .select_related('customer', 'vehicle', 'driver')
                     .order_by('status', '-date')[:10])
    planned_count = Trip.objects.filter(status='planned').count()
    outstanding_inv_qs = Invoice.objects.filter(is_paid=False)
    outstanding_amount = outstanding_inv_qs.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    outstanding_invoices = outstanding_inv_qs.select_related('trip__customer').order_by('-date')[:8]
    month_collected = (Invoice.objects
                       .filter(is_paid=True, paid_date__gte=month_start)
                       .aggregate(t=Sum('amount'))['t'] or Decimal('0'))

    context = {
        'business': business,
        'today': today,
        # admin / accountant
        'cash_position': cash_position,
        'month_revenue': month_revenue,
        'month_expenses': month_expenses,
        'month_profit': month_profit,
        'salary_this_month': salary_this_month,
        'active_employees': Employee.objects.filter(is_active=True).count(),
        'today_fuel_revenue': today_fuel_revenue,
        'today_fuel_litres': today_fuel_litres,
        'recent_entries': recent_entries,
        'recent_invoices': recent_invoices,
        'active_trips': active_trips,
        # petrol clerk
        'tank_list': tank_list,
        'today_sales': today_sales,
        'total_credit_balance': total_credit_balance,
        'outstanding_credit': outstanding_credit,
        # cargo clerk
        'pending_trips': pending_trips,
        'planned_count': planned_count,
        'outstanding_amount': outstanding_amount,
        'outstanding_invoices': outstanding_invoices,
        'month_collected': month_collected,
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
def journal_ledger(request):
    today = date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to   = request.GET.get('date_to')   or today.isoformat()
    source_filter = request.GET.get('source', '')

    qs = (JournalEntry.objects
          .filter(date__gte=date_from, date__lte=date_to)
          .select_related('created_by')
          .prefetch_related('lines__account')
          .order_by('-date', '-id'))

    if source_filter:
        qs = qs.filter(source_type=source_filter)

    source_types = (JournalEntry.objects
                    .values_list('source_type', flat=True)
                    .distinct()
                    .order_by('source_type'))

    total_debit = sum(e.total_debit for e in qs)

    return render(request, 'reports/journal_ledger.html', {
        'entries': qs,
        'date_from': date_from,
        'date_to': date_to,
        'source_filter': source_filter,
        'source_types': source_types,
        'total_debit': total_debit,
    })


def _dr(request):
    today = date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to   = request.GET.get('date_to')   or today.isoformat()
    return date_from, date_to


# ── Fuel Sales Report ─────────────────────────────────────────────────────────

@login_required
def fuel_report(request):
    date_from, date_to = _dr(request)
    fuel_filter = request.GET.get('fuel', '')

    cash_qs = (DailyFuelSale.objects
               .filter(date__gte=date_from, date__lte=date_to)
               .select_related('tank__fuel_type', 'recorded_by'))
    credit_qs = (CreditSale.objects
                 .filter(date__gte=date_from, date__lte=date_to)
                 .select_related('tank__fuel_type', 'customer', 'recorded_by'))

    if fuel_filter:
        cash_qs   = cash_qs.filter(tank__fuel_type__name=fuel_filter)
        credit_qs = credit_qs.filter(tank__fuel_type__name=fuel_filter)

    all_sales = []
    for s in cash_qs:
        all_sales.append({
            'date': s.date, 'fuel_type': s.tank.fuel_type.name,
            'litres': s.litres_sold, 'unit_price': s.unit_price,
            'amount': s.total_amount, 'sale_type': 'Cash', 'customer': '—',
        })
    for s in credit_qs:
        all_sales.append({
            'date': s.date, 'fuel_type': s.tank.fuel_type.name,
            'litres': s.litres, 'unit_price': s.unit_price,
            'amount': s.total_amount, 'sale_type': 'Credit', 'customer': s.customer.name,
        })
    all_sales.sort(key=lambda x: x['date'], reverse=True)

    cash_totals   = cash_qs.aggregate(litres=Sum('litres_sold'), amount=Sum('total_amount'))
    credit_totals = credit_qs.aggregate(litres=Sum('litres'),    amount=Sum('total_amount'))
    total_litres  = (cash_totals['litres'] or 0) + (credit_totals['litres'] or 0)
    total_amount  = (cash_totals['amount'] or 0) + (credit_totals['amount'] or 0)

    breakdown = {}
    for s in all_sales:
        ft = s['fuel_type']
        if ft not in breakdown:
            breakdown[ft] = {'litres': Decimal('0'), 'amount': Decimal('0')}
        breakdown[ft]['litres'] += s['litres']
        breakdown[ft]['amount'] += s['amount']

    return render(request, 'reports/fuel_report.html', {
        'all_sales': all_sales,
        'breakdown': breakdown,
        'total_litres': total_litres,
        'total_amount': total_amount,
        'cash_amount': cash_totals['amount'] or 0,
        'credit_amount': credit_totals['amount'] or 0,
        'fuel_types': FuelType.objects.all(),
        'fuel_filter': fuel_filter,
        'date_from': date_from,
        'date_to': date_to,
    })


# ── Trip Profitability Report ─────────────────────────────────────────────────

@login_required
def trip_report(request):
    date_from, date_to = _dr(request)

    trips = (Trip.objects
             .filter(date__gte=date_from, date__lte=date_to, status='completed')
             .select_related('customer', 'vehicle', 'driver')
             .prefetch_related('expenses'))

    rows = []
    total_freight  = Decimal('0')
    total_expenses = Decimal('0')
    total_profit   = Decimal('0')

    for trip in trips:
        exp    = trip.total_expenses()
        profit = trip.profit()
        margin = (profit / trip.freight_amount * 100) if trip.freight_amount else Decimal('0')
        rows.append({'trip': trip, 'expenses': exp, 'profit': profit, 'margin': margin})
        total_freight  += trip.freight_amount
        total_expenses += exp
        total_profit   += profit

    rows.sort(key=lambda x: x['profit'], reverse=True)
    total_margin = (total_profit / total_freight * 100) if total_freight else Decimal('0')

    return render(request, 'reports/trip_report.html', {
        'rows': rows,
        'total_freight': total_freight,
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'total_margin': total_margin,
        'date_from': date_from,
        'date_to': date_to,
    })


# ── Expenses by Category ──────────────────────────────────────────────────────

@login_required
def expense_report(request):
    date_from, date_to = _dr(request)

    petrol_by_cat  = (PetrolExpense.objects
                      .filter(date__gte=date_from, date__lte=date_to)
                      .values('category').annotate(total=Sum('amount')).order_by('category'))
    trip_by_cat    = (TripExpense.objects
                      .filter(date__gte=date_from, date__lte=date_to)
                      .values('category').annotate(total=Sum('amount')).order_by('category'))
    vehicle_by_cat = (VehicleExpense.objects
                      .filter(date__gte=date_from, date__lte=date_to)
                      .values('category').annotate(total=Sum('amount')).order_by('category'))
    salary_total   = (SalaryPayment.objects
                      .filter(paid_date__gte=date_from, paid_date__lte=date_to)
                      .aggregate(t=Sum('amount'))['t'] or Decimal('0'))

    petrol_total  = sum(r['total'] for r in petrol_by_cat)
    trip_total    = sum(r['total'] for r in trip_by_cat)
    vehicle_total = sum(r['total'] for r in vehicle_by_cat)
    grand_total   = petrol_total + trip_total + vehicle_total + salary_total

    return render(request, 'reports/expense_report.html', {
        'petrol_by_cat': petrol_by_cat,
        'trip_by_cat': trip_by_cat,
        'vehicle_by_cat': vehicle_by_cat,
        'petrol_total': petrol_total,
        'trip_total': trip_total,
        'vehicle_total': vehicle_total,
        'salary_total': salary_total,
        'grand_total': grand_total,
        'date_from': date_from,
        'date_to': date_to,
    })


# ── Income Statement ──────────────────────────────────────────────────────────

@login_required
def income_statement(request):
    date_from, date_to = _dr(request)

    revenue_lines = (JournalLine.objects
                     .filter(account__code__startswith='4',
                             entry__date__gte=date_from, entry__date__lte=date_to)
                     .values('account__code', 'account__name')
                     .annotate(total=Sum('credit'))
                     .order_by('account__code'))

    expense_lines = (JournalLine.objects
                     .filter(account__code__startswith='5',
                             entry__date__gte=date_from, entry__date__lte=date_to)
                     .values('account__code', 'account__name')
                     .annotate(total=Sum('debit'))
                     .order_by('account__code'))

    total_revenue  = sum(r['total'] for r in revenue_lines)
    total_expenses = sum(e['total'] for e in expense_lines)
    net_profit     = total_revenue - total_expenses
    business       = Business.get_solo()

    return render(request, 'reports/income_statement.html', {
        'revenue_lines': revenue_lines,
        'expense_lines': expense_lines,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'business': business,
        'date_from': date_from,
        'date_to': date_to,
    })


# ── Trial Balance ─────────────────────────────────────────────────────────────

@login_required
def trial_balance(request):
    today = date.today()
    as_of = request.GET.get('as_of') or today.isoformat()

    accounts = Account.objects.filter(is_active=True).order_by('code')
    rows = []
    total_debit  = Decimal('0')
    total_credit = Decimal('0')

    for account in accounts:
        lines   = JournalLine.objects.filter(account=account, entry__date__lte=as_of)
        debits  = lines.aggregate(t=Sum('debit'))['t']  or Decimal('0')
        credits = lines.aggregate(t=Sum('credit'))['t'] or Decimal('0')
        if debits == 0 and credits == 0:
            continue
        balance = debits - credits
        dr_bal  = balance if balance >= 0 else Decimal('0')
        cr_bal  = abs(balance) if balance < 0 else Decimal('0')
        total_debit  += dr_bal
        total_credit += cr_bal
        rows.append({'account': account, 'debit_balance': dr_bal, 'credit_balance': cr_bal})

    business = Business.get_solo()

    return render(request, 'reports/trial_balance.html', {
        'rows': rows,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
        'as_of': as_of,
        'business': business,
    })
