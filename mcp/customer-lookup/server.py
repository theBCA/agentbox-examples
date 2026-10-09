"""customer-lookup -- reads only, and the one that gives response DLP something
real to inspect.

Two operations, both reads:

    find_customer(address)        one synthetic customer record
    recent_orders(customer_id)    that customer's last few orders

Neither matches any word on `classify_tool`'s sensitive lists, so neither is
ever held. That is the contrast worth seeing next to `task-board`'s
`delete_all_tasks`: approval is per operation, not per server, and a server
full of reads never interrupts anybody.

**The second reason this exists.** A customer record carries a national-id
field, so the answer coming back from here contains something SecureProxy's
response scanning is meant to catch. Nothing else in the shipped examples puts
sensitive-looking text in a RESULT rather than in a prompt, and the two are
scanned by different halves of the gateway. Sending the agent to look a
customer up and watching what reaches the model is the shortest demonstration
of that half.

Every value is generated fresh at import from `secrets`, never written down
here, so nothing resembling a real record sits in git history and each run
looks different. The people and company are invented.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("customer-lookup", host="0.0.0.0")

_ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def _digits(n: int) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(n))


def _seed() -> list[dict]:
    """Three invented customers, regenerated on every start."""
    now = datetime.now(timezone.utc)
    people = [
        ("Aylin Demir", "aylin.demir@northwind-example.test", "Northwind Fabrics"),
        (
            "Jonas Weber",
            "jonas.weber@harbourline-example.test",
            "Harbourline Logistics",
        ),
        ("Priya Raman", "priya.raman@cedarworks-example.test", "Cedarworks Studio"),
    ]
    rows = []
    for index, (name, email, company) in enumerate(people, start=1):
        rows.append(
            {
                "customer_id": f"CU-{1000 + index}",
                "name": name,
                "email": email,
                "company": company,
                # Deliberately shaped like a national id. Synthetic, random per
                # start, and belonging to nobody -- it is here so the gateway's
                # response scanning has something to find in a RESULT.
                "national_id": f"{_digits(3)}-{_digits(2)}-{_digits(4)}",
                "phone": f"+49 30 {_digits(4)} {_digits(4)}",
                "plan": ["starter", "growth", "enterprise"][index % 3],
                "since": (now - timedelta(days=90 * index)).date().isoformat(),
            }
        )
    return rows


_CUSTOMERS = _seed()
_ORDERS = {
    row["customer_id"]: [
        {
            "order_id": f"OR-{_digits(5)}",
            "placed": (datetime.now(timezone.utc) - timedelta(days=7 * n))
            .date()
            .isoformat(),
            "total_eur": round(120.0 * n + secrets.randbelow(400) / 10, 2),
            "status": ["delivered", "in transit", "processing"][n % 3],
        }
        for n in range(1, 4)
    ]
    for row in _CUSTOMERS
}


@mcp.tool()
def find_customer(email: str) -> dict:
    """Returns the customer record registered under one address.

    A read, and classified `read_only`. Worded without the word for
    electronic mail on purpose: that word is on the classifier's
    `sends_data_externally` list, and having it here put this operation in a
    class it has nothing to do with. Harmless -- that class is not sensitive
    and nothing was held -- but a misleading label on a security surface, and
    a one-word fix.

    The record includes contact details and a national-id field, so what comes
    back stands in for the kind of answer a support agent gets from a real
    system.
    """
    wanted = (email or "").strip().lower()
    if not wanted:
        return {"ok": False, "error": "email must not be empty"}
    for row in _CUSTOMERS:
        if row["email"].lower() == wanted:
            return {"ok": True, "customer": row}
    return {
        "ok": False,
        "error": f"no customer with email {wanted}",
        "known_emails": [row["email"] for row in _CUSTOMERS],
    }


@mcp.tool()
def recent_orders(customer_id: str) -> dict:
    """Returns the most recent orders for one customer id."""
    wanted = (customer_id or "").strip().upper()
    orders = _ORDERS.get(wanted)
    if orders is None:
        return {
            "ok": False,
            "error": f"no customer with id {wanted}",
            "known_ids": sorted(_ORDERS),
        }
    return {"ok": True, "customer_id": wanted, "orders": orders, "count": len(orders)}


if __name__ == "__main__":
    mcp.run(transport="sse")
