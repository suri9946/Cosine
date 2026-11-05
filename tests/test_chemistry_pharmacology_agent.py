import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from agents.chemistry_pharmacology_agent import Agent2OutputInvalid, ChemistryPharmacologyAgent
from agents.ollama_client import CHEMLLM_MODEL, OllamaUnavailable


EVIDENCE = [{"evidence_id": "ev-1", "source_id": "src-1", "source_title": "Example",
            "source_url": "https://example.test", "page": 3, "section": "Mechanism",
            "text": "The supplied passage states a limited finding about paracetamol."}]


def output(evidence_ids=None):
    return {"answer": "The passage reports a finding.", "claims": [{
        "text": "The passage reports a finding.", "claim_type": "finding",
        "explanation": "This wording follows the supplied text.",
        "evidence_refs": evidence_ids if evidence_ids is not None else ["E1"],
        "uncertainty": "Limited to this source.", "requires_verification": True,
    }]}


class Agent2Tests(unittest.TestCase):
    def test_valid_claim_is_typed_and_raw_response_preserved(self):
        raw = {"model": CHEMLLM_MODEL, "done": True}
        client = Mock()
        client.chat.return_value = SimpleNamespace(model=CHEMLLM_MODEL, content=json.dumps(output()), raw=raw)
        result = ChemistryPharmacologyAgent(client).interpret("What does this passage say?", EVIDENCE)
        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.claims[0]["evidence_ids"], ["ev-1"])
        self.assertEqual(result.raw_response, raw)
        sent = json.loads(client.chat.call_args.args[1][1]["content"])
        self.assertEqual(sent["evidence"][0]["ref"], "E1")

    def test_exact_duplicate_claims_are_collapsed(self):
        payload = output() | {"claims": [output()["claims"][0], output()["claims"][0]]}
        client = Mock()
        client.chat.return_value = SimpleNamespace(model=CHEMLLM_MODEL, content=json.dumps(payload), raw={})
        result = ChemistryPharmacologyAgent(client).interpret("What does this passage say?", EVIDENCE)
        self.assertEqual(len(result.claims), 1)
        self.assertTrue(any("duplicate" in warning for warning in result.warnings))
        self.assertEqual(result.claims[0]["evidence_ids"], ["ev-1"])

    def test_empty_evidence_skips_model(self):
        client = Mock()
        result = ChemistryPharmacologyAgent(client).interpret("question", [])
        self.assertEqual(result.status, "INSUFFICIENT_EVIDENCE")
        client.chat.assert_not_called()

    def test_malformed_json_fails_closed(self):
        client = Mock()
        client.chat.return_value = SimpleNamespace(model=CHEMLLM_MODEL, content="not json", raw={})
        with self.assertRaises(Agent2OutputInvalid):
            ChemistryPharmacologyAgent(client).interpret("question", EVIDENCE)

    def test_truncated_output_fails_closed_and_keeps_raw_response(self):
        client = Mock()
        raw = {"done": True, "done_reason": "length"}
        client.chat.return_value = SimpleNamespace(model=CHEMLLM_MODEL, content="{", raw=raw)
        with self.assertRaises(Agent2OutputInvalid) as caught:
            ChemistryPharmacologyAgent(client).interpret("question", EVIDENCE)
        self.assertEqual(caught.exception.raw_response, raw)
        self.assertEqual(caught.exception.raw_content, "{")

    def test_unknown_citation_and_uncited_factual_claim_fail_closed(self):
        for ids in (["E99"], []):
            client = Mock()
            client.chat.return_value = SimpleNamespace(model=CHEMLLM_MODEL, content=json.dumps(output(ids)), raw={})
            with self.assertRaises(Agent2OutputInvalid):
                ChemistryPharmacologyAgent(client).interpret("question", EVIDENCE)

    def test_ollama_failure_propagates(self):
        client = Mock()
        client.chat.side_effect = OllamaUnavailable("service unavailable")
        with self.assertRaises(OllamaUnavailable):
            ChemistryPharmacologyAgent(client).interpret("question", EVIDENCE)

    def test_unknown_claim_may_report_absent_coverage(self):
        unknown = {"answer": "The supplied text does not address this.", "claims": [{
            "text": "The supplied text does not address this.", "claim_type": "unknown",
            "explanation": "Not present in supplied passages.", "evidence_refs": [],
            "uncertainty": "No evidence supplied.", "requires_verification": True,
        }]}
        client = Mock()
        client.chat.return_value = SimpleNamespace(model=CHEMLLM_MODEL, content=json.dumps(unknown), raw={})
        result = ChemistryPharmacologyAgent(client).interpret("question", EVIDENCE)
        self.assertEqual(result.claims[0]["claim_type"], "unknown")

    def test_conflicting_source_claim_can_cite_both_and_request_verification(self):
        evidence = EVIDENCE + [{**EVIDENCE[0], "evidence_id": "ev-2", "source_id": "src-2",
                                "text": "A second source reports a different interpretation."}]
        conflicting = output(["E1", "E2"])
        conflicting["claims"][0]["claim_type"] = "interpretation"
        conflicting["claims"][0]["requires_verification"] = True
        client = Mock()
        client.chat.return_value = SimpleNamespace(model=CHEMLLM_MODEL,
            content=json.dumps(conflicting), raw={"done": True})
        result = ChemistryPharmacologyAgent(client).interpret("Compare sources", evidence)
        self.assertEqual(result.claims[0]["evidence_ids"], ["ev-1", "ev-2"])
        self.assertTrue(result.claims[0]["requires_verification"])


if __name__ == "__main__":
    unittest.main()
