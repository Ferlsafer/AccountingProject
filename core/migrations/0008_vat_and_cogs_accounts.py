from django.db import migrations


def add_accounts(apps, schema_editor):
    Account = apps.get_model('core', 'Account')
    current_assets = Account.objects.filter(code='1000').first()
    liabilities    = Account.objects.filter(code='2000').first()
    expenses       = Account.objects.filter(code='5000').first()

    Account.objects.get_or_create(
        code='1140',
        defaults={'name': 'Input VAT Recoverable', 'type': 'asset', 'parent': current_assets},
    )
    Account.objects.get_or_create(
        code='2030',
        defaults={'name': 'VAT Payable', 'type': 'liability', 'parent': liabilities},
    )
    Account.objects.get_or_create(
        code='5050',
        defaults={'name': 'Cost of Fuel Sold', 'type': 'expense', 'parent': expenses},
    )


def remove_accounts(apps, schema_editor):
    Account = apps.get_model('core', 'Account')
    Account.objects.filter(code__in=['1140', '2030', '5050']).delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0007_mobile_money_accounts')]
    operations = [migrations.RunPython(add_accounts, remove_accounts)]
