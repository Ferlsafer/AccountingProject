from django.db import migrations

ACCOUNTS = [
    # (code, name, type, parent_code)
    # ── ASSETS ──────────────────────────────────────────
    ('1000', 'Current Assets',          'asset',     None),
    ('1010', 'Cash on Hand',            'asset',     '1000'),
    ('1020', 'Bank Account',            'asset',     '1000'),
    ('1100', 'Accounts Receivable',     'asset',     None),
    ('1110', 'Fuel Credit Customers',   'asset',     '1100'),
    ('1120', 'Cargo Credit Customers',  'asset',     '1100'),
    ('1200', 'Inventory',               'asset',     None),
    ('1210', 'Petrol Stock',            'asset',     '1200'),
    ('1220', 'Diesel Stock',            'asset',     '1200'),
    ('1230', 'Kerosene Stock',          'asset',     '1200'),
    ('1300', 'Fixed Assets',            'asset',     None),
    ('1310', 'Vehicles',                'asset',     '1300'),
    ('1320', 'Equipment',               'asset',     '1300'),
    ('1390', 'Accumulated Depreciation','asset',     '1300'),
    # ── LIABILITIES ─────────────────────────────────────
    ('2000', 'Current Liabilities',     'liability', None),
    ('2010', 'Accounts Payable',        'liability', '2000'),
    ('2020', 'Fuel Supplier Payable',   'liability', '2000'),
    ('2030', 'Accrued Salaries',        'liability', '2000'),
    ('2100', 'Long-term Liabilities',   'liability', None),
    ('2110', 'Loans Payable',           'liability', '2100'),
    # ── EQUITY ──────────────────────────────────────────
    ('3000', "Owner's Equity",          'equity',    None),
    ('3010', "Owner's Capital",         'equity',    '3000'),
    ('3020', 'Retained Earnings',       'equity',    '3000'),
    # ── REVENUE ─────────────────────────────────────────
    ('4000', 'Revenue',                 'revenue',   None),
    ('4010', 'Petrol Sales Revenue',    'revenue',   '4000'),
    ('4020', 'Diesel Sales Revenue',    'revenue',   '4000'),
    ('4030', 'Kerosene Sales Revenue',  'revenue',   '4000'),
    ('4040', 'Cargo Transport Revenue', 'revenue',   '4000'),
    ('4050', 'Other Revenue',           'revenue',   '4000'),
    # ── EXPENSES ────────────────────────────────────────
    ('5000', 'Cost of Sales',           'expense',   None),
    ('5010', 'Fuel Purchases (COGS)',   'expense',   '5000'),
    ('5100', 'Operating Expenses',      'expense',   None),
    ('5110', 'Salaries & Wages',        'expense',   '5100'),
    ('5120', 'Vehicle Fuel & Maintenance', 'expense', '5100'),
    ('5130', 'Trip Expenses',           'expense',   '5100'),
    ('5140', 'Petrol Station Expenses', 'expense',   '5100'),
    ('5150', 'Office & Admin Expenses', 'expense',   '5100'),
    ('5160', 'Utilities',               'expense',   '5100'),
    ('5170', 'Rent Expense',            'expense',   '5100'),
]


def seed_accounts(apps, schema_editor):
    Account = apps.get_model('core', 'Account')
    if Account.objects.exists():
        return
    created = {}
    for code, name, acct_type, parent_code in ACCOUNTS:
        parent = created.get(parent_code)
        obj = Account.objects.create(code=code, name=name, type=acct_type, parent=parent)
        created[code] = obj


def seed_business(apps, schema_editor):
    Business = apps.get_model('core', 'Business')
    if not Business.objects.filter(pk=1).exists():
        Business.objects.create(
            pk=1,
            name='TLC Business',
            tin='',
            address='Mbeya, Tanzania',
            base_currency='TZS',
        )


def reverse_seed(apps, schema_editor):
    apps.get_model('core', 'Account').objects.all().delete()
    apps.get_model('core', 'Business').objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_accounts, reverse_code=reverse_seed),
        migrations.RunPython(seed_business, reverse_code=migrations.RunPython.noop),
    ]
