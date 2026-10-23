"""Reproduce this portfolio analysis using Python 3 standard-library tools.
Run from any directory: python path/to/sql/run_analysis.py
The script reads the four CSVs and executes the accompanying SQLite SQL.
It writes a fresh result folder alongside this script. Source files are unchanged.
"""
from pathlib import Path
import csv
import json
import sqlite3

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'results'
OUT.mkdir(exist_ok=True)
conn = sqlite3.connect(':memory:')
conn.row_factory = sqlite3.Row
conn.executescript('''
CREATE TABLE Config (AsOfDate TEXT NOT NULL);
INSERT INTO Config VALUES ('2026-09-30');
CREATE TABLE Customers (CustomerID TEXT PRIMARY KEY, CustomerName TEXT, Region TEXT, Industry TEXT, AccountOwner TEXT);
CREATE TABLE Invoices (InvoiceID TEXT PRIMARY KEY, CustomerID TEXT, InvoiceDate TEXT, DueDate TEXT, InvoiceAmountCAD NUMERIC, Disputed TEXT, DisputeReason TEXT);
CREATE TABLE Payments (PaymentID TEXT PRIMARY KEY, InvoiceID TEXT, CustomerID TEXT, PaymentDate TEXT, PaymentAmountCAD NUMERIC);
CREATE TABLE Calendar (Date TEXT PRIMARY KEY, Year INTEGER, MonthNumber INTEGER, MonthName TEXT, YearMonth TEXT, YearMonthSort INTEGER);
''')
for name in ['Customers', 'Invoices', 'Payments', 'Calendar']:
    with (ROOT/'data'/f'{name}.csv').open(encoding='utf-8-sig', newline='') as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames
        conn.executemany(f'INSERT INTO {name} VALUES ({",".join("?" for _ in fields)})',
                         [tuple(row[k] for k in fields) for row in reader])
conn.executescript((HERE/'01_snapshot.sql').read_text(encoding='utf-8'))
rows=[dict(row) for row in conn.execute('SELECT * FROM ARSnapshot ORDER BY InvoiceID')]
with (OUT/'ARSnapshot.csv').open('w', newline='', encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
checks=[dict(row) for row in conn.execute((HERE/'02_validation.sql').read_text(encoding='utf-8'))]
summary=dict(conn.execute('''SELECT COUNT(*) AS invoice_rows,
ROUND(SUM(InvoiceAmountCAD),2) AS invoice_amount_cad,
ROUND(SUM(PaidToDateCAD),2) AS payments_cad,
ROUND(SUM(OutstandingCAD),2) AS outstanding_cad,
ROUND(SUM(CASE WHEN DaysOverdue>0 THEN OutstandingCAD ELSE 0 END),2) AS overdue_cad
FROM ARSnapshot''').fetchone())
result={'summary':summary,'checks':checks}
(OUT/'Reconciliation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
if any(row['IssueCount'] for row in checks):
    raise SystemExit('Validation found issues. Review the source records before using the results.')
