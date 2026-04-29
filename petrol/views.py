from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import render, redirect

from .models import DailyFuelSale, FuelPurchase, CreditCustomer, CreditSale, CreditPayment, PetrolExpense, Tank
from .forms import DailyFuelSaleForm, FuelPurchaseForm, CreditSaleForm, CreditPaymentForm, PetrolExpenseForm


def _date_range(request):
    today = date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to   = request.GET.get('date_to')   or today.isoformat()
    return date_from, date_to


# ── Daily Fuel Sales ─────────────────────────────────────────────────────────

@login_required
def daily_sale_list(request):
    date_from, date_to = _date_range(request)
    qs = DailyFuelSale.objects.filter(date__gte=date_from, date__lte=date_to).select_related('tank__fuel_type', 'recorded_by')
    totals = qs.aggregate(litres=Sum('litres_sold'), amount=Sum('total_amount'))
    return render(request, 'petrol/daily_sale_list.html', {
        'sales': qs, 'totals': totals, 'date_from': date_from, 'date_to': date_to,
    })


@login_required
def daily_sale_add(request):
    if request.method == 'POST':
        form = DailyFuelSaleForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                sale = form.save(commit=False)
                sale.recorded_by = request.user
                sale.total_amount = sale.litres_sold * sale.unit_price
                sale.save()
                sale.tank.current_stock -= sale.litres_sold
                sale.tank.save(update_fields=['current_stock'])
                sale.post_to_ledger(request.user)
            messages.success(request, f"Sale recorded: {sale.litres_sold}L of {sale.tank.fuel_type} — TZS {sale.total_amount:,.0f}")
            return redirect('petrol:daily_sale_list')
    else:
        form = DailyFuelSaleForm(initial={'date': date.today()})
    tanks = Tank.objects.filter(is_active=True).select_related('fuel_type')
    return render(request, 'petrol/daily_sale_form.html', {'form': form, 'tanks': tanks})


# ── Fuel Purchases ───────────────────────────────────────────────────────────

@login_required
def purchase_list(request):
    date_from, date_to = _date_range(request)
    qs = FuelPurchase.objects.filter(date__gte=date_from, date__lte=date_to).select_related('tank__fuel_type', 'supplier')
    totals = qs.aggregate(litres=Sum('litres'), amount=Sum('total_amount'))
    return render(request, 'petrol/purchase_list.html', {
        'purchases': qs, 'totals': totals, 'date_from': date_from, 'date_to': date_to,
    })


@login_required
def purchase_add(request):
    if request.method == 'POST':
        form = FuelPurchaseForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                purchase = form.save(commit=False)
                purchase.recorded_by = request.user
                purchase.total_amount = purchase.litres * purchase.unit_price
                purchase.save()
                purchase.tank.current_stock += purchase.litres
                purchase.tank.save(update_fields=['current_stock'])
                purchase.post_to_ledger(request.user)
            messages.success(request, f"Purchase recorded: {purchase.litres}L — TZS {purchase.total_amount:,.0f}")
            return redirect('petrol:purchase_list')
    else:
        form = FuelPurchaseForm(initial={'date': date.today()})
    return render(request, 'petrol/purchase_form.html', {'form': form})


# ── Credit Sales ─────────────────────────────────────────────────────────────

@login_required
def credit_sale_list(request):
    date_from, date_to = _date_range(request)
    qs = CreditSale.objects.filter(date__gte=date_from, date__lte=date_to).select_related('customer', 'tank__fuel_type')
    totals = qs.aggregate(litres=Sum('litres'), amount=Sum('total_amount'))
    customers = CreditCustomer.objects.filter(is_active=True)
    return render(request, 'petrol/credit_sale_list.html', {
        'sales': qs, 'totals': totals, 'customers': customers,
        'date_from': date_from, 'date_to': date_to,
    })


@login_required
def credit_sale_add(request):
    if request.method == 'POST':
        form = CreditSaleForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                sale = form.save(commit=False)
                sale.recorded_by = request.user
                sale.total_amount = sale.litres * sale.unit_price
                sale.save()
                sale.tank.current_stock -= sale.litres
                sale.tank.save(update_fields=['current_stock'])
                sale.customer.current_balance += sale.total_amount
                sale.customer.save(update_fields=['current_balance'])
                sale.post_to_ledger(request.user)
            messages.success(request, f"Credit sale recorded for {sale.customer} — TZS {sale.total_amount:,.0f}")
            return redirect('petrol:credit_sale_list')
    else:
        form = CreditSaleForm(initial={'date': date.today()})
    return render(request, 'petrol/credit_sale_form.html', {'form': form})


# ── Credit Payments ──────────────────────────────────────────────────────────

@login_required
def credit_payment_add(request):
    if request.method == 'POST':
        form = CreditPaymentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.recorded_by = request.user
                payment.save()
                payment.customer.current_balance -= payment.amount
                payment.customer.save(update_fields=['current_balance'])
                payment.post_to_ledger(request.user)
            messages.success(request, f"Payment of TZS {payment.amount:,.0f} recorded for {payment.customer}")
            return redirect('petrol:credit_sale_list')
    else:
        form = CreditPaymentForm(initial={'date': date.today()})
    return render(request, 'petrol/credit_payment_form.html', {'form': form})


# ── Petrol Expenses ──────────────────────────────────────────────────────────

@login_required
def expense_list(request):
    date_from, date_to = _date_range(request)
    qs = PetrolExpense.objects.filter(date__gte=date_from, date__lte=date_to)
    totals = qs.aggregate(amount=Sum('amount'))
    return render(request, 'petrol/expense_list.html', {
        'expenses': qs, 'totals': totals, 'date_from': date_from, 'date_to': date_to,
    })


@login_required
def expense_add(request):
    if request.method == 'POST':
        form = PetrolExpenseForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save(commit=False)
                expense.recorded_by = request.user
                expense.save()
                expense.post_to_ledger(request.user)
            messages.success(request, f"Expense recorded: {expense.description} — TZS {expense.amount:,.0f}")
            return redirect('petrol:expense_list')
    else:
        form = PetrolExpenseForm(initial={'date': date.today()})
    return render(request, 'petrol/expense_form.html', {'form': form})
