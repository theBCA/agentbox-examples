"""expense-approvals -- a business action where "should a human confirm this?"
answers itself.

Four operations, and the interesting part is that they are held for two
DIFFERENT reasons:

    list_pending()        a read; runs immediately
    approve_expense(id)   held -- the first line says "payment"
    refund_expense(id)    held -- "refund" is on the same financial list
    delete_expense(id)    held -- "delete", by the DESTRUCTIVE list instead

Three of the four are held, by two different patterns, which is the point:
the gate is about what an operation does rather than which server it lives
on, and operations a few lines apart in one file are treated differently.

**The classifier reads WORDS, in the name and the first docstring line.** That
is worth knowing before it surprises you, and it cuts both ways. Measured
against `cli.mcp_operation_class.classify_tool`:

* `approve_expense` is held only because its first line contains *payment*.
  Rewording that line to "cleared for release" makes the same operation run
  unheld -- so a money-moving operation can lose its gate to an innocent
  edit.
* `add_task` in the `task-board` example classifies as `read_only` even though
  it writes, because *records* is on no list.

So treat the heuristic as a good default and not as the decision. Where an
operation genuinely needs a gate, MCP annotations state it outright instead of
leaving it to vocabulary.

Amounts and ids are generated fresh at import. The vendors are invented.
"""

from __future__ import annotations

import secrets
import threading
from datetime import datetime, timedelta, timezone

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("expense-approvals", host="0.0.0.0")

_LOCK = threading.Lock()


def _seed() -> list[dict]:
    now = datetime.now(timezone.utc)
    vendors = [
        ("Harbourline Logistics", "freight"),
        ("Cedarworks Studio", "design"),
        ("Northwind Fabrics", "materials"),
        ("Blue Kettle Catering", "hospitality"),
    ]
    rows = []
    for index, (vendor, category) in enumerate(vendors, start=1):
        rows.append(
            {
                "expense_id": f"EX-{2000 + index}",
                "vendor": vendor,
                "category": category,
                "amount_eur": round(250.0 * index + secrets.randbelow(900) / 10, 2),
                "submitted": (now - timedelta(days=index)).date().isoformat(),
                "status": "pending",
            }
        )
    return rows


_EXPENSES = _seed()


def _find(expense_id: str) -> dict | None:
    wanted = (expense_id or "").strip().upper()
    for row in _EXPENSES:
        if row["expense_id"] == wanted:
            return row
    return None


def _missing(expense_id: str) -> dict:
    return {
        "ok": False,
        "error": f"no expense with id {(expense_id or '').strip().upper()}",
        "known_ids": [row["expense_id"] for row in _EXPENSES],
    }


@mcp.tool()
def list_pending() -> dict:
    """Returns every expense still awaiting a decision."""
    rows = [row for row in _EXPENSES if row["status"] == "pending"]
    return {
        "ok": True,
        "expenses": rows,
        "count": len(rows),
        "total_eur": round(sum(row["amount_eur"] for row in rows), 2),
    }


@mcp.tool()
def approve_expense(expense_id: str) -> dict:
    """Marks one expense as approved for payment.

    Held for an operator, and by the FINANCIAL list rather than the
    destructive one -- because this line says *payment*, not because anything
    understood that approving an expense commits money. Reword it and the gate
    goes away, which is the caveat the module docstring opens with.
    """
    row = _find(expense_id)
    if row is None:
        return _missing(expense_id)
    with _LOCK:
        row["status"] = "approved"
        row["decided_at"] = datetime.now(timezone.utc).isoformat()
    return {"ok": True, "expense": row}


@mcp.tool()
def refund_expense(expense_id: str) -> dict:
    """Refunds an already-paid expense back to the payer.

    Held for an operator: *refund* is on the financial word list, so this
    reaches the sensitive-actions queue rather than the ledger -- the same
    pattern that holds `approve_expense`, and a different one from
    `delete_expense` below.
    """
    row = _find(expense_id)
    if row is None:
        return _missing(expense_id)
    with _LOCK:
        row["status"] = "refunded"
        row["decided_at"] = datetime.now(timezone.utc).isoformat()
    return {"ok": True, "expense": row}


@mcp.tool()
def delete_expense(expense_id: str) -> dict:
    """Deletes one expense record permanently.

    Held for an operator, by the destructive word list rather than the
    financial one.
    """
    global _EXPENSES
    row = _find(expense_id)
    if row is None:
        return _missing(expense_id)
    with _LOCK:
        _EXPENSES = [r for r in _EXPENSES if r["expense_id"] != row["expense_id"]]
    return {"ok": True, "deleted": row["expense_id"], "count": len(_EXPENSES)}


if __name__ == "__main__":
    mcp.run(transport="sse")
