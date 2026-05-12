from django.urls import path
from . import views

app_name = 'petrol'

urlpatterns = [
    path('sales/',             views.daily_sale_list,    name='daily_sale_list'),
    path('sales/add/',         views.daily_sale_add,     name='daily_sale_add'),
    path('purchases/',                          views.purchase_list,     name='purchase_list'),
    path('purchases/add/',                      views.purchase_add,      name='purchase_add'),
    path('purchases/<int:pk>/edit/',            views.purchase_edit,     name='purchase_edit'),
    path('purchases/<int:pk>/approve/',         views.purchase_approve,  name='purchase_approve'),
    path('purchases/<int:pk>/return/',          views.purchase_return,   name='purchase_return'),
    path('purchases/<int:pk>/cancel/',          views.purchase_cancel,   name='purchase_cancel'),
    path('credit-sales/',      views.credit_sale_list,   name='credit_sale_list'),
    path('credit-sales/add/',  views.credit_sale_add,    name='credit_sale_add'),
    path('credit-payment/add/',views.credit_payment_add, name='credit_payment_add'),
    path('expenses/',          views.expense_list,       name='expense_list'),
    path('expenses/add/',      views.expense_add,        name='expense_add'),
    path('tanks/',                   views.tank_list,     name='tank_list'),
    path('tanks/add/',               views.tank_add,      name='tank_add'),
    path('tanks/<int:pk>/edit/',     views.tank_edit,     name='tank_edit'),
    path('suppliers/',               views.supplier_list, name='supplier_list'),
    path('suppliers/add/',           views.supplier_add,  name='supplier_add'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
]
