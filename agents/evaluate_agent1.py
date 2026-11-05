"""Run the fixed paracetamol retrieval benchmark; relevance is not truth."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.knowledge_agent import KnowledgeAgent

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "data" / "evaluation" / "paracetamol_agent1_benchmark.json"


def evaluate(agent: KnowledgeAgent | None = None) -> dict[str, Any]:
    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    agent = agent or KnowledgeAgent()
    if agent.bm25 is None:
        agent.load_documents()
    results = []
    for case in benchmark["cases"]:
        retrieved = agent.search(case["question"], top_k=5)
        expected_path = case["expected_path_contains"]
        expected_hit = next((i for i, item in enumerate(retrieved, start=1)
                             if expected_path and expected_path.lower() in item["source_path"].lower()), None)
        expected_page = case.get("expected_page")
        expected_page_hit = next((i for i, item in enumerate(retrieved, start=1)
                                  if expected_path and expected_path.lower() in item["source_path"].lower()
                                  and expected_page is not None and item.get("page") == expected_page), None)
        term_matches = [term for term in case["expected_terms"]
                        if any(term.lower() in item["text"].lower() for item in retrieved)]
        traceable = all(bool(item.get("source_id")) and bool(item.get("source_path"))
                        and bool(item.get("evidence_id")) and
                        (item.get("page") is not None or bool(item.get("section")))
                        for item in retrieved)
        assessment = agent.assess_evidence(case["question"], retrieved)
        results.append({
            "case_id": case["id"], "topic": case["topic"],
            "answer_present": case["answer_present"], "expected_page": expected_page,
            "expected_source_rank": expected_hit,
            "expected_source_page_rank": expected_page_hit,
            "retrieval_relevant": bool(term_matches), "matched_expected_terms": term_matches,
            "traceability_complete": traceable,
            "assessment_status": assessment["status"],
            "direct_candidate_count": assessment["direct_candidates"],
            "results": [{"source_path": x["source_path"], "source_id": x["source_id"],
                         "page": x["page"], "section": x["section"],
                         "evidence_id": x["evidence_id"], "evidence_type": x["evidence_type"],
                         "keyword_score": x["keyword_score"], "semantic_score": x["semantic_score"]}
                        for x in retrieved],
        })
    present = [r for r in results if r["answer_present"]]
    absent = [r for r in results if not r["answer_present"]]
    report = {
        "benchmark_id": benchmark["benchmark_id"],
        "scope": benchmark["scope"],
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "present_case_relevance_at_5": sum(r["retrieval_relevant"] for r in present) / max(1, len(present)),
            "expected_source_recall_at_5": sum(r["expected_source_rank"] is not None for r in present) / max(1, len(present)),
            "gold_source_page_recall_at_5": sum(r["expected_source_page_rank"] is not None
                                                   for r in present if r["expected_page"] is not None)
                                                   / max(1, sum(r["expected_page"] is not None for r in present)),
            "traceability_rate": sum(r["traceability_complete"] for r in results) / max(1, len(results)),
            "absent_cases_marked_insufficient": sum(r["assessment_status"] == "INSUFFICIENT_EVIDENCE" for r in absent) / max(1, len(absent)),
            "absent_cases_with_direct_candidates": sum(r["direct_candidate_count"] > 0 for r in absent),
        },
        "scientific_accuracy_assessed": False,
        "cases": results,
    }
    return report


if __name__ == "__main__":
    output = evaluate()
    target = ROOT / "data" / "processed" / "agent1_evaluation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output["metrics"], indent=2))
