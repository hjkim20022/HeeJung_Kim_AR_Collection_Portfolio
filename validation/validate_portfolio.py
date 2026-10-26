"""Re-run SQL and independently check this synthetic AR portfolio.

Run: python validation/validate_portfolio.py
Uses only the Python standard library. Source CSVs are never modified.
"""
from collections import defaultdict
import csv
from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "validation"
AS_OF = date(2026, 9, 30)
ZERO = Decimal("0.00")
MONEY_FIELDS = {
    "InvoiceAmountCAD", "PaidToDateCAD", "OutstandingCAD", "OverdueCAD",
    "Over90CAD", "DisputedOverdueCAD",
}
INT_FIELDS = {"DaysOverdue", "AgingSort", "IssueCount"}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def normalized(field, value):
    if field in MONEY_FIELDS:
        return money(value)
    if field in INT_FIELDS:
        return int(value)
    return str(value)


def compare_rows(expected, actual, key):
    left = {row[key]: row for row in expected}
    right = {row[key]: row for row in actual}
    errors = []
    if len(left) != len(expected) or len(right) != len(actual):
        errors.append("Duplicate row keys")
    if left.keys() != right.keys():
        errors.append("Row keys differ")
    for row_id in left.keys() & right.keys():
        a, b = left[row_id], right[row_id]
        if a.keys() != b.keys():
            errors.append(f"{row_id}: columns differ")
            continue
        for field in a:
            if normalized(field, a[field]) != normalized(field, b[field]):
                errors.append(f"{row_id}: {field} differs")
    return errors


def decimal_snapshot(invoices, payments):
    paid = defaultdict(lambda: ZERO)
    for row in payments:
        if date.fromisoformat(row["PaymentDate"]) <= AS_OF:
            paid[row["InvoiceID"]] += money(row["PaymentAmountCAD"])
    result = []
    for invoice in invoices:
        if date.fromisoformat(invoice["InvoiceDate"]) > AS_OF:
            continue
        amount = money(invoice["InvoiceAmountCAD"])
        paid_amount = paid[invoice["InvoiceID"]]
        outstanding = amount - paid_amount
        days = max(0, (AS_OF - date.fromisoformat(invoice["DueDate"])).days) if outstanding > 0 else 0
        if outstanding < 0:
            bucket, order, action = "Credit balance", -1, "Review credit balance"
        elif outstanding == 0:
            bucket, order, action = "Paid", 0, "Closed"
        elif days == 0:
            bucket, order, action = "Current", 1, "Not due"
        else:
            bands = [(30, "1-30", 2), (60, "31-60", 3), (90, "61-90", 4)]
            bucket, order = next(((label, sort) for cutoff, label, sort in bands if days <= cutoff), ("91+", 5))
            if invoice["Disputed"] == "Yes":
                action = "Dispute review"
            elif days > 90 or (days > 30 and outstanding >= 10000):
                action = "Priority follow-up"
            else:
                action = "Routine reminder"
        result.append({
            **invoice, "InvoiceAmountCAD": amount, "PaidToDateCAD": paid_amount,
            "OutstandingCAD": outstanding, "DaysOverdue": days,
            "AgingBucket": bucket, "AgingSort": order,
            "AsOfDate": AS_OF.isoformat(), "ActionGroup": action,
        })
    return result


def boundary_checks():
    schema = """
    CREATE TABLE Config (AsOfDate TEXT);
    INSERT INTO Config VALUES ('2026-09-30');
    CREATE TABLE Invoices (InvoiceID TEXT, CustomerID TEXT, InvoiceDate TEXT,
        DueDate TEXT, InvoiceAmountCAD NUMERIC, Disputed TEXT, DisputeReason TEXT);
    CREATE TABLE Payments (PaymentID TEXT, InvoiceID TEXT, CustomerID TEXT,
        PaymentDate TEXT, PaymentAmountCAD NUMERIC);
    """
    sql = (ROOT / "sql/01_snapshot.sql").read_text(encoding="utf-8")
    results = []

    def check(name, days, expected, amount="100.00", payments=(), disputed="No", invoice_date="2026-01-01"):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        try:
            conn.executescript(schema)
            conn.execute("INSERT INTO Invoices VALUES (?,?,?,?,?,?,?)", (
                "TEST", "C001", invoice_date, (AS_OF - timedelta(days=days)).isoformat(),
                amount, disputed, "Test dispute" if disputed == "Yes" else "",
            ))
            for i, (when, value) in enumerate(payments):
                conn.execute("INSERT INTO Payments VALUES (?,?,?,?,?)", (str(i), "TEST", "C001", when, value))
            conn.executescript(sql)
            row = conn.execute("SELECT * FROM ARSnapshot").fetchone()
            actual = None if row is None else (
                str(money(row["OutstandingCAD"])), row["DaysOverdue"],
                row["AgingBucket"], row["ActionGroup"],
            )
            results.append({"case": name, "passed": actual == expected})
        finally:
            conn.close()

    for days, bucket in [(0, "Current"), (1, "1-30"), (30, "1-30"), (31, "31-60"), (60, "31-60"), (61, "61-90"), (90, "61-90"), (91, "91+")]:
        action = "Not due" if days == 0 else "Priority follow-up" if days > 90 else "Routine reminder"
        unit = "day" if days == 1 else "days"
        check(f"Aging at {days} {unit} overdue", days, ("100.00", days, bucket, action))
    check("Paid invoice", 45, ("0.00", 0, "Paid", "Closed"), payments=[("2026-09-01", "100.00")])
    check("Two partial payments preserve invoice grain", 45, ("50.00", 45, "31-60", "Routine reminder"), payments=[("2026-09-01", "20.00"), ("2026-09-02", "30.00")])
    check("Payment after cutoff excluded", 15, ("100.00", 15, "1-30", "Routine reminder"), payments=[("2026-10-01", "100.00")])
    check("Payment on cutoff included", 15, ("0.00", 0, "Paid", "Closed"), payments=[("2026-09-30", "100.00")])
    check("Invoice after cutoff excluded", -1, None, invoice_date="2026-10-01")
    check("Dispute takes priority over age", 91, ("100.00", 91, "91+", "Dispute review"), disputed="Yes")
    check("Credit balance routed for review", 45, ("-50.00", 0, "Credit balance", "Review credit balance"), payments=[("2026-09-01", "150.00")])
    check("10000 CAD at 30 days remains routine", 30, ("10000.00", 30, "1-30", "Routine reminder"), amount="10000.00")
    check("Below 10000 CAD at 31 days remains routine", 31, ("9999.99", 31, "31-60", "Routine reminder"), amount="9999.99")
    check("10000 CAD at 31 days enters priority queue", 31, ("10000.00", 31, "31-60", "Priority follow-up"), amount="10000.00")
    return results


def main():
    subprocess.run([sys.executable, str(ROOT / "sql/run_analysis.py")], check=True, capture_output=True, text=True)
    customers = read_csv(ROOT / "data/Customers.csv")
    invoices = read_csv(ROOT / "data/Invoices.csv")
    payments = read_csv(ROOT / "data/Payments.csv")
    expected = decimal_snapshot(invoices, payments)
    actual = read_csv(ROOT / "sql/results/ARSnapshot.csv")
    reference = read_csv(ROOT / "data/ARSnapshot_reference.csv")
    sql_result = json.loads((ROOT / "sql/results/Reconciliation.json").read_text())
    checks = sql_result["checks"]
    comparisons = {
        "sql_snapshot": compare_rows(expected, actual, "InvoiceID"),
        "reference_snapshot": compare_rows(expected, reference, "InvoiceID"),
        "published_checks": compare_rows(checks, read_csv(HERE / "Checks.csv"), "CheckName"),
    }
    by_customer = {row["CustomerID"]: row for row in customers}
    summary = []
    for customer in customers:
        rows = [r for r in expected if r["CustomerID"] == customer["CustomerID"]]
        summary.append({
            **customer,
            "OutstandingCAD": sum((r["OutstandingCAD"] for r in rows), ZERO),
            "OverdueCAD": sum((r["OutstandingCAD"] for r in rows if r["DaysOverdue"] > 0), ZERO),
            "Over90CAD": sum((r["OutstandingCAD"] for r in rows if r["DaysOverdue"] > 90), ZERO),
            "DisputedOverdueCAD": sum((r["OutstandingCAD"] for r in rows if r["DaysOverdue"] > 0 and r["Disputed"] == "Yes"), ZERO),
        })
    worklist = [{**r, **by_customer[r["CustomerID"]]} for r in expected if r["DaysOverdue"] > 0]
    comparisons["customer_summary"] = compare_rows(summary, read_csv(HERE / "Customer_Summary.csv"), "CustomerID")
    comparisons["collection_worklist"] = compare_rows(worklist, read_csv(HERE / "Collection_Worklist.csv"), "InvoiceID")
    totals = {
        "invoice_amount_cad": sum((r["InvoiceAmountCAD"] for r in expected), ZERO),
        "payments_cad": sum((r["PaidToDateCAD"] for r in expected), ZERO),
        "outstanding_cad": sum((r["OutstandingCAD"] for r in expected), ZERO),
        "current_cad": sum((r["OutstandingCAD"] for r in expected if r["DaysOverdue"] == 0 and r["OutstandingCAD"] > 0), ZERO),
        "overdue_cad": sum((r["OutstandingCAD"] for r in expected if r["DaysOverdue"] > 0), ZERO),
    }
    comparisons["aggregate_sql_totals"] = [key for key, value in sql_result["summary"].items() if key in totals and money(value) != totals[key]]
    balance_difference = totals["invoice_amount_cad"] - totals["payments_cad"] - totals["outstanding_cad"]
    aging_difference = totals["current_cad"] + totals["overdue_cad"] - totals["outstanding_cad"]
    boundaries = boundary_checks()
    passed = not any(comparisons.values()) and not any(r["IssueCount"] for r in checks) and all(t["passed"] for t in boundaries) and balance_difference == 0 and aging_difference == 0
    result = {
        "status": "passed" if passed else "failed",
        "engine": "SQLite plus independent Python Decimal reconciliation",
        "snapshot_date": AS_OF.isoformat(),
        "source": "Committed synthetic CSV inputs in data/",
        "reproduce": "python validation/validate_portfolio.py",
        "source_counts": {"customers": len(customers), "invoices": len(invoices), "payment_allocations": len(payments)},
        "sql_validation_checks": checks,
        "invoice_rows_compared_to_reference_snapshot": len(reference),
        "comparison_errors": comparisons,
        "totals_cad": {key: str(value) for key, value in totals.items()},
        "balance_difference_cad": str(balance_difference),
        "aging_difference_cad": str(aging_difference),
        "customer_summary_rows_compared": len(summary),
        "collection_worklist_rows_compared": len(worklist),
        "boundary_tests": boundaries,
        "power_bi_status": "Power Query, DAX, report interactions and publication require separate testing in Power BI Desktop.",
    }
    (HERE / "Validation_Result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "sql_checks": len(checks), "boundary_tests": len(boundaries), "invoice_rows": len(reference), "comparison_errors": comparisons}, indent=2))
    if not passed:
        raise SystemExit("Validation failed; inspect validation/Validation_Result.json.")


if __name__ == "__main__":
    main()
