# Accounts Receivable and Collections Project Guide

**Project owner: HeeJung Kim** · Personal finance analytics portfolio

This case study uses synthetic invoices and payment allocations to show how a collections team can review overdue balances and prioritize follow-up.

## Explore the project

- [Three-page portfolio PDF](portfolio/HeeJung_Kim_AR_Collections_Portfolio.pdf): Overview, Customers and Collection Worklist.
- [Business findings and proposed actions](README.md).
- [Data validation and reproducible checks](validation/README.md).

The PDF and images show the report design using calculated results. A completed PBIX, screenshots from Power BI Desktop and a public viewing link are not yet included in this repository.

## Repository contents

| Folder | Contents |
|---|---|
| [data](data) | Synthetic customer, invoice, payment and calendar CSVs, plus a reference AR snapshot |
| [sql](sql) | SQLite snapshot transformation, data checks and a Python runner |
| [powerbi](powerbi) | Power Query transformation and DAX measures |
| [portfolio](portfolio) | Three report-design images and the complete PDF |
| [validation](validation) | Reproducible validation script, check results, customer summary and collection worklist |

## Reproduce the analysis

From the repository root, run:

```bash
python sql/run_analysis.py
python validation/validate_portfolio.py
```

Both scripts use Python 3 and its standard library; no additional packages are required. The validation script reruns the SQL analysis automatically, so the second command alone is sufficient for a full check.

SQL outputs are written to `sql/results/`. The validation script updates `validation/Validation_Result.json` and exits with an error if a check fails. Source CSVs are not modified.

## Build the Power BI report

1. In Power BI Desktop, import `Customers.csv`, `Invoices.csv`, `Payments.csv` and `Calendar.csv` from the `data` folder using **Get data > Text/CSV**. Name the queries **Customers**, **Invoices**, **Payments** and **Calendar**.
2. In Power Query, keep IDs as **Text**, dates as **Date**, monetary fields as **Fixed decimal number**, and calendar sorting fields as **Whole number**.
3. Create a blank query named **ARSnapshot**. Replace its Advanced Editor contents with [ARSnapshot.pq](powerbi/ARSnapshot.pq). The snapshot date is fixed at **30 September 2026**.
4. Create one-to-many, single-direction relationships from **Customers[CustomerID]** to **ARSnapshot[CustomerID]** and **Payments[CustomerID]**, and from **Calendar[Date]** to **Payments[PaymentDate]**. Calendar filters cash receipts; the AR snapshot remains fixed. Avoid a Calendar relationship to ARSnapshot for this design.
5. Create the measures from [Measures.dax](powerbi/Measures.dax) individually. Sort **ARSnapshot[AgingBucket]** by **AgingSort**, and **Calendar[YearMonth]** by **YearMonthSort**.
6. Build the three pages using the portfolio designs. Test the totals, customer filters, date filters and drill-through in Desktop before publishing.

With no filters, expected balances are **CAD 1,548,971.19 outstanding** and **CAD 980,235.72 overdue**. Compare more detailed rows with [ARSnapshot_reference.csv](data/ARSnapshot_reference.csv).

## Power BI verification

The SQL validation is reproducible from the committed files. Power BI verification covers the following separate checks:

- Refresh the PBIX from the source CSVs and compare the DAX totals with the reference snapshot.
- Confirm that customer filters affect receivables and payments, while date filters affect cash receipts only.
- Check drill-through navigation and capture screenshots of the finished report.
- Verify access to any published report link while signed out.

All data is fictional. Collection actions are proposed recommendations; this project does not claim actual cash recovery or business savings.

