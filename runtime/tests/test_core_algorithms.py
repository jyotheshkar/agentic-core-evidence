import tempfile
import unittest
from pathlib import Path
from core import CoreError, route_capabilities, keyword_baseline, evaluate_options, assess_evidence, assess_risk, guardian, safe_path, redact, now


def candidate(cid, caps, **kwargs):
    return {"id": cid, "capabilities": caps, "available": True, "trust": 2, "context_tokens": 100, "activation_cost": 1, **kwargs}


class AlgorithmTests(unittest.TestCase):
    def test_set_cover_cost_and_deterministic_tie_break(self):
        candidates = [candidate("b", ["x"]), candidate("a", ["x"]), candidate("combined", ["x", "y"], activation_cost=1.5)]
        result = route_capabilities(["x", "y"], candidates)
        self.assertEqual(result["selected"], ["combined"])
        self.assertEqual(route_capabilities(["x"], candidates[:2])["selected"], ["a"])
        self.assertEqual(result["coverage_matrix"]["y"]["a"], 0)

    def test_eligibility_tools_trust_compatibility_budget(self):
        candidates = [candidate("absent", ["x"], available=False), candidate("low", ["x"], trust=1), candidate("cloud", ["x"], required_tools=["paid-api"]), candidate("wrong", ["x"], compatible=False), candidate("large", ["x"], context_tokens=1000)]
        result = route_capabilities(["x"], candidates, context_budget=100)
        self.assertEqual(result["uncovered"], ["x"])
        self.assertEqual(len(result["excluded"]), 5)

    def test_dependency_closure_cycles_missing_conflicts(self):
        valid = route_capabilities(["x"], [candidate("a", ["x"], dependencies=["base"]), candidate("base", [])])
        self.assertEqual(valid["selected"], ["a", "base"])
        for candidates in [
            [candidate("a", ["x"], dependencies=["missing"])],
            [candidate("a", ["x"], dependencies=["b"]), candidate("b", [], dependencies=["a"])],
            [candidate("a", ["x"], dependencies=["b"], conflicts=["b"]), candidate("b", [])],
        ]:
            self.assertEqual(route_capabilities(["x"], candidates)["uncovered"], ["x"])

    def test_conflict_against_selected_not_silently_ignored(self):
        result = route_capabilities(["x", "y"], [candidate("a", ["x"], conflicts=["b"]), candidate("b", ["y"])])
        self.assertEqual(result["selected"], ["a"])
        self.assertEqual(result["uncovered"], ["y"])

    def test_weighted_coverage_preserves_priorities(self):
        result = route_capabilities({"important": 5, "nice": 1}, [candidate("a", ["nice"]), candidate("b", ["important"])], context_budget=100)
        self.assertEqual(result["selected"], ["b"])
        self.assertEqual(result["uncovered"], ["nice"])

    def test_baseline_routing_comparison_labelled_cases(self):
        candidates = [candidate("available", ["research"], tags=["research"]), candidate("unavailable", ["research"], tags=["research"], available=False)]
        self.assertEqual(keyword_baseline(["research"], candidates), ["available", "unavailable"])
        self.assertEqual(route_capabilities(["research"], candidates)["selected"], ["available"])

    def test_utility_feasibility_units_direction_and_sensitivity(self):
        criteria = [{"id": "quality", "min": 0, "max": 100, "unit": "score", "direction": "max", "weight": 1}, {"id": "cost", "min": 0, "max": 100, "unit": "GBP", "direction": "min", "weight": 1}]
        options = [{"id": "a", "values": {"quality": 90, "cost": 80}}, {"id": "b", "values": {"quality": 20, "cost": 10}}, {"id": "prohibited", "feasible": False, "values": {"quality": 100, "cost": 0}}]
        result = evaluate_options(options, criteria)
        self.assertIn("prohibited", result["excluded"])
        self.assertTrue(result["unstable"])
        self.assertTrue(result["choice_exists"])
        self.assertFalse(evaluate_options(options[:1], criteria)["choice_exists"])

    def test_utility_invalid_scale_rejected(self):
        with self.assertRaises(CoreError):
            evaluate_options([{"id": "a", "values": {"x": 5}}], [{"id": "x", "min": 0, "max": 1, "unit": "score", "direction": "max", "weight": 1}])

    def test_evidence_source_copies_not_independent(self):
        record = {"source_id": "source-1", "date": now(), "provenance": "Original", "directness": "DIRECT", "independence_group": "original", "contradictions": [], "missing_information": []}
        result = assess_evidence([record, dict(record, source_id="mirror")])
        self.assertEqual(result["independent_groups"], 1)
        self.assertIsNone(result["calibrated_probability"])
        self.assertEqual(assess_evidence([])["strength"], "MISSING")
        self.assertEqual(assess_evidence([dict(record, contradictions=["conflicting date"])])["strength"], "CONTESTED")

    def test_risk_ordinal_escalation_does_not_override_policy(self):
        risk = assess_risk(2, 3, "IRREVERSIBLE", "PUBLIC", ["human review"])
        self.assertTrue(risk["requires_escalation"])
        self.assertEqual(risk["score"], 6)
        result = guardian("runner", "email.send", "all", {}, [{"role": "*", "action": "*", "resource": "*", "decision": "ALLOW"}])
        self.assertEqual(result["decision"], "DENY")

    def test_guardian_deny_wins_and_arguments_bind_approval(self):
        allow = {"role": "runner", "action": "model.reason", "resource": "host:*", "decision": "ALLOW"}
        self.assertEqual(guardian("runner", "model.reason", "host:x", {}, [allow, dict(allow, decision="DENY")])["decision"], "DENY")
        approval_rule = [dict(allow, decision="REQUIRE_APPROVAL")]
        first = guardian("runner", "model.reason", "host:x", {"value": 1}, approval_rule)
        approved = [{"action_hash": first["action_hash"], "status": "APPROVED"}]
        self.assertEqual(guardian("runner", "model.reason", "host:x", {"value": 1}, approval_rule, approvals=approved)["decision"], "ALLOW")
        self.assertEqual(guardian("runner", "model.reason", "host:x", {"value": 2}, approval_rule, approvals=approved)["decision"], "REQUIRE_APPROVAL")

    def test_path_traversal_windows_drive_and_ads_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            for unsafe in ["../secret", "..\\secret", "C:\\secret", "C:relative", "artifact.txt:secret", "/absolute", ""]:
                with self.subTest(path=unsafe), self.assertRaises(CoreError):
                    safe_path(root, unsafe)
            self.assertEqual(safe_path(root, "artifacts/output.json"), Path(root).resolve() / "artifacts/output.json")

    def test_secret_redaction_nested_keys_and_text(self):
        value = {"password": "secretvalue", "nested": [{"text": "Bearer sometoken password=second sk-abcdefghijklmnop"}], "api_key": "another"}
        redacted = str(redact(value))
        for private in ["secretvalue", "sometoken", "second", "abcdefghijklmnop", "another"]:
            self.assertNotIn(private, redacted)


if __name__ == "__main__":
    unittest.main()
