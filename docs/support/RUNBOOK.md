# Local engine support runbook

This runbook covers the implemented Python/SQLite engine and synthetic demonstration. Added during maintenance on 10 November 2026, it does not describe a production service, real customer incident or AWS deployment.

## Establish the problem

Record the repository commit, Python/dependency versions, exact command, run ID, expected behaviour, observed state and first failing transition. Distinguish rejected input, failed tasks, in-flight requests and unknown outcomes. Preserve the database and export before attempting a repair.

The demonstration reports its database/export paths. In the JSON export, inspect the run `status` and each task's `status`, `attempts`, `error`, `deadline`, `request.request_hash` and ordered `events`. Execution success remains separate from `business_acceptance`.

Start in `runtime/` after installing dependencies:

```bash
python -B -m examples.support_case --scenario success
python -B -m examples.support_case --scenario retry
python -B -m examples.support_case --scenario ambiguous
```

These use the real engine, an injected clock and scripted fixture responses. They make no network calls or changes to an inventory service.

## State and recovery guide

| State or error | Meaning | Next action |
|---|---|---|
| `WAITING_HOST` | A persisted request has no acceptable receipt yet | Compare request hash, attempt, mode and deadline with the host observation. `resume()` retains an unexpired request without dispatching a duplicate. |
| `RETRYABLE_FAILURE` | A reversible task failed within its budget | Inspect `error`, `attempts` and `next_attempt_at`. After backoff, `resume()` admits the next attempt. Do not create a new run to bypass its budget. |
| `UNKNOWN_PENDING_RECONCILIATION` | The outcome cannot be established safely | Preserve the original request identity and collect evidence from its executor. There is no automatic retry. A matching, authorised receipt can reconcile the original request. Escalate if none is available. |
| `WAITING_APPROVAL` | Dispatch needs approval of the exact action hash | Review actual inputs, action and hash. Changed inputs need a new matching approval. A plugin or dashboard does not grant external permission. |
| `BLOCKED` | Policy, input binding or a dependency prevents execution | Inspect `GUARDIAN`/`TRANSITION` events and task errors. Correct the workflow/input through a new version or run as appropriate. Do not edit SQLite rows to fabricate success. |
| `FAILED` | No further automatic attempt is admitted | Preserve evidence and correct the cause. A late cancellation leaves this outcome intact. |
| `SUCCEEDED` | A schema-valid output and applicable evidence were accepted | Review the output separately for business acceptance. A late cancellation leaves the completed outcome intact. |
| `LOCAL_HANDLER_ERROR` mentioning `optional title` | Retrieval data contains a non-string title | Correct the corpus: `id`, `text` and any `title` must be strings. This is an input-contract problem, not a missing model or API key. |

## Read-only SQLite inspection

Run this Python snippet from `runtime/` after the `retry` demo. Use the actual path returned by your run if different:

```python
import json
import sqlite3
from pathlib import Path

database = Path(".demo-state/retry/state.sqlite").resolve()
with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
    connection.row_factory = sqlite3.Row
    for row in connection.execute("SELECT run_id, status, updated FROM runs ORDER BY created"):
        print(dict(row))
    for row in connection.execute("SELECT run_id, task_id, record FROM tasks"):
        record = json.loads(row["record"])
        print(row["run_id"], row["task_id"], record["status"], record["attempts"], record["error"])
    for row in connection.execute("SELECT sequence, run_id, task_id, kind, details FROM events ORDER BY sequence"):
        print(dict(row))
```

Use a copy for deeper investigation. A writable `Engine` instance creates/maintains schema and starts write transactions, so it is not read-only inspection.

## Setup and receipt troubleshooting

| Symptom | Check |
|---|---|
| `No module named core` or `examples.support_case` | Activate the intended environment and run the documented commands from `runtime/`. |
| `No module named jsonschema` | Install `runtime/requirements.txt` into that same interpreter. |
| `unable to open database file` | Choose a writable `--output-dir`; check permissions and free space. |
| `database is locked` | Identify another writer holding a transaction. The engine uses `BEGIN IMMEDIATE` and a bounded busy timeout. Avoid deleting state or launching parallel repair writers. |
| Receipt rejected after timeout | Use `resume()` to process timeout recovery. Do not attach an old receipt to a new attempt: request hashes are attempt-specific. |
| Receipt mode/evidence rejected | Offline receipts require `FIXTURE` evidence. A fixture cannot complete a live host request. Check both modes. |
| Pinned workflow/skill integrity failure | Compare versions/hashes with preserved source. Restore exact expected source or create a reviewed new version rather than accepting changed bytes silently. |

Cancellation stops local acceptance for the cancelled run; it cannot recall external effects. Cancelling unresolved work abandons that run's local reconciliation and is not proof that an external action never happened.

## Engineering escalation template

```text
Title: <state/error and affected local operation>
Source: <repository commit and changed-file status>
Environment: <OS, Python, dependencies>
Run/task: <run ID, task ID, attempt and scenario>
Expected: <specific contract or expected transition>
Observed: <actual state, error code and first relevant event>
Reproduce: <minimal inputs and exact commands>
Evidence: <reviewed export, ordered event range, relevant test>
Impact: <what is blocked; any external outcome still unknown>
Workaround: <verified workaround, or none established>
Requested decision: <input correction, code repair or reconciliation owner>
```

Review inputs/evidence before sharing. Recognised secret patterns are redacted, but exports may contain arbitrary user data. The included demonstration contains synthetic data only.

## Maintenance regressions

```bash
python -B -m unittest discover -s tests -p "test_support_regressions.py" -v
```

These reproduce terminal-cancellation and malformed-title problems addressed in the [10 November maintenance record](../verification/2026-11-10-maintenance.md).
