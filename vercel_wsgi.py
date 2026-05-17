import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accounting_system.settings')

from accounting_system.wsgi import application

app = application
