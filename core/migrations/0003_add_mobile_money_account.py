from django.db import migrations


def add_mobile_money(apps, schema_editor):
    Account = apps.get_model('core', 'Account')
    parent = Account.objects.filter(code='1000').first()
    Account.objects.get_or_create(
        code='1025',
        defaults={'name': 'Mobile Money', 'type': 'asset', 'parent': parent},
    )


class Migration(migrations.Migration):
    dependencies = [('core', '0002_seed_chart_of_accounts')]
    operations = [migrations.RunPython(add_mobile_money, reverse_code=migrations.RunPython.noop)]
