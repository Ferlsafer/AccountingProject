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
]
