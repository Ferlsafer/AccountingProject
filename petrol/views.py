from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone


def _can_manage_petrol(user):
    return user.is_staff or getattr(user, 'profile', None) and user.profile.role in ('admin', 'petrol_clerk')


def _can_approve_purchase(user):
    return user.is_staff or getattr(user, 'profile', None) and user.profile.role in ('admin', 'accountant')


def _is_admin(user):
    return user.is_staff or getattr(user, 'profile', None) and user.profile.role == 'admin'
from .models import DailyFuelSale, FuelPurchase, CreditCustomer, CreditSale, CreditPayment, PetrolExpense, Tank, FuelSupplier
from .forms import DailyFuelSaleForm, FuelPurchaseForm, CreditSaleForm, CreditPaymentForm, PetrolExpenseForm, TankForm, TankEditForm, FuelSupplierForm


def _date_range(request):
    today = date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to   = request.GET.get('date_to')   or today.isoformat()
    return date_from, date_to


# ── Daily Fuel Sales ─────────────────────────────────────────────────────────

@login_required
def daily_sale_list(request):
    date_from, date_to = _date_range(request)

    cash_qs = (DailyFuelSale.objects
               .filter(date__gte=date_from, date__lte=date_to)
               .select_related('tank__fuel_type', 'recorded_by'))

    credit_qs = (CreditSale.objects
                 .filter(date__gte=date_from, date__lte=date_to)
                 .select_related('tank__fuel_type', 'customer', 'recorded_by'))

    # Combine into a uniform list for the template
    all_sales = []
    for s in cash_qs:
        all_sales.append({
            'date': s.date,
            'tank': s.tank,
            'fuel_type': s.tank.fuel_type,
            'litres': s.litres_sold,
            'unit_price': s.unit_price,
            'total_amount': s.total_amount,
            'sale_type': 'cash',
            'customer': None,
            'recorded_by': s.recorded_by,
        })
    for s in credit_qs:
        all_sales.append({
            'date': s.date,
            'tank': s.tank,
            'fuel_type': s.tank.fuel_type,
            'litres': s.litres,
            'unit_price': s.unit_price,
            'total_amount': s.total_amount,
            'sale_type': 'credit',
            'customer': s.customer,
            'recorded_by': s.recorded_by,
        })

    all_sales.sort(key=lambda x: x['date'], reverse=True)

    cash_totals   = cash_qs.aggregate(litres=Sum('litres_sold'), amount=Sum('total_amount'))
    credit_totals = credit_qs.aggregate(litres=Sum('litres'),    amount=Sum('total_amount'))

    total_litres = (cash_totals['litres'] or 0) + (credit_totals['litres'] or 0)
    total_amount = (cash_totals['amount'] or 0) + (credit_totals['amount'] or 0)

    return render(request, 'petrol/daily_sale_list.html', {
        'all_sales': all_sales,
        'total_litres': total_litres,
        'total_amount': total_amount,
        'cash_amount': cash_totals['amount'] or 0,
        'credit_amount': credit_totals['amount'] or 0,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def daily_sale_add(request):
    if request.method == 'POST':
        form = DailyFuelSaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            if not sale.tank.selling_price:
                messages.error(request, f"No selling price set for {sale.tank}. Ask management to set it first.")
                tanks = Tank.objects.filter(is_active=True).select_related('fuel_type')
                return render(request, 'petrol/daily_sale_form.html', {'form': form, 'tanks': tanks})
            with transaction.atomic():
                sale.recorded_by = request.user
                sale.unit_price = sale.tank.selling_price
                sale.total_amount = sale.litres_sold * sale.unit_price
                sale.save()
                sale.tank.current_stock -= sale.litres_sold
                sale.tank.save(update_fields=['current_stock'])
                sale.post_to_ledger(request.user)
            messages.success(request, f"Sale recorded: {sale.litres_sold}L of {sale.tank.fuel_type} @ TZS {sale.unit_price:,.0f}/L — Total TZS {sale.total_amount:,.0f}")
            return redirect('petrol:daily_sale_list')
    else:
        form = DailyFuelSaleForm(initial={'date': date.today()})
    tanks = Tank.objects.filter(is_active=True).select_related('fuel_type')
    return render(request, 'petrol/daily_sale_form.html', {'form': form, 'tanks': tanks})


# ── Fuel Purchases ───────────────────────────────────────────────────────────

@login_required
def purchase_list(request):
    date_from, date_to = _date_range(request)
    status_filter = request.GET.get('status', '')
    qs = FuelPurchase.objects.filter(
        date__gte=date_from, date__lte=date_to
    ).select_related('tank__fuel_type', 'supplier', 'reviewed_by')
    if status_filter:
        qs = qs.filter(status=status_filter)
    totals = qs.aggregate(litres=Sum('litres'), amount=Sum('total_amount'))
    pending_count = FuelPurchase.objects.filter(status='pending').count()
    return render(request, 'petrol/purchase_list.html', {
        'purchases': qs,
        'totals': totals,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        'status_choices': FuelPurchase.STATUS_CHOICES,
        'pending_count': pending_count,
    })


@login_required
def purchase_add(request):
    if not _can_manage_petrol(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        form = FuelPurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.recorded_by = request.user
            purchase.total_amount = purchase.litres * purchase.unit_price
            purchase.status = 'pending'
            purchase.save()
            messages.success(request, f"Purchase submitted for approval: {purchase.litres}L — TZS {purchase.total_amount:,.0f}")
            return redirect('petrol:purchase_list')
    else:
        form = FuelPurchaseForm(initial={'date': date.today()})
    return render(request, 'petrol/purchase_form.html', {'form': form})


@login_required
def purchase_edit(request, pk):
    purchase = get_object_or_404(FuelPurchase, pk=pk)
    if purchase.status != 'returned':
        messages.error(request, "Only returned purchases can be edited.")
        return redirect('petrol:purchase_list')
    if not _can_manage_petrol(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        form = FuelPurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            p = form.save(commit=False)
            p.total_amount = p.litres * p.unit_price
            p.status = 'pending'
            p.review_note = ''
            p.save()
            messages.success(request, "Purchase resubmitted for approval.")
            return redirect('petrol:purchase_list')
    else:
        form = FuelPurchaseForm(instance=purchase)
    return render(request, 'petrol/purchase_form.html', {'form': form, 'purchase': purchase})


@login_required
def purchase_approve(request, pk):
    if not _can_approve_purchase(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    purchase = get_object_or_404(FuelPurchase, pk=pk, status='pending')
    if request.method == 'POST':
        with transaction.atomic():
            purchase.status = 'approved'
            purchase.reviewed_by = request.user
            purchase.reviewed_at = timezone.now()
            purchase.save()
            purchase.tank.current_stock += purchase.litres
            purchase.tank.last_purchase_price = purchase.unit_price
            purchase.tank.save(update_fields=['current_stock', 'last_purchase_price'])
            purchase.post_to_ledger(request.user)
        messages.success(request, f"Purchase approved and posted to ledger — {purchase.litres}L from {purchase.supplier}.")
        return redirect('petrol:purchase_list')
    return redirect('petrol:purchase_list')


@login_required
def purchase_return(request, pk):
    if not _can_approve_purchase(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    purchase = get_object_or_404(FuelPurchase, pk=pk, status='pending')
    if request.method == 'POST':
        note = request.POST.get('review_note', '').strip()
        if not note:
            messages.error(request, "Please provide a note explaining what needs to be corrected.")
            return redirect('petrol:purchase_list')
        purchase.status = 'returned'
        purchase.review_note = note
        purchase.reviewed_by = request.user
        purchase.reviewed_at = timezone.now()
        purchase.save()
        messages.success(request, "Purchase returned to clerk with note.")
        return redirect('petrol:purchase_list')
    return redirect('petrol:purchase_list')


@login_required
def purchase_cancel(request, pk):
    if not _is_admin(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    purchase = get_object_or_404(FuelPurchase, pk=pk)
    if purchase.status == 'approved':
        messages.error(request, "Approved purchases cannot be cancelled.")
        return redirect('petrol:purchase_list')
    if request.method == 'POST':
        note = request.POST.get('review_note', '').strip()
        if not note:
            messages.error(request, "Please provide a cancellation reason.")
            return redirect('petrol:purchase_list')
        purchase.status = 'cancelled'
        purchase.review_note = note
        purchase.reviewed_by = request.user
        purchase.reviewed_at = timezone.now()
        purchase.save()
        messages.success(request, "Purchase cancelled.")
        return redirect('petrol:purchase_list')
    return redirect('petrol:purchase_list')


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
        customer_type = request.POST.get('customer_type', 'existing')

        if customer_type == 'new':
            new_name = request.POST.get('new_customer_name', '').strip()
            new_phone = request.POST.get('new_customer_phone', '').strip()
            if not new_name:
                messages.error(request, 'Customer name is required when adding a new customer.')
                form = CreditSaleForm(request.POST)
                return render(request, 'petrol/credit_sale_form.html', {'form': form, 'customer_type': 'new'})
            customer, _ = CreditCustomer.objects.get_or_create(
                name=new_name,
                defaults={'phone': new_phone},
            )
            post_data = request.POST.copy()
            post_data['customer'] = customer.pk
            form = CreditSaleForm(post_data)
        else:
            form = CreditSaleForm(request.POST)

        if form.is_valid():
            sale = form.save(commit=False)
            if not sale.tank.selling_price:
                messages.error(request, f"No selling price set for {sale.tank}. Ask management to set it first.")
                return render(request, 'petrol/credit_sale_form.html', {'form': form, 'customer_type': customer_type})
            with transaction.atomic():
                sale.recorded_by = request.user
                sale.unit_price = sale.tank.selling_price
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
    return render(request, 'petrol/credit_sale_form.html', {'form': form, 'customer_type': 'existing'})


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
            from sales.views import create_receipt_for_payment
            receipt, created = create_receipt_for_payment(
                request.user,
                customer_name=payment.customer.name,
                amount=payment.amount,
                against_type='petrol_credit_payment',
                against_id=payment.pk,
            )
            if created:
                return redirect('sales:receipt_print', pk=receipt.pk)
            from urllib.parse import urlencode
            qs = urlencode({'against_type': 'petrol_credit_payment', 'against_id': payment.pk, 'amount': payment.amount})
            return redirect(f'/sales/receipts/add/?{qs}')
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


# ── Tanks ─────────────────────────────────────────────────────────────────────

@login_required
def tank_list(request):
    if not _can_manage_petrol(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    tanks = Tank.objects.select_related('fuel_type').all()
    return render(request, 'petrol/tank_list.html', {'tanks': tanks})


@login_required
def tank_add(request):
    if not _can_manage_petrol(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        form = TankForm(request.POST)
        if form.is_valid():
            t = form.save()
            messages.success(request, f"Tank '{t.name}' added.")
            return redirect('petrol:tank_list')
    else:
        form = TankForm()
    return render(request, 'petrol/tank_form.html', {'form': form, 'title': 'Add Tank'})


@login_required
def tank_edit(request, pk):
    if not _can_manage_petrol(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    tank = get_object_or_404(Tank, pk=pk)
    if request.method == 'POST':
        form = TankEditForm(request.POST, instance=tank)
        if form.is_valid():
            form.save()
            messages.success(request, f"Tank '{tank.name}' updated.")
            return redirect('petrol:tank_list')
    else:
        form = TankEditForm(instance=tank)
    return render(request, 'petrol/tank_form.html', {'form': form, 'title': 'Edit Tank', 'object': tank})


# ── Fuel Suppliers ────────────────────────────────────────────────────────────

@login_required
def supplier_list(request):
    if not _can_manage_petrol(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    suppliers = FuelSupplier.objects.all()
    return render(request, 'petrol/supplier_list.html', {'suppliers': suppliers})


@login_required
def supplier_add(request):
    if not _can_manage_petrol(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        form = FuelSupplierForm(request.POST)
        if form.is_valid():
            s = form.save()
            messages.success(request, f"Supplier '{s.name}' added.")
            return redirect('petrol:supplier_list')
    else:
        form = FuelSupplierForm()
    return render(request, 'petrol/supplier_form.html', {'form': form, 'title': 'Add Fuel Supplier'})


@login_required
def supplier_edit(request, pk):
    if not _can_manage_petrol(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    supplier = get_object_or_404(FuelSupplier, pk=pk)
    if request.method == 'POST':
        form = FuelSupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{supplier.name}' updated.")
            return redirect('petrol:supplier_list')
    else:
        form = FuelSupplierForm(instance=supplier)
    return render(request, 'petrol/supplier_form.html', {'form': form, 'title': 'Edit Supplier', 'object': supplier})
