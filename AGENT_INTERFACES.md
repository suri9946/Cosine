# Proposed Agent Interfaces

The four-agent contracts remain the long-term target. Agent 1's `KnowledgeAgent.search()` currently returns provenance-bearing result dictionaries. The shared Ollama client, Agent 2 interpreter, Agent 3 verifier, Agent 4 Judge and ordered orchestrator are implemented. Typed cross-agent Python interfaces are still being consolidated; the existing component boundaries are documented below.

## Current Agent 1 result fields

`KnowledgeAgent.search()` returns `evidence_id`, `source_id`, `source_path`, `source_url`, title/authors/identifiers where available, reuse notes, version date, page or section, extractor, extraction-quality status, retrieval scores, provisional evidence type, and passage text. Missing source metadata remains empty rather than inferred.

## Shared records

The system passes typed records rather than free-form agent messages. Minimal envelopes:

- `ResearchQuestion`: `question_id`, `text`, `drug_id="paracetamol"`, requested topics, timestamp, optional constraints.
- `EvidenceRecord`: `evidence_id`, `source_id`, `quote_or_passage`, `document_type`, `source_title`, `authors`, `date`, `DOI/PMID/PMCID`, `URL`, `page_or_section`, `extraction_method`, license/use notes, retrieval scores, limitations.
- `Claim`: `claim_id`, `text`, `claim_type` (established finding / interpretation / hypothesis / unknown), supporting evidence IDs, contradicting evidence IDs, limitations.
- `AgentResult`: `agent`, `status`, `records`, `warnings`, `errors`, `started_at`, `duration_ms`.

Unknown metadata stays null/unknown; it is never inferred from a filename without marking the inference.

## Contracts

| Component | Input | Output | Failure behavior |
|---|---|---|---|
| Agent 1 retrieval | `ResearchQuestion`, filters/top-k | Ranked `EvidenceRecord[]`, conflicts/gaps, retrieval status | Empty evidence or index error is explicit; never substitutes ungrounded facts |
| Agent 2 interpretation | Question plus Agent 1 evidence | Draft `Claim[]`, concise answer, uncertainty notes | Timeout/model unavailable returns error status; no uncited scientific claims accepted by downstream stages |
| Agent 3 verifier | Question and atomic claims | Independently found literature records mapped to claim IDs; support/contradiction/availability | Rate-limit or API failure returns partial status and preserves known metadata |
| Agent 4 Judge | Question, Agent 1 evidence, Agent 2 claims, Agent 3 records | Claim decisions, rejected/qualified claims, final answer or abstention | Judge failure cannot produce an unmarked approved answer |
| Orchestrator | Question | Result of ordered stages | Stops or returns clearly partial status when a required stage fails |

## Interface rules

1. Retrieval precedes interpretation.
2. Every final factual statement maps to evidence IDs and visible citations.
3. Agent 3 searches independently; it does not merely validate Agent 2's citations.
4. Agent 4 receives source records directly and can reject the LLM claim.
5. Agents return machine-readable status and warnings; no exception is silently swallowed.
6. Model outputs and retrieval scores are never presented as calibrated certainty.

## Python boundaries (implemented components; typed records still evolving)

```python
class Retriever(Protocol):
    def retrieve(self, question: ResearchQuestion) -> AgentResult: ...

class Interpreter(Protocol):
    def interpret(self, question: ResearchQuestion,
                  evidence: list[EvidenceRecord]) -> AgentResult: ...

class LiteratureVerifier(Protocol):
    def verify(self, question: ResearchQuestion,
               claims: list[Claim]) -> AgentResult: ...

class Judge(Protocol):
    def evaluate(self, question: ResearchQuestion, evidence: list[EvidenceRecord],
                 claims: list[Claim], verification: AgentResult) -> AgentResult: ...
```
