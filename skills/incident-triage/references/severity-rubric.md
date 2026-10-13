# Severity rubric

Read top to bottom and stop at the **first** row that matches. The first match
wins; do not average rows or pick the one that feels right.

| Severity | User impact | Data | Response |
|---|---|---|---|
| **S1** | A core flow is unusable for most users, or any data loss or unauthorised access is suspected | Loss, corruption or exposure suspected | Page immediately, around the clock |
| **S2** | A core flow is degraded or unusable for a subset, with no workaround | Intact | Page during working hours, same day |
| **S3** | A non-core flow is affected, or a core flow has a usable workaround | Intact | Next working day |
| **S4** | No user-visible impact: internal noise, a flapping alert, a cosmetic defect | Intact | Scheduled with other work |

## Signals that raise a severity by one row

Applied **after** the table above has chosen a row, and at most once. S1 is
already the top, so nothing raises it further.

- Authentication, payment or data-export flows are involved.
- The blast radius is growing while you are reading the report.

## Signals that do NOT raise it

- The report is emphatic, or came from someone senior.
- The incident is embarrassing.
- It happened before.

Urgency is about impact, not about who is asking. Two engineers reading the
same report with this table should reach the same row — if they do not, the
table needs a row, not a debate.

## Worked examples

Every row below is the actual output of `scripts/severity.py`, including the
escalation step — not a separate opinion about what it should say. A test in
the repo keeps them equal, because a rubric whose examples disagree with its
own script teaches the wrong lesson twice.

| Report | Severity | How it got there |
|---|---|---|
| Payments returning 503 in three regions for all users for 47 minutes | **S1** | core flow unusable for most users |
| Customer records may have leaked to an unauthorised third party | **S1** | data loss or unauthorised access suspected |
| Password reset emails delayed by about 20 minutes | **S1** | S2 (degraded, no workaround), raised by the auth signal |
| Search results load slowly for some users | **S2** | core flow degraded for a subset |
| Export to CSV fails for files over 50MB, smaller files fine with a workaround | **S2** | S3 (workaround exists), raised by the data-export signal |
| A disk-usage alert fires nightly at 04:00 and clears itself | **S4** | no user-visible impact |

Note the third and fifth rows. Both were raised one level by a flow signal,
and both are the kind of answer people argue about — which is the point of
having a script: the rubric decides, once, and the argument becomes a proposal
to change a row rather than a debate per incident.
