from django.urls import path
from . import views

app_name = 'cargo'

urlpatterns = [
    path('vehicles/',                views.vehicle_list, name='vehicle_list'),
    path('vehicles/add/',            views.vehicle_add,  name='vehicle_add'),
    path('vehicles/<int:pk>/edit/',  views.vehicle_edit, name='vehicle_edit'),
    path('drivers/',                 views.driver_list,  name='driver_list'),
    path('drivers/add/',             views.driver_add,   name='driver_add'),
    path('drivers/<int:pk>/edit/',   views.driver_edit,  name='driver_edit'),
    path('trips/',                         views.trip_list,            name='trip_list'),
    path('trips/add/',                     views.trip_add,             name='trip_add'),
    path('trips/<int:pk>/',               views.trip_detail,          name='trip_detail'),
    path('trips/<int:pk>/start/',         views.trip_start,           name='trip_start'),
    path('trips/<int:pk>/complete/',      views.trip_complete,        name='trip_complete'),
    path('trips/<int:pk>/cancel/',        views.trip_cancel,          name='trip_cancel'),
    path('trips/<int:pk>/expense/add/',   views.trip_expense_add,     name='trip_expense_add'),
    path('vehicle-expenses/',             views.vehicle_expense_list, name='vehicle_expense_list'),
    path('vehicle-expenses/add/',         views.vehicle_expense_add,  name='vehicle_expense_add'),
    path('customers/',                    views.customer_list,        name='customer_list'),
    path('customers/add/',               views.customer_add,         name='customer_add'),
    path('invoices/',                      views.invoice_list,         name='invoice_list'),
    path('invoices/<int:pk>/pay/',         views.invoice_pay,          name='invoice_pay'),
    path('invoices/<int:pk>/print/',       views.invoice_print,        name='invoice_print'),
]
