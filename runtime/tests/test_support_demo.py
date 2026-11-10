"""Exercise the documented local support scenarios through the real engine."""
import json
import tempfile
import unittest
from pathlib import Path

from examples.support_case import run_demo


class SupportDemoTests(unittest.TestCase):
    def test_supported_scenarios_preserve_checkpoint_and_attempt_bounds(self):
        cases = [("success", "SUCCEEDED", 1), ("retry", "SUCCEEDED", 2), ("ambiguous", "UNKNOWN_PENDING_RECONCILIATION", 1)]
        with tempfile.TemporaryDirectory() as directory:
            for scenario, expected_status, expected_attempts in cases:
                with self.subTest(scenario=scenario):
                    result = run_demo(Path(directory) / scenario, scenario)
                    self.assertEqual(result["status"], expected_status)
                    self.assertEqual(result["attempts"], expected_attempts)
                    self.assertTrue(result["same_request_after_reopen"])
                    self.assertEqual(result["pending_host_requests"], 0)
                    snapshot = json.loads(Path(result["export"]).read_text(encoding="utf-8"))
                    self.assertEqual(snapshot["mode"], "OFFLINE_TEST")
                    self.assertEqual(snapshot["business_acceptance"], "NOT_EVALUATED_BY_ENGINE")
                    if scenario == "ambiguous":
                        self.assertIsNone(snapshot["tasks"][0]["receipt"])
                    else:
                        self.assertEqual(snapshot["tasks"][0]["receipt"]["evidence"][0]["directness"], "FIXTURE")

    def test_unknown_scenario_is_rejected_before_creating_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "must-not-exist"
            with self.assertRaises(ValueError):
                run_demo(root, "unsupported")
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
