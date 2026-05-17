# TBC Management System — Client Presentation
### A Complete Business Management & Accounting Platform for Fuel and Cargo Operations

---

## Before You Present: What You Need to Know in Plain Language

This section is for you — read it carefully before the meeting. Once you understand the "why" behind each feature, you can speak confidently without sounding like you're reading a script.

### What Problem Does This System Solve?

Most petrol stations and cargo businesses in Tanzania run on a combination of:
- Manual notebooks for daily fuel sales
- WhatsApp messages to confirm deliveries
- Excel spreadsheets for expenses
- A separate accountant who tries to reconcile everything at month end

The result is: **missing money that nobody can explain, TRA filing that takes days, and a business owner who has no idea if they're profitable until they check the bank account.**

This system eliminates all of that. Every transaction — a litre of fuel sold, a truck delivering cargo, a payment received via M-Pesa — is automatically recorded in double-entry accounting the moment it happens. The accountant can see a real balance sheet in seconds, not days.

---

## 1. System Overview

**TBC Management System** is a web-based business management platform built specifically for:
- **Petrol stations** (fuel sales, credit customers, supplier purchases)
- **Cargo/transport businesses** (trips, invoices, vehicle management)
- **The accountant** who needs accurate financial reports and TRA compliance tools

It runs in a web browser — on computers, tablets, and mobile phones. Pump clerks can use it on their phones at the fuel station. The accountant uses it on a desktop. The business owner can check the dashboard from anywhere.

### What Makes It Different from Generic Accounting Software

Generic accounting software (QuickBooks, Sage, Wave) forces you to manually enter every transaction. They don't understand what a "fuel tank" or a "cargo trip" is.

This system is built **around your specific business**:
- When a fuel purchase is approved, the system automatically updates the tank's stock level AND records the bookkeeping entry — no double work
- When a cargo trip is completed, the system generates the invoice automatically
- When an M-Pesa payment is received, it knows whether it goes into the M-Pesa account or the bank account — different accounts for each mobile money platform

---

## 2. Who Uses the System and What They Can Do

The system has **four types of users**, each with exactly the access they need — nothing more, nothing less.

### Admin (Business Owner / Manager)
- Sees everything: all reports, all transactions, all staff activity
- Sets selling prices for fuel (clerks cannot change prices)
- Can cancel fuel purchase requests (with a mandatory written reason)
- Manages staff accounts — who can log in and what role they have
- Accesses the Management Hub: a central control panel for the whole business

### Petrol Clerk
- Records daily fuel sales (cash and credit)
- Submits fuel purchase requests to be approved
- Cannot set prices — prices come from management
- Mobile-optimised view — works on a phone at the pump
- Cannot see financial reports or accounting data

### Cargo Clerk
- Manages trips from start to finish (plan → in progress → complete)
- Records trip expenses (toll fees, driver allowances, loading costs)
- Records vehicle maintenance expenses
- Generates invoices on trip completion
- Cannot see financial reports

### Accountant
- Full access to all financial reports
- Approves or returns fuel purchase requests (with a written note explaining what needs correction)
- Manages salaries and petty cash
- Runs VAT returns, bank reconciliation, balance sheets
- Cannot modify prices or cancel purchases (that's admin only)

> **Why this separation matters:** It's called **segregation of duties** — a fundamental accounting control. The person who handles cash shouldn't be the one approving purchases. The clerk who records fuel sales shouldn't be able to see what the business owes suppliers. This system enforces that automatically.

---

## 3. Petrol Station Module

### 3.1 Fuel Tank Management

Each physical tank at the station is registered in the system with:
- Fuel type (Petrol, Diesel, Kerosene)
- Capacity in litres
- **Current stock level** — updated automatically every time fuel is sold or purchased
- **Last purchase price** (cost per litre from the supplier)
- **Selling price** — set by management, not the clerk

The clerk sees the current stock on every screen. The accountant sees the stock value on the balance sheet.

### 3.2 Fuel Purchase Approval Workflow

This is one of the most important features in the system. Here is exactly how it works:

```
Clerk submits purchase request
         ↓
Status: PENDING (visible to accountant and admin)
         ↓
Accountant reviews:
  → APPROVE: stock updated, ledger posted, purchase locked
  → RETURN: sent back to clerk with a written note explaining what to fix
         ↓
Clerk corrects and resubmits
         ↓
Admin can CANCEL at any point (must write a reason)
```

**Why this matters:**
- Without approval, a dishonest clerk could record a fake fuel purchase and pocket the cash
- The accountant's note creates a paper trail — every return and correction is recorded
- An approved purchase **cannot be cancelled** — this prevents someone from approving a purchase, taking the stock, then cancelling the record to hide it
- When the accountant approves, the system automatically: records the supplier payment, updates the tank stock, extracts input VAT (18%), and records the net cost into the fuel inventory account

### 3.3 Daily Cash Fuel Sales

The clerk selects the tank, enters litres sold. That is all.

The system automatically:
- Applies the management-set selling price
- Calculates the total
- Updates the tank stock (reduces it)
- Records the accounting entry:
  - Cash received → Cash account (Dr)
  - Revenue (net of VAT) → Fuel Revenue account (Cr)
  - VAT portion → VAT Payable account (Cr)
  - Cost of fuel sold → COGS account (Dr)
  - Fuel inventory → Inventory account (Cr)

This is **full accrual accounting happening automatically** at the point of sale.

### 3.4 Credit Fuel Sales

Some customers (garages, fleet operators) buy fuel on credit. The system:
- Tracks their outstanding balance
- Records the sale against their account (Accounts Receivable)
- When they pay, records the payment and reduces their balance
- The AR Aging report shows who owes how much and for how long

### 3.5 Selling Price vs. Cost Price

**Selling price** = what you charge customers. Set by admin on each tank. Clerks cannot see or change it.

**Cost price (purchase price)** = what you paid the supplier per litre. Updated automatically every time a purchase is approved.

The difference between selling price and cost price, after VAT, is your **gross margin per litre**. The income statement calculates this automatically as Gross Profit.

---

## 4. Cargo / Transport Module

### 4.1 Trip Lifecycle

Every delivery goes through a clear lifecycle:

```
PLANNED → IN PROGRESS → COMPLETED → Invoice generated automatically
                      → CANCELLED
```

When a trip is marked COMPLETED, the system creates an invoice for the customer automatically — the clerk doesn't need to do anything extra.

### 4.2 What Gets Tracked on Each Trip

- Vehicle and driver assigned
- Origin and destination
- Cargo description and weight
- Freight amount (what you charge the customer)
- **Trip expenses** — toll fees, driver allowances, loading costs, fuel — all recorded per trip
- **Profit per trip** — automatically calculated: Freight Amount minus all Trip Expenses

This means the accountant can tell you exactly which routes are profitable and which are losing money.

### 4.3 Vehicle Expenses

Separate from trip expenses, vehicle expenses track:
- Maintenance and repairs
- Tyre replacements
- Insurance
- Periodic fuel costs

These post automatically to the expense accounts in the ledger.

### 4.4 Invoice and Payment

When an invoice is paid, the clerk records:
- How much was paid
- Which payment method: Cash, Bank Transfer, M-Pesa, Yas (Tigo Pesa), HaloPesa, or Airtel Money

The system routes the payment to the **correct account** for that payment method automatically. M-Pesa payments go to the M-Pesa account. Airtel Money payments go to the Airtel Money account. This is critical for bank reconciliation later.

---

## 5. Sales Module (The Paper Trail)

### 5.1 The Sales Process Flow

```
Customer enquiry
      ↓
  Job Order (captures the request)
      ↓
  Quotation (formal price offer, can be printed and sent)
      ↓
  Accepted → Trip created in Cargo module
      ↓
  Delivery Note (proof of delivery, signed by recipient)
      ↓
  Invoice (payment request)
      ↓
  Receipt (proof of payment received)
```

Every document has a unique reference number generated automatically. Every document can be printed.

### 5.2 Quotations

Quotations include:
- Line-item breakdown of services
- VAT calculation (18%)
- Valid-until date
- Status tracking (Draft → Sent → Accepted/Rejected)

When a customer accepts a quotation, the linked Job Order advances automatically. No manual status changes needed.

### 5.3 Receipts

When any payment is received — whether for a cargo invoice or a petrol credit balance — the system can generate a **receipt** automatically. The receipt links back to what it was paid for (which invoice, which credit balance).

---

## 6. The Accounting Engine — Explained Simply

### What is Double-Entry Bookkeeping?

Every financial transaction affects two accounts simultaneously. This is a 500-year-old accounting principle that ensures your books always balance.

**Example:** You sell 1,000 litres of petrol for TZS 3,200,000.

| Account | Debit (Dr) | Credit (Cr) |
|---|---|---|
| Cash on Hand | 3,200,000 | — |
| Fuel Revenue (net) | — | 2,711,864 |
| VAT Payable | — | 488,136 |
| Cost of Fuel Sold | 2,372,881 | — |
| Petrol Stock (inventory) | — | 2,372,881 |

Total Debits: 5,572,881 = Total Credits: 5,572,881 ✓

The books always balance. If they don't, there's an error — the system catches this and alerts you.

**Every single transaction in this system posts these entries automatically.** The accountant never needs to manually enter a journal entry for routine operations.

### 6.1 Chart of Accounts — 49 Accounts

The Chart of Accounts is the backbone of the accounting system. Think of it as a filing system with 49 categories:

**Assets** (things the business owns):
- Cash on Hand (1010) — physical cash in the till
- Bank Account (1020) — money in the bank
- M-Pesa (1025), Yas/Tigo Pesa (1026), HaloPesa (1027), Airtel Money (1028) — separate accounts for each mobile money platform
- Petty Cash (1030)
- Input VAT Recoverable (1140) — VAT paid on purchases, claimable from TRA
- Accounts Receivable (1110/1120) — money owed by customers
- Petrol Stock (1210), Diesel Stock (1220), Kerosene Stock (1230) — fuel inventory value

**Liabilities** (things the business owes):
- Fuel Supplier Payable (2020) — money owed to fuel suppliers on credit terms
- VAT Payable (2030) — VAT collected from customers, owed to TRA

**Equity** (owner's investment):
- Owner's Capital (3010)
- Retained Earnings (3020)

**Revenue** (income):
- Petrol Sales (4010), Diesel Sales (4020), Kerosene Sales (4030)
- Cargo Freight Revenue (4040)

**Expenses** (costs):
- Cost of Fuel Sold (5050) — the purchase cost of fuel that has been sold
- Salaries (5110), Vehicle Expenses (5120), Trip Expenses (5130), Station Expenses (5140)
- Petty Cash Expenses (5190)

### 6.2 Why Separate Mobile Money Accounts?

This is a question that will impress the client if you raise it proactively.

Each mobile money platform (M-Pesa, Yas, HaloPesa, Airtel) is a completely separate "wallet." The money in your M-Pesa account cannot be seen in your Airtel Money account.

If you had one combined "Mobile Money" account:
- You couldn't tell how much float you have on each platform
- You couldn't reconcile — M-Pesa has its own statement, Airtel Money has its own statement, you can't match them to a combined account

Separate accounts means: when the accountant opens the M-Pesa statement, they reconcile **only the M-Pesa account**. Each platform reconciles independently against its own statement. This is international best practice.

### 6.3 VAT — How the System Handles It

Tanzania standard VAT rate: **18%**

Fuel prices and cargo freight rates in Tanzania are **VAT-inclusive** — the price the customer pays already includes VAT.

**How to extract VAT from a VAT-inclusive price:**
`VAT = Total Amount × 18 ÷ 118`

Example: Customer pays TZS 1,000,000 for fuel.
- VAT = 1,000,000 × 18/118 = TZS 152,542
- Net Revenue = 847,458

The system does this calculation automatically on every sale. The VAT goes to account 2030 (VAT Payable), not into revenue. This means your income statement shows **real revenue** — not inflated by VAT you're just collecting on behalf of TRA.

**Input VAT** (VAT on your fuel purchases): When you buy fuel from a supplier, you also pay VAT. That VAT goes to account 1140 (Input VAT Recoverable). You can offset this against what you owe TRA.

**Net VAT Payable = Output VAT (collected from customers) minus Input VAT (paid to suppliers)**

### 6.4 Cost of Goods Sold (COGS) — Why It Matters

This was a critical gap that we fixed. Here's why it matters:

**Without COGS tracking:**
You sell 10,000 litres of petrol at TZS 3,200/L = TZS 32,000,000 revenue.
The income statement shows TZS 32,000,000 revenue, minus salaries and running costs.
Looks like a huge profit — but it's completely misleading because you haven't accounted for the TZS 27,000,000 you spent buying that fuel from the supplier.

**With COGS tracking:**
Revenue: TZS 32,000,000
Minus Cost of Fuel Sold: TZS 23,728,814 (net cost at 2,800/L, ex-VAT)
= **Gross Profit: TZS 8,271,186** (actual profit from selling fuel before operating costs)

Now you know your true gross margin is about 26% — which tells you if you're pricing correctly.

The system calculates COGS using the last approved purchase price from the supplier, adjusted to remove the VAT component (since the inventory account holds net-of-VAT values).

---

## 7. Financial Reports — What Each One Tells You

### 7.1 Dashboard (Live)
The home page. Shows:
- Today's cash position across all accounts
- This month's revenue, expenses, and profit
- Pending fuel purchases waiting for approval
- Outstanding credit balances
- Active trips
- Tank fuel levels

Any business owner or manager can see the health of the business at a glance, right now.

### 7.2 Income Statement (Profit & Loss)
**Question it answers: Is the business making money?**

Structure:
```
Revenue (net of VAT)
  - Petrol Sales
  - Diesel Sales
  - Cargo Freight
= Total Revenue

Less: Cost of Fuel Sold (COGS)
= GROSS PROFIT  ← how much you make from selling before running costs

Less: Operating Expenses
  - Salaries
  - Vehicle Maintenance
  - Station Expenses
  - Trip Costs
= NET PROFIT (or Loss)
```

Can be run for any period: daily, weekly, monthly, yearly.

### 7.3 Balance Sheet
**Question it answers: What does the business own and what does it owe — right now?**

```
ASSETS                          LIABILITIES
Cash: 5,200,000                 Supplier Payable: 3,000,000
Bank: 12,400,000                VAT Payable: 890,000
M-Pesa: 2,100,000               
Fuel Inventory: 8,700,000       EQUITY
Receivables: 4,500,000          Owner Capital: 20,000,000
                                Retained Earnings: 9,010,000
TOTAL: 32,900,000               TOTAL: 32,900,000 ✓
```

If both sides match, the books are correct. The system checks this automatically and shows a warning if they don't balance.

### 7.4 Trial Balance
**Question it answers: Are the books mathematically correct?**

Lists every account with its balance. Total debits must equal total credits. This is the starting point before preparing the Income Statement and Balance Sheet. The system produces it instantly for any date.

### 7.5 AR Aging Report (Accounts Receivable)
**Question it answers: Who owes us money, and how long have they owed it?**

| Customer | 0-30 days | 31-60 days | 61-90 days | Over 90 days | Total |
|---|---|---|---|---|---|
| Juma Fleet | 850,000 | — | — | — | 850,000 |
| ABC Garage | — | 1,200,000 | — | — | 1,200,000 |
| Old Customer | — | — | — | 3,400,000 | 3,400,000 |

The red entries (over 90 days) need immediate attention. An accountant uses this report to decide who to call for payment today.

The system uses **FIFO matching** (First In, First Out) — payments are applied to the oldest outstanding balance first, which is the correct accounting treatment.

### 7.6 Supplier AP Report (Accounts Payable)
**Question it answers: Who do we owe money to, and when does it become overdue?**

Shows all fuel purchases bought on credit (supplier extends 30-day payment terms). Each purchase is flagged as Current or Overdue. Prevents the business from accidentally missing supplier payment deadlines and damaging supplier relationships.

### 7.7 Cash Position
**Question it answers: Exactly how much money do we have, and where is it?**

Shows live balances for:
- Cash on Hand
- Bank Account
- M-Pesa
- Yas (Tigo Pesa)
- HaloPesa
- Airtel Money
- Petty Cash

Plus: today's inflows and outflows on each account, and a 7-day movement table showing cash trends.

This is the report a business owner checks every morning.

### 7.8 VAT Return
**Question it answers: How much VAT do we owe TRA this month?**

```
Output VAT (collected from customers):    TZS 1,245,000
  - Cash Fuel Sales:                         890,000
  - Credit Fuel Sales:                        180,000
  - Cargo Freight:                             175,000

Input VAT (paid to suppliers, claimable):  TZS 412,000
  - Fuel Purchases:                           412,000

NET VAT PAYABLE TO TRA:                   TZS 833,000
```

The report also shows the four TRA filing boxes, ready to copy directly into the TRA return form. This turns a day of work into 5 minutes.

### 7.9 Bank Reconciliation
**Question it answers: Does our system match the bank statement?**

This is the most important **control** in accounting. Here's the process in plain language:

1. The accountant opens the bank statement (or M-Pesa statement) for, say, May 2026
2. In the system, they start a reconciliation: select the account, set the period, enter the closing balance from the statement
3. The system shows every transaction recorded in the system for that account and period
4. The accountant ticks each transaction that appears on the statement
5. When the "Difference" card shows zero — the books match the bank statement exactly
6. Click "Lock & Finalise" — the reconciliation is permanently recorded, ticked entries are frozen

**Why this matters:** It catches missing entries, duplicate entries, and bank charges not yet recorded. Without reconciliation, your cash balance in the books could be wildly different from your actual bank balance — and you'd never know until it's too late.

Each account (bank, M-Pesa, Airtel Money, etc.) reconciles separately against its own statement.

---

## 8. Mobile App (PWA)

The system installs as an app on Android and iPhone — no App Store required.

**How to install:** Open the website in Chrome on your phone → tap the menu → "Add to Home Screen." It installs like a normal app and works offline for cached pages.

**What pump clerks get on their phone:**
- Bottom navigation bar: Home | Petrol | Cargo | Finance | Purchases
- Optimised touch targets — large buttons easy to tap at a busy pump
- Can record fuel sales immediately as they happen
- Submit fuel purchase requests from the forecourt

This eliminates the "I'll write it in the notebook and enter it later" problem — which is where discrepancies start.

---

## 9. Security

The system was built with security at every layer:

### Role-Based Access
- Financial reports (balance sheet, VAT return, income statement, reconciliation) are **completely blocked** for anyone who is not an accountant or admin — even if they know the URL
- Clerks see only what they need to do their job

### Data Integrity
- Every financial transaction is wrapped in a **database transaction** — if anything fails mid-way (power cut, network error), the entire operation rolls back. You never get half-posted entries
- Double-entry is enforced mathematically — if debits ≠ credits, the system refuses to save
- Approved fuel purchases are **locked** — they cannot be cancelled or edited to prevent stock manipulation

### Approval Controls
- Fuel purchases require accountant approval before any money or stock is recorded
- Admin cancellations require a written reason — creates an audit trail
- Returned purchases require a written note explaining what needs fixing

### Production Readiness
- Secret keys and debug mode are configured via environment variables — safe to deploy to a server
- Passwords validated against common password lists (no "password123")
- CSRF protection on all forms — prevents cross-site attacks
- XSS protection built into Django templates automatically

---

## 10. Technical Foundation (For Credibility)

You don't need to memorise this, but it answers "what's it built on?" if asked:

| Component | Technology | Why |
|---|---|---|
| Backend | Python / Django 5.1 | Stable, mature, used by Instagram and Disqus |
| Database | SQLite → PostgreSQL-ready | Start simple, scale when needed |
| Frontend | Bootstrap 5, Bootstrap Icons | Consistent, responsive, no external JS frameworks |
| Accounting | Custom double-entry engine | Built specifically for this business, not generic |
| Mobile | Progressive Web App | No App Store, works on any device |
| Auth | Django's built-in auth | Industry-standard, battle-tested |

**Database indexes** are in place on the most-queried fields (transaction dates, account codes, purchase status) — reports run fast even with years of data.

**All financial calculations use Decimal arithmetic** (not floating point) — this prevents rounding errors in money calculations. A common mistake in cheap systems that leads to cents accumulating into real discrepancies over time.

---

## 11. What the System Does NOT Cover (Honest Gaps)

It's better to say this yourself than have the client discover it:

### Not in This Version
- **Fixed asset register / depreciation** — trucks and equipment aren't tracked as depreciating assets yet. You'd track vehicle expenses (maintenance, fuel) but not annual depreciation
- **Payroll calculation** — salary amounts are recorded when paid, but the system doesn't calculate payroll from timesheets or contracts automatically
- **Bank statement import (CSV)** — reconciliation is currently manual tick. The foundation is built; automated CSV import from bank statements is the next step
- **Multi-currency transactions** — the system supports TZS and USD as a business setting, but individual transactions are all in the base currency

### Why These Are Not Blockers
Everything that matters for **daily operations** and **monthly TRA compliance** is covered. The gaps above are either niche (depreciation affects mostly large capital-heavy businesses) or planned features (CSV import is already designed, just waiting for implementation).

---

## 12. Summary — Why This System Wins

| What a Manual/Spreadsheet Business Does | What This System Does |
|---|---|
| Clerk writes sales in a notebook | Clerk records on phone at the pump, instantly |
| Accountant re-enters data into Excel | Zero re-entry — data flows automatically |
| VAT calculated once a month, manually | VAT calculated on every transaction, report in 30 seconds |
| Balance sheet takes 2 days to prepare | Balance sheet is live — press a button |
| "How much is in M-Pesa?" requires calling someone | Cash Position report — every account balance, right now |
| Fuel purchases approved verbally | Written approval trail with notes, locked after approval |
| Supplier payment missed, relationship damaged | Supplier AP report shows exactly what's due |
| Month-end reconciliation takes 3 days | Bank reconciliation per account, tick-by-tick, done in an hour |
| Profit only known at year end | Net profit visible any time, for any period |

---

## 13. Questions the Client Might Ask — Your Answers

**"Can multiple people use it at the same time?"**
Yes — it's a web application. The petrol clerk is recording sales while the accountant is reviewing reports while the admin is checking the dashboard. All simultaneously, all seeing live data.

**"What happens if the internet goes down?"**
The app is installed on phones as a PWA and caches recently viewed pages. For recording new transactions, you need internet. A good practice is to have a backup mobile hotspot. For a critical business operation like a petrol station, internet connectivity is a basic infrastructure requirement.

**"Can we change the VAT rate if TRA changes it?"**
The VAT rate (18%) is defined as a single constant in the codebase. Changing it requires a developer to update one line and deploy. It's not a settings screen yet — that's a 30-minute addition if needed.

**"How do we migrate our existing data?"**
The system has a demo data loader. For real migration, historical data can be imported via the admin panel or a custom script. The chart of accounts and opening balances can be set up to reflect the current state of the business on day one.

**"Is it hosted in Tanzania? What about TRA data requirements?"**
The system can be hosted anywhere — a Tanzanian server (e.g., Tanzania Data Centers), a VPS in Nairobi, or a cloud provider. Data sovereignty requirements can be met by choosing a local host. The application itself is infrastructure-agnostic.

**"What about backups?"**
The database is a standard SQLite file (or PostgreSQL in production). Automated daily backups are a server configuration task — standard practice on any VPS or cloud host. The database can be backed up to another server or cloud storage automatically.

**"Can we add more fuel types or tanks?"**
Yes — everything is configurable. Add a new tank type, new fuel type, new expense category, new account — all through the admin interface. No developer needed for configuration.

---

*System built with Django 5.1.15 · Python 3.12 · Bootstrap 5 · 16 development milestones · Full double-entry accounting engine*
