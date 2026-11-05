# End-to-End Research Workflow

The full flow is implemented in `agents/orchestrator.py` and exposed through `app.py`. All agents have focused tests; the complete suite now passes 38 tests. One live end-to-end formula question passed. The full application evaluation is not yet complete. Agent 3 can be partial if the public APIs are unreachable, and this prevents a fully approved answer.

1. **Question intake:** assign a request ID; identify topic/scope; preserve the question. Current supported subject is paracetamol only.
2. **Evidence retrieval (Agent 1):** search approved local corpus using keyword BM25 and semantic retrieval; optionally rerank; return passages with source/page/section provenance, relevant limitations, and candidate conflicts.
3. **Evidence sufficiency gate:** if no relevant local evidence is found, stop or ask Agent 3 for literature search according to workflow policy. Do not ask the LLM to fill a missing evidence gap.
4. **Interpretation (Agent 2):** send only question and selected evidence to Ollama; request atomic claims linked to evidence IDs and clear hypothesis/uncertainty labels.
5. **Independent verification (Agent 3):** search NCBI/Europe PMC for each material claim, capture PMID/PMCID/DOI, date, study type, full-text availability and license. Record both support and contradiction.
6. **Independent judgment (Agent 4):** compare each claim to local evidence and external verification; assess source type, relevance, version, and disagreement. Reject unsupported citations/claims, mark uncertainty, request targeted additional retrieval if useful, otherwise abstain.
7. **Final response:** answer only approved claims, cite source title/identifier/link and page/section where available, explain unresolved disagreement and missing evidence, and include research-assistant limitation.
8. **Audit trail:** log stage status, source IDs, model ID/version, API identifiers and errors without storing credentials. Store deterministic processed artifacts separately from original files.

## Error paths

- Parser fails for one file: retain the source record, report extraction failure, continue with other sources.
- No extractable text: flag OCR/manual review; never index an empty document as evidence.
- Embedding unavailable: report semantic search unavailable; optionally use BM25 only and identify this limitation.
- External API unavailable/rate-limited: preserve partial results and mark independent verification incomplete.
- LLM unavailable: return retrieved evidence and a clear incomplete status; do not invent a generated answer.
- Judge unavailable: do not label the answer as reviewed; return an abstention/partial result.
