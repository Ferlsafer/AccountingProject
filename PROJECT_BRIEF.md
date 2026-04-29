# Project Brief: TLC Accounting System

## Context
I'm a solo developer building a Django accounting system for a client who runs a petrol station and a cargo transportation business in Mbeya, Tanzania. I have 5 days to build a demo, then 5 days to refine after a client presentation. You (Claude Code) are my only collaborator. Speed matters, but rework matters more — I'd rather you pause and ask than guess wrong and force me to debug.

## Hard rules — read before every task

1. **Do not over-engineer.** No microservices, no Celery, no Redis, no Docker, no DRF, no custom user model, no abstract base classes "for the future." Plain Django, function-based or simple class-based views, Django templates, SQLite.
2. **Stop and ask if a requirement is ambiguous.** Do not invent business logic. If you're unsure whether a fuel sale should reduce tank stock automatically, ask. If you're unsure what fields an invoice needs, ask.
3. **One vertical slice at a time.** Finish a feature end-to-end (model → migration → form → view → URL → template → manually testable) before starting the next. Do not generate 15 models then 15 views then 15 templates.
4. **Commit-sized changes.** After each working feature, tell me "this is a good point to commit" and summarize what changed.
5. **Run migrations and check imports before declaring something done.** Do not say "done" without verifying the dev server starts and the page renders.
6. **Reuse Django built-ins.** Use Django auth, Django admin, Django messages framework, Django forms. Do not reinvent these.
7. **Match the existing structure.** Once I have a pattern (e.g., how I name templates, how I structure views), follow it. Do not introduce new patterns mid-project.
8. **No JavaScript frameworks.** Vanilla JS only, sparingly. HTMX is allowed if a feature genuinely needs it (probably won't).

## Tech stack
- Python 3.11+, Django 5.x, SQLite (dev), Bootstrap 5 via CDN, vanilla JS, Django admin for low-frequency CRUD.

## Project structure
```
accounting_system/
├── accounting_system/   # settings, root urls
├── core/                # Business, UserProfile, Account, JournalEntry, JournalLine, Employee, SalaryPayment
├── petrol/              # FuelType, Tank, DailyFuelSale, FuelSupplier, FuelPurchase, CreditCustomer, CreditSale, PetrolExpense
├── cargo/               # Vehicle, Driver, CargoCustomer, Trip, TripExpense, VehicleExpense, Invoice
├── reports/             # Dashboard + reports views (no models)
├── templates/
│   ├── base.html
│   ├── core/
│   ├── petrol/
│   ├── cargo/
│   └── reports/
├── static/
└── manage.py
```

## Modules to build

### Core
- `Business` (singleton: name, TIN, address, base_currency choice of TZS/USD with TZS default, fiscal_year fixed Jan–Dec)
- Custom `UserProfile` extending User with role: admin, petrol_clerk, cargo_clerk, accountant
- `Account` (chart of accounts: code, name, type, parent) — seed with a basic Tanzanian-style chart in a data migration
- `JournalEntry` + `JournalLine` (double-entry ledger; every transaction posts here via `post_to_ledger()` method on the source model)
- `Employee` (name, role, monthly_salary, is_active) — basic only, NO PAYE/NSSF logic
- `SalaryPayment` (employee, month, amount, paid_date) — simple monthly entry, posts to ledger as salary expense

### Petrol Station
- FuelType (Petrol/Diesel/Kerosene), Tank, DailyFuelSale (per fuel type per day), FuelSupplier, FuelPurchase, CreditCustomer, CreditSale, CreditPayment, PetrolExpense
- Tank stock decreases on FuelSale, increases on FuelPurchase
- DailyFuelSale and CreditSale post to ledger automatically

### Cargo
- Vehicle, Driver, CargoCustomer, Trip (status: planned/in_progress/completed/cancelled), TripExpense, VehicleExpense, Invoice
- Trip has computed `total_expenses()` and `profit()` methods
- Completing a trip auto-creates an Invoice
- Invoice payment posts to ledger

### Reports (read-only views)
1. Dashboard — today's fuel sales total, today's trips, this month's profit, cash position
2. Daily Fuel Sales report (date range + fuel type filter)
3. Trip Profitability report (date range, sortable by profit)
4. Expenses by Category (combined petrol + cargo + salaries)
5. Income Statement (date range)
6. Trial Balance (proves debits = credits)
- All reports: HTML tables with totals, print-friendly CSS, no PDF export yet

## Ledger posting pattern (use this everywhere)
Every transactional model has a `post_to_ledger(user)` method. It creates one `JournalEntry` with `source_type` and `source_id` pointing back to the transaction, plus the appropriate `JournalLine` rows. Wrap in `transaction.atomic()`. Do NOT post on every save — call explicitly from views after the form is valid, or use a `post_save` signal with a guard flag. Pick one approach and stick to it across all modules; tell me which you chose and why.

## Authentication
- Django built-in auth, login required for everything except the login page
- Admin users see all menus
- Clerks see only their domain's menus (petrol_clerk sees petrol module only, etc.)
- Accountant sees reports + ledger
- Use Django groups + permissions, not a custom permission system

## Currency display
- Settings table has `base_currency` ('TZS' or 'USD'), default 'TZS'
- Custom template tag `{% currency amount %}` formats based on Business.base_currency
- All amounts stored as Decimal(15, 2) regardless

## Demo data
- Management command: `python manage.py loaddemo`
- 30 days of activity, ~90 fuel sales, ~40 trips, mixed paid/unpaid, realistic Tanzanian context (Mbeya, Dar es Salaam, Tunduma routes; TZS prices ~3,200/litre petrol; Tanzanian names)
- Idempotent — can be run multiple times safely (clear demo data first)

## Deliverable shape per session
At the end of each session, give me:
1. What was built (one paragraph)
2. How to test it manually (3–5 click steps)
3. What to do next session
4. Any decisions you made that I should review

## What I will provide each session
A specific feature to build, e.g., "Today: build the petrol module models, migrations, admin registration, and seed data."

## What you should NOT do
- Don't build all modules at once
- Don't refactor existing code unless I ask
- Don't add fields to models "just in case"
- Don't add tests for the demo build (we'll add tests in the refinement phase)
- Don't change the project structure without asking
- Don't write more than ~200 lines of code without pausing to let me review

## First task (in next message)
I'll give you the first task in the next message. Read this brief, confirm you understand by listing the 8 hard rules in your own words, and ask any clarifying questions before I assign work.