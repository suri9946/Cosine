"""Run the expanded Agent 1 retrieval/provenance slice of the system dataset."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.knowledge_agent import KnowledgeAgent


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "evaluation" / "paracetamol_system_cases.json"
OUTPUT = ROOT / "data" / "processed" / "system_retrieval_evaluation.json"


def evaluate_retrieval(agent: KnowledgeAgent | None = None, *, write_output: bool = True) -> dict[str, Any]:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    agent = agent or KnowledgeAgent()
    if agent.bm25 is None:
        agent.load_documents()
    evaluated: list[dict[str, Any]] = []
    for case in dataset["cases"]:
        results = agent.search(case["question"], top_k=5)
        assessment = agent.assess_evidence(case["question"], results)
        source_path = case.get("expected_path_contains", "")
        source_rank = next((rank for rank, record in enumerate(results, 1)
                            if source_path and source_path.lower() in str(record.get("source_path", "")).lower()), None)
        page_rank = next((rank for rank, record in enumerate(results, 1)
                          if source_path and source_path.lower() in str(record.get("source_path", "")).lower()
                          and case.get("expected_page") is not None
                          and record.get("page") == case["expected_page"]), None)
        matched = [term for term in case.get("expected_terms", [])
                   if any(term.casefold() in str(record.get("text", "")).casefold() for record in results)]
        traceable = all(record.get("evidence_id") and record.get("source_id") and record.get("source_path")
                        and (record.get("page") is not None or record.get("section")) for record in results)
        evaluated.append({"case_id": case["id"], "topic": case["topic"],
                          "answer_present": case["answer_present"], "expected_source_rank": source_rank,
                          "expected_source_page_rank": page_rank,
                          "expected_terms": case.get("expected_terms", []), "matched_terms": matched,
                          "assessment_status": assessment["status"], "traceability_complete": traceable,
                          "candidate_count": len(results)})
    answerable = [case for case in evaluated if case["answer_present"]]
    expected_source = [case for case in answerable if case.get("expected_source_rank") is not None]
    expected_source_total = sum(bool(case.get("expected_path_contains")) for case in dataset["cases"] if case["answer_present"])
    expected_page_total = sum(case.get("expected_page") is not None for case in dataset["cases"])
    expected_page_hits = sum(case.get("expected_source_page_rank") is not None for case in evaluated)
    absent = [case for case in evaluated if not case["answer_present"] and case["topic"] == "insufficient_evidence"]
    all_returned_traceable = [case for case in evaluated if case["candidate_count"] > 0]
    report = {
        "dataset_id": dataset["dataset_id"],
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Agent 1 retrieval and provenance only; does not assess scientific accuracy or claim correctness.",
        "metrics": {
            "case_count": len(evaluated),
            "answerable_term_coverage": sum(bool(case["matched_terms"]) for case in answerable) / max(len(answerable), 1),
            "expected_source_recall_at_5": len(expected_source) / max(expected_source_total, 1),
            "expected_source_page_recall_at_5": expected_page_hits / max(expected_page_total, 1),
            "traceability_rate_returned_cases": sum(case["traceability_complete"] for case in all_returned_traceable) / max(len(all_returned_traceable), 1),
            "absent_question_insufficient_rate": sum(case["assessment_status"] == "INSUFFICIENT_EVIDENCE" for case in absent) / max(len(absent), 1),
            "absent_question_count": len(absent),
        },
        "scientific_accuracy_assessed": False,
        "cases": evaluated,
    }
    if write_output:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = evaluate_retrieval()
    print(json.dumps({"dataset": result["dataset_id"], "metrics": result["metrics"],
                      "scientific_accuracy_assessed": False}, indent=2))
