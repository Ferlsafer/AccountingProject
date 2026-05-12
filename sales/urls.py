from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),

    # Job Orders
    path('job-orders/',                      views.job_order_list,       name='job_order_list'),
    path('job-orders/add/',                  views.job_order_create,     name='job_order_create'),
    path('job-orders/<int:pk>/',             views.job_order_detail,     name='job_order_detail'),
    path('job-orders/<int:pk>/edit/',        views.job_order_edit,       name='job_order_edit'),
    path('job-orders/<int:pk>/transition/',  views.job_order_transition, name='job_order_transition'),
    # Quotations
    path('quotations/',                        views.quotation_list,       name='quotation_list'),
    path('quotations/add/',                    views.quotation_create,     name='quotation_create'),
    path('quotations/<int:pk>/',               views.quotation_detail,     name='quotation_detail'),
    path('quotations/<int:pk>/edit/',          views.quotation_edit,       name='quotation_edit'),
    path('quotations/<int:pk>/transition/',    views.quotation_transition, name='quotation_transition'),
    path('quotations/<int:pk>/print/',         views.quotation_print,      name='quotation_print'),
    # Step 9: delivery notes
    # Step 10: receipts
    # Step 12: unified invoices
]
