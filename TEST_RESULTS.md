# Test and Validation Results

Date: 2026-11-01. This report covers the approved Agent 1 implementation stage. Retrieval results do not establish scientific accuracy or clinical safety.

## Corpus and chemistry validation

| Check | Result | Evidence |
|---|---|---|
| PDF open/page count | PASS | 12 PDFs; 144 pages total |
| Native text presence | PARTIAL | 134/144 pages have native text; FDA label pages 2–11 require scan handling |
| Scan rendering | PASS | pypdfium2 5.14.0 rendered pages 2–11; all rendered pages have the same SHA-256; representative pages 2, 3 and 11 visually inspected |
| Scan OCR | REVIEW REQUIRED / EXCLUDED | Tesseract generated text for page 2 only after detecting identical render pages; OCR contains recognition errors and was not indexed |
| MedlinePlus duplicate handling | PASS WITH VERSION LIMITATION | Four PDFs have identical full extracted text and distinct PDF hashes/creation dates; identity as different publication versions is unproven; one copy indexed, originals preserved |
| XML/TXT extraction | PASS | Existing CC BY JATS XML parsed into sections; plain text ingested with source metadata; no source file edits |
| PubChem JSON | PASS | One compound record parsed; formula, weight, and identifiers are exposed as a provenance-bearing retrieval record |
| Four SDF structures | PASS | Four one-record SDF files parsed/sanitized using RDKit 2026.09.1; each formula C8H9NO2 and each canonical SMILES `CC(=O)Nc1ccc(O)cc1`; 2D/3D conformer flags distinguish the coordinate records |
| Source-file integrity | PASS | All 20 local files with hashes in `SOURCE_MANIFEST.csv` still match their recorded SHA-256 |

## Agent 1 tests and retrieval benchmark

Command: `.venv312\Scripts\python.exe -m unittest discover -s tests -v`

| Test | Result |
|---|---|
| Recursive nested PDF/TXT/XML ingestion and source metadata | PASS |
| Scan-only page reporting, render-duplicate handling, OCR exclusion | PASS |
| Four MedlinePlus PDFs deduplicated for indexing without deleting originals | PASS |
| Four SDFs and PubChem JSON chemical parsing | PASS |
| Provenance graph edges marked lexical/non-assertive | PASS |
| Manifest hash integrity | PASS |
| Agent 1 regression suite | PASS - six standard-library unittest checks; source hash integrity included |

The benchmark contains eight answerable cases and two intentionally absent questions. The cached `sentence-transformers/all-MiniLM-L6-v2` model was evaluated in offline mode after network access to Hugging Face was refused.

| Measure | Result |
|---|---:|
| Answerable-case relevance@5 (expected-term check) | 1.00 |
| Expected-source recall@5 | 1.00 |
| Source/page traceability across all cases | 1.00 |
| Absent cases marked `INSUFFICIENT_EVIDENCE` | 1.00 (2/2) |
| Direct candidates returned for absent cases | 0 (2 cases) |
| Gold source-page retrieval@5 | PASS - 1.00 (one exact gold source/page case) |
| Scientific accuracy / claim correctness | NOT ASSESSED |

Full per-case retrieval evidence is in `data/processed/agent1_evaluation.json`; the benchmark and test definitions are versioned in `data/evaluation/` and `tests/`.

## Earlier acquisition checks

- Europe PMC XML: parses; CC BY statement present; derived text attribution recorded.
- DailyMed candidate PDFs: returned valid PDFs and opened locally; reuse conditions are preserved in `SOURCE_MANIFEST.csv`; files are not redistributed.
- PubChem source records: retained URLs and source metadata in the manifest. No new research sources were acquired during Agent 1 implementation.

## Limitations

- Final regression suite and benchmark rerun passed after the last metadata/evaluator edits.
- The main console smoke test passed: it loaded the corpus, indexed 589 chunks, displayed the ready prompt, and exited normally on `exit`.
- Retrieval relevance is judged by query-term overlap and expected source/page, not by expert review of scientific claims.
- PDF OCR output remains excluded until human proofreading. No OCR text is presented as verified label content.

## Full-system directive — Milestone B and Agent 2 stage

- Full suite after shared client: 11 tests passed in 33.799 seconds. Python compilation passed; pip check: no broken requirements.
- Live /api/chat: configured ChemLLM produced OK. with 32 output tokens; configured Llama 3.2 produced OK with 8 tokens. These are connectivity/smoke checks only.
- Agent 2 tests are being added; final executed results will be appended after test and live evidence-grounded run.


## Milestone C — Agent 2 evidence-bound interpretation

- Focused Agent 2/shared-client tests: 11 passed before final regression; Agent 2 covers empty evidence, valid structured claims, preserved raw response, malformed JSON, unknown and absent citations, upstream errors, and unknown/insufficient content.
- Full regression suite: 17 tests passed in 30.892 seconds. This run preceded the added truncated-output test; rerun after that test before reporting final count.
- Live integration: Agent 1 loaded 589 chunks and retrieved two evidence passages for a mechanism question. Installed ChemLLM returned a completed structured response with two claims, each citing one of the supplied evidence IDs. No independent scientific accuracy review was done.
- First live attempt with three passages and a 700-token output limit returned malformed/truncated JSON. The agent now checks Ollama's completion flag, fails closed on truncation, and retains raw content/response on invalid output.


- Final Milestone C regression: .venv312\Scripts\python.exe -m unittest discover -s tests -v — 19 passed in 31.038 seconds.
- compileall passed for main.py, agents/, and 	ests/; pip check reported no broken requirements.


## Milestone D Agent 3 checks

- Focused mocked suite: 4 tests passed (provider queries and metadata, duplicate handling, no-result vs partial errors, safe error detail and invalid input).
- Read-only live service probe: blocked. Python requests to eutils.ncbi.nlm.nih.gov and www.ebi.ac.uk both failed with ProxyError; no source response was obtained. API policy reviewed from official NCBI and PMC documentation. Do not treat mock tests as live API validation.


- Live Agent 3 validation completed after a read-only API network check was allowed: query used paracetamol/acetaminophen plus metabolism, NAPQI and liver-toxicity terms. PubMed and Europe PMC both responded; four unique metadata records were returned (Europe PMC abstracts and OA/license metadata where provided). Full text was not downloaded. Search-result relevance/claim support was not established by this check.



## Milestones E?G focused validation (partial)

- Judge and orchestrator focused suite: 12 tests passed after corrections. Coverage includes approval from valid local evidence, unknown IDs, absent evidence, external API failure, invalid JSON, AMPA/NAPQI deterministic rejection, stage failures, partial verification, raw response audit, and Agent 1 insufficient-evidence stop.
- Live Llama Judge check: one corpus-derived prostaglandin claim and Agent 3 `PARTIAL` status produced decision `NEEDS_MORE_EVIDENCE`; model response completed. This is a plumbing/safeguard check, not a scientific accuracy result.
- Final end-to-end console check passed for a chemical-property question: Agent 1 retrieved five chemical structure/property records, Agent 2 returned a validated formula claim with a mapped evidence ID, Agent 3 returned five metadata records, and Agent 4 approved with source IDs retained. Run status `APPROVED` describes pipeline review only, not scientific accuracy.


## Final integrated verification (2026-11-01)

- Full regression suite at the previous checkpoint: 37 tests passed in 33.637 seconds at the prior checkpoint.
- Live `app.py` run using the installed ChemLLM and Llama models plus the read-only PubMed/Europe PMC APIs completed one question end to end. It returned `APPROVED` for the paracetamol molecular formula and displayed five traceable local chemical records. Its JSON audit contains the original question and both raw model responses. This is a single plumbing check, not scientific validation.
- The prior live attempt failed closed after ChemLLM emitted unsupported generic content and malformed/truncated output. Agent 2 was tightened to use short evidence aliases mapped to exact retrieved IDs, shorter claims, and bounded output. The final run passed; the initial failure remains in the local audit trail.
- Expanded 18-case Agent 1 retrieval evaluation: answerable term coverage 1.00; expected-source recall@5 1.00; expected source-page recall@5 1.00 (one labeled page case); traceability rate 1.00; insufficient-evidence rate 1.00 for 3 absent-answer cases. These are retrieval metrics and do not establish scientific claim correctness.
- Explicit Python compilation passed for all 21 files in `main.py`, `app.py`, `agents/` and `tests/`; `pip check` reported no broken requirements. A recursive scan also reported five inaccessible temporary directories left by a failed test cleanup, so compilation was repeated over the explicit source file list.


- The console display test verifies stage statuses, Agent 2 evidence IDs, Agent 3 PMID/PMCID/DOI links, Agent 4 decisions, and local source/page traceability.


## Final rerun after 18-case dataset and console output test

- Full regression: 38 tests passed in 32.898 seconds.
- Explicit Python compilation: 21 files passed; `pip check`: no broken requirements.
- Agent 1 retrieval evaluation rerun on 18 cases: answerable-term coverage 1.00; expected-source recall@5 1.00; source-page recall@5 1.00 for the single page-labeled case; provenance traceability 1.00; 3/3 explicitly absent answer cases marked insufficient. The two AMPA/APABA adversarial cases are separately checked by Judge tests, not counted as absent-answer retrieval cases.
- Scientific accuracy remains unassessed.

- Run audit tests verify per-stage timing keys and persistence; the integrated console displays stage timings.

- Final post-timing implementation regression: 38 tests passed in 32.898 seconds; explicit compilation passed for 21 files; `pip check` found no broken requirements.

## Final master-build verification (2026-11-01)

- Full regression rerun: 40 tests passed in 33.347 seconds. Targeted Agent 3 and Judge tests: 13 passed.
- System retrieval evaluation rerun in Hugging Face offline mode using the cached embedding model: 18 cases; answerable-term coverage 1.00; expected-source recall@5 1.00; source-page recall@5 1.00 (one page-labeled case); traceability 1.00; 3/3 absent-answer cases marked insufficient. `scientific_accuracy_assessed` is false.
- Python compilation of project Python modules and `pip check` passed. A broad compile scan encountered inaccessible temporary directories created by test cleanup; this did not affect the test suite or explicit source compilation.
- A current Europe PMC lookup returned HTTP 503 (temporary service error); Agent 3 reports partial verification instead of treating it as a no-results response. A previous live query against both providers succeeded. No full text or new research file was downloaded in this checkpoint.
- The successful live console run predates the latest stage-timing display change; stage timing and console output are covered by automated tests. No new model/API end-to-end run was performed in this checkpoint.

## Runtime resilience check — 2026-11-01

- Focused Agent 2, Judge, console, and question-routing tests: 23 passed. Full regression: 46 passed in 56.681 seconds.
- Explicit compilation: 22 Python files passed. `pip check`: no broken requirements.
- Live local four-stage test: Agent 1 `RETRIEVAL_RELEVANT_REVIEW_REQUIRED`; Agent 2 `COMPLETED`; Agent 3 `PARTIAL`; Agent 4 `NEEDS_MORE_EVIDENCE`; no stage errors. End-to-end status `NEEDS_MORE_EVIDENCE`. This exercised local models and safe handling of unavailable external verification; it is not scientific validation.
- Run audit: `data/processed/runs/12ff4517407d483cb0f6600fde62a089.json`.
- External APIs remain network-dependent. Zero failures cannot be guaranteed; the tested behavior is to retry invalid Judge formatting once, preserve audit evidence, and abstain safely if services/models are unavailable.

- Repeated the original mechanism question live after hardening: Agent 1 relevant, Agent 2 completed with one duplicate removed, Agent 3 partial (`ProxyError` from both providers), Agent 4 ran and returned `NEEDS_MORE_EVIDENCE`; no stage error. Final status was `NEEDS_MORE_EVIDENCE` (safe, expected because network verification was blocked and local mechanism evidence was judged insufficient). Audit: `data/processed/runs/19dc0f89ad9e4e7a920900fea2dbe048.json`.
- Repeated live molecular formula/structure question: all four stages ran; Agent 4 returned `NEEDS_MORE_EVIDENCE` due Agent 3 being unavailable. Audit: `data/processed/runs/12ff4517407d483cb0f6600fde62a089.json`.
