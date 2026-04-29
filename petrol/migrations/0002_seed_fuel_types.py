from django.db import migrations


def seed_fuel_types(apps, schema_editor):
    FuelType = apps.get_model('petrol', 'FuelType')
    for name in ['Petrol', 'Diesel', 'Kerosene']:
        FuelType.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [('petrol', '0001_initial')]
    operations = [migrations.RunPython(seed_fuel_types, reverse_code=migrations.RunPython.noop)]
