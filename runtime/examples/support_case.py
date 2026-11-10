"""Reproduce checkpoint, retry and uncertain-outcome support cases offline.

Run from runtime/: python -m examples.support_case --scenario retry
No model, mail provider or network adapter is used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import Engine, compile_workflow, now


def workflow(scenario: str) -> dict:
    requirement = {
        "goal": "Demonstrate diagnosis of a synthetic inventory support case",
        "business_context": "Independent offline portfolio demonstration",
        "stakeholders": ["support reviewer"],
        "available_inputs": ["case"],
        "outcomes": ["schema-valid fixture output or an explicit unresolved state"],
        "constraints": ["No network or external writes"],
        "forbidden_actions": ["email.send"],
        "assumptions": ["The case and host response are synthetic fixtures"],
        "operating_mode": "OFFLINE_TEST",
        "acceptance_tests": ["Bounded attempts and mode-labelled evidence"],
    }
    task = {
        "id": "triage",
        "role": "support_reviewer",
        "handler": "host",
        "action": "model.reason",
        "resource": "host:triage",
        "input_refs": ["input:case"],
        "instructions": "Return the declared synthetic support summary; perform no external action.",
        "output_schema": {
            "type": "object",
            "required": ["case_id", "finding", "next_action"],
            "properties": {key: {"type": "string"} for key in ["case_id", "finding", "next_action"]},
            "additionalProperties": False,
        },
        "timeout_seconds": 30,
        "retry_budget": 1,
        # The ambiguous case deliberately models a host that cannot guarantee
        # repeat safety. No external operation is actually performed here.
        "reversible": scenario != "ambiguous",
    }
    return compile_workflow(
        "support_demo_" + scenario, "1.0.0", requirement, [task],
        policy=[{"role": "support_reviewer", "action": "model.reason", "resource": "host:triage", "decision": "ALLOW"}],
    )


def fixture_receipt(request: dict) -> dict:
    return {
        "request_hash": request["request_hash"],
        "mode": "OFFLINE_TEST",
        "executor": "local support demo fixture",
        "invocation_ref": "fixture://support-demo/triage",
        "output": {
            "case_id": "synthetic-001",
            "finding": "Fixture: compare order history with stock movements before changing stock.",
            "next_action": "Collect reproduction steps and timestamped evidence for engineering review.",
        },
        "evidence": [{
            "source_id": "synthetic-support-case",
            "date": now(),
            "provenance": "Scripted fixture; no model inference or actual customer incident",
            "directness": "FIXTURE",
            "independence_group": "support-demo-fixture",
            "contradictions": [],
            "missing_information": ["No real inventory system was queried"],
        }],
    }


def run_demo(root: Path, scenario: str = "success") -> dict:
    if scenario not in {"success", "retry", "ambiguous"}:
        raise ValueError("Unsupported demonstration scenario")
    root = Path(root).resolve()
    current_time = [1000.0]
    engine = Engine(root / "state.sqlite", root, clock=lambda: current_time[0])
    package = workflow(scenario)
    engine.register_workflow(package)
    run_id = engine.start_run(
        package["workflow_id"], package["version"],
        {"case": {"id": "synthetic-001", "symptom": "Reported order quantity differs from displayed stock"}},
        mode="OFFLINE_TEST",
    )
    engine.advance(run_id)
    first_request = engine.pending_host(run_id)[0]

    # Reopen the same database before responding: resuming a checkpoint must
    # retain the in-flight request rather than dispatching another attempt.
    engine = Engine(root / "state.sqlite", root, clock=lambda: current_time[0])
    engine.resume(run_id)
    resumed_request = engine.pending_host(run_id)[0]
    if first_request["request_hash"] != resumed_request["request_hash"]:
        raise RuntimeError("Checkpoint resume changed the pending request")

    if scenario == "retry":
        engine.fail_task(run_id, "triage", "DEMO_TRANSPORT_FAILURE", "Synthetic reversible transport failure")
        current_time[0] += 2
        engine.resume(run_id)
    elif scenario == "ambiguous":
        engine.fail_task(run_id, "triage", "DEMO_UNKNOWN_OUTCOME", "Synthetic missing host acknowledgement", ambiguous=True)
        current_time[0] += 100
        engine.resume(run_id)

    if scenario != "ambiguous":
        engine.submit_receipt(run_id, "triage", fixture_receipt(engine.pending_host(run_id)[0]))
    snapshot = engine.inspect(run_id)
    export_path = engine.export_run(run_id)
    return {
        "scenario": scenario,
        "mode": snapshot["mode"],
        "run_id": run_id,
        "status": snapshot["status"],
        "attempts": snapshot["tasks"][0]["attempts"],
        "same_request_after_reopen": True,
        "pending_host_requests": len(engine.pending_host(run_id)),
        "event_count": len(snapshot["events"]),
        "database": str(engine.db_path),
        "export": export_path,
        "scope": "Synthetic local engine demonstration; no external effects or business acceptance",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["success", "retry", "ambiguous"], default="success")
    parser.add_argument("--output-dir", type=Path, help="Local state directory; defaults to .demo-state/<scenario>")
    args = parser.parse_args()
    root = args.output_dir or Path(".demo-state") / args.scenario
    print(json.dumps(run_demo(root, args.scenario), indent=2))


if __name__ == "__main__":
    main()
