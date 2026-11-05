import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from agents.judge_agent import JudgeAgent, JudgeOutputInvalid
from agents.ollama_client import JUDGE_MODEL, OllamaUnavailable


EVIDENCE = [{"evidence_id": "ev-1", "source_id": "src-1", "source_title": "Local source",
             "source_url": "https://example.test", "page": 4, "text": "Retrieved passage text."}]


def verification(status="COMPLETED", provider_errors=None):
    item_status = "RECORDS_FOUND" if status == "COMPLETED" else "PARTIAL"
    return SimpleNamespace(status=status, claims=[SimpleNamespace(
        claim_id="a2-1", status=item_status, records=[{"provider": "Europe PMC", "pmid": "1", "abstract": "Candidate."}],
        provider_errors=provider_errors or {})])


def response(claim_text="A supported statement.", evidence_ids=None, decision="APPROVED"):
    return {"claims": [{"claim_id": "a2-1", "decision": decision,
                        "rationale": "The provided passage supports the wording.",
                        "evidence_ids": evidence_ids if evidence_ids is not None else ["ev-1"]}],
            "answer": claim_text}


class JudgeTests(unittest.TestCase):
    def test_approved_decision_returns_validated_claim_text_and_raw(self):
        client = Mock()
        raw = {"model": JUDGE_MODEL, "done": True}
        client.chat.return_value = SimpleNamespace(model=JUDGE_MODEL, content=json.dumps(response()), raw=raw)
        claim = {"claim_id": "a2-1", "text": "A supported statement.", "claim_type": "finding", "evidence_ids": ["ev-1"]}
        result = JudgeAgent(client).evaluate("question", EVIDENCE, SimpleNamespace(status="COMPLETED", claims=[claim]), verification())
        self.assertEqual(result.status, "APPROVED")
        self.assertEqual(result.answer, "A supported statement.")
        self.assertEqual(result.raw_response, raw)

    def test_external_provider_failure_prevents_full_approval(self):
        client = Mock()
        client.chat.return_value = SimpleNamespace(model=JUDGE_MODEL, content=json.dumps(response()), raw={})
        claim = {"claim_id": "a2-1", "text": "A supported statement.", "claim_type": "finding", "evidence_ids": ["ev-1"]}
        result = JudgeAgent(client).evaluate("question", EVIDENCE, SimpleNamespace(status="COMPLETED", claims=[claim]),
            verification("PARTIAL", {"PubMed": "ProxyError"}))
        self.assertEqual(result.status, "NEEDS_MORE_EVIDENCE")

    def test_missing_agent3_claim_mapping_prevents_full_approval(self):
        client = Mock()
        client.chat.return_value = SimpleNamespace(model=JUDGE_MODEL, content=json.dumps(response()), raw={})
        claim = {"claim_id": "a2-1", "text": "A supported statement.", "claim_type": "finding", "evidence_ids": ["ev-1"]}
        verification_result = SimpleNamespace(status="COMPLETED", claims=[])
        result = JudgeAgent(client).evaluate("question", EVIDENCE,
            SimpleNamespace(status="COMPLETED", claims=[claim]), verification_result)
        self.assertEqual(result.status, "NEEDS_MORE_EVIDENCE")

    def test_ampa_apaba_pathway_flag_overrides_judge_approval(self):
        for molecule in ("AMPA", "APABA"):
            with self.subTest(molecule=molecule):
                client = Mock()
                client.chat.return_value = SimpleNamespace(model=JUDGE_MODEL, content=json.dumps(response()), raw={})
                claim = {"claim_id": "a2-1", "text": f"{molecule} is converted to NAPQI in paracetamol metabolism.",
                         "claim_type": "finding", "evidence_ids": ["ev-1"]}
                result = JudgeAgent(client).evaluate("question", EVIDENCE, SimpleNamespace(status="COMPLETED", claims=[claim]), verification())
                self.assertEqual(result.status, "NEEDS_REVISION")
                self.assertEqual(result.claims[0].decision, "NEEDS_REVISION")
                self.assertTrue(result.claims[0].warnings)

    def test_unknown_claim_cannot_be_approved_without_evidence(self):
        client = Mock()
        client.chat.return_value = SimpleNamespace(model=JUDGE_MODEL,
            content=json.dumps(response(evidence_ids=[])), raw={})
        claim = {"claim_id": "a2-1", "text": "Not known from evidence.", "claim_type": "unknown", "evidence_ids": []}
        result = JudgeAgent(client).evaluate("question", EVIDENCE, SimpleNamespace(status="COMPLETED", claims=[claim]), verification())
        self.assertEqual(result.status, "NEEDS_MORE_EVIDENCE")

    def test_unknown_claim_reference_is_rejected_before_model(self):
        client = Mock()
        claim = {"claim_id": "a2-1", "text": "Finding.", "claim_type": "finding", "evidence_ids": ["invented"]}
        result = JudgeAgent(client).evaluate("question", EVIDENCE, SimpleNamespace(status="COMPLETED", claims=[claim]), verification())
        self.assertEqual(result.status, "NEEDS_REVISION")
        client.chat.assert_not_called()

    def test_missing_inputs_abstain(self):
        client = Mock()
        result = JudgeAgent(client).evaluate("question", [], SimpleNamespace(status="COMPLETED", claims=[]), verification())
        self.assertEqual(result.status, "ABSTAIN")
        client.chat.assert_not_called()

    def test_invalid_judge_json_fails_closed(self):
        client = Mock()
        client.chat.side_effect = [
            SimpleNamespace(model=JUDGE_MODEL, content="not json", raw={"attempt": 1}),
            SimpleNamespace(model=JUDGE_MODEL, content="not json", raw={"attempt": 2}),
        ]
        claim = {"claim_id": "a2-1", "text": "Finding.", "claim_type": "finding", "evidence_ids": ["ev-1"]}
        result = JudgeAgent(client).evaluate("question", EVIDENCE,
            SimpleNamespace(status="COMPLETED", claims=[claim]), verification())
        self.assertEqual(client.chat.call_count, 2)
        self.assertEqual(result.status, "NEEDS_MORE_EVIDENCE")
        self.assertEqual(result.claims[0].decision, "NEEDS_MORE_EVIDENCE")
        self.assertEqual(result.raw_response, {"attempt": 2})
        self.assertIn("retry", result.reasons[0])

    def test_invalid_first_response_retries_and_accepts_valid_response(self):
        client = Mock()
        client.chat.side_effect = [
            SimpleNamespace(model=JUDGE_MODEL, content='{"claims":[]}', raw={}),
            SimpleNamespace(model=JUDGE_MODEL, content=json.dumps(response()), raw={"valid": True}),
        ]
        claim = {"claim_id": "a2-1", "text": "A supported statement.", "claim_type": "finding", "evidence_ids": ["ev-1"]}
        result = JudgeAgent(client).evaluate("question", EVIDENCE,
            SimpleNamespace(status="COMPLETED", claims=[claim]), verification())
        self.assertEqual(result.status, "APPROVED")
        self.assertEqual(client.chat.call_count, 2)
        self.assertIn("exact claim_id", client.chat.call_args.args[1][0]["content"])

    def test_model_unavailable_returns_safe_abstention(self):
        client = Mock()
        client.chat.side_effect = OllamaUnavailable("service unavailable")
        claim = {"claim_id": "a2-1", "text": "A claim.", "claim_type": "finding", "evidence_ids": ["ev-1"]}
        result = JudgeAgent(client).evaluate("question", EVIDENCE,
            SimpleNamespace(status="COMPLETED", claims=[claim]), verification())
        self.assertEqual(result.status, "NEEDS_MORE_EVIDENCE")
        self.assertIsNone(result.model)
        self.assertIn("unavailable", result.reasons[0])


if __name__ == "__main__":
    unittest.main()
