import unittest

from agents.knowledge_agent import classify_passage, get_question_topic


class QuestionTopicDetectionTests(unittest.TestCase):
    def test_plain_structure_question_routes_to_chemical_properties(self):
        question = "explain the structure of paracetamol"
        self.assertEqual(get_question_topic(question), "chemical_properties")
        result = classify_passage("Paracetamol molecular structure C8H9NO2 contains atoms and bonds.",
                                  question, "paracetamol")
        self.assertEqual(result["evidence_type"], "DIRECT_EVIDENCE_CANDIDATE")

    def test_long_term_harm_question_routes_to_safety(self):
        question = "can taking paracetamol kill humans in long term"
        self.assertEqual(get_question_topic(question), "side_effects")
        result = classify_passage("Long-term paracetamol exposure can cause liver injury and toxicity.",
                                  question, "paracetamol")
        self.assertEqual(result["evidence_type"], "DIRECT_EVIDENCE_CANDIDATE")


if __name__ == "__main__":
    unittest.main()
