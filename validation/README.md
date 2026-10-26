# Data Validation

Automated checks compare the synthetic source records, SQL calculations and reference outputs.

## Run

From the repository root, using Python 3:

```bash
python validation/validate_portfolio.py
```

The script reruns the SQLite analysis, calculates an independent invoice snapshot with Python Decimal and compares every output field. It writes [Validation_Result.json](Validation_Result.json) and exits with an error if a check fails.

## Results

Snapshot date: **30 September 2026**.

| Check | Result |
|---|---|
| SQL data-quality checks | 10 checks; zero issues |
| Invoice snapshot | 480 rows matched SQL and the reference snapshot |
| Customer summaries | 40 rows matched |
| Collection worklist | 105 overdue invoice rows matched |
| Invoice amounts minus payments minus outstanding | CAD 0.00 difference |
| Current plus overdue minus outstanding | CAD 0.00 difference |
| Boundary scenarios | 18 passed |

## Coverage

The [SQL checks](../sql/02_validation.sql) cover duplicate IDs, missing customer or invoice references, payment/customer mismatches, invalid date order, nonpositive transaction amounts and negative outstanding balances.

Boundary tests cover aging thresholds at 0, 1, 30, 31, 60, 61, 90 and 91 days; fully paid and partially paid invoices; cutoff dates; dispute routing; credit-balance routing; and the CAD 10,000 priority threshold.

The credit-balance scenario uses a separate test fixture. Negative balances in the source dataset are flagged for review.

## Files

| File | Purpose |
|---|---|
| [validate_portfolio.py](validate_portfolio.py) | Validation and boundary tests |
| [Validation_Result.json](Validation_Result.json) | Results from the latest run, including all 10 SQL checks |
| [Customer_Summary.csv](Customer_Summary.csv) | Customer-level reference totals |
| [Collection_Worklist.csv](Collection_Worklist.csv) | Reference overdue invoices and action categories |

The calculation under test is [sql/01_snapshot.sql](../sql/01_snapshot.sql). These results cover source data and SQL calculations; Power BI Desktop behavior requires separate verification.

