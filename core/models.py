from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.contrib.auth.models import User


class Business(models.Model):
    CURRENCY_CHOICES = [
        ('TZS', 'TZS — Tanzanian Shilling'),
        ('USD', 'USD — US Dollar'),
    ]
    name = models.CharField(max_length=200)
    tin = models.CharField('TIN', max_length=50, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    base_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='TZS')

    class Meta:
        verbose_name_plural = 'Business settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton — prevent deletion

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'name': 'TLC Business'})
        return obj

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('petrol_clerk', 'Petrol Clerk'),
        ('cargo_clerk', 'Cargo Clerk'),
        ('accountant', 'Accountant'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"


class Account(models.Model):
    TYPE_CHOICES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='children'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"


class JournalEntry(models.Model):
    date = models.DateField()
    reference = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    source_type = models.CharField(max_length=50, blank=True)
    source_id = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='journal_entries')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Journal entries'
        ordering = ['-date', '-created_at']

    @property
    def total_debit(self):
        return self.lines.aggregate(t=models.Sum('debit'))['t'] or Decimal('0')

    @property
    def total_credit(self):
        return self.lines.aggregate(t=models.Sum('credit'))['t'] or Decimal('0')

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit

    def __str__(self):
        return f"{self.reference} — {self.description}"


class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_lines')
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.account} | Dr {self.debit} Cr {self.credit}"


class Employee(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100)
    monthly_salary = models.DecimalField(max_digits=15, decimal_places=2)
    phone = models.CharField(max_length=50, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SalaryPayment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='salary_payments')
    month = models.DateField(help_text='Use the first day of the month being paid')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_date = models.DateField()
    notes = models.TextField(blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='salary_payments')

    class Meta:
        unique_together = [['employee', 'month']]
        ordering = ['-month', 'employee']

    def __str__(self):
        return f"{self.employee} — {self.month.strftime('%B %Y')}"

    def _reverse_ledger_entry(self):
        JournalEntry.objects.filter(source_type='salary_payment', source_id=self.pk).delete()

    def post_to_ledger(self, user):
        self._reverse_ledger_entry()
        salary_acct = Account.objects.get(code='5110')
        cash_acct = Account.objects.get(code='1010')
        ref = f"SAL-{self.pk}-{self.month.strftime('%Y%m')}"
        entry = JournalEntry.objects.create(
            date=self.paid_date,
            reference=ref,
            description=f"Salary — {self.employee} ({self.month.strftime('%B %Y')})",
            source_type='salary_payment',
            source_id=self.pk,
            created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=salary_acct, debit=self.amount, credit=Decimal('0')),
            JournalLine(entry=entry, account=cash_acct, debit=Decimal('0'), credit=self.amount),
        ])


class PettyCashTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('inflow_from_main_cash', 'Inflow from Main Cash'),
        ('inflow_other', 'Inflow from Other Source'),
        ('expense', 'Expense'),
        ('return_to_main_cash', 'Return to Main Cash'),
    ]
    date = models.DateField()
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    expense_category = models.CharField(max_length=100, blank=True)
    expense_account = models.ForeignKey(
        Account, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='petty_cash_expenses',
    )
    description = models.TextField()
    receipt_reference = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='petty_cash_transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"PCT-{self.pk} | {self.get_transaction_type_display()} | {self.amount}"

    def clean(self):
        if not self.description:
            raise ValidationError("Description is required.")
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Amount must be positive.")

    def post_to_ledger(self, user):
        petty_cash = Account.objects.get(code='1030')
        main_cash = Account.objects.get(code='1010')
        owner_capital = Account.objects.get(code='3010')
        fallback_expense = Account.objects.get(code='5190')
        zero = Decimal('0')

        if self.transaction_type == 'inflow_from_main_cash':
            dr_acct, cr_acct = petty_cash, main_cash
        elif self.transaction_type == 'inflow_other':
            dr_acct, cr_acct = petty_cash, owner_capital
        elif self.transaction_type == 'expense':
            dr_acct = self.expense_account if self.expense_account else fallback_expense
            cr_acct = petty_cash
        elif self.transaction_type == 'return_to_main_cash':
            dr_acct, cr_acct = main_cash, petty_cash
        else:
            raise ValueError(f"Unknown transaction type: {self.transaction_type}")

        ref = f"PCT-{self.pk}-{str(self.date).replace('-', '')}"
        with transaction.atomic():
            entry = JournalEntry.objects.create(
                date=self.date,
                reference=ref,
                description=f"Petty Cash — {self.get_transaction_type_display()}: {self.description}",
                source_type='petty_cash',
                source_id=self.pk,
                created_by=user,
            )
            JournalLine.objects.bulk_create([
                JournalLine(entry=entry, account=dr_acct, debit=self.amount, credit=zero),
                JournalLine(entry=entry, account=cr_acct, debit=zero, credit=self.amount),
            ])
        assert entry.is_balanced, f"Ledger imbalance on petty cash entry {ref}"
