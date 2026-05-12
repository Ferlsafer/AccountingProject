from datetime import date as today_date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Customer, JobOrder, Quotation, DeliveryNote
from .forms import CustomerForm, JobOrderForm, QuotationForm, QuotationLineFormSet, DeliveryNoteForm


@login_required
def customer_list(request):
    q = request.GET.get('q', '').strip()
    qs = Customer.objects.all()
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(phone__icontains=q)
    return render(request, 'sales/customer_list.html', {'customers': qs, 'q': q})


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.name}' added.")
            return redirect('sales:customer_list')
    else:
        form = CustomerForm()
    return render(request, 'sales/customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Customer '{customer.name}' updated.")
            return redirect('sales:customer_detail', pk=pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'sales/customer_form.html', {'form': form, 'title': 'Edit Customer', 'customer': customer})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'sales/customer_detail.html', {'customer': customer})


# ── Job Orders ────────────────────────────────────────────────────────────────

# Valid forward transitions only
_JOB_TRANSITIONS = {
    'draft':       ['quoted', 'cancelled'],
    'quoted':      ['accepted', 'cancelled'],
    'accepted':    ['in_progress', 'cancelled'],
    'in_progress': ['completed', 'cancelled'],
    'completed':   [],
    'cancelled':   [],
}


@login_required
def job_order_list(request):
    today = today_date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to = request.GET.get('date_to') or today.isoformat()
    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()

    qs = (JobOrder.objects
          .filter(date__gte=date_from, date__lte=date_to)
          .select_related('customer', 'created_by'))
    if status_filter:
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(customer__name__icontains=q)

    return render(request, 'sales/job_order_list.html', {
        'job_orders': qs,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        'q': q,
        'status_choices': JobOrder.STATUS_CHOICES,
    })


@login_required
def job_order_create(request):
    if request.method == 'POST':
        form = JobOrderForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            messages.success(request, f"Job Order {job.reference} created.")
            return redirect('sales:job_order_detail', pk=job.pk)
    else:
        form = JobOrderForm(initial={'date': today_date.today()})
    return render(request, 'sales/job_order_form.html', {'form': form, 'title': 'New Job Order'})


@login_required
def job_order_detail(request, pk):
    job = get_object_or_404(JobOrder, pk=pk)
    labels = dict(JobOrder.STATUS_CHOICES)
    allowed_next = [
        (val, labels[val]) for val in _JOB_TRANSITIONS.get(job.status, [])
    ]
    return render(request, 'sales/job_order_detail.html', {
        'job': job,
        'allowed_next': allowed_next,
    })


@login_required
def job_order_edit(request, pk):
    job = get_object_or_404(JobOrder, pk=pk)
    if job.status in ('completed', 'cancelled'):
        messages.error(request, "Completed or cancelled job orders cannot be edited.")
        return redirect('sales:job_order_detail', pk=pk)
    if request.method == 'POST':
        form = JobOrderForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"Job Order {job.reference} updated.")
            return redirect('sales:job_order_detail', pk=pk)
    else:
        form = JobOrderForm(instance=job)
    return render(request, 'sales/job_order_form.html', {'form': form, 'title': 'Edit Job Order', 'job': job})


@login_required
def job_order_transition(request, pk):
    if request.method != 'POST':
        return redirect('sales:job_order_detail', pk=pk)
    job = get_object_or_404(JobOrder, pk=pk)
    new_status = request.POST.get('status')
    allowed = _JOB_TRANSITIONS.get(job.status, [])
    if new_status not in allowed:
        messages.error(request, f"Cannot move from '{job.get_status_display()}' to '{new_status}'.")
        return redirect('sales:job_order_detail', pk=pk)
    job.status = new_status
    job.save()
    messages.success(request, f"Job Order {job.reference} moved to {job.get_status_display()}.")
    return redirect('sales:job_order_detail', pk=pk)


# ── Quotations ────────────────────────────────────────────────────────────────

_QUO_TRANSITIONS = {
    'draft':    ['sent', 'rejected'],
    'sent':     ['accepted', 'rejected', 'expired'],
    'accepted': [],
    'rejected': [],
    'expired':  [],
}


@login_required
def quotation_list(request):
    today = today_date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to = request.GET.get('date_to') or today.isoformat()
    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()

    qs = (Quotation.objects
          .filter(date__gte=date_from, date__lte=date_to)
          .select_related('customer', 'job_order', 'created_by'))
    if status_filter:
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(customer__name__icontains=q)

    return render(request, 'sales/quotation_list.html', {
        'quotations': qs,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        'q': q,
        'status_choices': Quotation.STATUS_CHOICES,
    })


@login_required
def quotation_create(request):
    if request.method == 'POST':
        form = QuotationForm(request.POST)
        formset = QuotationLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            quotation = form.save(commit=False)
            quotation.created_by = request.user
            quotation.save()
            formset.instance = quotation
            formset.save()
            messages.success(request, f"Quotation {quotation.reference} created.")
            return redirect('sales:quotation_detail', pk=quotation.pk)
    else:
        form = QuotationForm(initial={'date': today_date.today()})
        formset = QuotationLineFormSet()
    return render(request, 'sales/quotation_form.html', {
        'form': form, 'formset': formset, 'title': 'New Quotation',
    })


@login_required
def quotation_detail(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    labels = dict(Quotation.STATUS_CHOICES)
    allowed_next = [
        (val, labels[val]) for val in _QUO_TRANSITIONS.get(quotation.status, [])
    ]
    return render(request, 'sales/quotation_detail.html', {
        'quotation': quotation,
        'allowed_next': allowed_next,
    })


@login_required
def quotation_edit(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    if quotation.status in ('accepted', 'rejected', 'expired'):
        messages.error(request, "This quotation can no longer be edited.")
        return redirect('sales:quotation_detail', pk=pk)
    if request.method == 'POST':
        form = QuotationForm(request.POST, instance=quotation)
        formset = QuotationLineFormSet(request.POST, instance=quotation)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Quotation {quotation.reference} updated.")
            return redirect('sales:quotation_detail', pk=pk)
    else:
        form = QuotationForm(instance=quotation)
        formset = QuotationLineFormSet(instance=quotation)
    return render(request, 'sales/quotation_form.html', {
        'form': form, 'formset': formset,
        'title': 'Edit Quotation', 'quotation': quotation,
    })


@login_required
def quotation_transition(request, pk):
    if request.method != 'POST':
        return redirect('sales:quotation_detail', pk=pk)
    quotation = get_object_or_404(Quotation, pk=pk)
    new_status = request.POST.get('status')
    if new_status not in _QUO_TRANSITIONS.get(quotation.status, []):
        messages.error(request, "Invalid status transition.")
        return redirect('sales:quotation_detail', pk=pk)
    quotation.status = new_status
    quotation.save()
    # If accepted and linked to a job order, advance job order to 'accepted'
    if new_status == 'accepted' and quotation.job_order:
        job = quotation.job_order
        if job.status in ('draft', 'quoted'):
            job.status = 'accepted'
            job.save()
    messages.success(request, f"Quotation {quotation.reference} marked as {quotation.get_status_display()}.")
    return redirect('sales:quotation_detail', pk=pk)


@login_required
def quotation_print(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    from core.models import Business
    business = Business.objects.first()
    return render(request, 'sales/quotation_print.html', {
        'quotation': quotation,
        'business': business,
    })


# ── Delivery Notes ────────────────────────────────────────────────────────────

@login_required
def delivery_note_list(request):
    today = today_date.today()
    date_from = request.GET.get('date_from') or today.replace(day=1).isoformat()
    date_to = request.GET.get('date_to') or today.isoformat()
    q = request.GET.get('q', '').strip()

    qs = (DeliveryNote.objects
          .filter(date__gte=date_from, date__lte=date_to)
          .select_related('customer', 'trip', 'created_by'))
    if q:
        qs = qs.filter(customer__name__icontains=q)

    return render(request, 'sales/delivery_note_list.html', {
        'delivery_notes': qs,
        'date_from': date_from,
        'date_to': date_to,
        'q': q,
    })


@login_required
def delivery_note_create(request):
    from cargo.models import Trip
    trip_id = request.GET.get('trip')
    trip = None
    initial = {'date': today_date.today()}

    if trip_id:
        trip = Trip.objects.filter(pk=trip_id).select_related('driver', 'vehicle').first()
        if trip:
            initial.update({
                'trip': trip.pk,
                'origin': trip.origin,
                'destination': trip.destination,
                'cargo_description': trip.cargo_description[:255] if trip.cargo_description else '',
                'driver_name': trip.driver.name,
                'vehicle_plate': trip.vehicle.plate_number,
            })

    if request.method == 'POST':
        form = DeliveryNoteForm(request.POST)
        if form.is_valid():
            dn = form.save(commit=False)
            dn.created_by = request.user
            dn.save()
            messages.success(request, f"Delivery Note {dn.reference} created.")
            return redirect('sales:delivery_note_print', pk=dn.pk)
    else:
        form = DeliveryNoteForm(initial=initial)

    return render(request, 'sales/delivery_note_form.html', {
        'form': form, 'title': 'New Delivery Note', 'prefill_trip': trip,
    })


@login_required
def delivery_note_detail(request, pk):
    dn = get_object_or_404(DeliveryNote, pk=pk)
    return render(request, 'sales/delivery_note_detail.html', {'dn': dn})


@login_required
def delivery_note_edit(request, pk):
    dn = get_object_or_404(DeliveryNote, pk=pk)
    if request.method == 'POST':
        form = DeliveryNoteForm(request.POST, instance=dn)
        if form.is_valid():
            form.save()
            messages.success(request, f"Delivery Note {dn.reference} updated.")
            return redirect('sales:delivery_note_detail', pk=pk)
    else:
        form = DeliveryNoteForm(instance=dn)
    return render(request, 'sales/delivery_note_form.html', {
        'form': form, 'title': 'Edit Delivery Note', 'dn': dn,
    })


@login_required
def delivery_note_print(request, pk):
    dn = get_object_or_404(DeliveryNote, pk=pk)
    from core.models import Business
    business = Business.objects.first()
    return render(request, 'sales/delivery_note_print.html', {'dn': dn, 'business': business})
