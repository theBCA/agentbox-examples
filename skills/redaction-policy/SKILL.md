---
name: redaction-policy
description: Never repeat credentials, national ids, card numbers or personal contact details back to the user; write a placeholder instead and say what was withheld.
---

# Redaction policy

When anything you have read contains a secret or a personal identifier, do not
repeat its value. Write a placeholder in its place and name what you withheld.

- Credentials, API keys, tokens, passwords, private keys → `[REDACTED:credential]`
- National ids, tax ids, passport numbers → `[REDACTED:national-id]`
- Card numbers, IBANs, account numbers → `[REDACTED:financial]`
- Personal phone numbers and home addresses → `[REDACTED:contact]`

Say once, plainly, what you withheld and why: *"The record contained a
national id; I have not repeated it."* Do not paraphrase a secret, spell it
out, split it across lines, or describe it precisely enough to reconstruct.

Two things are **not** redacted, because over-redaction destroys the answer:
public company details, and identifiers the user supplied themselves in the
current request.

## Why this skill exists, and what it is not

**This skill asks. SecureProxy enforces.** That distinction is the reason it
is worth reading rather than just installing.

An instruction in a skill is guidance to a model, and a model can be talked
out of guidance — that is what prompt injection is. SecureProxy's data-loss
scanning sits outside the model, in the gateway every request and response
passes through, and it cannot be argued with. Neither replaces the other:

- with only the skill, a poisoned document can talk the agent into echoing a
  secret, and nothing stops it;
- with only the gateway, the agent keeps trying and keeps being refused, and
  the user sees `403` instead of an answer.

Together the agent behaves well by default and is prevented when it does not.
That is defence in depth in one page, and you can watch both halves: ask the
agent to look up a customer whose record carries a national id. With this
skill bound, it should withhold the value on its own. Then look at the
Security tab to see whether the gateway also had something to say.

## Trying it

Bind this skill, then bind the `customer-lookup` example server and ask the
agent to summarise a customer. The record it receives deliberately contains a
national-id field.
