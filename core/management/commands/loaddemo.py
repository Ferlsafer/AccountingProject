import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Account, Business, Employee, SalaryPayment
from petrol.models import (CreditCustomer, CreditPayment, CreditSale,
                            DailyFuelSale, FuelPurchase, FuelSupplier,
                            FuelType, PetrolExpense, Tank)
from cargo.models import (CargoCustomer, Driver, Invoice, Trip, TripExpense,
                           Vehicle, VehicleExpense)

ACCOUNTS = [
    ('1000', 'Current Assets',              'asset',     None),
    ('1010', 'Cash on Hand',                'asset',     '1000'),
    ('1020', 'Bank Account',                'asset',     '1000'),
    ('1025', 'Mobile Money',                'asset',     '1000'),
    ('1100', 'Accounts Receivable',         'asset',     None),
    ('1110', 'Fuel Credit Customers',       'asset',     '1100'),
    ('1120', 'Cargo Credit Customers',      'asset',     '1100'),
    ('1200', 'Inventory',                   'asset',     None),
    ('1210', 'Petrol Stock',                'asset',     '1200'),
    ('1220', 'Diesel Stock',                'asset',     '1200'),
    ('1230', 'Kerosene Stock',              'asset',     '1200'),
    ('1300', 'Fixed Assets',                'asset',     None),
    ('1310', 'Vehicles',                    'asset',     '1300'),
    ('1320', 'Equipment',                   'asset',     '1300'),
    ('1390', 'Accumulated Depreciation',    'asset',     '1300'),
    ('2000', 'Current Liabilities',         'liability', None),
    ('2010', 'Accounts Payable',            'liability', '2000'),
    ('2020', 'Fuel Supplier Payable',       'liability', '2000'),
    ('2030', 'Accrued Salaries',            'liability', '2000'),
    ('2100', 'Long-term Liabilities',       'liability', None),
    ('2110', 'Loans Payable',               'liability', '2100'),
    ("3000", "Owner's Equity",              'equity',    None),
    ("3010", "Owner's Capital",             'equity',    '3000'),
    ("3020", 'Retained Earnings',           'equity',    '3000'),
    ('4000', 'Revenue',                     'revenue',   None),
    ('4010', 'Petrol Sales Revenue',        'revenue',   '4000'),
    ('4020', 'Diesel Sales Revenue',        'revenue',   '4000'),
    ('4030', 'Kerosene Sales Revenue',      'revenue',   '4000'),
    ('4040', 'Cargo Transport Revenue',     'revenue',   '4000'),
    ('4050', 'Other Revenue',               'revenue',   '4000'),
    ('5000', 'Cost of Sales',               'expense',   None),
    ('5010', 'Fuel Purchases (COGS)',       'expense',   '5000'),
    ('5100', 'Operating Expenses',          'expense',   None),
    ('5110', 'Salaries & Wages',            'expense',   '5100'),
    ('5120', 'Vehicle Fuel & Maintenance',  'expense',   '5100'),
    ('5130', 'Trip Expenses',               'expense',   '5100'),
    ('5140', 'Petrol Station Expenses',     'expense',   '5100'),
    ('5150', 'Office & Admin Expenses',     'expense',   '5100'),
    ('5160', 'Utilities',                   'expense',   '5100'),
    ('5170', 'Rent Expense',                'expense',   '5100'),
]


def _d(amount_int):
    return Decimal(str(amount_int))


def _prev_month_first(today, n=1):
    month = today.month - n
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


class Command(BaseCommand):
    help = 'Reset the database and load 30 days of realistic TBC demo data'

    def handle(self, *args, **options):
        self.stdout.write('Flushing database...')
        call_command('flush', '--no-input', verbosity=0)

        random.seed(42)
        today = date.today()

        with transaction.atomic():
            self.stdout.write('  Building chart of accounts...')
            admin = self._setup_base(today)

            self.stdout.write('  Loading petrol station data (30 days)...')
            tanks = self._setup_petrol(admin, today)

            self.stdout.write('  Loading cargo trips & expenses (40 trips)...')
            self._setup_cargo(admin, today)

            self.stdout.write('  Recording salary payments (2 months)...')
            self._setup_salaries(admin, today)

        self.stdout.write(self.style.SUCCESS(
            '\nDemo data loaded successfully!'
            '\n  URL: http://127.0.0.1:8000/'
            '\n'
            '\n  User          Password    Role'
            '\n  admin         admin1234   Admin (full access)'
            '\n  accountant    demo1234    Accountant'
            '\n  petrol        demo1234    Petrol Clerk'
            '\n  cargo         demo1234    Cargo Clerk'
        ))

    # ── Base: accounts, business, admin user ──────────────────────────────────

    def _setup_base(self, today):
        created = {}
        for code, name, acct_type, parent_code in ACCOUNTS:
            obj = Account.objects.create(
                code=code, name=name, type=acct_type,
                parent=created.get(parent_code),
            )
            created[code] = obj

        Business.objects.create(
            pk=1,
            name='TBC',
            tin='TZA-123456-A',
            address='Mbeya, Tanzania',
            phone='+255 23 250 0000',
            base_currency='TZS',
        )

        admin = User.objects.create_superuser('admin', 'admin@tbc.co.tz', 'admin1234')
        admin.first_name = 'System'
        admin.last_name = 'Admin'
        admin.save()
        admin.profile.role = 'admin'
        admin.profile.save()

        # Demo accounts for each role
        for username, first, last, role in [
            ('petrol',     'Juma',    'Petrol',   'petrol_clerk'),
            ('cargo',      'Salim',   'Cargo',    'cargo_clerk'),
            ('accountant', 'Amina',   'Finance',  'accountant'),
        ]:
            u = User.objects.create_user(username, f'{username}@tbc.co.tz', 'demo1234')
            u.first_name = first
            u.last_name = last
            u.save()
            u.profile.role = role
            u.profile.save()

        return admin

    # ── Petrol station ────────────────────────────────────────────────────────

    def _setup_petrol(self, admin, today):
        petrol   = FuelType.objects.create(name='Petrol')
        diesel   = FuelType.objects.create(name='Diesel')
        kerosene = FuelType.objects.create(name='Kerosene')

        tank_p = Tank.objects.create(name='Tank A — Petrol',   fuel_type=petrol,   capacity=_d(20000), current_stock=_d(0))
        tank_d = Tank.objects.create(name='Tank B — Diesel',   fuel_type=diesel,   capacity=_d(30000), current_stock=_d(0))
        tank_k = Tank.objects.create(name='Tank C — Kerosene', fuel_type=kerosene, capacity=_d(10000), current_stock=_d(0))

        puma = FuelSupplier.objects.create(
            name='Puma Energy Tanzania Ltd',
            contact_person='Salim Mwangi',
            phone='+255 22 219 4000',
        )
        FuelSupplier.objects.create(
            name='Oryx Energies Tanzania',
            contact_person='Amina Haule',
            phone='+255 22 219 5000',
        )

        # Credit customers
        c1 = CreditCustomer.objects.create(name='Mbozi District Council', phone='+255 25 240 0001', credit_limit=_d(10000000))
        c2 = CreditCustomer.objects.create(name='Jikokoa Cooperative',    phone='+255 25 240 0002', credit_limit=_d(5000000))
        c3 = CreditCustomer.objects.create(name='TBC Mining Co',          phone='+255 25 240 0003', credit_limit=_d(8000000))
        credit_custs = [c1, c2, c3]

        # ── Fuel purchases ─────────────────────────────────────────────────────
        PURCHASES = [
            # (day_ago, tank, litres, unit_price, method)
            (29, tank_p, _d(20000), _d(2800), 'bank'),
            (29, tank_d, _d(30000), _d(2700), 'bank'),
            (29, tank_k, _d(10000), _d(2400), 'bank'),
            (14, tank_p, _d(15000), _d(2820), 'cash'),
            (14, tank_d, _d(20000), _d(2720), 'cash'),
            ( 3, tank_d, _d(10000), _d(2730), 'mobile'),
        ]
        for day_ago, tank, litres, unit_price, method in PURCHASES:
            fp = FuelPurchase.objects.create(
                date=today - timedelta(days=day_ago),
                supplier=puma, tank=tank,
                litres=litres, unit_price=unit_price,
                total_amount=litres * unit_price,
                payment_method=method,
                invoice_number=f'PI-{day_ago}-{tank.pk}',
                recorded_by=admin,
            )
            tank.current_stock += litres
            tank.save(update_fields=['current_stock'])
            fp.post_to_ledger(admin)

        # ── Daily cash fuel sales (30 days) ────────────────────────────────────
        P_PRICE = _d(3200)
        D_PRICE = _d(3100)
        K_PRICE = _d(2800)

        for i in range(30):
            d = today - timedelta(days=29 - i)

            for _ in range(2):
                litres = _d(random.randrange(200, 560, 10))
                if tank_p.current_stock >= litres:
                    sale = DailyFuelSale.objects.create(
                        date=d, tank=tank_p, litres_sold=litres,
                        unit_price=P_PRICE, total_amount=litres * P_PRICE,
                        recorded_by=admin,
                    )
                    tank_p.current_stock -= litres
                    tank_p.save(update_fields=['current_stock'])
                    sale.post_to_ledger(admin)

            for _ in range(2):
                litres = _d(random.randrange(300, 760, 10))
                if tank_d.current_stock >= litres:
                    sale = DailyFuelSale.objects.create(
                        date=d, tank=tank_d, litres_sold=litres,
                        unit_price=D_PRICE, total_amount=litres * D_PRICE,
                        recorded_by=admin,
                    )
                    tank_d.current_stock -= litres
                    tank_d.save(update_fields=['current_stock'])
                    sale.post_to_ledger(admin)

            if i % 4 == 0:
                litres = _d(random.randrange(100, 310, 10))
                if tank_k.current_stock >= litres:
                    sale = DailyFuelSale.objects.create(
                        date=d, tank=tank_k, litres_sold=litres,
                        unit_price=K_PRICE, total_amount=litres * K_PRICE,
                        recorded_by=admin,
                    )
                    tank_k.current_stock -= litres
                    tank_k.save(update_fields=['current_stock'])
                    sale.post_to_ledger(admin)

        # ── Credit sales ───────────────────────────────────────────────────────
        CREDIT_DAYS = [27, 24, 20, 16, 12, 9, 6, 3]
        for idx, day_ago in enumerate(CREDIT_DAYS):
            cust = credit_custs[idx % 3]
            litres = _d(random.randrange(500, 2010, 50))
            if tank_d.current_stock >= litres:
                cs = CreditSale.objects.create(
                    date=today - timedelta(days=day_ago),
                    customer=cust, tank=tank_d,
                    litres=litres, unit_price=D_PRICE,
                    total_amount=litres * D_PRICE,
                    recorded_by=admin,
                )
                tank_d.current_stock -= litres
                tank_d.save(update_fields=['current_stock'])
                cust.current_balance += cs.total_amount
                cust.save(update_fields=['current_balance'])
                cs.post_to_ledger(admin)

        # ── Credit payments ────────────────────────────────────────────────────
        for day_ago, cust, amount in [
            (18, c1, _d(2500000)),
            (10, c2, _d(1800000)),
            ( 4, c1, _d(3000000)),
        ]:
            cp = CreditPayment.objects.create(
                date=today - timedelta(days=day_ago),
                customer=cust, amount=amount,
                reference=f'REC-2026-{day_ago:03d}',
                recorded_by=admin,
            )
            cust.current_balance -= amount
            cust.save(update_fields=['current_balance'])
            cp.post_to_ledger(admin)

        # ── Petrol station expenses ────────────────────────────────────────────
        for day_ago, desc, cat, amount in [
            (26, 'Pump maintenance service',     'maintenance', 280000),
            (22, 'Safety equipment purchase',    'supplies',    150000),
            (19, 'Water bills',                  'utilities',    85000),
            (15, 'Generator service',            'maintenance', 195000),
            (12, 'Station cleaning supplies',    'supplies',     45000),
            ( 8, 'Electricity bill — April',     'utilities',   210000),
            ( 5, 'Fire extinguisher refill',     'supplies',     70000),
            ( 2, 'Signage & branding update',    'other',       320000),
        ]:
            pe = PetrolExpense.objects.create(
                date=today - timedelta(days=day_ago),
                description=desc, category=cat,
                amount=_d(amount), recorded_by=admin,
            )
            pe.post_to_ledger(admin)

        return (tank_p, tank_d, tank_k)

    # ── Cargo: vehicles, drivers, customers, trips ────────────────────────────

    def _setup_cargo(self, admin, today):
        v1 = Vehicle.objects.create(plate_number='T 123 ABC', make='Scania',   model='R450',   year=2019)
        v2 = Vehicle.objects.create(plate_number='T 456 DEF', make='Volvo',    model='FH 460', year=2020)
        v3 = Vehicle.objects.create(plate_number='T 789 GHI', make='Mercedes', model='Actros', year=2018)
        vehicles = [v1, v2, v3]

        d1 = Driver.objects.create(name='Mohamed Ally',  phone='+255 754 100 001', license_number='TZ-DL-11001')
        d2 = Driver.objects.create(name='John Mwaisela', phone='+255 754 100 002', license_number='TZ-DL-11002')
        d3 = Driver.objects.create(name='Saidi Chuma',   phone='+255 754 100 003', license_number='TZ-DL-11003')
        d4 = Driver.objects.create(name='Baraka Mushi',  phone='+255 754 100 004', license_number='TZ-DL-11004')
        drivers = [d1, d2, d3, d4]

        cc1 = CargoCustomer.objects.create(name='CRDB Bank Logistics',   phone='+255 22 211 2222')
        cc2 = CargoCustomer.objects.create(name='Azam Industries Ltd',   phone='+255 22 217 0000')
        cc3 = CargoCustomer.objects.create(name='MeTL Group Tanzania',   phone='+255 22 213 3000')
        cc4 = CargoCustomer.objects.create(name='Dar Commodities Ltd',   phone='+255 22 215 5555')
        cc5 = CargoCustomer.objects.create(name='Tunduma Border Traders',phone='+255 25 250 1111')
        customers = [cc1, cc2, cc3, cc4, cc5]

        # (origin, destination, freight_min, freight_max)
        ROUTES = [
            ('Mbeya',        'Dar es Salaam', 1800000, 2800000),
            ('Mbeya',        'Tunduma',        700000, 1100000),
            ('Mbeya',        'Dodoma',        1200000, 1800000),
            ('Mbeya',        'Iringa',         900000, 1400000),
            ('Mbeya',        'Songea',        1000000, 1600000),
            ('Dar es Salaam','Mbeya',         1900000, 2900000),
            ('Mbeya',        'Arusha',        2200000, 3200000),
            ('Mbeya',        'Njombe',         700000, 1050000),
        ]
        CARGOS = [
            'Building materials (cement, steel)',
            'Consumer goods (foodstuffs)',
            'Agricultural produce (maize)',
            'Electronics and appliances',
            'Petroleum products',
            'Textiles and clothing',
            'Medical supplies',
            'Industrial machinery',
        ]
        TRIP_EXP = [
            # (category, description, min, max)
            ('fuel',             'Diesel fuel en route',   250000, 600000),
            ('toll',             'Weighbridge & toll fees',  80000, 200000),
            ('driver_allowance', 'Driver road allowance',    50000, 150000),
            ('loading',          'Loading & offloading fee', 40000, 120000),
        ]

        # (day_ago, final_status)
        SCHEDULE = [
            (29, 'completed'), (28, 'completed'), (27, 'completed'),
            (26, 'completed'), (25, 'completed'), (24, 'completed'),
            (23, 'completed'), (22, 'completed'), (21, 'cancelled'),
            (20, 'completed'), (19, 'completed'), (18, 'completed'),
            (17, 'completed'), (16, 'completed'), (15, 'completed'),
            (14, 'completed'), (13, 'completed'), (12, 'cancelled'),
            (11, 'completed'), (10, 'completed'), ( 9, 'completed'),
            ( 8, 'completed'), ( 7, 'completed'), ( 6, 'completed'),
            ( 5, 'completed'), ( 4, 'completed'), ( 3, 'completed'),
            ( 2, 'in_progress'),( 2, 'in_progress'),( 1, 'in_progress'),
            ( 1, 'in_progress'),( 1, 'planned'),   ( 0, 'planned'),
            ( 0, 'planned'),
            # extra completed for volume
            (29, 'completed'), (26, 'completed'), (22, 'completed'),
            (18, 'completed'), (14, 'completed'), (10, 'completed'),
            ( 7, 'completed'),
        ]

        for idx, (day_ago, status) in enumerate(SCHEDULE):
            trip_date = today - timedelta(days=day_ago)
            origin, dest, fmin, fmax = ROUTES[idx % len(ROUTES)]
            freight = _d((random.randint(fmin, fmax) // 50000) * 50000)

            trip = Trip.objects.create(
                vehicle=vehicles[idx % len(vehicles)],
                driver=drivers[idx % len(drivers)],
                customer=customers[idx % len(customers)],
                origin=origin, destination=dest,
                date=trip_date,
                cargo_description=CARGOS[idx % len(CARGOS)],
                freight_amount=freight,
                status=status,
                created_by=admin,
            )

            if status in ('completed', 'in_progress'):
                n_exp = random.randint(2, 4)
                for cat, desc, emin, emax in TRIP_EXP[:n_exp]:
                    exp_d = min(trip_date + timedelta(days=random.randint(0, 2)), today)
                    exp = TripExpense.objects.create(
                        trip=trip, description=desc,
                        amount=_d((random.randint(emin, emax) // 5000) * 5000),
                        category=cat, date=exp_d, recorded_by=admin,
                    )
                    exp.post_to_ledger(admin)

            if status == 'completed':
                inv_date = min(trip_date + timedelta(days=random.randint(0, 2)), today)
                inv = Invoice.objects.create(
                    trip=trip,
                    number=f'INV-{trip.pk:04d}-{trip_date.year}',
                    date=inv_date,
                    amount=freight,
                    issued_by=admin,
                )
                # Trips 8+ days old: always paid; last 7 days: unpaid (to demo AR workflow)
                should_pay = day_ago >= 8
                if should_pay:
                    paid_date = min(inv_date + timedelta(days=random.randint(1, 4)), today)
                    method = random.choice(['cash', 'bank', 'mobile'])
                    inv.is_paid = True
                    inv.paid_date = paid_date
                    inv.payment_method = method
                    inv.paid_by = admin
                    inv.save()
                    inv.post_to_ledger(admin)

        # ── Vehicle expenses ───────────────────────────────────────────────────
        for day_ago, veh, desc, cat, amount in [
            (27, v1, 'Engine oil change',         'maintenance', 180000),
            (23, v2, 'Tyre replacement x2',       'tyre',        650000),
            (20, v1, 'Brake pad replacement',     'repair',      320000),
            (17, v3, 'Annual insurance premium',  'insurance',  1200000),
            (14, v2, 'Fuel filter change',        'maintenance',  85000),
            (11, v3, 'Alternator repair',         'repair',      410000),
            ( 8, v1, 'Front suspension service',  'maintenance', 275000),
            ( 5, v2, 'Windscreen replacement',    'repair',      480000),
            ( 3, v3, 'Routine service & wash',    'maintenance', 220000),
        ]:
            ve = VehicleExpense.objects.create(
                vehicle=veh, description=desc, category=cat,
                amount=_d(amount), date=today - timedelta(days=day_ago),
                recorded_by=admin,
            )
            ve.post_to_ledger(admin)

    # ── Employees and salary payments ─────────────────────────────────────────

    def _setup_salaries(self, admin, today):
        STAFF = [
            ('Emmanuel Mwangi', 'General Manager',   1400000),
            ('Amina Hassan',    'Accountant',          950000),
            ('Joseph Mbeki',    'Cashier',             580000),
            ('Halima Juma',     'Petrol Attendant',    480000),
            ('Rashidi Ally',    'Cargo Supervisor',    720000),
            ('Grace Nyambura',  'Petrol Attendant',    480000),
        ]
        employees = [
            Employee.objects.create(
                name=name, role=role,
                monthly_salary=_d(salary),
                hire_date=today - timedelta(days=random.randint(180, 900)),
                is_active=True,
            )
            for name, role, salary in STAFF
        ]

        for n_ago in [2, 1, 0]:
            month_first = _prev_month_first(today, n_ago)
            paid_date = month_first.replace(day=28)
            if paid_date > today:        # current month: use a recent date
                paid_date = today - timedelta(days=2)
            for emp in employees:
                sp = SalaryPayment.objects.create(
                    employee=emp,
                    month=month_first,
                    amount=emp.monthly_salary,
                    paid_date=paid_date,
                    posted_by=admin,
                )
                sp.post_to_ledger(admin)
