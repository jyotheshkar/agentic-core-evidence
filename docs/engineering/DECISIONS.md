# Engineering decisions for the local engine

Recorded 10 November 2026 from implemented source and maintenance review. These decisions cover a local prototype, not historical production operations or an AWS deployment.

## 1. Keep checkpoints and events in SQLite

**Decision:** store workflows, runs, tasks, approval records and ordered events together. State changes use `BEGIN IMMEDIATE` transactions and commit together; failures roll back.

**Reason:** a local process can resume after restart without coordinating a separate database service. Ordered events connect the current task state to preceding decisions.

**Tradeoff:** SQLite permits one writer at a time with bounded contention waiting. This is a local sequential engine, not a distributed scheduler. Events are local observations rather than independent attestations of external work.

**Evidence:** `Engine._connection`, `_transition`, `_event`; checkpoint and racing-receipt tests in `runtime/tests/test_core_engine.py`.

## 2. Separate retryable failure from unknown outcome

**Decision:** admit bounded exponential backoff for declared reversible tasks. An ambiguous outcome moves to `UNKNOWN_PENDING_RECONCILIATION` without automatic redispatch. A later receipt must match the original request and current authority.

**Reason:** a missing acknowledgement does not prove failure. Repeating uncertain work can duplicate effects. Stable run/task IDs, request hashes and attempt numbers support investigation of the original attempt.

**Tradeoff:** work may remain unresolved until the host supplies reliable evidence. The caller's reversibility declaration must be correct. The local engine cannot guarantee remote exactly-once execution or undo external effects.

**Evidence:** `_failure`, `submit_receipt`, `resume`; timeout/stale-receipt and ambiguous-reconciliation tests; [offline scenarios](../../runtime/examples/support_case.py).

## 3. Bind acceptance to request, schema and mode

**Decision:** validate output schemas, request hashes, current authority and evidence mode before accepting receipts. Keep referenced text as untrusted data. The local retrieval handler uses deterministic lexical overlap.

**Reason:** output from an old attempt, changed input or an offline fixture must not complete a different live request. Lexical retrieval makes data flow inspectable without model credentials.

**Tradeoff:** schema validity establishes shape rather than truth or business acceptance. Local receipts are host attestations, not provider signatures. Lexical overlap is not factual confidence or a semantic relevance metric.

**Evidence:** `contracts.validate`, `_dispatch_context`, `_retrieve`, `submit_receipt`; fixture/live, schema and hash-binding tests.

## 4. Preserve terminal outcomes on late cancellation

**Reproduced problem:** `cancel()` after success/failure rewrote the run to `CANCELLED` while tasks retained their completed states, creating contradictory diagnostics.

**Decision:** make cancellation a no-op for terminal runs. Return the existing snapshot and add no cancellation event. Active-run cancellation retains its previous behaviour.

**Tradeoff:** callers must inspect the returned state; requesting cancellation does not mean completed work was cancelled.

**Evidence:** success, failure and blocked late-cancellation cases in `runtime/tests/test_support_regressions.py`.

## 5. Validate optional retrieval metadata before scoring

**Reproduced problem:** a numeric corpus `title` passed the `id`/`text` check, then raised an uncaught `TypeError`. The transaction rolled back without a persisted task diagnostic.

**Decision:** require optional titles to be strings. Invalid metadata raises `CoreError` through the existing failure path, persisting `LOCAL_HANDLER_ERROR` and attempt state.

**Tradeoff:** malformed data is rejected rather than silently coerced. Retry admission still follows declared budget/reversibility; callers should correct deterministic malformed input rather than retry it repeatedly.

**Evidence:** `_retrieve`; `test_numeric_corpus_title_persists_failure_diagnostic` in the maintenance regression suite.

## Source and design boundary

The original core, October export and proposed AWS designs have distinct identities in [original provenance](../../SOURCE_PROVENANCE.json). November changes and fresh checks are recorded in the [maintenance report](../verification/2026-11-10-maintenance.md). Local synthetic tests do not establish the target AWS architecture's implementation or deployment.
