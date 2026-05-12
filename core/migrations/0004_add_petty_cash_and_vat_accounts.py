from django.db import migrations


NEW_ACCOUNTS = [
    # (code, name, type, parent_code)
    ('1030', 'Petty Cash',                  'asset',     '1000'),
    ('1350', 'VAT Receivable',              'asset',     '1000'),
    ('2200', 'VAT Payable',                 'liability', '2000'),
    ('5190', 'Miscellaneous Petty Expenses','expense',   '5100'),
]


def add_accounts(apps, schema_editor):
    Account = apps.get_model('core', 'Account')
    for code, name, acct_type, parent_code in NEW_ACCOUNTS:
        parent = Account.objects.filter(code=parent_code).first()
        Account.objects.get_or_create(
            code=code,
            defaults={'name': name, 'type': acct_type, 'parent': parent},
        )


def remove_accounts(apps, schema_editor):
    codes = [code for code, *_ in NEW_ACCOUNTS]
    apps.get_model('core', 'Account').objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0003_add_mobile_money_account')]
    operations = [migrations.RunPython(add_accounts, reverse_code=remove_accounts)]
