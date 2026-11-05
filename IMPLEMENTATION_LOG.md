# Implementation Log

## 2026-11-01 — Audit

- Inspected existing app, corpus, environment, and test availability.
- `main.py` exits because `data/documents` is missing; pytest is unavailable and no test files were present.
- No app code or source data changed.

## 2026-11-01 — Paracetamol corpus and architecture milestone

- Verified candidates using direct HTTP requests to NCBI/Europe PMC, DailyMed, and PubChem. Ordinary restricted shell requests initially failed through the configured proxy; read-only network access was authorized for direct retrieval.
- Downloaded and verified: Europe PMC JATS XML for PMC5744234 (CC BY), DailyMed 2020 candidate PDF, DailyMed 2026 current product-label PDF, PubChem 2D SDF, and PubChem 3D SDF. Generated an attributed text derivative from the licensed XML.
- Direct PMC PDF URL returned an anti-bot HTML page (not saved); Europe PMC XML succeeded. PMC4498995's full-text endpoint returned HTTP 500 and its author-manuscript license was unclear, so no full-text copy was acquired.
- PubChem JSON was checked; its current response SHA-256 exactly matched the existing JSON, so the redundant copy was not retained.
- Validated PDF signatures/opening, 144 total PDF pages, page-level text presence, XML license/parsing, JSON record structure, SDF record headers, and file hashes. Detailed outcomes are in `TEST_RESULTS.md` and acquisition log.
- Added acquisition/coverage registers and documented system architecture, agent interfaces, schemas, workflow, and evaluation methodology.
- Preserved original corpus and application code; no dependencies installed. Agent 1 remains NOT STARTED.
- At the time this acquisition report was written, owner review was pending. The owner later approved this milestone and the four-agent architecture before Agent 1 work began.

## 2026-11-01 — Agent 1 implementation stage

- Owner approved research acquisition and four-agent architecture; scope remains paracetamol only. Agents 2–4 are not implemented.
- Added `agents/document_ingestion.py`: recursive PDF/TXT/JATS XML extraction, manifest metadata/hash preservation, 1-based PDF pages, XML sections, and page-level extraction/OCR quality reporting. The legacy custom-PDF-directory path remains available in `KnowledgeAgent`.
- Added `agents/chemical_processing.py`: PubChem JSON property extraction and RDKit 2026.09.1 parsing/sanitization. Four SDF files each produced one valid paracetamol record with formula C8H9NO2 and identical canonical SMILES.
- Added `agents/knowledge_graph.py`: serialized paracetamol/source/evidence/concept graph; concept links are lexical only and marked as non-scientific assertions.
- Updated `agents/knowledge_agent.py` to default to the real nested corpus, retain existing embedding/BM25/RRF retrieval, and return evidence IDs, source URLs, source IDs, reuse notes, page/section and extraction quality. `main.py` now displays provenance fields.
- Installed verified Windows x64 wheel `rdkit==2026.9.1` (SHA-256 verified against PyPI) plus Pillow 13.0.0, and approved `pypdfium2==5.14.0` wheel (PyPI SHA-256 `149fd5c6397b8df8bf7911a93506eff0be874f877afe7ac936cf5d37d21a6a06`) into `.venv312` only. Tesseract was already installed on the machine.
- Rendered FDA scan-only pages 2–11. Their PNG renders have the same hash; pages 2, 3, and 11 were visually inspected. OCR text is imperfect, retained only in a derived audit report and excluded from indexed evidence.
- Confirmed four MedlinePlus PDFs have identical full extracted text while byte hashes and PDF timestamps differ. Version identity remains unresolved; one canonical text copy is indexed, and all source files remain preserved.
- Added `data/evaluation/paracetamol_agent1_benchmark.json`, an evaluator, and standard-library unit tests. Final suite: six tests passed. The benchmark ran offline with the cached embedding model after the environment refused Hugging Face network requests.
- Final benchmark: expected-term relevance@5 1.00, expected-source recall@5 1.00, gold source-page recall@5 1.00, provenance traceability 1.00, insufficient-evidence status for both absent questions 1.00, and zero direct candidates for absent questions. These are retrieval measures, not scientific accuracy.
- Final `main.py` smoke test loaded and indexed 589 chunks, printed the ready prompt, and exited normally on `exit`. Agent 1's defined acceptance criteria pass; implementation is ready for owner review. Agent 2 has not started.

## 2026-11-01 — Full-system directive and Milestone B

- User authorized continuing from Agent 1 through the complete four-agent paracetamol system, superseding the previous pause before Agent 2.
- Audited installed environment and exact Ollama model registrations; retained model weights. Added .gitignore, .env.example, pinned 
equirements.txt, and shared bounded agents/ollama_client.py. No packages were installed because the audited packages were already available.
- Full test suite: 11 tests passed; Python compilation passed; pip check reported no broken requirements. Live Ollama chat smoke passed for ChemLLM (OK. at 32 tokens) and Llama 3.2 (OK at 8 tokens); an earlier truncated ChemLLM attempt was not counted.
- Began Milestone C: added evidence-bound Agent 2 module and six mocked tests. Live evidence-grounded Agent 2 check and test results will be recorded after execution.


## 2026-11-01 — Milestone C Agent 2 implementation

- Added agents/chemistry_pharmacology_agent.py: exact ChemLLM model, bounded supplied evidence, evidence-only prompt, JSON schema, evidence-ID allowlist validation, typed claims and uncertainty fields, no model call on empty evidence, and raw response preservation. Only claim texts that pass validation form the returned answer; free-form summary text is not surfaced.
- Added focused mocked tests for valid claim schema, empty corpus evidence, malformed/truncated output, unknown or missing evidence IDs, upstream error, and explicit unknown response.
- Real integration retrieved two Agent 1 passages and received two structured, evidence-ID-linked claims from local ChemLLM. One earlier long response truncated; a second bounded request completed. This validates plumbing only, not scientific correctness.
- Full suite before adding the truncation-specific regression: 17 tests passed. Final rerun follows.


- Final Milestone C verification: full suite 19 passed in 31.038 seconds; compileall passed; pip check reported no broken requirements. Milestone C is complete as an initial Agent 2 implementation, not a scientific-validation claim. Milestone D is next.


## 2026-11-01 — Milestone D Agent 3 initial implementation

- Read current official NCBI E-utilities usage guidance: no-key usage should stay at or below three requests/second; API key allows a higher default of 10/second. PMC documents automated retrieval channels and says per-article license terms vary. Implemented a lower bounded request pace, optional key/email/tool fields, and no full-text downloads.
- Added agents/literature_verification_agent.py: claim-oriented PubMed ESearch/ESummary and Europe PMC core search; metadata, abstracts (where supplied), provenance URLs, OA/license indicators, cross-provider PMID deduplication, and explicit per-provider partial/unavailable statuses.
- Added four mocked tests. Live Python API test was attempted and both providers returned ProxyError from the configured network proxy. No records were downloaded. Alternative: mocked response validation is passing; real service reachability remains pending a network path that permits outbound HTTPS.



## Milestones E?G ? Judge, orchestration and console (implementation in progress)

- Added `agents/judge_agent.py`: exact Llama Judge model, claim-by-claim structured decisions, local evidence ID validation, deterministic AMPA/APABA plus NAPQI safeguard, and no approval when verification is incomplete. Final answer text is built only from reviewed Agent 2 claims.
- Added `agents/orchestrator.py`: ordered Agent 1 ? Agent 2 ? Agent 3 ? Agent 4 flow, insufficient-evidence stop, fail-closed stage errors, and per-run local JSON audit with raw model responses and source provenance.
- Added `app.py`; preserved the retrieval-only `main.py` console.
- Added seven Judge tests and five orchestrator tests. Focused results: 12 tests passed after fixing an audit serializer bug and a Windows temp-directory permission issue in the test harness.
- Live Judge check used one corpus-derived mechanism claim and marked Agent 3 unavailable; installed Llama returned a completed decision and the deterministic gate correctly set `NEEDS_MORE_EVIDENCE`. This checks model plumbing and fail-closed behavior only.
- Remaining: full 4-agent regression, comprehensive scenario dataset/evaluation, console smoke, final documentation and acceptance.


## Agent 2 output-boundary correction and live integrated console

- A first end-to-end attempt caught ChemLLM returning a long generic safety discussion to a molecular-formula question. It failed closed; the raw response is preserved in that run record.
- A second attempt exposed a model-mistyped SHA-256 evidence ID. Agent 2 was changed to cite short enumerated passage labels which code maps to the exact evidence IDs; the Judge may cite other real records from the same retrieval result but cannot invent IDs.
- Final live console run completed the full four-stage path for the molecular formula question. Agent 2 returned a validated formula claim, Agent 3 returned five candidate metadata records, and Agent 4 approved the pipeline claim. Audit record contains both raw model outputs, the question, evidence and external records.
- Final full suite at this checkpoint: 37 tests passed in 33.637 seconds; retrieval evaluation 17 cases with reported metrics in `data/processed/system_retrieval_evaluation.json`. Scientific accuracy remains unassessed.


## Final test/documentation checkpoint ? 2026-11-01

- Expanded the scenario dataset to 18 cases, including both AMPA and APABA false toxic-metabolite pathways. The deterministic Judge test rejects both.
- Final retrieval report metrics: answerable-term coverage 1.00; expected-source recall@5 1.00; exact source-page recall@5 1.00 (one gold page case); traceability 1.00; insufficient-evidence behavior 3/3 absent-answer cases.
- Full suite passed: 38 tests in 32.898 seconds. Explicit compile passed for 21 files. `pip check` found no broken requirements.
- One real end-to-end console run passed. Broader claim correctness remains unassessed; the application reports review workflow decisions rather than calibrated scientific accuracy.

- Added per-stage millisecond timings to run results and JSON audit records; console displays them. Mock audit and display tests passed. Latest full suite: 38 passed in 32.898 seconds; explicit compile 21 files passed; `pip check` clean.

## Master-build verification update — 2026-11-01

- Full suite: 40 tests passed in 33.347 seconds; focused Agent 3 and Judge suite: 13 passed.
- Re-ran the 18-case retrieval benchmark with Hugging Face offline mode using cached weights. Metrics: answerable-term coverage 1.00; expected-source recall@5 1.00; source-page recall@5 1.00 for one labeled page case; traceability 1.00; absent-answer insufficient rate 1.00 (3 cases). Scientific accuracy is not evaluated.
- Python compilation and `pip check` passed. The latest Europe PMC API request returned temporary HTTP 503; Agent 3 represented it as partial verification. No files or model weights were downloaded.

## Runtime resilience and live retest — 2026-11-01

- Agent 2 now removes exact duplicate claim text with identical evidence IDs and records a warning.
- Agent 4 now receives explicit allowed claim/evidence IDs in its prompt and constrained JSON schema; invalid output gets one corrective retry. If the model is unavailable or still returns invalid output, the Judge returns a safe `NEEDS_MORE_EVIDENCE` result without approving the draft.
- Console stage labels now distinguish failed stages from stages that did not run. Retrieval intent detection now recognizes plain structure questions and long-term harm/safety wording.
- Validation: full suite 46 passed in 56.681 seconds; compilation of 22 Python files passed; `pip check` passed.
- Live local run: all four stages executed for a paracetamol molecular-formula/structure question. Agent 1 found chemical records, Agent 2 produced one deduplicated claim, Agent 3 was partial/unavailable, and Agent 4 ran. Overall result was `NEEDS_MORE_EVIDENCE`, correctly avoiding full approval because external verification was partial. Audit: `data/processed/runs/12ff4517407d483cb0f6600fde62a089.json`.
- Repeated the original mechanism question live after the change. The Judge returned a valid needs-more-evidence review instead of invalid IDs; duplicate Agent 2 draft was removed. Both literature providers hit `ProxyError`, so global status remained `NEEDS_MORE_EVIDENCE` with no stage exception.
