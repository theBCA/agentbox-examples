---
name: incident-triage
description: Triage an incident report to a severity with the rubric in this skill, then write it up in the standard shape.
---

# Incident triage

When given an incident, outage or alert, do three things in order.

1. **Assign a severity** using `references/severity-rubric.md`. It is a table,
   not a judgement call — read it rather than guessing.
2. **Check your own answer** by running the script in this skill:
   `python3 <skill root>/scripts/severity.py "<one-line summary>"`. It applies
   the same rubric mechanically. Where it disagrees with you, say so and
   explain which signal you weighted differently.
3. **Write it up** in the shape of `assets/incident-report.md`. Same headings,
   same order, every time.

Never assign a severity without naming the rubric row that produced it.
An incident with no user impact is **S4**, not "low" — the rubric's
vocabulary is the one the on-call rota is scheduled against.

## What this skill demonstrates

A skill is a **directory**, not a single file, and this one uses all three
kinds of content so you can see when each is worth having:

- **`references/severity-rubric.md`** — read on demand, not up front. It is a
  lookup table; loading it into every prompt would cost tokens on every
  unrelated turn. Read it when triaging and not otherwise.
- **`scripts/severity.py`** — a mechanical check the agent can *run*. The
  value is not that it is cleverer than the model; it is that it is
  deterministic, so two triages of the same text agree. Stdlib only, offline,
  and it writes nothing.
- **`assets/incident-report.md`** — the output shape, so five incidents come
  out comparable instead of five different essays.

Your instructions name this skill's root path; everything above is relative
to it.

## Trying it

Paste an outage description into the app's console and ask for a triage. Then
ask for the same text again — the severity should be identical, which is the
script doing its job rather than the model being consistent by luck.
