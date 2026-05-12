from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q


def _is_finance(user):
    return user.is_staff or (
        hasattr(user, 'profile') and user.profile.role in ('admin', 'accountant')
    )

finance_required = user_passes_test(_is_finance, login_url='/accounts/login/')

from core.models import Business, Account, JournalEntry, JournalLine, SalaryPayment, Employee, BankReconciliation
from petrol.models import DailyFuelSale, CreditSale, CreditPayment, PetrolExpense, FuelType, Tank, CreditCustomer, FuelPurchase, FuelSupplier
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


@finance_required
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

@finance_required
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

@finance_required
def income_statement(request):
    date_from, date_to = _dr(request)

    revenue_lines = list(JournalLine.objects
                     .filter(account__code__startswith='4',
                             entry__date__gte=date_from, entry__date__lte=date_to)
                     .values('account__code', 'account__name')
                     .annotate(total=Sum('credit'))
                     .order_by('account__code'))

    cogs_lines = list(JournalLine.objects
                     .filter(account__code='5050',
                             entry__date__gte=date_from, entry__date__lte=date_to)
                     .values('account__code', 'account__name')
                     .annotate(total=Sum('debit')))

    opex_lines = list(JournalLine.objects
                     .filter(account__code__startswith='5',
                             entry__date__gte=date_from, entry__date__lte=date_to)
                     .exclude(account__code='5050')
                     .values('account__code', 'account__name')
                     .annotate(total=Sum('debit'))
                     .order_by('account__code'))

    total_revenue  = sum(r['total'] for r in revenue_lines)
    total_cogs     = sum(c['total'] for c in cogs_lines)
    gross_profit   = total_revenue - total_cogs
    total_opex     = sum(e['total'] for e in opex_lines)
    net_profit     = gross_profit - total_opex
    business       = Business.get_solo()

    return render(request, 'reports/income_statement.html', {
        'revenue_lines': revenue_lines,
        'cogs_lines':    cogs_lines,
        'opex_lines':    opex_lines,
        'total_revenue': total_revenue,
        'total_cogs':    total_cogs,
        'gross_profit':  gross_profit,
        'total_opex':    total_opex,
        'net_profit':    net_profit,
        'business':      business,
        'date_from':     date_from,
        'date_to':       date_to,
    })


# ── Trial Balance ─────────────────────────────────────────────────────────────

@finance_required
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


# ── Balance Sheet ─────────────────────────────────────────────────────────────

@finance_required
def balance_sheet(request):
    today = date.today()
    as_at = request.GET.get('as_at') or today.isoformat()
    business = Business.get_solo()

    def _account_balance(acct, normal='debit'):
        lines = JournalLine.objects.filter(account=acct, entry__date__lte=as_at)
        agg = lines.aggregate(dr=Sum('debit'), cr=Sum('credit'))
        dr = agg['dr'] or Decimal('0')
        cr = agg['cr'] or Decimal('0')
        return (dr - cr) if normal == 'debit' else (cr - dr)

    sections = {'asset': [], 'liability': [], 'equity': []}
    normals   = {'asset': 'debit', 'liability': 'credit', 'equity': 'credit'}

    for acct_type in ('asset', 'liability', 'equity'):
        for acct in Account.objects.filter(type=acct_type, is_active=True, parent__isnull=False).order_by('code'):
            bal = _account_balance(acct, normals[acct_type])
            if bal:
                sections[acct_type].append({'account': acct, 'balance': bal})

    # Net income for the period up to as_at folds into equity
    rev_agg = JournalLine.objects.filter(account__type='revenue', entry__date__lte=as_at).aggregate(t=Sum('credit'))
    exp_agg = JournalLine.objects.filter(account__type='expense', entry__date__lte=as_at).aggregate(t=Sum('debit'))
    net_income = (rev_agg['t'] or Decimal('0')) - (exp_agg['t'] or Decimal('0'))

    total_assets      = sum(r['balance'] for r in sections['asset'])
    total_liabilities = sum(r['balance'] for r in sections['liability'])
    total_equity      = sum(r['balance'] for r in sections['equity']) + net_income
    total_l_e         = total_liabilities + total_equity
    balanced          = abs(total_assets - total_l_e) < Decimal('0.01')

    return render(request, 'reports/balance_sheet.html', {
        'assets': sections['asset'],
        'liabilities': sections['liability'],
        'equity': sections['equity'],
        'net_income': net_income,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_equity,
        'total_l_e': total_l_e,
        'balanced': balanced,
        'as_at': as_at,
        'business': business,
    })


# ── AR Aging ──────────────────────────────────────────────────────────────────

@finance_required
def ar_aging(request):
    today = date.today()
    business = Business.get_solo()

    BUCKETS = [(0, 30), (31, 60), (61, 90), (91, None)]

    def _age_bucket(days):
        for lo, hi in BUCKETS:
            if hi is None or days <= hi:
                return lo
        return 91

    # ── Petrol credit customers ──
    petrol_rows = []
    for cust in CreditCustomer.objects.filter(current_balance__gt=0):
        sales = list(cust.credit_sales.order_by('date'))
        total_paid = cust.payments.aggregate(t=Sum('amount'))['t'] or Decimal('0')

        buckets = {0: Decimal('0'), 31: Decimal('0'), 61: Decimal('0'), 91: Decimal('0')}
        remaining_payment = total_paid
        for sale in sales:
            if remaining_payment >= sale.total_amount:
                remaining_payment -= sale.total_amount
                continue
            unpaid = sale.total_amount - remaining_payment
            remaining_payment = Decimal('0')
            days_old = (today - sale.date).days
            key = _age_bucket(days_old)
            buckets[key] += unpaid

        petrol_rows.append({
            'name': cust.name,
            'phone': cust.phone,
            'type': 'Petrol Credit',
            'current': buckets[0],
            'd31_60': buckets[31],
            'd61_90': buckets[61],
            'd90plus': buckets[91],
            'total': cust.current_balance,
        })

    # ── Cargo unpaid invoices ──
    cargo_rows = []
    for inv in Invoice.objects.filter(is_paid=False).select_related('trip__customer'):
        days_old = (today - inv.date).days
        key = _age_bucket(days_old)
        buckets = {0: Decimal('0'), 31: Decimal('0'), 61: Decimal('0'), 91: Decimal('0')}
        buckets[key] = inv.amount
        cargo_rows.append({
            'name': inv.trip.customer.name,
            'phone': getattr(inv.trip.customer, 'phone', ''),
            'type': f'Cargo — {inv.number}',
            'current': buckets[0],
            'd31_60': buckets[31],
            'd61_90': buckets[61],
            'd90plus': buckets[91],
            'total': inv.amount,
        })

    all_rows = petrol_rows + cargo_rows
    totals = {
        'current': sum(r['current'] for r in all_rows),
        'd31_60':  sum(r['d31_60']  for r in all_rows),
        'd61_90':  sum(r['d61_90']  for r in all_rows),
        'd90plus': sum(r['d90plus'] for r in all_rows),
        'total':   sum(r['total']   for r in all_rows),
    }

    return render(request, 'reports/ar_aging.html', {
        'rows': all_rows,
        'totals': totals,
        'today': today,
        'business': business,
    })


# ── Supplier AP ───────────────────────────────────────────────────────────────

@finance_required
def supplier_ap(request):
    today = date.today()
    business = Business.get_solo()

    credit_purchases = (FuelPurchase.objects
        .filter(status='approved', payment_method='credit')
        .select_related('supplier', 'tank__fuel_type')
        .order_by('supplier__name', 'date'))

    # Group by supplier
    supplier_map = {}
    for p in credit_purchases:
        sid = p.supplier_id
        if sid not in supplier_map:
            supplier_map[sid] = {
                'supplier': p.supplier,
                'invoices': [],
                'total': Decimal('0'),
            }
        days_old = (today - p.date).days
        supplier_map[sid]['invoices'].append({
            'purchase': p,
            'days_old': days_old,
            'overdue': days_old > 30,
        })
        supplier_map[sid]['total'] += p.total_amount

    suppliers = sorted(supplier_map.values(), key=lambda x: x['supplier'].name)
    grand_total = sum(s['total'] for s in suppliers)

    return render(request, 'reports/supplier_ap.html', {
        'suppliers': suppliers,
        'grand_total': grand_total,
        'today': today,
        'business': business,
    })


# ── Cash Position ─────────────────────────────────────────────────────────────

@finance_required
def cash_position(request):
    today = date.today()
    business = Business.get_solo()

    CASH_ACCOUNTS = ['1010', '1020', '1025', '1026', '1027', '1028', '1030']
    LABELS = {
        '1010': ('Cash on Hand',          'icon-green'),
        '1020': ('Bank Account',          'icon-blue'),
        '1025': ('M-Pesa',                'icon-amber'),
        '1026': ('Yas (Tigo Pesa)',        'icon-teal'),
        '1027': ('HaloPesa',              'icon-purple'),
        '1028': ('Airtel Money',          'icon-red'),
        '1030': ('Petty Cash',            'icon-gray'),
    }

    accounts_data = []
    total_balance = Decimal('0')
    total_in_today = Decimal('0')
    total_out_today = Decimal('0')

    for code in CASH_ACCOUNTS:
        acct = Account.objects.filter(code=code).first()
        if not acct:
            continue

        all_lines = JournalLine.objects.filter(account=acct)
        agg = all_lines.aggregate(dr=Sum('debit'), cr=Sum('credit'))
        balance = (agg['dr'] or Decimal('0')) - (agg['cr'] or Decimal('0'))

        today_lines = all_lines.filter(entry__date=today)
        today_agg   = today_lines.aggregate(dr=Sum('debit'), cr=Sum('credit'))
        in_today    = today_agg['dr'] or Decimal('0')
        out_today   = today_agg['cr'] or Decimal('0')

        total_balance   += balance
        total_in_today  += in_today
        total_out_today += out_today

        label, icon = LABELS[code]
        accounts_data.append({
            'account': acct,
            'label': label,
            'icon': icon,
            'balance': balance,
            'in_today': in_today,
            'out_today': out_today,
            'net_today': in_today - out_today,
        })

    # 7-day cash movement
    seven_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        lines = JournalLine.objects.filter(
            account__code__in=CASH_ACCOUNTS, entry__date=d
        ).aggregate(dr=Sum('debit'), cr=Sum('credit'))
        seven_days.append({
            'date': d,
            'inflow':  lines['dr'] or Decimal('0'),
            'outflow': lines['cr'] or Decimal('0'),
            'net':     (lines['dr'] or Decimal('0')) - (lines['cr'] or Decimal('0')),
        })

    return render(request, 'reports/cash_position.html', {
        'accounts': accounts_data,
        'total_balance': total_balance,
        'total_in_today': total_in_today,
        'total_out_today': total_out_today,
        'net_today': total_in_today - total_out_today,
        'seven_days': seven_days,
        'today': today,
        'business': business,
    })


# ── Bank Reconciliation ───────────────────────────────────────────────────────

@finance_required
def reconciliation_list(request):
    # Only cash/bank accounts are reconcilable (asset accounts starting with 10)
    cash_accounts = Account.objects.filter(type='asset', code__startswith='10', is_active=True)
    reconciliations = BankReconciliation.objects.select_related('account', 'created_by').all()
    return render(request, 'reports/reconciliation_list.html', {
        'reconciliations': reconciliations,
        'cash_accounts': cash_accounts,
        'today': date.today(),
    })


@finance_required
def reconciliation_create(request):
    if request.method != 'POST':
        return redirect('reports:reconciliation_list')

    account_id = request.POST.get('account')
    period_start = request.POST.get('period_start')
    period_end = request.POST.get('period_end')
    statement_balance = request.POST.get('statement_balance')

    if not all([account_id, period_start, period_end, statement_balance]):
        messages.error(request, 'All fields are required.')
        return redirect('reports:reconciliation_list')

    recon = BankReconciliation.objects.create(
        account_id=account_id,
        period_start=period_start,
        period_end=period_end,
        statement_balance=statement_balance,
        created_by=request.user,
    )
    return redirect('reports:reconciliation_detail', pk=recon.pk)


@finance_required
def reconciliation_detail(request, pk):
    recon = get_object_or_404(BankReconciliation, pk=pk)

    # Opening balance: net movement on this account before period_start
    pre = JournalLine.objects.filter(
        account=recon.account, entry__date__lt=recon.period_start
    ).aggregate(dr=Sum('debit'), cr=Sum('credit'))
    opening_balance = (pre['dr'] or Decimal('0')) - (pre['cr'] or Decimal('0'))

    # All lines within the period
    lines = JournalLine.objects.filter(
        account=recon.account,
        entry__date__range=[recon.period_start, recon.period_end],
    ).select_related('entry').order_by('entry__date', 'entry__id')

    if request.method == 'POST' and not recon.is_locked:
        from django.db import transaction as db_transaction
        action     = request.POST.get('action')
        ticked_ids = set(int(x) for x in request.POST.getlist('cleared'))
        all_ids    = {line.pk for line in lines}
        now        = timezone.now()

        with db_transaction.atomic():
            # Clear selected lines — two bulk UPDATEs instead of N individual saves
            if ticked_ids:
                JournalLine.objects.filter(pk__in=ticked_ids & all_ids).update(
                    is_reconciled=True,
                    reconciled_at=now,
                    reconciled_by=request.user,
                    reconciliation=recon,
                )
            # Unclear lines that were unticked (only those previously tied to this recon)
            JournalLine.objects.filter(
                pk__in=(all_ids - ticked_ids), reconciliation=recon
            ).update(
                is_reconciled=False,
                reconciled_at=None,
                reconciled_by=None,
                reconciliation=None,
            )
            if action == 'lock':
                recon.is_locked = True
                recon.locked_at = now
                recon.save(update_fields=['is_locked', 'locked_at'])

        if action == 'lock':
            messages.success(request, 'Reconciliation locked and finalised.')
            return redirect('reports:reconciliation_list')

        messages.success(request, 'Progress saved.')
        return redirect('reports:reconciliation_detail', pk=recon.pk)

    # Build rows with running balance
    running = opening_balance
    rows = []
    cleared_total = opening_balance
    for line in lines:
        net = line.debit - line.credit
        running += net
        if line.is_reconciled:
            cleared_total += net
        rows.append({
            'line': line,
            'net': net,
            'running_balance': running,
        })

    system_balance = running
    difference = recon.statement_balance - cleared_total

    return render(request, 'reports/reconciliation_detail.html', {
        'recon': recon,
        'rows': rows,
        'opening_balance': opening_balance,
        'system_balance': system_balance,
        'cleared_balance': cleared_total,
        'difference': difference,
        'today': date.today(),
    })


# ── VAT Return ────────────────────────────────────────────────────────────────

@finance_required
def vat_return(request):
    date_from, date_to = _dr(request)

    # Output VAT: credits posted to account 2030 (collected from customers)
    output_lines = list(JournalLine.objects
        .filter(account__code='2030', entry__date__gte=date_from, entry__date__lte=date_to)
        .values('entry__source_type')
        .annotate(total=Sum('credit'))
        .order_by('entry__source_type'))

    output_vat = sum(r['total'] for r in output_lines if r['total'])

    # Breakdown by source
    output_by_source = {r['entry__source_type']: r['total'] for r in output_lines if r['total']}

    # Input VAT: debits posted to account 1140 (paid on purchases, reclaimable)
    input_lines = list(JournalLine.objects
        .filter(account__code='1140', entry__date__gte=date_from, entry__date__lte=date_to)
        .values('entry__source_type')
        .annotate(total=Sum('debit'))
        .order_by('entry__source_type'))

    input_vat = sum(r['total'] for r in input_lines if r['total'])

    net_vat = output_vat - input_vat  # positive = payable to TRA

    # Taxable turnover = net revenue for the period (revenue accounts)
    taxable_sales = JournalLine.objects.filter(
        account__code__startswith='4',
        entry__date__gte=date_from, entry__date__lte=date_to,
    ).aggregate(t=Sum('credit'))['t'] or Decimal('0')

    return render(request, 'reports/vat_return.html', {
        'date_from':       date_from,
        'date_to':         date_to,
        'output_vat':      output_vat,
        'output_by_source': output_by_source,
        'input_vat':       input_vat,
        'input_lines':     input_lines,
        'net_vat':         net_vat,
        'taxable_sales':   taxable_sales,
        'today':           date.today(),
        'business':        Business.get_solo(),
    })
