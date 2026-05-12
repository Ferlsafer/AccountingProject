Phase 1.5 Implementation Report

  What was built

  7 deliverables shipped in one sprint:

  ---
  1. Petty Cash Module (core app)

  A dedicated petty cash ledger separate from the main cash account.

  How it works:
  - The accountant records a transaction — choose one of 4 types: Inflow from Main Cash, Inflow from Other Source, Expense, or Return to Main Cash
  - Each transaction automatically posts a double-entry journal line to the general ledger:
    - Inflow from main: Debit Petty Cash (1030) / Credit Cash on Hand (1010)
    - Expense: Debit the expense account or 5190 (Misc) / Credit Petty Cash (1030)
    - Return: Debit Cash on Hand / Credit Petty Cash
  - The petty cash list shows a running balance day by day
  - A printable monthly statement can be printed at any time

  Where to find it: Sidebar → Finance → Petty Cash

  ---
  2. Sales Customer Registry (sales app)
  
  A standalone customer list for the Sales section — separate from the cargo customer list.

  - Each customer has: name, phone, email, address, TIN, type (Petrol / Cargo / Both), credit limit
  - Why separate? The cargo module has its own CargoCustomer and petrol has CreditCustomer. The Sales customer list is for quoting, invoicing, and
  receipts. The name-match logic means: if a petrol credit customer pays and their name matches a Sales customer, the receipt is created automatically.

  Where to find it: Sidebar → Sales → Customers

  ---
  3. Job Orders

  A job order is the starting document — it captures what the customer wants moved, from where, to where.

  Lifecycle (forward-only):
  Draft → Quoted → Accepted → In Progress → Completed
                             ↘ Cancelled (from any stage)

  - Creating a quotation from a job order auto-advances the job to Quoted
  - Accepting a quotation auto-advances the linked job to Accepted

  Where to find it: Sidebar → Sales → Job Orders

  ---
  4. Quotations

  A formal price offer sent to the customer. Each quotation has line items (description, quantity, unit price). The template calculates the subtotal live
  as you type.

  Lifecycle:
  Draft → Sent → Accepted → (job order also becomes Accepted)
               ↘ Rejected / Expired

  Quotations can be printed to a clean A4 document for sending to the customer.

  Where to find it: Sidebar → Sales → Quotations

  ---
  5. Delivery Notes

  Issued when cargo is physically delivered. Links to an existing cargo trip and records: driver name, vehicle plate, recipient name, and whether the
  signature was received. Prints as a professional handover document with a signature box.

  Where to find it: Sidebar → Sales → Delivery Notes

  ---
  6. Receipts

  A receipt is issued when a customer pays. Receipts can be linked to:
  - A cargo invoice (payment for a completed trip)
  - A petrol credit payment (a credit customer paying their fuel debt)
  - Other (standalone payment)
  
  Auto-receipt flow: When a cargo invoice or petrol credit payment is marked as paid, the system tries to find a matching Sales customer by name. If found,
   it creates the receipt automatically and redirects to the print page. If not found, it opens the receipt form pre-filled with the amount so the user can
   pick the customer manually.

  Where to find it: Sidebar → Sales → Receipts

  ---
  7. Unified Invoice View
  
  A single read-only list combining cargo invoices and petrol credit sales. Filter by date range, source (Cargo / Petrol), status (Paid / Unpaid), or
  customer name. Each row has a View button and a Pay button (for unpaid items).

  Where to find it: Sidebar → Sales → All Invoices

  ---
  How to explain this to the customer (TBC)
  
  ▎ "Before, when a customer called asking for transport, there was no document trail until the driver left and an invoice was issued. Now the process is: 
  ▎ you create a Job Order (the enquiry), send a Quotation with the price, the customer accepts, the driver does the trip, you issue a Delivery Note at 
  ▎ destination, and when they pay you print a Receipt — all connected, all in one system. The accountant can also track the petty cash tin separately 
  ▎ instead of mixing it with the main cash account."

  Key selling points for the client meeting:
  1. Every payment produces a printed receipt — professional, with a reference number
  2. The quotation can be printed and emailed to the customer 
  3. Unpaid cargo invoices are visible in one place — no more hunting through the cargo module
  4. Petty cash has its own running balance and printable monthly statement — the accountant can reconcile the tin at any time
  5. Everything ties into the ledger automatically — no double entry by the accountant

  ---
  loaddemo — now fully updated

  The command now covers all Phase 1.5 features. Running python manage.py loaddemo loads:

  ┌─────────────────────────┬──────────────────────────────────────────────────────────────┐
  │         Section         │                       Records created                        │
  ├─────────────────────────┼──────────────────────────────────────────────────────────────┤
  │ Chart of accounts       │ +4 new accounts (1030, 1350, 2200, 5190)                     │
  ├─────────────────────────┼──────────────────────────────────────────────────────────────┤
  │ Sales customers         │ 5 (including TBC Mining Co for auto-receipt name-match demo) │
  ├─────────────────────────┼──────────────────────────────────────────────────────────────┤
  │ Job orders              │ 6 (all statuses: draft → completed)                          │
  ├─────────────────────────┼──────────────────────────────────────────────────────────────┤
  │ Quotations + line items │ 4 quotations, 1 line item each                               │
  ├─────────────────────────┼──────────────────────────────────────────────────────────────┤
  │ Delivery notes          │ 4 (linked to completed cargo trips)                          │
  ├─────────────────────────┼──────────────────────────────────────────────────────────────┤
  │ Receipts                │ 4 (linked to paid cargo invoices)                            │
  ├─────────────────────────┼──────────────────────────────────────────────────────────────┤
  │ Petty cash transactions │ 10 (2 inflows, 7 expenses, 1 return)                         │
  └─────────────────────────┴──────────────────────────────────────────────────────────────┘
