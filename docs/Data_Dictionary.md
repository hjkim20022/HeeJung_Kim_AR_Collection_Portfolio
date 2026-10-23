# Data dictionary

All data is synthetic. Source currencies are CAD. Raw CSV dates use YYYY-MM-DD. Blank DisputeReason means no reason is recorded; it is not a monetary zero.

| Table/file | Grain and key | Important columns |
|---|---|---|
| Customers | One row per fictional customer; CustomerID | CustomerName, Region, Industry, AccountOwner |
| Invoices | One row per invoice; InvoiceID | CustomerID, InvoiceDate, DueDate, InvoiceAmountCAD, Disputed, DisputeReason |
| Payments | One payment allocation per row; PaymentID | InvoiceID, CustomerID, PaymentDate, PaymentAmountCAD. An invoice may have multiple allocations. |
| Calendar | One row per day in 2026; Date | Year, MonthNumber, MonthName, YearMonth, YearMonthSort |
| ARSnapshot_reference | One row per eligible invoice at the fixed reporting date; InvoiceID | The derived fields below, plus invoice/customer/date/dispute fields |

## Derived fields

| Field | Definition |
|---|---|
| PaidToDateCAD | Sum of allocated payments with PaymentDate on or before AsOfDate |
| OutstandingCAD | InvoiceAmountCAD minus PaidToDateCAD, in cents |
| DaysOverdue | Maximum of zero and AsOfDate minus DueDate for positive balances; zero for paid invoices |
| AgingBucket | Paid, Current, 1-30, 31-60, 61-90, 91+. Credit balances have a separate exception label. |
| AgingSort | -1 for credit, 0 paid, 1 current, 2-5 for successive overdue bands |
| AsOfDate | Fixed 2026-09-30 reporting date |
| ActionGroup | Demonstration routing rule based on balance, dispute flag and days overdue; see build guide |

The reference snapshot and validation CSVs are calculated outputs, not new independent source datasets. Do not append them to the raw invoice records or sum both together.

The Excel ARSnapshot is an earlier reference built using formulas. Power BI imports saved values from that workbook; it does not recalculate the Excel file. This kit rebuilds the snapshot from raw records with Power Query or SQL so that the preparation steps can be inspected.
