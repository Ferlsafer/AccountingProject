from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('ledger/',            views.journal_ledger,   name='journal_ledger'),
    path('fuel/',              views.fuel_report,      name='fuel_report'),
    path('trips/',             views.trip_report,      name='trip_report'),
    path('expenses/',          views.expense_report,   name='expense_report'),
    path('income-statement/',  views.income_statement, name='income_statement'),
    path('trial-balance/',     views.trial_balance,    name='trial_balance'),
]
