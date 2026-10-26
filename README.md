# Accounts Receivable & Collections

**Project owner: HeeJung Kim** · Personal finance analytics portfolio

**Business question:** Which customers hold overdue balances, how old are those balances, and which invoices should a collections team review first?

**Status:** SQL analysis and reconciliation are complete. This repository includes Power Query, DAX and report designs; Power BI Desktop validation and a published interactive report are not yet documented.

## Three-page portfolio

The portfolio covers **all three pages** of the Accounts Receivable & Collections report design:

| 01 — Overview | 02 — Customers | 03 — Collection worklist |
|:---:|:---:|:---:|
| [![Overview: receivables KPIs, aging and monthly cash collections](portfolio/01_Overview.png)](portfolio/01_Overview.png) | [![Customers: top overdue accounts and disputed balances](portfolio/02_Customers.png)](portfolio/02_Customers.png) | [![Collection worklist: overdue invoice review and follow-up queues](portfolio/03_Worklist.png)](portfolio/03_Worklist.png) |
| Outstanding and overdue KPIs, aging bands and cash collected by month | Customer concentration, top five overdue accounts and dispute review | Invoice-level follow-up priorities, disputes and reconciliation |

**[View my three-page portfolio PDF →](portfolio/HeeJung_Kim_AR_Collections_Portfolio.pdf)**

*The images and PDF present the report design using validated synthetic data. They are design previews. Completed Power BI screenshots and an interactive report link are not yet included.*

## Data and scope

40 fictional customers, 480 invoices and 425 payment allocations. Reporting date: **30 September 2026**. All amounts are CAD. Source: the synthetic CSV inputs in the [`data`](data) folder. This is a portfolio demonstration, not employer or client data.

Invoices and payments cover January to September 2026. There are no opening receivables, credit notes, refunds, write-offs, foreign exchange or tax adjustments. Every payment is allocated to an invoice. This is one balance snapshot; monthly collections are cash receipts, not a trend of historical receivables balances.

## Three findings

1. **$980,235.72 is overdue, or 63.3% of $1,548,971.19 outstanding.** There are 105 overdue invoices among 165 open invoices.
2. **$471,979.98 is more than 90 days overdue.** This is 48.1% of overdue receivables and identifies a large group for review. Age alone does not establish default or uncollectibility.
3. **The five largest overdue customer balances total $282,805.87, or 28.9% of overdue receivables.** Customers C027, C018, C020, C031 and C017 provide a focused starting list. Across all customers, disputed overdue invoices total $263,310.83.

## Two proposed actions

1. **Review the top five overdue accounts with their account owners.** Check invoice details and prior correspondence, prioritize older undisputed balances, agree the next follow-up, and track an owner and next-contact date.
2. **Route disputed invoices to a separate resolution queue.** Review the $263,310.83 disputed overdue balance with the relevant owner before routine collection reminders. Record the reason, evidence required, next step and target resolution date.

These are proposed actions supported by the synthetic data. Their effect on collections has not been measured.

## Calculation and validation

Payments are grouped by InvoiceID before joining to invoices. This keeps one row per invoice and prevents invoice amounts from being multiplied by partial-payment rows.

- Outstanding = invoice amount minus payments dated on or before the snapshot date.
- An invoice due on the snapshot date is current. Overdue requires a positive outstanding balance and a due date before the snapshot date.
- Aging bands: Current, 1-30, 31-60, 61-90 and 91+ days.
- Fully paid invoices are excluded from aging exposure.
- The collection action categories are transparent demonstration rules, not a credit-risk prediction.

| Reconciliation | CAD |
|---|---:|
| Invoice amount | 4,873,723.46 |
| Payments through 30 September | 3,324,752.27 |
| Outstanding balance | 1,548,971.19 |
| Current plus overdue | 1,548,971.19 |
| Difference | 0.00 |

Run `python validation/validate_portfolio.py` to reproduce the checks. The script reruns the SQLite analysis, independently calculates balances and aging with Python Decimal, compares all 480 invoice rows with the committed reference snapshot, checks 40 customer summary rows and 105 collection worklist rows, and runs 18 boundary tests. The latest results show zero issues across the 10 SQL checks, no row discrepancies, and a CAD 0.00 difference in both balance and aging reconciliation.

See [how validation works](validation/README.md), the [validation script](validation/validate_portfolio.py), and the [machine-readable results](validation/Validation_Result.json).

The automated checks cover the source data and SQL results. Power Query refreshes, DAX measures and report interactions require separate validation in Power BI Desktop.

## Reproduce the SQL analysis

Requires Python 3. No additional packages are needed.

```bash
python sql/run_analysis.py
```

The script reads the CSVs, runs SQLite SQL, and writes `sql/results/ARSnapshot.csv` and `sql/results/Reconciliation.json`. Dates use ISO YYYY-MM-DD. The transformation uses integer cents for aggregation. Duplicate primary keys stop the load.

- [Snapshot transformation](sql/01_snapshot.sql)
- [Validation queries](sql/02_validation.sql)
- [Power Query transformation](powerbi/ARSnapshot.pq)
- [DAX measures](powerbi/Measures.dax)
- [Project guide and Power BI setup](START_HERE.md)

## Report design

1. **Overview:** outstanding and overdue balances, aging distribution and monthly cash collections.
2. **Customers:** overdue exposure by customer, concentration and proposed actions.
3. **Collection worklist:** invoice detail, owner, outstanding amount, days overdue, dispute reason and proposed action category.

The intended model uses Customers to filter ARSnapshot and Payments, and Calendar to filter Payments only. The AR snapshot remains fixed at 30 September 2026.

## Profile

[LinkedIn](https://www.linkedin.com/in/hee-jung-kim-1428781bb/) | [GitHub](https://github.com/hjkim20022)

## Technical references

- [Microsoft: star schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema)
- [Microsoft: group rows in Power Query](https://learn.microsoft.com/en-us/power-query/group-by)
- [Microsoft: merge queries](https://learn.microsoft.com/en-us/power-query/merge-queries-overview)
- [Microsoft: CALCULATE](https://learn.microsoft.com/en-us/dax/calculate-function-dax)
- [Microsoft: drill-through](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-drillthrough)
- [Microsoft: Publish to web](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web)

