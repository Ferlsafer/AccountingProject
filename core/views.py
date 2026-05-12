from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404

from .models import Account, Employee, SalaryPayment, UserProfile, PettyCashTransaction
from .forms import EmployeeForm, SalaryPaymentForm, UserCreateForm, UserEditForm, PettyCashTransactionForm


# ── User Management ───────────────────────────────────────────────────────────

@login_required
def user_list(request):
    users = User.objects.select_related('profile').order_by('first_name', 'username')
    return render(request, 'core/user_list.html', {'users': users})


@login_required
def user_add(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = User.objects.create_user(
                username=d['username'],
                password=d['password1'],
                first_name=d['first_name'],
                last_name=d['last_name'],
            )
            user.profile.role = d['role']
            user.profile.save()
            messages.success(request, f"Account created for {user.get_full_name() or user.username} ({user.profile.get_role_display()}).")
            return redirect('core:user_list')
    else:
        form = UserCreateForm()
    return render(request, 'core/user_form.html', {'form': form})


@login_required
def user_edit(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            u.first_name = d['first_name']
            u.last_name  = d['last_name']
            u.is_active  = d['is_active']
            if d['password1']:
                u.set_password(d['password1'])
            u.save()
            u.profile.role = d['role']
            u.profile.save()
            messages.success(request, f"Account updated for {u.get_full_name() or u.username}.")
            return redirect('core:user_list')
    else:
        form = UserEditForm(initial={
            'first_name': u.first_name,
            'last_name':  u.last_name,
            'role':       u.profile.role,
            'is_active':  u.is_active,
        })
    return render(request, 'core/user_edit_form.html', {'form': form, 'edited_user': u})


# ── Chart of Accounts ─────────────────────────────────────────────────────────

@login_required
def account_list(request):
    type_filter = request.GET.get('type', '')
    accounts = Account.objects.filter(is_active=True)
    if type_filter:
        accounts = accounts.filter(type=type_filter)
    return render(request, 'core/account_list.html', {
        'accounts': accounts,
        'type_filter': type_filter,
        'type_choices': Account.TYPE_CHOICES,
    })


# ── Employees ─────────────────────────────────────────────────────────────────

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'core/employee_list.html', {'employees': employees})


@login_required
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f"Employee '{employee.name}' added.")
            return redirect('core:employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'core/employee_form.html', {'form': form})


# ── Salary Payments ───────────────────────────────────────────────────────────

@login_required
def salary_list(request):
    today = date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to   = request.GET.get('date_to')   or today.isoformat()

    payments = (SalaryPayment.objects
                .filter(paid_date__gte=date_from, paid_date__lte=date_to)
                .select_related('employee', 'posted_by'))
    total = payments.aggregate(t=Sum('amount'))['t'] or 0

    return render(request, 'core/salary_list.html', {
        'payments': payments,
        'total': total,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def salary_add(request):
    if request.method == 'POST':
        form = SalaryPaymentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.posted_by = request.user
                payment.save()
                payment.post_to_ledger(request.user)
            messages.success(request, f"Salary payment recorded for {payment.employee} — TZS {payment.amount:,.0f}")
            return redirect('core:salary_list')
    else:
        form = SalaryPaymentForm(initial={'paid_date': date.today()})
    return render(request, 'core/salary_form.html', {'form': form})


# ── Petty Cash ────────────────────────────────────────────────────────────────

def _petty_cash_balance():
    from django.db.models import Sum
    from .models import JournalLine, Account
    acct = Account.objects.filter(code='1030').first()
    if not acct:
        return Decimal('0')
    agg = acct.journal_lines.aggregate(dr=Sum('debit'), cr=Sum('credit'))
    return (agg['dr'] or Decimal('0')) - (agg['cr'] or Decimal('0'))


@login_required
def petty_cash_list(request):
    today = date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to = request.GET.get('date_to') or today.isoformat()
    type_filter = request.GET.get('transaction_type', '')

    qs = PettyCashTransaction.objects.filter(
        date__gte=date_from, date__lte=date_to
    ).select_related('expense_account', 'created_by').order_by('date', 'id')

    if type_filter:
        qs = qs.filter(transaction_type=type_filter)

    # Build running balance
    opening_agg = PettyCashTransaction.objects.filter(date__lt=date_from)
    # Compute opening balance from ledger lines before date_from
    from .models import JournalLine, Account, JournalEntry
    acct = Account.objects.filter(code='1030').first()
    opening = Decimal('0')
    if acct:
        entries_before = JournalEntry.objects.filter(
            source_type='petty_cash', date__lt=date_from
        ).values_list('id', flat=True)
        agg = acct.journal_lines.filter(entry_id__in=entries_before).aggregate(
            dr=Sum('debit'), cr=Sum('credit')
        )
        opening = (agg['dr'] or Decimal('0')) - (agg['cr'] or Decimal('0'))

    rows = []
    running = opening
    for t in qs:
        if t.transaction_type in ('inflow_from_main_cash', 'inflow_other'):
            running += t.amount
        elif t.transaction_type == 'expense':
            running -= t.amount
        elif t.transaction_type == 'return_to_main_cash':
            running -= t.amount
        rows.append({'transaction': t, 'balance': running})

    current_balance = _petty_cash_balance()

    return render(request, 'core/petty_cash_list.html', {
        'rows': rows,
        'current_balance': current_balance,
        'date_from': date_from,
        'date_to': date_to,
        'type_filter': type_filter,
        'transaction_types': PettyCashTransaction.TRANSACTION_TYPES,
    })


@login_required
def petty_cash_add(request):
    if request.method == 'POST':
        form = PettyCashTransactionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                t = form.save(commit=False)
                t.created_by = request.user
                t.save()
                t.post_to_ledger(request.user)
            messages.success(request, f"Petty cash transaction recorded — TZS {t.amount:,.0f}")
            return redirect('core:petty_cash_detail', pk=t.pk)
    else:
        form = PettyCashTransactionForm(initial={'date': date.today()})
    return render(request, 'core/petty_cash_form.html', {
        'form': form,
        'expense_accounts': Account.objects.filter(type='expense').order_by('code'),
    })


@login_required
def petty_cash_detail(request, pk):
    t = get_object_or_404(PettyCashTransaction, pk=pk)
    from .models import JournalEntry
    entry = JournalEntry.objects.filter(source_type='petty_cash', source_id=pk).first()
    return render(request, 'core/petty_cash_detail.html', {'transaction': t, 'entry': entry})


@login_required
def petty_cash_statement(request):
    today = date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to = request.GET.get('date_to') or today.isoformat()

    from .models import JournalLine, Account, JournalEntry
    acct = Account.objects.filter(code='1030').first()

    # Opening balance = all ledger movements on 1030 before date_from
    opening = Decimal('0')
    if acct:
        entries_before = JournalEntry.objects.filter(
            source_type='petty_cash', date__lt=date_from
        ).values_list('id', flat=True)
        agg = acct.journal_lines.filter(entry_id__in=entries_before).aggregate(
            dr=Sum('debit'), cr=Sum('credit')
        )
        opening = (agg['dr'] or Decimal('0')) - (agg['cr'] or Decimal('0'))

    transactions = PettyCashTransaction.objects.filter(
        date__gte=date_from, date__lte=date_to
    ).order_by('date', 'id')

    rows = []
    running = opening
    for t in transactions:
        in_amt = out_amt = Decimal('0')
        if t.transaction_type in ('inflow_from_main_cash', 'inflow_other'):
            in_amt = t.amount
            running += t.amount
        else:
            out_amt = t.amount
            running -= t.amount
        rows.append({'transaction': t, 'in_amt': in_amt, 'out_amt': out_amt, 'balance': running})

    closing = running

    return render(request, 'core/petty_cash_statement.html', {
        'rows': rows,
        'opening': opening,
        'closing': closing,
        'date_from': date_from,
        'date_to': date_to,
    })
