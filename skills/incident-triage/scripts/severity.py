#!/usr/bin/env python3
"""Assign a severity to one incident summary, using this skill's rubric.

    python3 <skill root>/scripts/severity.py "<one-line summary>"

Prints the severity and the signals that produced it, and exits 0. Reads the
summary from argv, or from stdin when no argument is given.

Deterministic on purpose: the point is not that this is cleverer than the
model, it is that two triages of the same text agree. Where the model and this
script disagree, that disagreement is worth saying out loud rather than
quietly resolving.

Deliberately stdlib-only, offline and side-effect free. A skill's `scripts/`
directory is the one place a skill ships code the agent will execute, and
skill-scanner is the only gate on it -- package-guard governs package
installs, not arbitrary scripts. A helper here that opened a socket, shelled
out or wrote a file would be teaching the wrong thing in an example of the
folder shape, so this one does none of those.
"""

from __future__ import annotations

import re
import sys

#: First match wins, mirroring the rubric's own instruction. Order matters.
_ROWS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "S1",
        "data loss, corruption or unauthorised access is suspected",
        re.compile(
            r"\b(data loss|lost data|corrupt\w*|breach\w*|exfiltrat\w*|"
            r"unauthoris\w*|unauthoriz\w*|leaked?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "S1",
        "a core flow is unusable for most users",
        re.compile(
            r"\b(all|every|most|widespread|complete|total)\b.{0,40}"
            r"\b(users?|customers?|regions?|down|unavailable|failing)\b"
            r"|\b(outage|down for everyone|hard down)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "S2",
        "a core flow is degraded for a subset with no workaround",
        re.compile(
            r"\b(some|subset|partial|intermittent|degraded|slow|delayed|"
            r"timing out|timeouts?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "S3",
        "a workaround exists, or a non-core flow is affected",
        re.compile(
            r"\b(workaround|manually|retry|retries|only affects|edge case|"
            r"non-critical)\b",
            re.IGNORECASE,
        ),
    ),
)

#: Raises the severity by one row. Matches the rubric's own list.
_ESCALATORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "a sensitive flow is involved (auth, payment or data export)",
        re.compile(
            r"\b(auth\w*|login|log in|sign[- ]?in|password|payment|billing|"
            r"checkout|invoice|export)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "the blast radius is still growing",
        re.compile(
            r"\b(spreading|growing|escalating|more regions|worsening)\b", re.IGNORECASE
        ),
    ),
)

_ORDER = ("S1", "S2", "S3", "S4")


def _raise_one(severity: str) -> str:
    index = _ORDER.index(severity)
    return _ORDER[max(0, index - 1)]


def triage(summary: str) -> tuple[str, list[str]]:
    """The severity and the reasons for it, in the order they were applied."""
    text = summary or ""
    reasons: list[str] = []

    severity = "S4"
    for level, why, pattern in _ROWS:
        if pattern.search(text):
            severity = level
            reasons.append(f"{level}: {why}")
            break
    else:
        reasons.append("S4: nothing in the summary indicates user-visible impact")

    for why, pattern in _ESCALATORS:
        if pattern.search(text) and severity != "S1":
            severity = _raise_one(severity)
            reasons.append(f"raised to {severity}: {why}")

    return severity, reasons


def main(argv: list[str]) -> int:
    summary = " ".join(argv[1:]).strip() or sys.stdin.read().strip()
    if not summary:
        print('usage: severity.py "<one-line incident summary>"')
        return 2
    severity, reasons = triage(summary)
    print(severity)
    for reason in reasons:
        print(f"  - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
