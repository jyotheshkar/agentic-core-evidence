"""Regression cases reproduced during the 10 November maintenance review."""
import tempfile
import unittest
from pathlib import Path

from core import Engine
from test_core_engine import package, receipt, task


class SupportRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.engine = Engine(self.root / "state.sqlite", self.root)

    def tearDown(self):
        self.temp.cleanup()

    def start(self, pkg, inputs=None):
        self.engine.register_workflow(pkg)
        run_id = self.engine.start_run(pkg["workflow_id"], pkg["version"], inputs or {"cases": []}, "OFFLINE_TEST")
        self.engine.advance(run_id)
        return run_id

    def test_late_cancel_preserves_success_and_events(self):
        run_id = self.start(package())
        request = self.engine.pending_host(run_id)[0]
        completed = self.engine.submit_receipt(run_id, "reason", receipt(request))
        cancelled = self.engine.cancel(run_id)
        self.assertEqual(cancelled["status"], "SUCCEEDED")
        self.assertEqual(cancelled["tasks"], completed["tasks"])
        self.assertEqual(cancelled["events"], completed["events"])
        self.assertEqual(self.engine.resume(run_id)["status"], "SUCCEEDED")

    def test_late_cancel_preserves_failure_and_events(self):
        run_id = self.start(package([task(retry_budget=0)]))
        failed = self.engine.fail_task(run_id, "reason", "CONFIRMED_FAILURE", "Synthetic confirmed failure")
        cancelled = self.engine.cancel(run_id)
        self.assertEqual(cancelled["status"], "FAILED")
        self.assertEqual(cancelled["tasks"], failed["tasks"])
        self.assertEqual(cancelled["events"], failed["events"])

    def test_late_cancel_preserves_blocked_outcome(self):
        run_id = self.start(package(policy=[]))
        blocked = self.engine.inspect(run_id)
        cancelled = self.engine.cancel(run_id)
        self.assertEqual(cancelled["status"], "BLOCKED")
        self.assertEqual(cancelled["events"], blocked["events"])

    def test_numeric_corpus_title_persists_failure_diagnostic(self):
        retrieve = task(
            id="retrieve", handler="retrieve", action="files.read", resource="input:policies",
            input_refs=["input:policies"], arguments={"corpus_ref": "input:policies"},
            output_schema={"type": "object"}, retry_budget=0,
        )
        run_id = self.start(package([retrieve]), {"policies": [{"id": "p1", "text": "Stock policy", "title": 42}]})
        result = self.engine.inspect(run_id)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["tasks"][0]["error"]["code"], "LOCAL_HANDLER_ERROR")
        self.assertIn("optional title", result["tasks"][0]["error"]["message"])
        reopened = Engine(self.root / "state.sqlite", self.root)
        self.assertEqual(reopened.inspect(run_id)["tasks"][0]["error"], result["tasks"][0]["error"])


if __name__ == "__main__":
    unittest.main()
