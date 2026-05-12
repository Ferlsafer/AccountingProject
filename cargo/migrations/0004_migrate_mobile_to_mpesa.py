from django.db import migrations


def migrate_mobile_to_mpesa(apps, schema_editor):
    Invoice = apps.get_model('cargo', 'Invoice')
    Invoice.objects.filter(payment_method='mobile').update(payment_method='mpesa')


class Migration(migrations.Migration):
    dependencies = [('cargo', '0003_expand_payment_method_choices')]
    operations = [migrations.RunPython(migrate_mobile_to_mpesa, migrations.RunPython.noop)]
