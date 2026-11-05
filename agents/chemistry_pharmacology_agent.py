"""Evidence-bound chemistry/pharmacology interpretation using the local ChemLLM."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from agents.ollama_client import CHEMLLM_MODEL, OllamaClient


class Agent2OutputInvalid(ValueError):
    """The model response did not satisfy Agent 2's evidence contract."""

    def __init__(self, message: str, *, raw_response: dict[str, Any] | None = None,
                 raw_content: str | None = None) -> None:
        super().__init__(message)
        self.raw_response = raw_response
        self.raw_content = raw_content


@dataclass(frozen=True)
class InterpretationResult:
    status: str
    model: str
    answer: str
    claims: list[dict[str, Any]]
    warnings: list[str]
    raw_response: dict[str, Any] | None
    raw_content: str | None


_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "maxItems": 2,
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "maxLength": 240},
                    "claim_type": {"type": "string", "enum": ["finding", "interpretation", "hypothesis", "unknown"]},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                    "uncertainty": {"type": "string", "maxLength": 140},
                    "requires_verification": {"type": "boolean"},
                },
                "required": ["text", "claim_type", "evidence_refs", "uncertainty", "requires_verification"],
            },
        },
    },
    "required": ["claims"],
}


class ChemistryPharmacologyAgent:
    """Interpret retrieved passages without treating model memory as evidence."""

    def __init__(self, client: OllamaClient | None = None, *, model: str = CHEMLLM_MODEL,
                 max_evidence: int = 5, max_passage_chars: int = 1200,
                 max_tokens: int = 450) -> None:
        if max_evidence < 1 or max_passage_chars < 1 or max_tokens < 1:
            raise ValueError("evidence and output limits must be positive")
        self.client = client or OllamaClient()
        self.model = model
        self.max_evidence = max_evidence
        self.max_passage_chars = max_passage_chars
        self.max_tokens = max_tokens

    def interpret(self, question: str, evidence: Sequence[Mapping[str, Any]]) -> InterpretationResult:
        if not question.strip():
            raise ValueError("question must not be empty")
        selected = [dict(item) for item in evidence[:self.max_evidence]
                    if isinstance(item.get("evidence_id"), str) and item.get("evidence_id")
                    and isinstance(item.get("text"), str) and item.get("text", "").strip()]
        if not selected:
            return InterpretationResult("INSUFFICIENT_EVIDENCE", self.model, "", [],
                                        ["No usable Agent 1 passages were supplied."], None, None)
        ref_to_id = {f"E{index}": str(item["evidence_id"]) for index, item in enumerate(selected, 1)}
        context = [{"ref": f"E{index}", **{key: item.get(key) for key in (
            "source_id", "source_title", "source_url", "page", "section", "text"
        )}} for index, item in enumerate(selected, 1)]
        for record in context:
            record["text"] = str(record["text"])[:self.max_passage_chars]
        system = (
            "You are a chemistry and pharmacology research assistant. Use only the supplied passages. "
            "Do not use pretrained knowledge to add factual claims. Each factual claim must cite one or more "
            "provided evidence refs (E1, E2, etc.) exactly. Never construct a reference. If passages do not answer the question, say so and return no claim "
            "or an unknown claim with no evidence IDs. Distinguish a source statement from your interpretation; "
            "mark uncertain or mechanistic claims for independent verification. Return only a claims array; do not "
            "write a summary answer. Return at most two claims, each with one sentence of at most 25 words. Focus strictly on the requested question; "
            "do not add generic drug background, side effects, interactions, or medical advice unless the supplied "
            "passage directly answers that request. "
            "Do not give dosing or treatment advice. "
            "Return only the requested JSON object."
        )
        user = json.dumps({"question": question, "drug_scope": "paracetamol", "evidence": context}, ensure_ascii=False)
        output_schema = deepcopy(_SCHEMA)
        output_schema["properties"]["claims"]["items"]["properties"]["evidence_refs"]["items"]["enum"] = list(ref_to_id)
        response = self.client.chat(self.model, [
            {"role": "system", "content": system}, {"role": "user", "content": user}
        ], temperature=0.0, max_tokens=self.max_tokens, format=output_schema)
        if response.raw.get("done") is False or response.raw.get("done_reason") in {"length", "max_tokens"}:
            raise Agent2OutputInvalid("ChemLLM output was truncated before completion.",
                                      raw_response=response.raw, raw_content=response.content)
        try:
            payload = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise Agent2OutputInvalid("ChemLLM returned invalid JSON.", raw_response=response.raw,
                                      raw_content=response.content) from exc
        claims = payload.get("claims") if isinstance(payload, dict) else None
        if not isinstance(claims, list):
            raise Agent2OutputInvalid("ChemLLM JSON is missing claims.", raw_response=response.raw,
                                      raw_content=response.content)
        normalized: list[dict[str, Any]] = []
        seen_claims: set[tuple[str, tuple[str, ...]]] = set()
        duplicate_count = 0
        for claim in claims:
            if not isinstance(claim, dict):
                raise Agent2OutputInvalid("Each claim must be a JSON object.", raw_response=response.raw,
                                          raw_content=response.content)
            required = ("text", "claim_type", "evidence_refs", "uncertainty", "requires_verification")
            if any(key not in claim for key in required):
                raise Agent2OutputInvalid("A claim is missing required fields.", raw_response=response.raw,
                                          raw_content=response.content)
            if (not isinstance(claim["text"], str) or not claim["text"].strip()
                    or not isinstance(claim["claim_type"], str)
                    or claim["claim_type"] not in {"finding", "interpretation", "hypothesis", "unknown"}
                    or not isinstance(claim["uncertainty"], str)
                    or not isinstance(claim["requires_verification"], bool)
                    or not isinstance(claim["evidence_refs"], list)
                    or any(not isinstance(ref, str) or ref not in ref_to_id for ref in claim["evidence_refs"])):
                raise Agent2OutputInvalid("Claim fields are invalid or cite an unknown evidence reference.",
                                          raw_response=response.raw, raw_content=response.content)
            if claim["claim_type"] != "unknown" and not claim["evidence_refs"]:
                raise Agent2OutputInvalid("A factual claim must cite supplied evidence.",
                                          raw_response=response.raw, raw_content=response.content)
            mapped = [ref_to_id[ref] for ref in claim["evidence_refs"]]
            signature = (" ".join(claim["text"].casefold().split()), tuple(sorted(mapped)))
            if signature in seen_claims:
                duplicate_count += 1
                continue
            seen_claims.add(signature)
            normalized.append({"claim_id": f"a2-{len(normalized)+1}", "explanation": "",
                               **{key: value for key, value in claim.items() if key != "evidence_refs"},
                               "evidence_ids": mapped})
        # Only validated claims are exposed as the answer. The model's free-form
        # summary may contain statements that are not represented/cited by claims.
        grounded_answer = "\n".join(claim["text"] for claim in normalized)
        warnings = ["Agent 2 output is a draft interpretation, not scientific validation."]
        if duplicate_count:
            warnings.append(f"Removed {duplicate_count} exact duplicate claim(s) from the model draft.")
        return InterpretationResult("COMPLETED", response.model, grounded_answer, normalized, warnings,
                                    response.raw, response.content)
