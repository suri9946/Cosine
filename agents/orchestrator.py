"""Ordered four-agent orchestration with fail-closed stage handling."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, fields, is_dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.chemistry_pharmacology_agent import ChemistryPharmacologyAgent
from agents.judge_agent import JudgeAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.literature_verification_agent import LiteratureVerificationAgent


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if hasattr(value, "__dict__"):
        return {str(key): _plain(item) for key, item in vars(value).items()
                if not str(key).startswith("_")}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


@dataclass(frozen=True)
class ResearchRun:
    request_id: str
    question: str
    status: str
    answer: str
    retrieval_assessment: dict[str, Any]
    evidence: list[dict[str, Any]]
    interpretation: Any
    verification: Any
    judgment: Any
    stage_errors: dict[str, str]
    audit_path: str | None
    stage_timings_ms: dict[str, int] = field(default_factory=dict)


class ResearchOrchestrator:
    def __init__(self, retriever: KnowledgeAgent | None = None,
                 interpreter: ChemistryPharmacologyAgent | None = None,
                 verifier: LiteratureVerificationAgent | None = None,
                 judge: JudgeAgent | None = None,
                 *, audit_dir: Path | str | None = None, top_k: int = 5) -> None:
        self.retriever = retriever or KnowledgeAgent()
        self.interpreter = interpreter or ChemistryPharmacologyAgent()
        self.verifier = verifier or LiteratureVerificationAgent()
        self.judge = judge or JudgeAgent()
        self.audit_dir = Path(audit_dir) if audit_dir else PROJECT_ROOT / "data" / "processed" / "runs"
        self.top_k = top_k

    def run(self, question: str, on_progress: Any = None) -> ResearchRun:
        request_id = uuid.uuid4().hex
        run_started = time.perf_counter()
        timings: dict[str, int] = {}

        def finish(run: ResearchRun) -> ResearchRun:
            timings["total"] = round((time.perf_counter() - run_started) * 1000)
            return self._audit(replace(run, stage_timings_ms=dict(timings)))

        def notify(stage: str, status: str, details: Any = None) -> None:
            if callable(on_progress):
                try:
                    on_progress(stage, status, details)
                except Exception:
                    pass

        if not isinstance(question, str) or not question.strip():
            notify("intake", "failed", {"error": "question is empty"})
            return finish(ResearchRun(request_id, str(question or ""), "ABSTAIN", "", {"status": "INVALID_QUESTION"}, [],
                                      None, None, None, {"intake": "question is empty"}, None))
        errors: dict[str, str] = {}
        stage_started = time.perf_counter()
        notify("agent1", "running", {"stage_name": "Scientific Knowledge Retrieval"})
        try:
            evidence = self.retriever.search(question, top_k=self.top_k)
            assessment = self.retriever.assess_evidence(question, evidence)
        except Exception as exc:
            timings["agent1"] = round((time.perf_counter() - stage_started) * 1000)
            notify("agent1", "failed", {"error": type(exc).__name__})
            return finish(ResearchRun(request_id, question, "ABSTAIN", "", {"status": "RETRIEVAL_FAILED"}, [],
                                      exc, None, None, {"agent1": type(exc).__name__}, None))
        timings["agent1"] = round((time.perf_counter() - stage_started) * 1000)
        a1_status = "completed" if assessment.get("status") == "RETRIEVAL_RELEVANT_REVIEW_REQUIRED" else "needs_attention"
        notify("agent1", a1_status, {
            "evidence": evidence,
            "assessment": assessment,
            "candidates_count": len(evidence),
            "timing_ms": timings["agent1"],
        })
        if assessment.get("status") != "RETRIEVAL_RELEVANT_REVIEW_REQUIRED":
            notify("agent2", "waiting", {"message": "Skipped due to insufficient retrieval evidence"})
            notify("agent3", "waiting", {"message": "Skipped due to insufficient retrieval evidence"})
            notify("agent4", "waiting", {"message": "Skipped due to insufficient retrieval evidence"})
            result = ResearchRun(request_id, question, "ABSTAIN", "", assessment, evidence, None, None, None,
                                 {}, None)
            return finish(result)
        stage_started = time.perf_counter()
        notify("agent2", "running", {
            "stage_name": "Chemistry & Pharmacology Analysis",
            "model": getattr(self.interpreter, "model", "ChemLLM-7B"),
        })
        try:
            interpretation = self.interpreter.interpret(question, evidence)
        except Exception as exc:
            timings["agent2"] = round((time.perf_counter() - stage_started) * 1000)
            notify("agent2", "failed", {"error": type(exc).__name__})
            return finish(ResearchRun(request_id, question, "PARTIAL", "", assessment, evidence, exc, None, None,
                                      {"agent2": type(exc).__name__}, None))
        timings["agent2"] = round((time.perf_counter() - stage_started) * 1000)
        a2_status = "completed" if getattr(interpretation, "status", "") == "COMPLETED" else "needs_attention"
        notify("agent2", a2_status, {
            "interpretation": interpretation,
            "claims": getattr(interpretation, "claims", []),
            "timing_ms": timings["agent2"],
        })
        if getattr(interpretation, "status", "") != "COMPLETED":
            notify("agent3", "waiting", {"message": "Skipped due to incomplete interpretation"})
            notify("agent4", "waiting", {"message": "Skipped due to incomplete interpretation"})
            return finish(ResearchRun(request_id, question, "ABSTAIN", "", assessment, evidence,
                                     interpretation, None, None, {}, None))
        stage_started = time.perf_counter()
        notify("agent3", "running", {
            "stage_name": "Scientific Literature Verification",
            "providers": ["NCBI PubMed", "Europe PMC"],
        })
        try:
            verification = self.verifier.verify(interpretation.claims)
        except Exception as exc:
            # Preserve the local evidence and claims, but do not suggest an
            # independently verified answer if Agent 3 failed unexpectedly.
            errors["agent3"] = type(exc).__name__
            verification = {"status": "UNAVAILABLE", "claims": [], "warnings": ["Verifier raised an error."]}
        timings["agent3"] = round((time.perf_counter() - stage_started) * 1000)
        v_status = verification.get("status", "") if isinstance(verification, dict) else getattr(verification, "status", "")
        a3_status = "completed" if v_status == "COMPLETED" else ("failed" if v_status == "UNAVAILABLE" else "needs_attention")
        notify("agent3", a3_status, {
            "verification": verification,
            "status": v_status,
            "timing_ms": timings["agent3"],
        })
        stage_started = time.perf_counter()
        notify("agent4", "running", {
            "stage_name": "Scientific Quality Review",
            "model": getattr(self.judge, "model", "llama3.2:3b"),
        })
        try:
            judgment = self.judge.evaluate(question, evidence, interpretation, verification)
        except Exception as exc:
            errors["agent4"] = type(exc).__name__
            timings["agent4"] = round((time.perf_counter() - stage_started) * 1000)
            notify("agent4", "failed", {"error": type(exc).__name__})
            return finish(ResearchRun(request_id, question, "ABSTAIN", "", assessment, evidence,
                                      interpretation, verification, exc, errors, None))
        timings["agent4"] = round((time.perf_counter() - stage_started) * 1000)
        final_status = judgment.status
        if errors or final_status not in {"APPROVED", "APPROVED_WITH_LIMITATIONS"}:
            if final_status in {"APPROVED", "APPROVED_WITH_LIMITATIONS"}:
                final_status = "NEEDS_MORE_EVIDENCE"
        notify("agent4", "completed", {
            "judgment": judgment,
            "final_status": final_status,
            "timing_ms": timings["agent4"],
        })
        result = ResearchRun(request_id, question, final_status, judgment.answer, assessment, evidence,
                             interpretation, verification, judgment, errors, None)
        return finish(result)

    def _audit(self, run: ResearchRun) -> ResearchRun:
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        path = self.audit_dir / f"{run.request_id}.json"
        payload = _plain(run)
        payload["created_at"] = datetime.now(timezone.utc).isoformat()
        payload["audit_path"] = str(path)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
        return replace(run, audit_path=str(path))
