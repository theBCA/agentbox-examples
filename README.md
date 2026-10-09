# examples/

Skills and MCP servers you can drop into your own AgentBox application. Every
one runs with **no credential and no internet**, and each makes a *different*
control decide — so the library doubles as the shortest tour of the platform.

Nothing here is imported automatically. Copy a directory into your app's
repository, rebuild, and it is yours.

## MCP servers

| Server | Operations | What it demonstrates |
|---|---|---|
| [`task-board`](mcp/task-board/) | `add_task`, `list_tasks`, `complete_task`, **`delete_all_tasks`** | The simplest useful server, and the destructive-operation hold. Start here. |
| [`customer-lookup`](mcp/customer-lookup/) | `find_customer`, `recent_orders` | Reads are never held — and the record carries a national-id field, so the gateway's **response** scanning has something real to inspect. |
| [`expense-approvals`](mcp/expense-approvals/) | `list_pending`, **`approve_expense`**, **`refund_expense`**, **`delete_expense`** | Three operations held for **two different reasons**, one line apart in the same file. |

**Bold operations are held for an operator.** That is not a property of the
server — it is per operation, decided by `cli.mcp_operation_class.classify_tool`
from the operation's name and the first line of its docstring:

| Class | Words that reach it | Held? |
|---|---|---|
| `destructive` | delete, remove, drop, destroy, purge, wipe, truncate, terminate, kill | **yes** |
| `financial_payment_identity` | payment, invoice, charge, refund, transfer, withdraw, billing, ssn, passport… | **yes** |
| `accesses_credentials` | credential, secret, password, api_key, token, auth, vault, oauth | **yes** |
| `sends_data_externally` | send, post, publish, notify, email, upload, share, export | no |
| `writes_external` | write, create, update, edit, modify, set, save, insert | no |

**Read that table before naming your own operations**, because it cuts both
ways and the examples show it in both directions:

- `approve_expense` is held **only** because its summary line contains
  *payment*. Nothing understood that approving an expense commits money — the
  word did it. Reword the line and the gate disappears.
- `add_task` classifies as `read_only` even though it writes, because
  *records* is on no list.

So treat it as a good default, not as the decision. Where an operation
genuinely needs a gate, declare it with MCP annotations rather than leaving it
to vocabulary. `tests/unit/tools/test_examples_library.py` holds every claim
above to the real classifier.

## Skills

| Skill | Shape | What it demonstrates |
|---|---|---|
| [`redaction-policy`](skills/redaction-policy/) | one file | **A skill asks; a control enforces.** Defence in depth in one page — and you can watch both halves. |
| [`citation-discipline`](skills/citation-discipline/) | one file | Skills shaping **tool use**, so the agent's account of what it did can be lined up against the audit trail. |
| [`incident-triage`](skills/incident-triage/) | `SKILL.md` + `references/` + `scripts/` + `assets/` | All three kinds of skill content, and **when each is worth having**. |

A skill is a **directory**, not a file. `incident-triage` is the one to read
for that: a rubric in `references/` read on demand rather than loaded into
every prompt, a deterministic check in `scripts/` the agent *runs*, and an
output shape in `assets/`.

A skill's `scripts/` is the one place it ships code the agent will execute,
and the Skill Scanner is the only gate on it — Package Guard governs package
installs, not arbitrary scripts. The example there is stdlib-only, offline and
writes nothing, deliberately.

## Adding one to your application

**A skill** — copy it into your repository's `skills/` directory:

```bash
cp -r examples/skills/redaction-policy  <your-app>/skills/
```

Rebuild the app. A bundled skill is scanned, and **auto-approved once it scans
clean** — bundling it from your own repository is itself the trust decision.

**An MCP server** — copy it into your repository's `mcp/` directory:

```bash
cp -r examples/mcp/task-board  <your-app>/mcp/
```

All three of `Dockerfile`, `server.py` and `env.example` must be present, even
if `env.example` is empty. A directory missing one is skipped with a warning
rather than offered for binding, and the app then refuses to be created with
*"Unknown bundled MCP server(s) for this source"* — which names the server
without saying what is missing. Measured 2026-09-21, on these very examples.

Rebuild, then approve it. A bundled MCP server is **deliberately not
auto-bound**, unlike a skill:

1. **Admin → MCP**, find `<your-app-id>__task-board`
2. Enable it, then validate it
3. Approve its **tool fingerprint**
4. Bind it to the application
5. **Rebuild**

A freshly added app therefore cannot call its own bundled server, by design —
that is the approval gate working, not a wiring fault. Until step 5 the bridge
answers `502 MCP server is not assigned to this application.`

## Known: a SECOND bundled server may not come up

Measured live on a real install 2026-09-21, and it contradicts the five steps
above, so read this before following them.

An application that bundles **one** MCP server works end to end. The starter's
own `notes-server` was enabled, validated, fingerprint-approved, bound and
rebuilt, and then `save_note` persisted a record and `list_notes` read it
back — and `delete_all_notes` was held for an operator with an approval id,
exactly as documented.

An application bundling **two** was not so reliable. On one app, `task-board`
went through all five steps cleanly: 4 tools discovered, fingerprint approved,
bound, and every operation called through the bridge — `list_tasks` returned
its JSON and `delete_all_tasks` came back `403 This action (destructive)
requires approval`. On a second app, the same server ended up stuck:

```
pipeline_state         registered
enabled                true
health_status          unreachable
tools                  []
last_validation_error  "server and url are required"
```

The container was up, listening on 8000, uvicorn started, on the right network
with the right recorded IP — and its log showed **zero inbound requests**. The
controller's effective registry contained only the first server. So it could
not be fingerprinted, bound or called, and the state is one it cannot leave on
its own: discovery needs a probe, and the probe never comes.

The divergence was the first step: `enable` returned **409 Conflict** on that
app and 200 on the other. A later retry of `enable` returned 200 — too late.

**What an operator sees is the worst part.** `fingerprint/approve` then fails
with `502 managed-mcp-bridge unreachable: Client error '404 Not Found'`, which
sends them to check a service that is healthy and answering. The bridge's own
404 means *that server is not in my registry* — precise and actionable — and
it is flattened into an outage report on the way out.

**So, for now:** add one example server at a time, check
`GET /api/v1/admin/mcp/<app-id>__<name>/status` shows `health_status: healthy`
and a non-empty `tools` before moving on, and if `enable` returns 409 delete
the app and re-add it rather than retrying the remaining steps.

## Naming: pick something specific

Bindings are made by **name**, and a name that two applications share is
refused rather than resolved by guesswork (`422 Skill name … is not unique on
this install`). An application's own bundled skill always wins its own name,
so copying these into one app is safe — but if you copy the same skill into
two applications and neither bundles it, rename one. `executive-summary-tone`
in the shipped starters is exactly this case.

## What is deliberately absent

Two proposed servers are **not** here yet, pending a decision, because they
are sharp enough to be worth discussing before they become something people
copy:

- **`web-fetch`** (`fetch(url)`) — would demonstrate egress policy driven by
  the *agent's* choice of destination rather than by an app endpoint, which is
  the realistic threat shape. The current egress demo cannot show that.
- **`file-sandbox`** (`read_file` / `write_file` scoped to the writable path)
  — would demonstrate agentic-file-guard scanning what the agent writes to
  itself.

And one for `demos/` rather than here: a **deliberately poisoned skill**, so
the Skill Scanner has something real to quarantine. That belongs beside the
other adversarial fixtures, never in a directory whose purpose is to be
copied.
