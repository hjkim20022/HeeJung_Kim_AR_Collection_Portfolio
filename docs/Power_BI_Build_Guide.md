# Power BI build guide

Build a fixed-date snapshot for **30 September 2026**. Use the original Excel workbook or the four raw CSVs; choose one source route. The workbook route is described below.

## 1. Prepare the data

Import the named Customers, Invoices, Payments and Calendar tables from `data/AR_Collections_PowerBI_Starter.xlsx`. Choose Transform Data. Do not import the existing ARSnapshot table because you will rebuild it from raw records.

Set IDs, names, regions, industries, owners and dispute fields to Text. Set InvoiceDate, DueDate, PaymentDate and Calendar[Date] to Date. Use Fixed decimal number for CAD amounts. Use Whole number for Year, MonthNumber and YearMonthSort.

In Power Query, choose New Source > Blank Query. Name it **ARSnapshot**. Open Advanced Editor and replace its contents with `powerbi/ARSnapshot.pq`. The query references the imported Invoices and Payments queries by name.

Review the applied steps. Payments are filtered to the snapshot date and grouped by InvoiceID before merging. Missing payment matches become zero; unmatched invoices remain in the result. Invoice dates after the snapshot are excluded.

Confirm ARSnapshot has 480 rows. Disable load for the staging Invoices query. Keep Customers, ARSnapshot, Payments and Calendar enabled. Choose Close & Apply.

The supplied M code is prepared for this schema; its execution must be checked in Desktop. If you want an initial layout before implementing Power Query, the supplied reference CSV can be used temporarily, but label that version as using a prepared snapshot.

## 2. Create the model

Remove incorrect auto-detected relationships. Create these active, single-direction relationships:

| One side | Many side | Filter direction |
|---|---|---|
| Customers[CustomerID] | ARSnapshot[CustomerID] | Customers to ARSnapshot |
| Customers[CustomerID] | Payments[CustomerID] | Customers to Payments |
| Calendar[Date] | Payments[PaymentDate] | Calendar to Payments |

Do not add a relationship between Payments and ARSnapshot. Their invoice-level relationship is handled by the grouped transformation. Do not link Calendar to ARSnapshot for this design: Calendar filters cash receipts, while ARSnapshot is a fixed-date balance.

Mark Calendar as a date table using Date. Sort Calendar[YearMonth] by YearMonthSort. Sort ARSnapshot[AgingBucket] by AgingSort. Use fields from Customers for customer, region and industry filters.

## 3. Add measures and verify totals

Create each measure in `powerbi/Measures.dax` separately with Modeling > New measure. Use currency formatting with CAD in the visual titles; format Overdue Share as 0.0%.

Clear all filters and match these results:

| Measure | Expected result |
|---|---:|
| Outstanding AR | $1,548,971.19 |
| Overdue AR | $980,235.72 |
| Overdue Share | 63.2830% |
| Current AR | $568,735.47 |
| AR Over 90 Days | $471,979.98 |
| Open Invoices | 165 |
| Disputed Overdue AR | $263,310.83 |
| Priority Follow-up AR | $383,360.28 |
| Cash Collected, January-September | $3,324,752.27 |
| Cash Collected, September only | $424,614.20 |

Amounts should reconcile within $0.01. Reconcile both the all-customer total and selected customer C027: Outstanding AR and Overdue AR are each $62,415.58. Do not proceed past unexplained differences.

## 4. Build page 1: Overview

Use a 16:10 canvas, or a custom 1280 by 800 canvas to match the preview. Use a pale background, navy text, teal for current/cash values, and warm orange for overdue values. Use legible labels and limited decimal places in cards; preserve cents in the detailed table.

| Element | Fields/settings |
|---|---|
| Title | Accounts receivable & collections |
| Subtitle/card | Snapshot Date Label. Add Synthetic portfolio data / CAD. |
| Region slicer | Customers[Region] |
| Four cards | Outstanding AR, Overdue AR, Overdue Share, AR Over 90 Days |
| Aging bar chart | ARSnapshot[AgingBucket] and Outstanding AR; filter OutstandingCAD > 0; sort by AgingSort |
| Collection line chart | Calendar[YearMonth] and Cash Collected; filter Calendar[Date] to January 1-September 30, 2026 |
| Note | Receivables are a fixed-date balance. Monthly collections are cash receipts. |

Disable interactions from the aging chart to the collections chart. Do not add a general date slicer to this page. Selecting an aging bucket changes the balance population but should not imply that historic cash receipts are for that bucket.

## 5. Build page 2: Customers

Add Region and Industry slicers. Use a horizontal bar chart with CustomerName and Overdue AR, sorted descending, filtered to the top 10 customers by Overdue AR. Add cards for Disputed Overdue AR and AR Over 90 Days.

Add a customer table containing CustomerID, CustomerName, AccountOwner, Outstanding AR, Overdue AR and Disputed Overdue AR. This also supplies the CustomerID context for drill-through. The preview PDF shows the five largest balances for readability; use top 10 in the interactive report.

Use the three findings and two actions in README as your initial narrative. They refer to the unfiltered dataset. If users filter the page, either keep this narrative clearly labeled "All-customer snapshot findings" or replace it with measures that respond to filters. Do not display fixed findings as if they update with slicers.

## 6. Build page 3: Collection worklist

Use a table with CustomerName, AccountOwner, InvoiceID, DueDate, OutstandingCAD, DaysOverdue, Disputed, DisputeReason and ActionGroup. Filter OutstandingCAD > 0 and DaysOverdue > 0. Set IDs and DaysOverdue to Don't summarize. Use outstanding descending as the default sort, with the ActionGroup slicer to choose a queue.

Add Region and ActionGroup slicers. Add Customers[CustomerID] to Drill-through. Test by right-clicking a row in the customer table on page 2. The target page must show only that customer's invoices. Confirm the Back button returns to page 2. Clear the drill-through filter when using page 3 as an all-customer worklist.

ActionGroup rules are evaluated in this order:

1. Credit balance: review separately. None exists in the supplied data.
2. Zero balance: Closed. Positive balance with no overdue days: Not due.
3. Any overdue disputed balance: Dispute review.
4. Other overdue balances: Priority follow-up if more than 90 days overdue, or more than 30 days overdue with at least $10,000 outstanding.
5. Remaining overdue balances: Routine reminder.

These are demonstration routing rules. They are not validated collection policy, a default prediction or permission to write off balances. Actual follow-up dates and contact notes belong in a maintained operational record, not invented columns in a historical snapshot.

## 7. Check behavior and share

- Compare an unpaid, paid and partially paid invoice against the source records.
- Check due-today and 30/31, 60/61, 90/91-day boundaries.
- Check a customer filter changes both AR and payment results, while a collection-period filter changes only payments.
- Test drill-through, clear filters and reload the report.
- Save the PBIX and capture actual report and model screenshots.
- Replace the design-preview images in README with the real report images, and update the status accurately.
- Record the practice walkthrough after testing the report.

If your tenant permits Publish to web, it creates a public report that viewers can open without signing in. Use only this fictional dataset. Tenant settings and licensing determine availability. If public publishing is unavailable, share actual screenshots, the short recording and the GitHub case study as the initial portfolio.

Test the final viewing link in a private/signed-out window before putting it on your resume. Keep your existing working portfolio link until the replacement is tested. Neither this pack nor the preview has changed your existing public report.

## Resume use after completion

Only use the following after you personally build, test and can explain the report:

> Built an accounts receivable dashboard in Power BI using SQL, Power Query and DAX to analyse 480 synthetic invoices and 425 payment allocations; reconciled balances, identified overdue customer exposure and designed a collection worklist.

Add the verified public report and GitHub repository links as clickable hyperlinks. Keep the project under Projects, separate from professional treasury experience. Do not claim a reduction in overdue balances or recovered cash without a real measured outcome.
