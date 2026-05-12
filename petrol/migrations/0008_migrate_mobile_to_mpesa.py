from django.db import migrations


def migrate_mobile_to_mpesa(apps, schema_editor):
    FuelPurchase = apps.get_model('petrol', 'FuelPurchase')
    FuelPurchase.objects.filter(payment_method='mobile').update(payment_method='mpesa')


class Migration(migrations.Migration):
    dependencies = [('petrol', '0007_expand_payment_method_choices')]
    operations = [migrations.RunPython(migrate_mobile_to_mpesa, migrations.RunPython.noop)]
