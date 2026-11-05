import unittest
from unittest.mock import Mock

import requests

from agents.literature_verification_agent import LiteratureVerificationAgent


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class Agent3Tests(unittest.TestCase):
    def test_query_drops_question_and_corpus_stopwords(self):
        query = LiteratureVerificationAgent._query(
            "What is the molecular formula listed in the local chemical record for paracetamol?"
        )
        self.assertIn('"molecular"', query)
        self.assertIn('"formula"', query)
        self.assertEqual(query.count("paracetamol"), 1)
        for noise in ('"the"', '"listed"', '"local"', '"record"'):
            self.assertNotIn(noise, query)

    def test_queries_both_providers_and_preserves_metadata(self):
        session = Mock()
        session.headers = {}
        session.get.side_effect = [
            Response({"esearchresult": {"idlist": ["12345"]}}),
            Response({"result": {"uids": ["12345"], "12345": {
                "title": "Paracetamol study", "authors": [{"name": "A Author"}],
                "pubdate": "2024 Jan", "fulljournalname": "Example Journal"}}}),
            Response({"resultList": {"result": [{
                "title": "Paracetamol study", "authorString": "A Author", "pubYear": "2024",
                "journalTitle": "Example Journal", "doi": "10.1234/example", "pmid": "12345",
                "pmcid": "PMC123", "abstractText": "Abstract text", "isOpenAccess": "Y",
                "license": "CC BY"}]}}),
        ]
        agent = LiteratureVerificationAgent(session=session, min_interval=0)
        result = agent.verify([{"claim_id": "a2-1", "text": "paracetamol liver metabolism"}])
        self.assertEqual(result.status, "COMPLETED")
        check = result.claims[0]
        self.assertEqual(check.status, "RECORDS_FOUND")
        self.assertEqual(check.claim_id, "a2-1")
        record = check.records[0]
        self.assertEqual(record["provider"], "Europe PMC")
        self.assertEqual(record["license"], "CC BY")
        self.assertEqual(record["abstract"], "Abstract text")
        self.assertFalse(record["full_text_downloaded"])
        self.assertEqual(session.get.call_count, 3)
        self.assertIn("paracetamol", session.get.call_args_list[0].kwargs["params"]["term"])

    def test_no_records_is_distinguished_from_provider_failure(self):
        session = Mock()
        session.headers = {}
        session.get.side_effect = [Response({"esearchresult": {"idlist": []}}),
                                  Response({"resultList": {"result": []}})]
        result = LiteratureVerificationAgent(session=session, min_interval=0).verify([
            {"claim_id": "c1", "text": "unusual paracetamol formulation"}])
        self.assertEqual(result.claims[0].status, "NO_RECORDS")
        self.assertEqual(result.status, "COMPLETED")

    def test_provider_error_is_safely_recorded_without_request_details(self):
        session = Mock()
        session.headers = {}
        session.get.side_effect = [requests.Timeout("secret-url-with-api-key"),
                                  Response({"resultList": {"result": []}})]
        result = LiteratureVerificationAgent(session=session, min_interval=0).verify([
            {"claim_id": "c1", "text": "paracetamol mechanism"}])
        self.assertEqual(result.claims[0].status, "PARTIAL")
        self.assertIn("PubMed", result.claims[0].provider_errors)
        self.assertNotIn("secret-url", str(result))

    def test_invalid_claim_is_reported_and_not_requested(self):
        session = Mock()
        session.headers = {}
        result = LiteratureVerificationAgent(session=session, min_interval=0).verify([{"claim_id": "x"}])
        self.assertEqual(result.claims[0].status, "INVALID_CLAIM")
        session.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
