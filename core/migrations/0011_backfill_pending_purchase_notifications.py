from django.db import migrations


def backfill_notifications(apps, schema_editor):
    FuelPurchase = apps.get_model('petrol', 'FuelPurchase')
    Notification = apps.get_model('core', 'Notification')
    UserProfile = apps.get_model('core', 'UserProfile')

    pending = FuelPurchase.objects.filter(status='pending').select_related(
        'tank__fuel_type', 'supplier', 'recorded_by'
    )
    if not pending.exists():
        return

    recipients = list(
        UserProfile.objects.filter(
            role__in=('admin', 'accountant'), user__is_active=True
        ).select_related('user')
    )

    notifs = []
    for purchase in pending:
        submitted_by = purchase.recorded_by
        clerk_name = (
            submitted_by.get_full_name() or submitted_by.username
            if submitted_by else 'Unknown'
        )
        msg = (
            f"Fuel purchase request: {purchase.litres}L {purchase.tank.fuel_type} "
            f"from {purchase.supplier} — TZS {purchase.total_amount:,.0f} (by {clerk_name})"
        )
        link = '/petrol/purchases/'
        for profile in recipients:
            if submitted_by and profile.user_id == submitted_by.pk:
                continue
            notifs.append(Notification(
                recipient=profile.user,
                message=msg,
                link=link,
            ))

    if notifs:
        Notification.objects.bulk_create(notifs)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_add_notification'),
        ('petrol', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_notifications, migrations.RunPython.noop),
    ]
