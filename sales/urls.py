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
    # Delivery Notes
    path('delivery-notes/',                   views.delivery_note_list,   name='delivery_note_list'),
    path('delivery-notes/add/',               views.delivery_note_create, name='delivery_note_create'),
    path('delivery-notes/<int:pk>/',          views.delivery_note_detail, name='delivery_note_detail'),
    path('delivery-notes/<int:pk>/edit/',     views.delivery_note_edit,   name='delivery_note_edit'),
    path('delivery-notes/<int:pk>/print/',    views.delivery_note_print,  name='delivery_note_print'),
    # Receipts
    path('receipts/',                   views.receipt_list,   name='receipt_list'),
    path('receipts/add/',               views.receipt_create, name='receipt_create'),
    path('receipts/<int:pk>/',          views.receipt_detail, name='receipt_detail'),
    path('receipts/<int:pk>/print/',    views.receipt_print,  name='receipt_print'),
    # Unified Invoices
    path('invoices/', views.unified_invoices, name='unified_invoices'),
]
