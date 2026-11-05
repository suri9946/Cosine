import logging
import unittest
from pathlib import Path

from agents.chemical_processing import chemical_evidence_documents, validate_chemical_sources
from agents.document_ingestion import ingest_corpus, sha256_file
from agents.knowledge_graph import build_evidence_graph

ROOT = Path(__file__).resolve().parents[1]
logging.disable(logging.CRITICAL)


class Agent1DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents, cls.report = ingest_corpus(ROOT)

    def test_nested_pdf_txt_xml_ingestion_preserves_provenance(self):
        self.assertEqual(self.report["files_seen"], 15)
        self.assertEqual(len(self.report["page_checks"]), 144)
        xml = [d for d in self.documents if d.metadata.get("local_path", "").endswith(".xml")]
        self.assertGreater(len(xml), 0)
        self.assertTrue(all(d.metadata.get("source_url") for d in xml))
        self.assertTrue(all(d.metadata.get("license_reuse") for d in xml))
        self.assertTrue(all(d.metadata.get("section") for d in xml))

    def test_scan_only_pages_are_ocr_diagnostic_not_indexed(self):
        scan_path = "20210403_bf001b70-6164-1ec9-e053-2a95a90a1274.pdf"
        pages = [r for r in self.report["page_checks"] if scan_path in r.get("local_path", "")]
        blank = [r for r in pages if r.get("character_count") == 0]
        self.assertEqual(len(blank), 10)
        self.assertTrue(all(r.get("ocr_status") for r in blank))
        self.assertTrue(all(not (d.metadata.get("local_path", "").endswith(scan_path)
                                 and d.metadata.get("page") in range(2, 12)) for d in self.documents))
        self.assertEqual(len(self.report["repeated_render_groups"]), 1)
        self.assertEqual(self.report["repeated_render_groups"][0]["pages"], list(range(2, 12)))

    def test_medlineplus_exact_text_duplicates_preserve_originals_and_index_one(self):
        groups = self.report["exact_text_duplicate_groups"]
        self.assertEqual(len(groups), 1)
        group = groups[0]
        all_paths = [group["canonical_path"], *group["duplicate_paths"]]
        self.assertEqual(len(all_paths), 4)
        self.assertTrue(all((ROOT / p).exists() for p in all_paths))
        indexed = [d for d in self.documents if "MedlinePlus Drug Information_doc" in d.metadata.get("source", "")]
        self.assertEqual(len(indexed), 6)

    def test_all_sdf_files_validate_to_same_paracetamol_structure(self):
        report = validate_chemical_sources(ROOT)
        self.assertEqual(report["status"], "validated")
        self.assertEqual(report["sdf_file_count"], 4)
        self.assertEqual(len(report["sdf_records"]), 4)
        self.assertTrue(all(r["parse_status"] == "parsed" for r in report["sdf_records"]))
        self.assertEqual({r["formula"] for r in report["sdf_records"]}, {"C8H9NO2"})
        self.assertEqual(len({r["canonical_smiles"] for r in report["sdf_records"]}), 1)
        self.assertEqual(report["json_status"], "valid_json")
        self.assertGreaterEqual(len(chemical_evidence_documents(ROOT)), 5)

    def test_all_manifest_source_hashes_still_match(self):
        import csv
        with (ROOT / "SOURCE_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        checked = [r for r in rows if r.get("local_filename") and r.get("sha256")]
        self.assertEqual(len(checked), 20)
        for row in checked:
            source = ROOT / row["local_filename"].replace("\\", "/")
            self.assertTrue(source.is_file(), source)
            self.assertEqual(sha256_file(source).lower(), row["sha256"].lower(), source)

    def test_graph_edges_retain_source_evidence_and_lexical_basis(self):
        graph = build_evidence_graph(self.documents)
        self.assertIn("paracetamol", {n.get("drug_id") for n in graph["nodes"]})
        self.assertTrue(any(edge["relation"] == "contains_evidence" for edge in graph["edges"]))
        self.assertTrue(all(not edge.get("scientific_assertion", False)
                            for edge in graph["edges"] if edge["relation"] == "mentions_concept"))


if __name__ == "__main__":
    unittest.main()
