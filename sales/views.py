from datetime import date as today_date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Customer, JobOrder
from .forms import CustomerForm, JobOrderForm


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
