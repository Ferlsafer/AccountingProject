from django.db import migrations


def add_mobile_money_accounts(apps, schema_editor):
    Account = apps.get_model('core', 'Account')
    parent = Account.objects.filter(code='1000').first()

    # Rename the generic 1025 to the specific platform
    Account.objects.filter(code='1025').update(name='Mobile Money — M-Pesa')

    # Add the remaining platforms
    for code, name in [
        ('1026', 'Mobile Money — Yas (Tigo Pesa)'),
        ('1027', 'Mobile Money — HaloPesa'),
        ('1028', 'Mobile Money — Airtel Money'),
    ]:
        Account.objects.get_or_create(
            code=code,
            defaults={'name': name, 'type': 'asset', 'parent': parent},
        )


def reverse_mobile_money_accounts(apps, schema_editor):
    Account = apps.get_model('core', 'Account')
    Account.objects.filter(code='1025').update(name='Mobile Money')
    Account.objects.filter(code__in=['1026', '1027', '1028']).delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0006_bank_reconciliation')]
    operations = [
        migrations.RunPython(add_mobile_money_accounts, reverse_mobile_money_accounts)
    ]
