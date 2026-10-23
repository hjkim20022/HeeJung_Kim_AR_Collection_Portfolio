// Create a blank query called ARSnapshot in Power Query.
// Paste this into Advanced Editor after importing Invoices and Payments.
// This is a fixed-date snapshot. Changing the date requires refresh.
let
    SnapshotDate = #date(2026, 9, 30),
    InvoiceTypes = Table.TransformColumnTypes(Invoices, {
        {"InvoiceID", type text}, {"CustomerID", type text},
        {"InvoiceDate", type date}, {"DueDate", type date},
        {"InvoiceAmountCAD", Currency.Type}, {"Disputed", type text},
        {"DisputeReason", type text}
    }),
    PaymentTypes = Table.TransformColumnTypes(Payments, {
        {"InvoiceID", type text}, {"PaymentDate", type date},
        {"PaymentAmountCAD", Currency.Type}
    }),
    InvoicesAtDate = Table.SelectRows(InvoiceTypes, each [InvoiceDate] <= SnapshotDate),
    PaymentsAtDate = Table.SelectRows(PaymentTypes, each [PaymentDate] <= SnapshotDate),
    PaidByInvoice = Table.Group(PaymentsAtDate, {"InvoiceID"}, {
        {"PaidToDateCAD", each List.Sum([PaymentAmountCAD]), Currency.Type}
    }),
    Joined = Table.NestedJoin(InvoicesAtDate, {"InvoiceID"}, PaidByInvoice, {"InvoiceID"}, "Paid", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(Joined, "Paid", {"PaidToDateCAD"}, {"PaidToDateCAD"}),
    ZeroForNoPayment = Table.ReplaceValue(Expanded, null, 0, Replacer.ReplaceValue, {"PaidToDateCAD"}),
    Balance = Table.AddColumn(ZeroForNoPayment, "OutstandingCAD", each Number.Round([InvoiceAmountCAD] - [PaidToDateCAD], 2), Currency.Type),
    DaysLate = Table.AddColumn(Balance, "DaysOverdue", each if [OutstandingCAD] > 0 then List.Max({0, Duration.Days(SnapshotDate - [DueDate])}) else 0, Int64.Type),
    Bucket = Table.AddColumn(DaysLate, "AgingBucket", each
        if [OutstandingCAD] < 0 then "Credit balance"
        else if [OutstandingCAD] = 0 then "Paid"
        else if [DaysOverdue] = 0 then "Current"
        else if [DaysOverdue] <= 30 then "1-30"
        else if [DaysOverdue] <= 60 then "31-60"
        else if [DaysOverdue] <= 90 then "61-90" else "91+", type text),
    BucketOrder = Table.AddColumn(Bucket, "AgingSort", each
        if [OutstandingCAD] < 0 then -1
        else if [OutstandingCAD] = 0 then 0
        else if [DaysOverdue] = 0 then 1
        else if [DaysOverdue] <= 30 then 2
        else if [DaysOverdue] <= 60 then 3
        else if [DaysOverdue] <= 90 then 4 else 5, Int64.Type),
    AsOf = Table.AddColumn(BucketOrder, "AsOfDate", each SnapshotDate, type date),
    Action = Table.AddColumn(AsOf, "ActionGroup", each
        if [OutstandingCAD] < 0 then "Review credit balance"
        else if [OutstandingCAD] = 0 then "Closed"
        else if [DaysOverdue] = 0 then "Not due"
        else if [Disputed] = "Yes" then "Dispute review"
        else if [DaysOverdue] > 90 or ([DaysOverdue] > 30 and [OutstandingCAD] >= 10000) then "Priority follow-up"
        else "Routine reminder", type text)
in
    Action
