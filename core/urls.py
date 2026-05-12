from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('users/',              views.user_list, name='user_list'),
    path('users/add/',          views.user_add,  name='user_add'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('accounts/',       views.account_list, name='account_list'),
    path('employees/',      views.employee_list, name='employee_list'),
    path('employees/add/',  views.employee_add,  name='employee_add'),
    path('salaries/',       views.salary_list,   name='salary_list'),
    path('salaries/add/',   views.salary_add,    name='salary_add'),
    # Petty cash
    path('petty-cash/',             views.petty_cash_list,      name='petty_cash_list'),
    path('petty-cash/add/',         views.petty_cash_add,       name='petty_cash_add'),
    path('petty-cash/<int:pk>/',    views.petty_cash_detail,    name='petty_cash_detail'),
    path('petty-cash/statement/',   views.petty_cash_statement, name='petty_cash_statement'),
    # Master data
    path('accounts/add/',            views.account_add,       name='account_add'),
    path('accounts/<int:pk>/edit/',  views.account_edit,      name='account_edit'),
    path('settings/',                views.business_settings, name='business_settings'),
    path('management/',              views.management_hub,    name='management_hub'),
]
