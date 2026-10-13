---
name: citation-discipline
description: Attribute every fact to the operation that produced it, and say plainly when something was not looked up.
---

# Citation discipline

Every concrete fact in your answer — a number, a name, a date, a status —
carries a short attribution naming where it came from:

> Three orders are open (`recent_orders`), the most recent placed 2026-09-14
> (`recent_orders`). The customer is on the growth plan (`find_customer`).

Rules, in order of importance:

1. **A fact with no source is not stated.** If you did not look it up, say
   that you did not: *"I have not checked their current balance."*
2. **Attribute to the operation, not to "the system".** `find_customer` is
   useful to a reader; "the database" is not.
3. **Do not attribute your own inference to a lookup.** If you added two
   numbers, say so: *"€430 total, added from the three order totals."*
4. **A failed call is a fact too.** *"`recent_orders` returned no customer
   with that id, so order history is unknown."*

## Why this skill exists

Two reasons, and the second is the one people do not expect.

**It makes the agent's reasoning checkable.** An answer that names its sources
can be verified line by line. An answer that does not has to be trusted whole,
and a confident sentence is indistinguishable from a fabricated one.

**It makes the agent's TOOL USE visible.** This is the half worth having on an
AgentBox install. Every operation an agent calls is brokered, classified, and
recorded — and an answer that cites its calls lets you line up what the agent
says it did against what the platform recorded it doing. When those two
disagree, you want to find out from a citation rather than from an incident.

It also exposes over-calling. An agent that cites the same lookup four times
in one answer is telling you it made four round trips where one would do.

## Trying it

Bind this skill alongside any example server, ask a question that needs two
lookups, and compare the attributions in the answer with the audit trail under
Security.
