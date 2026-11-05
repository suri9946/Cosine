import unittest
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace

from app import display_result


class AppOutputTests(unittest.TestCase):
    def test_displays_stage_states_claims_external_ids_and_source_pages(self):
        result = SimpleNamespace(
            status="NEEDS_MORE_EVIDENCE",
            retrieval_assessment={"status": "RETRIEVAL_RELEVANT_REVIEW_REQUIRED"},
            interpretation=SimpleNamespace(status="COMPLETED", claims=[{
                "claim_id": "a2-1", "claim_type": "finding", "text": "A supported finding.",
                "evidence_ids": ["ev-1"]}]),
            verification=SimpleNamespace(status="PARTIAL", claims=[SimpleNamespace(
                claim_id="a2-1", status="RECORDS_FOUND", records=[{
                    "provider": "Europe PMC", "title": "Example article", "pmid": "123",
                    "pmcid": "PMC123", "doi": "10.1234/example", "source_url": "https://example.test"}])]),
            judgment=SimpleNamespace(status="NEEDS_MORE_EVIDENCE", claims=[SimpleNamespace(
                claim_id="a2-1", decision="NEEDS_MORE_EVIDENCE", rationale="External verification incomplete.",
                warnings=[] )], reasons=["Independent verification is partial."]),
            answer="", evidence=[{"evidence_id": "ev-1", "source_id": "src-1", "source_title": "Local source",
                                  "source_url": "https://local.test", "page": 7, "section": "Safety"}],
            stage_errors={}, audit_path="data/processed/runs/test.json",
            stage_timings_ms={"agent1": 1, "total": 2},
        )
        output = StringIO()
        with redirect_stdout(output):
            display_result(result)
        rendered = output.getvalue()
        for expected in ("Agent 1 retrieval", "Agent 2 interpretation", "Agent 3 literature search",
                         "Agent 4 judgment", "Stage timings", "PMID 123", "PMCID PMC123", "DOI 10.1234/example",
                         "Evidence ev-1", "page 7", "Audit record"):
            self.assertIn(expected, rendered)

    def test_failed_agent_stage_is_not_displayed_as_not_run(self):
        result = SimpleNamespace(
            status="ABSTAIN", retrieval_assessment={"status": "RETRIEVAL_RELEVANT_REVIEW_REQUIRED"},
            interpretation=None, verification=None, judgment=ValueError("invalid"),
            answer="", evidence=[], stage_errors={"agent4": "JudgeOutputInvalid"},
            audit_path=None, stage_timings_ms={},
        )
        output = StringIO()
        with redirect_stdout(output):
            display_result(result)
        self.assertIn("Agent 4 judgment: FAILED (JudgeOutputInvalid)", output.getvalue())


if __name__ == "__main__":
    unittest.main()
