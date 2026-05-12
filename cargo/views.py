from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction


def _can_manage_cargo(user):
    return user.is_staff or getattr(user, 'profile', None) and user.profile.role in ('admin', 'cargo_clerk')
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404

from core.models import Business
from .models import Trip, TripExpense, VehicleExpense, Invoice, Vehicle, Driver, CargoCustomer
from .forms import TripForm, TripExpenseForm, VehicleExpenseForm, InvoicePayForm, CargoCustomerForm, VehicleForm, DriverForm


def _date_range(request):
    today = date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to   = request.GET.get('date_to')   or today.isoformat()
    return date_from, date_to


# ── Vehicles ──────────────────────────────────────────────────────────────────

@login_required
def vehicle_list(request):
    if not _can_manage_cargo(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    vehicles = Vehicle.objects.all()
    return render(request, 'cargo/vehicle_list.html', {'vehicles': vehicles})


@login_required
def vehicle_add(request):
    if not _can_manage_cargo(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            v = form.save()
            messages.success(request, f"Vehicle '{v.plate_number}' registered.")
            return redirect('cargo:vehicle_list')
    else:
        form = VehicleForm()
    return render(request, 'cargo/vehicle_form.html', {'form': form, 'title': 'Register Vehicle'})


@login_required
def vehicle_edit(request, pk):
    if not _can_manage_cargo(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vehicle '{vehicle.plate_number}' updated.")
            return redirect('cargo:vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'cargo/vehicle_form.html', {'form': form, 'title': 'Edit Vehicle', 'object': vehicle})


# ── Drivers ───────────────────────────────────────────────────────────────────

@login_required
def driver_list(request):
    if not _can_manage_cargo(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    drivers = Driver.objects.all()
    return render(request, 'cargo/driver_list.html', {'drivers': drivers})


@login_required
def driver_add(request):
    if not _can_manage_cargo(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            d = form.save()
            messages.success(request, f"Driver '{d.name}' registered.")
            return redirect('cargo:driver_list')
    else:
        form = DriverForm()
    return render(request, 'cargo/driver_form.html', {'form': form, 'title': 'Register Driver'})


@login_required
def driver_edit(request, pk):
    if not _can_manage_cargo(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, f"Driver '{driver.name}' updated.")
            return redirect('cargo:driver_list')
    else:
        form = DriverForm(instance=driver)
    return render(request, 'cargo/driver_form.html', {'form': form, 'title': 'Edit Driver', 'object': driver})


# ── Trips ─────────────────────────────────────────────────────────────────────

@login_required
def trip_list(request):
    date_from, date_to = _date_range(request)
    status_filter = request.GET.get('status', '')

    qs = (Trip.objects
          .filter(date__gte=date_from, date__lte=date_to)
          .select_related('customer', 'vehicle', 'driver'))
    if status_filter:
        qs = qs.filter(status=status_filter)

    totals = qs.aggregate(freight=Sum('freight_amount'))
    return render(request, 'cargo/trip_list.html', {
        'trips': qs,
        'totals': totals,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        'status_choices': Trip.STATUS_CHOICES,
    })


@login_required
def trip_add(request):
    if request.method == 'POST':
        customer_type = request.POST.get('customer_type', 'existing')

        if customer_type == 'new':
            new_name = request.POST.get('new_customer_name', '').strip()
            new_phone = request.POST.get('new_customer_phone', '').strip()
            if not new_name:
                messages.error(request, 'Customer name is required when adding a new customer.')
                form = TripForm(request.POST)
                return render(request, 'cargo/trip_form.html', {'form': form, 'customer_type': 'new'})
            customer, _ = CargoCustomer.objects.get_or_create(
                name=new_name,
                defaults={'phone': new_phone},
            )
            post_data = request.POST.copy()
            post_data['customer'] = customer.pk
            form = TripForm(post_data)
        else:
            form = TripForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                trip = form.save(commit=False)
                trip.created_by = request.user
                trip.save()
            messages.success(request, f"Trip {trip} created.")
            return redirect('cargo:trip_detail', pk=trip.pk)
        customer_type_ctx = customer_type
    else:
        form = TripForm(initial={'date': date.today()})
        customer_type_ctx = 'existing'
    return render(request, 'cargo/trip_form.html', {'form': form, 'customer_type': customer_type_ctx})


@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip.objects.select_related('customer', 'vehicle', 'driver', 'created_by'), pk=pk)
    expenses = trip.expenses.select_related('recorded_by').order_by('date')
    expense_form = TripExpenseForm(initial={'date': date.today()})
    invoice = getattr(trip, 'invoice', None)
    pay_form = InvoicePayForm(instance=invoice) if invoice and not invoice.is_paid else None

    return render(request, 'cargo/trip_detail.html', {
        'trip': trip,
        'expenses': expenses,
        'expense_form': expense_form,
        'invoice': invoice,
        'pay_form': pay_form,
    })


@login_required
def trip_start(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == 'POST' and trip.status == 'planned':
        trip.status = 'in_progress'
        trip.save(update_fields=['status'])
        messages.success(request, f"Trip {trip} marked as In Progress.")
    return redirect('cargo:trip_detail', pk=pk)


@login_required
def trip_complete(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == 'POST' and trip.status == 'in_progress':
        with transaction.atomic():
            trip.status = 'completed'
            trip.save(update_fields=['status'])
            if not hasattr(trip, 'invoice'):
                Invoice.objects.create(
                    trip=trip,
                    number=f"INV-{trip.pk}-{trip.date.year}",
                    date=date.today(),
                    amount=trip.freight_amount,
                    issued_by=request.user,
                )
        messages.success(request, f"Trip completed. Invoice generated.")
    return redirect('cargo:trip_detail', pk=pk)


@login_required
def trip_cancel(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == 'POST' and trip.status in ('planned', 'in_progress'):
        trip.status = 'cancelled'
        trip.save(update_fields=['status'])
        messages.warning(request, f"Trip {trip} cancelled.")
    return redirect('cargo:trip_detail', pk=pk)


@login_required
def trip_expense_add(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == 'POST':
        form = TripExpenseForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save(commit=False)
                expense.trip = trip
                expense.recorded_by = request.user
                expense.save()
                expense.post_to_ledger(request.user)
            messages.success(request, f"Expense recorded: {expense.description} — TZS {expense.amount:,.0f}")
        else:
            messages.error(request, "Please correct the errors in the expense form.")
    return redirect('cargo:trip_detail', pk=pk)


# ── Vehicle Expenses ──────────────────────────────────────────────────────────

@login_required
def vehicle_expense_list(request):
    date_from, date_to = _date_range(request)
    vehicle_filter = request.GET.get('vehicle', '')

    qs = (VehicleExpense.objects
          .filter(date__gte=date_from, date__lte=date_to)
          .select_related('vehicle', 'recorded_by'))
    if vehicle_filter:
        qs = qs.filter(vehicle_id=vehicle_filter)

    totals = qs.aggregate(amount=Sum('amount'))
    vehicles = Vehicle.objects.filter(is_active=True)
    return render(request, 'cargo/vehicle_expense_list.html', {
        'expenses': qs,
        'totals': totals,
        'vehicles': vehicles,
        'vehicle_filter': vehicle_filter,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def vehicle_expense_add(request):
    if request.method == 'POST':
        form = VehicleExpenseForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save(commit=False)
                expense.recorded_by = request.user
                expense.save()
                expense.post_to_ledger(request.user)
            messages.success(request, f"Vehicle expense recorded: {expense.description} — TZS {expense.amount:,.0f}")
            return redirect('cargo:vehicle_expense_list')
    else:
        form = VehicleExpenseForm(initial={'date': date.today()})
    return render(request, 'cargo/vehicle_expense_form.html', {'form': form})


# ── Cargo Customers ───────────────────────────────────────────────────────────

@login_required
def customer_list(request):
    customers = CargoCustomer.objects.all()
    return render(request, 'cargo/customer_list.html', {'customers': customers})


@login_required
def customer_add(request):
    if request.method == 'POST':
        form = CargoCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.name}' added.")
            return redirect('cargo:customer_list')
    else:
        form = CargoCustomerForm()
    return render(request, 'cargo/customer_form.html', {'form': form})


# ── Invoices ──────────────────────────────────────────────────────────────────

@login_required
def invoice_list(request):
    date_from, date_to = _date_range(request)
    paid_filter = request.GET.get('paid', '')

    qs = (Invoice.objects
          .filter(date__gte=date_from, date__lte=date_to)
          .select_related('trip__customer', 'trip__vehicle'))
    if paid_filter == '1':
        qs = qs.filter(is_paid=True)
    elif paid_filter == '0':
        qs = qs.filter(is_paid=False)

    totals = qs.aggregate(amount=Sum('amount'))
    paid_total   = qs.filter(is_paid=True).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    unpaid_total = qs.filter(is_paid=False).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    return render(request, 'cargo/invoice_list.html', {
        'invoices': qs,
        'totals': totals,
        'paid_total': paid_total,
        'unpaid_total': unpaid_total,
        'paid_filter': paid_filter,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('trip__customer', 'trip__vehicle', 'trip__driver', 'issued_by'),
        pk=pk,
    )
    expenses = invoice.trip.expenses.order_by('date')
    business = Business.get_solo()
    return render(request, 'cargo/invoice_print.html', {
        'invoice': invoice,
        'expenses': expenses,
        'business': business,
    })


@login_required
def invoice_pay(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, is_paid=False)
    if request.method == 'POST':
        form = InvoicePayForm(request.POST, instance=invoice)
        if form.is_valid():
            with transaction.atomic():
                inv = form.save(commit=False)
                inv.is_paid = True
                inv.paid_by = request.user
                inv.save()
                inv.post_to_ledger(request.user)
            messages.success(request, f"Invoice {invoice.number} marked as paid.")
            from sales.views import create_receipt_for_payment
            receipt, created = create_receipt_for_payment(
                request.user,
                customer_name=invoice.trip.customer.name,
                amount=invoice.amount,
                against_type='cargo_invoice',
                against_id=invoice.pk,
            )
            if created:
                return redirect('sales:receipt_print', pk=receipt.pk)
            from urllib.parse import urlencode
            qs = urlencode({'against_type': 'cargo_invoice', 'against_id': invoice.pk, 'amount': invoice.amount})
            return redirect(f'/sales/receipts/add/?{qs}')
    else:
        form = InvoicePayForm(instance=invoice)
    return render(request, 'cargo/invoice_pay_form.html', {'form': form, 'invoice': invoice})
