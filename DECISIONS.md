# Decisions

## 2026-11-01 — Initial scope

- Initial development and evaluation focus only on paracetamol (acetaminophen).
- Do not acquire ibuprofen or other drug datasets. Keep architecture modular for possible future additions without implementing multi-drug behavior now.
- Preserve original local sources and application code.

## 2026-11-01 — Research acquisition and architecture milestone (approved)

- Download only sources with verified public endpoints and appropriate access; record reuse terms and limitations individually.
- Acquired the CC BY Esh et al. review from Europe PMC XML after the PMC PDF endpoint served an anti-bot HTML page. The XML remains the source; generated text is attributed.
- The PMC4498995 author manuscript has no verified reuse license; record metadata only and do not copy the full text.
- Keep DailyMed label PDFs as local references, including the 2020 historical candidate and the 2026 Medline product label; rights/reuse beyond access were not confirmed, so do not redistribute them absent permission.
- Preserve the existing PubChem JSON when the current endpoint returns an exact duplicate. Retain separately named SDF snapshots only when their hashes differ from existing files.
- Owner approved the research acquisition milestone and the documented four-agent architecture; Agent 1 may proceed. Agents 2–4 remain unimplemented.
- No application code, dependencies, or existing original research files were changed during this milestone.

## 2026-11-01 — Agent 1 implementation choices

- Keep the existing `KnowledgeAgent` BM25, SentenceTransformer, cosine, RRF and evidence-label logic; add ingestion and provenance as small modules rather than replacing retrieval.
- Default data input is the existing `data/research/paracetamol` corpus. Index only one canonical copy from the four MedlinePlus PDFs because full extracted text matches; preserve all four originals and record that the distinct PDF metadata does not establish version identity.
- Use RDKit 2026.09.1 in `.venv312` for SDF validation, and pypdfium2 5.14.0 plus the existing Tesseract installation for rendered-page review/OCR. Dependencies are installed in the project virtual environment only; package versions, licenses and verified wheel hashes are recorded in `AGENT1_DEPENDENCIES.md`.
- Scan-only label text remains excluded from retrieval because Tesseract output is unverified. Pages 2–11 were rendered, are pixel-identical, and representative pages were visually checked.
- Keep evidence-graph concept links lexical and label them as non-assertive; do not infer scientific relations.
- Benchmark acceptance for this stage: answerable source retrieval@5, gold source/page retrieval when specified, traceability fields, duplicate-family behavior, and insufficient-evidence status for absent questions. Passing retrieval metrics do not establish scientific accuracy.
- No additional research documents are authorized by this implementation step; corpus gaps are recommendations for owner review.

## 2026-11-01 — Full-system build directive

- The user's Master Build Directive supersedes the earlier Agent 1 review pause and authorizes ordered implementation of the integrated four-agent application. Paracetamol-only scope, preservation, no model downloads, and scientific-evidence safeguards remain in force.
- Keep the exact already-installed ChemLLM model for Agent 2 and llama3.2:3b for Agent 4. Use shared OllamaClient; default keep_alive=0 releases model memory after each request.
- Agent 2 factual claims must cite supplied Agent 1 evidence IDs; malformed outputs and unknown citations fail closed. Preserve raw response for run audit.

## 2026-11-01 — Agent 3 access behavior

- Search PubMed and Europe PMC independently at conservative request intervals; NCBI key/email are optional and remain local environment configuration.
- Return literature candidates/abstracts without asserting support or contradiction. Do not acquire full text when network access is unavailable or license terms are not affirmatively understood.
- Preserve partial/unavailable state when a provider cannot be reached; do not turn an API failure into a no-records result.


- Official API guidance reviewed 2026-11-01: NCBI E-Utilities requests are limited to 3/sec without a key (10/sec default with a key); this client runs at no more than 2/sec without a key. PMC states automated retrieval should use its approved services and per-article reuse terms vary. References: https://eutilities.github.io/site/API_Key/usageandkey/ and https://pmc.ncbi.nlm.nih.gov/tools/developers/.



## 2026-11-01 ? Agent 2 evidence reference format and run decisions

- Agent 2 receives short labels (`E1`, `E2`, ?) for retrieved passages. The application maps these labels to immutable Agent 1 evidence IDs after validating them. This prevents a model from fabricating or mistyping long hash IDs.
- The Judge may cite any evidence ID from the current Agent 1 result, but cannot introduce an ID outside that set. The displayed answer is derived from the validated Agent 2 claim, not the Judge's free-form summary.
- Per-run audit JSON preserves the question, evidence provenance, structured results, raw model responses, external records and stage errors. An `APPROVED` pipeline status is not a claim of scientific accuracy or clinical safety.
