import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from agents.orchestrator import ResearchOrchestrator
from agents.chemistry_pharmacology_agent import Agent2OutputInvalid

AUDIT_DIR = Path(__file__).resolve().parents[1] / "data" / "processed" / "orchestrator_test"

EVIDENCE = [{"evidence_id": "ev-1", "evidence_type": "DIRECT_EVIDENCE_CANDIDATE", "text": "passage"}]
ASSESSMENT = {"status": "RETRIEVAL_RELEVANT_REVIEW_REQUIRED", "direct_candidates": 1}
CLAIM = {"claim_id": "a2-1", "text": "Claim.", "claim_type": "finding", "evidence_ids": ["ev-1"]}


class OrchestratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        for path in AUDIT_DIR.glob("*.json"):
            path.unlink()

    def tearDown(self):
        for path in AUDIT_DIR.glob("*.json"):
            path.unlink()

    def setup_pipeline(self, tmp_path):
        retriever = Mock()
        retriever.search.return_value = EVIDENCE
        retriever.assess_evidence.return_value = ASSESSMENT
        interpreter = Mock()
        interpreter.interpret.return_value = SimpleNamespace(status="COMPLETED", claims=[CLAIM], raw_response={"model": "m"})
        verifier = Mock()
        verifier.verify.return_value = SimpleNamespace(status="COMPLETED", claims=[SimpleNamespace(
            claim_id="a2-1", status="RECORDS_FOUND", records=[], provider_errors={})])
        judge = Mock()
        judge.evaluate.return_value = SimpleNamespace(status="APPROVED", answer="Claim.")
        return ResearchOrchestrator(retriever, interpreter, verifier, judge, audit_dir=tmp_path), retriever, interpreter, verifier, judge

    def test_happy_path_audits_complete_run_and_raw_stages(self):
        orchestrator, _, interpreter, verifier, judge = self.setup_pipeline(AUDIT_DIR)
        result = orchestrator.run("question")
        self.assertEqual(result.status, "APPROVED")
        self.assertEqual(set(result.stage_timings_ms), {"agent1", "agent2", "agent3", "agent4", "total"})
        self.assertTrue(Path(result.audit_path).is_file())
        payload = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
        self.assertEqual(payload["question"], "question")
        self.assertEqual(payload["stage_timings_ms"], result.stage_timings_ms)
        self.assertEqual(payload["interpretation"]["raw_response"], {"model": "m"})
        interpreter.interpret.assert_called_once()
        verifier.verify.assert_called_once()
        judge.evaluate.assert_called_once()

    def test_insufficient_local_retrieval_stops_before_models(self):
        orchestrator, retriever, interpreter, verifier, judge = self.setup_pipeline(AUDIT_DIR)
        retriever.assess_evidence.return_value = {"status": "INSUFFICIENT_EVIDENCE"}
        result = orchestrator.run("absent topic")
        self.assertEqual(result.status, "ABSTAIN")
        interpreter.interpret.assert_not_called()
        verifier.verify.assert_not_called()
        judge.evaluate.assert_not_called()

    def test_agent3_failure_cannot_return_approval(self):
        orchestrator, _, _, verifier, judge = self.setup_pipeline(AUDIT_DIR)
        verifier.verify.side_effect = TimeoutError()
        judge.evaluate.return_value = SimpleNamespace(status="APPROVED", answer="Claim.")
        result = orchestrator.run("question")
        self.assertEqual(result.status, "NEEDS_MORE_EVIDENCE")
        self.assertEqual(result.stage_errors["agent3"], "TimeoutError")

    def test_agent2_error_fails_closed(self):
        orchestrator, _, interpreter, verifier, judge = self.setup_pipeline(AUDIT_DIR)
        interpreter.interpret.side_effect = Agent2OutputInvalid(
            "invalid output", raw_response={"model": "ChemLLM", "done_reason": "length"}, raw_content="{"
        )
        result = orchestrator.run("question")
        self.assertEqual(result.status, "PARTIAL")
        self.assertEqual(result.stage_errors["agent2"], "Agent2OutputInvalid")
        payload = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
        self.assertEqual(payload["interpretation"]["raw_response"]["done_reason"], "length")
        verifier.verify.assert_not_called()
        judge.evaluate.assert_not_called()

    def test_judge_error_abstains(self):
        orchestrator, _, _, _, judge = self.setup_pipeline(AUDIT_DIR)
        judge.evaluate.side_effect = ValueError()
        result = orchestrator.run("question")
        self.assertEqual(result.status, "ABSTAIN")
        self.assertEqual(result.stage_errors["agent4"], "ValueError")
        self.assertEqual(Path(result.audit_path).parent, AUDIT_DIR)


if __name__ == "__main__":
    unittest.main()
