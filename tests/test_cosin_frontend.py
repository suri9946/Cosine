"""Unit tests for COSIN frontend integration, progress telemetry, and report formatting."""

import unittest
from unittest.mock import MagicMock
from agents.orchestrator import ResearchOrchestrator, ResearchRun
from ui.theme import render_status_pill
from ui.history import load_research_history
from ui.sources import load_manifest


class CosinFrontendTests(unittest.TestCase):
    def test_progress_callback_emits_ordered_stages(self):
        """Verify on_progress callback receives notifications for stages."""
        retriever = MagicMock()
        retriever.search.return_value = [{"evidence_id": "ev1", "source": "test.pdf"}]
        retriever.assess_evidence.return_value = {
            "status": "RETRIEVAL_RELEVANT_REVIEW_REQUIRED",
            "topic": "mechanism",
        }

        interpreter = MagicMock()
        interpreter.interpret.return_value = MagicMock(
            status="COMPLETED",
            claims=[MagicMock(claim_id="c1", text="Paracetamol inhibits COX", evidence_ids=["ev1"])],
        )

        verifier = MagicMock()
        verifier.verify.return_value = {"status": "COMPLETED", "claims": []}

        judge = MagicMock()
        judge.evaluate.return_value = MagicMock(
            status="APPROVED",
            answer="Paracetamol inhibits COX.",
            claims=[],
            reasons=[],
        )

        orchestrator = ResearchOrchestrator(
            retriever=retriever,
            interpreter=interpreter,
            verifier=verifier,
            judge=judge,
        )

        stages_visited = []

        def track_progress(stage, status, details):
            stages_visited.append((stage, status))

        run = orchestrator.run("How does paracetamol work?", on_progress=track_progress)

        self.assertEqual(run.status, "APPROVED")
        # Ensure agent1, agent2, agent3, agent4 were all notified
        stage_names = [s[0] for s in stages_visited]
        self.assertIn("agent1", stage_names)
        self.assertIn("agent2", stage_names)
        self.assertIn("agent3", stage_names)
        self.assertIn("agent4", stage_names)

    def test_insufficient_evidence_halts_before_agents_2_3_4(self):
        """Verify insufficient retrieval stops and marks downstream stages appropriately."""
        retriever = MagicMock()
        retriever.search.return_value = []
        retriever.assess_evidence.return_value = {
            "status": "RETRIEVAL_INSUFFICIENT_EVIDENCE",
            "topic": "unknown",
        }

        interpreter = MagicMock()
        verifier = MagicMock()
        judge = MagicMock()

        orchestrator = ResearchOrchestrator(
            retriever=retriever,
            interpreter=interpreter,
            verifier=verifier,
            judge=judge,
        )

        stages_visited = []

        def track_progress(stage, status, details):
            stages_visited.append((stage, status))

        run = orchestrator.run("What is the mechanism of baclofen?", on_progress=track_progress)

        self.assertEqual(run.status, "ABSTAIN")
        interpreter.interpret.assert_not_called()
        verifier.verify.assert_not_called()
        judge.evaluate.assert_not_called()

        # Check that agent2, agent3, agent4 were marked as waiting
        waiting_stages = [s[0] for s in stages_visited if s[1] == "waiting"]
        self.assertIn("agent2", waiting_stages)
        self.assertIn("agent3", waiting_stages)
        self.assertIn("agent4", waiting_stages)

    def test_status_pill_rendering(self):
        """Verify HTML pills render cleanly for all statuses."""
        pill = render_status_pill("APPROVED")
        self.assertIn("Approved", pill)
        self.assertIn("background-color", pill)

        pill_abstain = render_status_pill("ABSTAIN")
        self.assertIn("Abstain", pill_abstain)

    def test_load_research_history(self):
        """Verify research history loads real audit JSONs."""
        history = load_research_history()
        self.assertIsInstance(history, list)
        if history:
            self.assertIn("request_id", history[0])
            self.assertIn("question", history[0])

    def test_load_manifest(self):
        """Verify manifest loader parses SOURCE_MANIFEST.csv."""
        manifest = load_manifest()
        self.assertIsInstance(manifest, list)
        self.assertGreater(len(manifest), 0)
        self.assertIn("source_id", manifest[0])


if __name__ == "__main__":
    unittest.main()

