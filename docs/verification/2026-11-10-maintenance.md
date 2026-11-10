# Maintenance validation: 10 November 2026

## Scope and source identity

The maintained base was public commit `72de3f177f9046fdfbf49b4251c26b49d87070e4` (tree `24fa7cdf954020aa27f9de2a79865a3623848aed`). The [machine-readable record](2026-11-10-maintenance.json) binds modified runtime/test files by SHA-256. The published maintenance commit can be read from this file's Git history; this report does not guess its future commit ID.

[SOURCE_PROVENANCE.json](../../SOURCE_PROVENANCE.json) and [core-tests.json](core-tests.json) remain unchanged historical evidence for the original export. Their byte-preservation statements and 35-test result apply to that baseline, not to the changed runtime.

## Changes verified

- Preserved terminal run outcomes when a late cancellation arrives. Success, failure and blocked outcomes now remain intact with no extra cancellation event.
- Validated optional corpus titles before retrieval scoring. A numeric title now becomes a persisted `LOCAL_HANDLER_ERROR` instead of an uncaught exception rolling back all diagnostics.
- Added an offline support demonstration that reopens SQLite checkpoints, exercises bounded retries and leaves ambiguous outcomes unresolved without automatic retry.
- Added regression/demo tests, a support runbook and engineering decisions. Updated CI discovery to include every `test_*.py` module.

## Local execution results

Executed in Linux with Python **3.12.14** and preinstalled dependencies. No dependency installation was performed for this local validation. `jsonschema` was 4.26.0; the complete observed dependency versions are in the JSON record. Some transitive versions differ from the pinned requirements, so this local run is not a fresh pinned-install result. The GitHub workflow separately installs those pins on Python 3.11.

Commands below were run from `runtime/`:

```bash
python -B -m unittest discover -s tests -p 'test_*.py' -v
python -B -m examples.support_case --scenario success
python -B -m examples.support_case --scenario retry
python -B -m examples.support_case --scenario ambiguous
```

| Check | Observed result |
|---|---|
| Full current unit suite | **41 tests passed**, 0 failures/errors |
| Success demonstration | `SUCCEEDED`, 1 attempt; same request after reopening |
| Retry demonstration | `SUCCEEDED`, 2 attempts; same original request after reopening |
| Ambiguous-outcome demonstration | `UNKNOWN_PENDING_RECONCILIATION`, 1 attempt; no automatic redispatch |
| Demonstration exports | SQLite and redacted JSON written locally; each run remains `OFFLINE_TEST` |

The 41 tests comprise the original 35 test methods plus two demonstration test methods and four maintenance regression methods. One demonstration test exercises all three scenarios. Test count is not a claim of production reliability or completeness.

## Practical limits

All examples, receipts and cases are synthetic. No model, inventory service, email provider or AWS account was contacted. No real support incident, measured operational improvement, remote exactly-once guarantee, security certification or cloud deployment is established. Business acceptance remains `NOT_EVALUATED_BY_ENGINE`.

The runbook's escalation and investigation steps are documentation for this local engine. They do not claim prior ownership of customer SLAs or on-call operations. Code and documentation were maintained with Codex/model assistance; original attribution remains in [NOTICE.md](../../NOTICE.md).
