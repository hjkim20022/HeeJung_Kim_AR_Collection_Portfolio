-- Every result should be zero for this demonstration dataset.
SELECT 'Duplicate invoice IDs' AS CheckName, COUNT(*) - COUNT(DISTINCT InvoiceID) AS IssueCount FROM Invoices
UNION ALL SELECT 'Duplicate payment IDs', COUNT(*) - COUNT(DISTINCT PaymentID) FROM Payments
UNION ALL SELECT 'Invoices without customers', COUNT(*) FROM Invoices i LEFT JOIN Customers c USING(CustomerID) WHERE c.CustomerID IS NULL
UNION ALL SELECT 'Payments without invoices', COUNT(*) FROM Payments p LEFT JOIN Invoices i USING(InvoiceID) WHERE i.InvoiceID IS NULL
UNION ALL SELECT 'Payment customer mismatch', COUNT(*) FROM Payments p JOIN Invoices i USING(InvoiceID) WHERE p.CustomerID <> i.CustomerID
UNION ALL SELECT 'Payment before invoice', COUNT(*) FROM Payments p JOIN Invoices i USING(InvoiceID) WHERE p.PaymentDate < i.InvoiceDate
UNION ALL SELECT 'Due date before invoice', COUNT(*) FROM Invoices WHERE DueDate < InvoiceDate
UNION ALL SELECT 'Nonpositive invoices', COUNT(*) FROM Invoices WHERE InvoiceAmountCAD <= 0
UNION ALL SELECT 'Nonpositive payments', COUNT(*) FROM Payments WHERE PaymentAmountCAD <= 0
UNION ALL SELECT 'Negative outstanding balances', COUNT(*) FROM ARSnapshot WHERE OutstandingCAD < 0;
