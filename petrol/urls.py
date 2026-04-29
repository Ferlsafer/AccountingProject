from django.urls import path
from . import views

app_name = 'petrol'

urlpatterns = [
    path('sales/',             views.daily_sale_list,    name='daily_sale_list'),
    path('sales/add/',         views.daily_sale_add,     name='daily_sale_add'),
    path('purchases/',         views.purchase_list,      name='purchase_list'),
    path('purchases/add/',     views.purchase_add,       name='purchase_add'),
    path('credit-sales/',      views.credit_sale_list,   name='credit_sale_list'),
    path('credit-sales/add/',  views.credit_sale_add,    name='credit_sale_add'),
    path('credit-payment/add/',views.credit_payment_add, name='credit_payment_add'),
    path('expenses/',          views.expense_list,       name='expense_list'),
    path('expenses/add/',      views.expense_add,        name='expense_add'),
]
