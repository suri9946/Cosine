import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SystemDatasetTests(unittest.TestCase):
    def test_dataset_covers_required_paracetamol_topics_and_abstention(self):
        data = json.loads((ROOT / "data/evaluation/paracetamol_system_cases.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        topics = {case["topic"] for case in cases}
        self.assertTrue({"mechanism_of_action", "pharmacology", "pharmacokinetics", "metabolism_napqi",
                         "toxicology_safety", "chemical_properties", "molecular_structure",
                         "source_page_traceability", "insufficient_evidence"}.issubset(topics))
        self.assertTrue(any(not case["answer_present"] and case["topic"] == "insufficient_evidence" for case in cases))
        for case_id, chemical in (("MISINFO-AMPA-01", "AMPA"), ("MISINFO-APABA-01", "APABA")):
            bad_pathway = next(case for case in cases if case["id"] == case_id)
            self.assertIn("NEEDS_REVISION", bad_pathway["expected_behavior"])
            self.assertIn(chemical, bad_pathway["question"])
            self.assertIn("NAPQI", bad_pathway["question"])

    def test_all_cases_have_unique_ids_and_explicit_expected_behavior(self):
        data = json.loads((ROOT / "data/evaluation/paracetamol_system_cases.json").read_text(encoding="utf-8"))
        ids = [case["id"] for case in data["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(case.get("expected_behavior") for case in data["cases"]))
        self.assertIn("not expert scientific ground truth", data["scope"])


if __name__ == "__main__":
    unittest.main()
