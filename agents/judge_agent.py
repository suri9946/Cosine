"""Independent claim review with deterministic evidence and pathway safeguards."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from agents.ollama_client import JUDGE_MODEL, OllamaClient, OllamaError


class JudgeOutputInvalid(ValueError):
    """The Judge model response violates the review contract."""

    def __init__(self, message: str, *, raw_response: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.raw_response = raw_response


@dataclass(frozen=True)
class ClaimJudgment:
    claim_id: str
    decision: str
    rationale: str
    evidence_ids: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class JudgeResult:
    status: str
    claims: list[ClaimJudgment]
    answer: str
    reasons: list[str]
    model: str | None
    raw_response: dict[str, Any] | None


_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"claims": {"type": "array", "items": {
        "type": "object", "properties": {
            "claim_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["APPROVED", "APPROVED_WITH_LIMITATIONS", "NEEDS_REVISION", "NEEDS_MORE_EVIDENCE", "ABSTAIN"]},
            "rationale": {"type": "string"},
            "evidence_ids": {"type": "array", "items": {"type": "string"}},
        }, "required": ["claim_id", "decision", "rationale", "evidence_ids"]
    }}, "answer": {"type": "string"}}, "required": ["claims", "answer"]
}

_PATHWAY_ERROR = re.compile(r"\b(?:AMPA|APABA)\b", re.I)
_NAPQI = re.compile(r"\b(?:NAPQI|toxic metabolite|metabolism|metabolite)\b", re.I)


def _field(value: Any, name: str, default: Any = None) -> Any:
    return value.get(name, default) if isinstance(value, Mapping) else getattr(value, name, default)


class JudgeAgent:
    """Judge Agent 2 claims against source evidence and Agent 3 candidates."""

    def __init__(self, client: OllamaClient | None = None, *, model: str = JUDGE_MODEL,
                 max_evidence: int = 8, max_abstract_chars: int = 1800, max_tokens: int = 900) -> None:
        self.client = client or OllamaClient()
        self.model = model
        self.max_evidence = max_evidence
        self.max_abstract_chars = max_abstract_chars
        self.max_tokens = max_tokens

    def evaluate(self, question: str, evidence: Sequence[Mapping[str, Any]], interpretation: Any,
                 verification: Any) -> JudgeResult:
        try:
            return self._evaluate_once(question, evidence, interpretation, verification)
        except JudgeOutputInvalid as first_error:
            try:
                result = self._evaluate_once(
                    question, evidence, interpretation, verification,
                    repair_feedback=(
                        "Your previous response violated the identifier/schema contract. "
                        "Return exactly one decision for each supplied claim, preserving each exact claim_id. "
                        "Use only evidence IDs supplied in local_evidence. Do not create claims or numeric IDs. "
                        "If the evidence is inadequate, choose NEEDS_MORE_EVIDENCE."
                    ),
                )
                return result
            except (JudgeOutputInvalid, OllamaError) as retry_error:
                return self._safe_abstention(
                    interpretation, "Judge output remained invalid after one retry", retry_error
                )
        except OllamaError as exc:
            return self._safe_abstention(interpretation, "Judge model is unavailable", exc)

    def _safe_abstention(self, interpretation: Any, reason: str, error: Exception) -> JudgeResult:
        """Keep the workflow auditable when Judge inference or validation fails."""
        claims = _field(interpretation, "claims", []) or []
        safe_claims: list[ClaimJudgment] = []
        for claim in claims:
            claim_id = str(_field(claim, "claim_id", ""))
            refs = _field(claim, "evidence_ids", []) or []
            safe_claims.append(ClaimJudgment(
                claim_id=claim_id,
                decision="NEEDS_MORE_EVIDENCE",
                rationale="No valid Judge review was produced; the draft was not approved.",
                evidence_ids=[ref for ref in refs if isinstance(ref, str)],
                warnings=["Judge inference or output validation failed; this is a safe fallback, not an AI review."],
            ))
        raw = getattr(error, "raw_response", None)
        return JudgeResult(
            "NEEDS_MORE_EVIDENCE", safe_claims, "",
            [f"{reason}; abstained safely ({type(error).__name__})."], None, raw,
        )

    def _evaluate_once(self, question: str, evidence: Sequence[Mapping[str, Any]], interpretation: Any,
                       verification: Any, repair_feedback: str | None = None) -> JudgeResult:
        claims = _field(interpretation, "claims", []) or []
        stage_status = _field(interpretation, "status", "COMPLETED")
        verify_status = _field(verification, "status", "UNAVAILABLE")
        if not evidence or not claims or stage_status != "COMPLETED":
            return JudgeResult("ABSTAIN", [], "", ["Required local evidence or valid Agent 2 claims are unavailable."], None, None)
        selected = [dict(item) for item in evidence[:self.max_evidence]]
        allowed_ids = {str(item.get("evidence_id")) for item in selected if item.get("evidence_id")}
        claim_payload: list[dict[str, Any]] = []
        for claim in claims:
            claim_data = dict(claim) if isinstance(claim, Mapping) else vars(claim)
            refs = claim_data.get("evidence_ids", [])
            if not isinstance(refs, list) or any(ref not in allowed_ids for ref in refs):
                return JudgeResult("NEEDS_REVISION", [], "", ["Agent 2 claim references evidence outside the supplied Agent 1 result."], None, None)
            if claim_data.get("claim_type") != "unknown" and not refs:
                return JudgeResult("NEEDS_MORE_EVIDENCE", [], "", ["Factual claim has no local evidence reference."], None, None)
            claim_payload.append({key: claim_data.get(key) for key in
                                  ("claim_id", "text", "claim_type", "explanation", "evidence_ids", "uncertainty", "requires_verification")})

        verification_claims = _field(verification, "claims", []) or []
        external: list[dict[str, Any]] = []
        provider_errors = False
        expected_claim_ids = {str(_field(claim, "claim_id", "")) for claim in claims}
        returned_claim_ids = {str(_field(item, "claim_id", "")) for item in verification_claims}
        verification_gap = expected_claim_ids != returned_claim_ids
        for item in verification_claims:
            provider_errors = provider_errors or bool(_field(item, "provider_errors", {}))
            verification_gap = verification_gap or _field(item, "status", "UNAVAILABLE") != "RECORDS_FOUND"
            for record in (_field(item, "records", []) or []):
                data = dict(record) if isinstance(record, Mapping) else asdict(record)
                data["abstract"] = str(data.get("abstract", ""))[:self.max_abstract_chars]
                external.append(data)
        local_context = [{key: item.get(key) for key in (
            "evidence_id", "source_id", "source_title", "source_url", "page", "section", "text"
        )} for item in selected]
        for item in local_context:
            item["text"] = str(item.get("text", ""))[:2200]
        system = (
            "You are an independent scientific evidence judge. Evaluate each claim against the actual supplied local "
            "passages and external literature records. A search result is not proof; abstracts and source type matter. "
            "Do not infer scientific facts from model memory. Reject unsupported statements, distinguish evidence from "
            "interpretation, preserve uncertainty, and abstain when needed. Cite only the provided local evidence IDs. "
            "Do not provide medical advice or dosing. Return only the requested JSON. "
            "Return exactly one review item for every supplied Agent 2 claim, with its exact claim_id. "
            "Evidence IDs must be copied exactly from the supplied local evidence; never invent or renumber them. "
            "Do not create extra claims. If evidence is insufficient, use NEEDS_MORE_EVIDENCE."
        )
        if repair_feedback:
            system += " " + repair_feedback
        user = json.dumps({"question": question, "allowed_claim_ids": [
                               str(_field(claim, "claim_id", "")) for claim in claims],
                           "allowed_evidence_ids": sorted(allowed_ids), "local_evidence": local_context,
                           "agent2_claims": claim_payload, "agent3_literature_candidates": external}, ensure_ascii=False)
        output_schema = deepcopy(_SCHEMA)
        output_schema["properties"]["claims"]["minItems"] = len(claim_payload)
        output_schema["properties"]["claims"]["maxItems"] = len(claim_payload)
        output_schema["properties"]["claims"]["items"]["properties"]["claim_id"]["enum"] = [
            str(claim["claim_id"]) for claim in claim_payload]
        output_schema["properties"]["claims"]["items"]["properties"]["evidence_ids"]["items"]["enum"] = sorted(allowed_ids)
        response = self.client.chat(self.model, [{"role": "system", "content": system},
            {"role": "user", "content": user}], temperature=0.0, max_tokens=self.max_tokens, format=output_schema)
        if response.raw.get("done") is False:
            raise JudgeOutputInvalid("Judge output was truncated before completion.", raw_response=response.raw)
        try:
            parsed = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise JudgeOutputInvalid("Judge returned invalid JSON.", raw_response=response.raw) from exc
        items = parsed.get("claims") if isinstance(parsed, dict) else None
        answer = parsed.get("answer") if isinstance(parsed, dict) else None
        if not isinstance(items, list) or not isinstance(answer, str):
            raise JudgeOutputInvalid("Judge response is missing claims or answer.", raw_response=response.raw)
        by_id = {str(_field(c, "claim_id", "")): c for c in claims}
        judgments: list[ClaimJudgment] = []
        invalid_refs = False
        for item in items:
            if not isinstance(item, dict) or item.get("claim_id") not in by_id:
                raise JudgeOutputInvalid("Judge returned an unknown claim ID.", raw_response=response.raw)
            decision, rationale, refs = item.get("decision"), item.get("rationale"), item.get("evidence_ids")
            if (not isinstance(decision, str) or decision not in {"APPROVED", "APPROVED_WITH_LIMITATIONS", "NEEDS_REVISION", "NEEDS_MORE_EVIDENCE", "ABSTAIN"}
                    or not isinstance(rationale, str) or not isinstance(refs, list)
                    or any(not isinstance(ref, str) for ref in refs)):
                raise JudgeOutputInvalid("Judge returned invalid decision fields.", raw_response=response.raw)
            source_claim = by_id[item["claim_id"]]
            # Agent 4 may independently select any supplied Agent 1 record,
            # but cannot cite an ID absent from the retrieval input.
            invalid_refs = invalid_refs or any(ref not in allowed_ids for ref in refs)
            if _field(source_claim, "claim_type", "") != "unknown" and not refs:
                invalid_refs = True
            text = str(_field(source_claim, "text", ""))
            pathway_flag = bool(_PATHWAY_ERROR.search(text) and _NAPQI.search(text))
            warnings = ["Potential AMPA/APABA toxic-metabolite pathway claim requires direct authoritative evidence."] if pathway_flag else []
            if pathway_flag:
                decision = "NEEDS_REVISION"
            elif _field(source_claim, "claim_type", "") == "unknown":
                decision = "NEEDS_MORE_EVIDENCE"
            judgments.append(ClaimJudgment(item["claim_id"], decision, rationale, refs, warnings))
        if invalid_refs:
            return JudgeResult("NEEDS_REVISION", judgments, "", ["Judge cited an unknown local evidence ID."], response.model, response.raw)
        if len(judgments) != len(claims):
            raise JudgeOutputInvalid("Judge did not return a decision for every claim.", raw_response=response.raw)
        decisions = {j.decision for j in judgments}
        if any(j.warnings for j in judgments):
            status = "NEEDS_REVISION"
        elif "NEEDS_REVISION" in decisions:
            status = "NEEDS_REVISION"
        elif "ABSTAIN" in decisions:
            status = "ABSTAIN"
        elif ("NEEDS_MORE_EVIDENCE" in decisions or verify_status != "COMPLETED"
              or provider_errors or verification_gap):
            status = "NEEDS_MORE_EVIDENCE"
        elif "APPROVED_WITH_LIMITATIONS" in decisions:
            status = "APPROVED_WITH_LIMITATIONS"
        else:
            status = "APPROVED"
        # Expose only claim text which survived review; discard free-form summary.
        approved_text = [str(_field(by_id[j.claim_id], "text", "")) for j in judgments
                         if j.decision in {"APPROVED", "APPROVED_WITH_LIMITATIONS"}]
        reasons = ["Agent 4 decisions are rule-checked draft assessments, not proof of scientific accuracy."]
        if verify_status != "COMPLETED" or provider_errors or verification_gap:
            reasons.append("Independent literature verification was partial or unavailable.")
        return JudgeResult(status, judgments, "\n".join(approved_text), reasons, response.model, response.raw)
