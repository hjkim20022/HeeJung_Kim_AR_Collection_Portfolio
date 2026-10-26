# Data Validation

Validation for **HeeJung Kim's Accounts Receivable and Collections portfolio**.

These checks test whether the synthetic source data, calculated balances and published reference outputs agree.

## Run the checks

From the repository root:

```bash
python validation/validate_portfolio.py
```

The script uses Python 3 and its standard library. It reruns the SQLite analysis, calculates an independent invoice snapshot with Python Decimal, compares the saved outputs, and tests boundary scenarios. It writes [Validation_Result.json](Validation_Result.json) and exits with an error if a check fails.

## Results for 30 September 2026

| Check | Result |
|---|---|
| SQL data-quality checks | All 10 returned zero issues |
| Invoice snapshot comparison | All 480 rows matched SQL and the committed reference snapshot |
| Customer summary comparison | All 40 rows matched |
| Collection worklist comparison | All 105 overdue invoice rows matched |
| Invoice amount minus payments minus outstanding | CAD 0.00 difference |
| Current plus overdue minus outstanding | CAD 0.00 difference |
| Boundary scenarios | All 18 passed |

Invoice amounts total **CAD 4,873,723.46**, payments total **CAD 3,324,752.27**, and outstanding balances total **CAD 1,548,971.19**. Current balances of **CAD 568,735.47** plus overdue balances of **CAD 980,235.72** reconcile to the same outstanding total.

## What is checked

The 10 SQL checks cover duplicate IDs, missing customer or invoice references, payment/customer mismatches, invalid date order, nonpositive transaction amounts and negative outstanding balances in the source dataset.

The 18 boundary scenarios cover aging thresholds at 0, 1, 30, 31, 60, 61, 90 and 91 days; fully paid and partially paid invoices; transactions around the cutoff date; dispute routing; credit-balance routing; and the CAD 10,000 priority threshold. Credit-balance routing is tested using a separate fixture; negative balances in the source dataset are still flagged for review.

Payments are aggregated by InvoiceID before joining invoices. The independent calculation compares every output field, including outstanding amount, aging bucket and action category, using one row per invoice.

## Files

| File | Purpose |
|---|---|
| [validate_portfolio.py](validate_portfolio.py) | Reproducible validation and boundary tests |
| [Validation_Result.json](Validation_Result.json) | Latest machine-readable results |
| [Checks.csv](Checks.csv) | Saved results of the 10 SQL checks |
| [Customer_Summary.csv](Customer_Summary.csv) | Customer-level reference totals |
| [Collection_Worklist.csv](Collection_Worklist.csv) | Reference list of overdue invoices for review |

The source transformation is [sql/01_snapshot.sql](../sql/01_snapshot.sql); the data-quality queries are [sql/02_validation.sql](../sql/02_validation.sql).

## Scope

These results validate the committed synthetic dataset and SQL calculations. Power Query refreshes, DAX measures, relationships, filters, drill-through and publication require separate testing in Power BI Desktop.

The collection categories are transparent demonstration rules, not predictions of default. Proposed actions have not produced measured cash recovery or savings.

