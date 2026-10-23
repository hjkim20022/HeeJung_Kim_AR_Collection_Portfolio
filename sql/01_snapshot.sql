-- SQLite dialect. Run after loading data with sql/run_analysis.py.
-- Aggregate payments to invoice grain BEFORE joining invoices.
-- Dates are ISO YYYY-MM-DD. Arithmetic uses integer cents.
DROP VIEW IF EXISTS ARSnapshot;
CREATE VIEW ARSnapshot AS
WITH Paid AS (
    SELECT InvoiceID,
           SUM(CAST(ROUND(PaymentAmountCAD * 100) AS INTEGER)) AS PaidCents
    FROM Payments
    WHERE PaymentDate <= (SELECT AsOfDate FROM Config)
    GROUP BY InvoiceID
), Balance AS (
    SELECT i.*, c.AsOfDate,
           CAST(ROUND(i.InvoiceAmountCAD * 100) AS INTEGER) AS InvoiceCents,
           COALESCE(p.PaidCents, 0) AS PaidCents,
           CAST(ROUND(i.InvoiceAmountCAD * 100) AS INTEGER) - COALESCE(p.PaidCents, 0) AS OutstandingCents
    FROM Invoices i CROSS JOIN Config c
    LEFT JOIN Paid p ON p.InvoiceID = i.InvoiceID
    WHERE i.InvoiceDate <= c.AsOfDate
), Aged AS (
    SELECT *, CASE WHEN OutstandingCents > 0
             THEN MAX(0, CAST(julianday(AsOfDate) - julianday(DueDate) AS INTEGER))
             ELSE 0 END AS DaysOverdue
    FROM Balance
)
SELECT InvoiceID, CustomerID, InvoiceDate, DueDate,
       InvoiceCents / 100.0 AS InvoiceAmountCAD,
       PaidCents / 100.0 AS PaidToDateCAD,
       OutstandingCents / 100.0 AS OutstandingCAD,
       DaysOverdue,
       CASE WHEN OutstandingCents < 0 THEN 'Credit balance'
            WHEN OutstandingCents = 0 THEN 'Paid'
            WHEN DaysOverdue = 0 THEN 'Current'
            WHEN DaysOverdue <= 30 THEN '1-30'
            WHEN DaysOverdue <= 60 THEN '31-60'
            WHEN DaysOverdue <= 90 THEN '61-90' ELSE '91+' END AS AgingBucket,
       CASE WHEN OutstandingCents < 0 THEN -1
            WHEN OutstandingCents = 0 THEN 0
            WHEN DaysOverdue = 0 THEN 1
            WHEN DaysOverdue <= 30 THEN 2
            WHEN DaysOverdue <= 60 THEN 3
            WHEN DaysOverdue <= 90 THEN 4 ELSE 5 END AS AgingSort,
       Disputed, DisputeReason, AsOfDate,
       CASE WHEN OutstandingCents < 0 THEN 'Review credit balance'
            WHEN OutstandingCents = 0 THEN 'Closed'
            WHEN DaysOverdue = 0 THEN 'Not due'
            WHEN Disputed = 'Yes' THEN 'Dispute review'
            WHEN DaysOverdue > 90 OR (DaysOverdue > 30 AND OutstandingCents >= 1000000)
                 THEN 'Priority follow-up'
            ELSE 'Routine reminder' END AS ActionGroup
FROM Aged;
