# Best Life AI Roadmap

**Objective:** complete the existing Best Life AI application as an evidence-grounded four-agent scientific research system, initially and exclusively for paracetamol (acetaminophen). Preserve Agent 1 and all source research files. The system must abstain or report partial failure when evidence or an agent is unavailable.

**Current status:** Milestones A?F completed, G completed for the console baseline, H and I in progress for expanded evaluation and final acceptance. Updated 2026-11-01.

## Target architecture

```text
Question / console UI
  -> Orchestrator
      -> Agent 1: local PDF/TXT/XML/chemical corpus; hybrid retrieval + evidence provenance
      -> Agent 2: ChemLLM through Ollama; evidence-bound structured interpretation
      -> Agent 3: independent PubMed E-utilities + Europe PMC REST verification
      -> Agent 4: Llama 3.2 Judge through Ollama + deterministic safety rules
  -> final answer or explicit partial result / abstention
```

All agents exchange typed records with stable evidence/claim identifiers. Original research files remain immutable; derived artifacts stay under `data/processed/`. Agent 1 is an existing preserved component, not a rewrite target. No additional drug, model download, paid service, or source redistribution is in scope.

## Milestones

### A. Existing project audit and persistent roadmap â€” COMPLETED

- Inspect source, corpus, interfaces, dependencies, tests, documentation, and console entry point.
- Confirm Agent 1 state and preserve its evaluation artifacts.
- Query local Ollama tags and show metadata for both exact requested models.
- Record audit, current state, decisions, and next action in `ROADMAP.md`, `PROJECT_STATE.md`, and `SESSION_LOG.md`.
- Evidence: six Agent 1 tests and compilation passed on 2026-11-01; both models are present and `/api/show` succeeds.

### B. Environment, configuration, and Ollama model integration ? COMPLETED

- Added `.gitignore` protection
- Added `.env.example`
- Added a pinned runtime dependency file
- Implemented one Ollama HTTP client
- Validated exact model identifiers
- Tested mocked error/success cases and performed real `/api/chat` calls against both installed models. ChemLLM returned `OK.` with a 32-token allowance; Llama returned `OK` with 8 tokens.
- Updated roadmap, checkpoint, session log, tracker, and test report at stage completion.

### C. Agent 2 ChemLLM integration ? COMPLETED

- Accept the user question plus only Agent 1 evidence records; send an evidence-grounded prompt to the exact configured ChemLLM model.
- Return schema-validated claims with explanation, evidence IDs, evidence status, uncertainty, and independent-verification requirements.
- Preserve raw response and structured result for run auditing; do not invent citations or promote model knowledge to verified evidence.
- Eight mocked checks pass: valid structured claims/raw preservation, empty evidence, malformed JSON, unknown/uncited IDs, service error, and explicit unknown answer.
- Live evidence-grounded mechanism check completed against two Agent 1 results with the exact installed ChemLLM; returned two claims citing only supplied IDs. This demonstrates interface operation, not scientific accuracy.
- Eight Agent 2 mocked checks pass, including truncated output, absent evidence and conflicting-source citations.
- An initial live call with a longer context and 700-token limit returned truncated JSON; the agent now detects incomplete responses and preserves raw failure output. A shorter two-passage call with a 1200-token allowance completed successfully.

### D. Agent 3 PubMed and Europe PMC verification ? COMPLETED

- Implement independent claim-oriented searches using NCBI E-utilities and Europe PMC REST.
- Use optional `.env` credentials, descriptive User-Agent/tool/email, public/API-key rate limits, bounded timeouts, and safe logging.
- Retrieve metadata and abstracts; retrieve full text only when openly available and license/access terms permit. Never bypass restrictions or treat an abstract as full text.
- Return supporting, contradicting, mixed, insufficient, or unverified status with query and publication provenance.
- Test against mocked services and run read-only real API checks; record any network restriction accurately.
- Four mocked Agent 3 tests pass. A read-only live query succeeded against PubMed and Europe PMC and returned four metadata records; no full text was downloaded. This checks connectivity/mapping only, not claim support.

### E. Agent 4 Judge and deterministic safeguards ? COMPLETED

- Send question, Agent 1 evidence, Agent 2 claims, and Agent 3 report to the exact Llama model.
- Combine Judge output with deterministic source/claim/evidence checks; fail closed if a required stage failed.
- Detect unsupported AMPA/APABA toxic-metabolite pathway claims and require direct reliable evidence rather than relying on model judgment alone.
- Emit `APPROVED`, `APPROVED_WITH_LIMITATIONS`, `NEEDS_REVISION`, `NEEDS_MORE_EVIDENCE`, or `ABSTAIN`, with reasons and no uncalibrated numeric confidence.
- Test fabricated pathway, citation mismatch, contradictions, unsupported claims, uncertainty, and Judge outage.

### F. Central orchestrator and typed inter-agent contracts ? COMPLETED

- Implement the ordered Agent 1 -> Agent 2 -> Agent 3 -> Agent 4 pipeline and stable request, evidence, claim, and stage-result schemas.
- Preserve evidence IDs/provenance across stages; record each stage's status/timing, model IDs, API identifiers, and safe errors without credentials.
- Do not silently skip a failed stage or present a full approval when any required agent failed.
- Test success, partial failure, insufficient evidence, timeout, and schema-invalid responses.
- Five orchestrator failure-path tests pass. Raw Agent 2 and Agent 4 responses are retained in the per-run JSON audit record.

### G. Application interface and usability ? COMPLETED (initial console acceptance)

- Retain the current console interaction where practical and connect it to the orchestrator.
- Show stage states/timings, retrieved evidence/source/page, interpretation, verification identifiers, Judge decision, limitations, and final answer.
- Show a clear partial/abstain response and useful loading/error messages. Do not expose credentials.

### H. Testing, debugging, and scientific evaluation ? IN PROGRESS

- Preserve and rerun all six Agent 1 regression tests and its existing benchmark.
- Add paracetamol cases for mechanisms/prostaglandins, ADME/CYP, NAPQI/glutathione, toxicity, chemical properties/structure, formulations/interactions, conflicting evidence, absent answers, and intentionally incorrect AMPA/APABA claims.
- Measure retrieval, provenance, verification/citation correctness, contradiction handling, hallucination flags, abstention, stage communications, and end-to-end success. Report only executed results; do not claim scientific accuracy from code execution.
- Use mocks for repeatable unit tests plus real model/API checks where available.
- The 18-case retrieval evaluation has executed; metrics are recorded in `data/processed/system_retrieval_evaluation.json`. It checks retrieval/provenance, not claim correctness. Mocks cover missing evidence, citations, partial APIs, judge safeguards and orchestration failures.

### I. Documentation and final acceptance ? IN PROGRESS

- Update setup/startup, environment, model/API configuration, architecture, interfaces, tests, troubleshooting, recovery, and known limitations.
- Create a Windows `README.md` with exact startup commands.
- Run compilation, dependency, unit, integration, and end-to-end checks; update all project state files.
- Declare completion only when every Part 15 criterion is met; otherwise list remaining work honestly.

## Shared task status

- **COMPLETED:** Agent 1 local ingestion/retrieval/chemical processing/provenance; six Agent 1 tests and initial 10-case retrieval benchmark; source hash validation; four-agent design; Milestone A audit; Milestone B configuration/shared Ollama client and real low-token checks for both installed models.
- **COMPLETED:** Milestone C, Agent 2 evidence-bound ChemLLM module, mocked tests, and one actual corpus integration.
- **COMPLETED:** Agent 1, Agent 2, and Agent 3 initial implementation.
- **COMPLETED:** Agent 4 Judge, orchestrator, and integrated console baseline; full regression and one live four-stage question passed.
- **IN PROGRESS:** Milestones H?I: final regression/docs reconciliation and expert-reviewed evaluation planning.
- **BLOCKED:** none currently. The NCBI key is optional; public limits are sufficient. Direct Python calls initially encountered the environment proxy; a later read-only request approved for API validation succeeded against both providers.
- **NEEDS REVIEW:** no approval gate is currently required for the authorized ordinary implementation milestones. Report any genuinely destructive, paid, new-model, or major architecture decision before taking that action.

## Dependencies and verified environment

- Windows 11; Python 3.12.10; project virtual environment `.venv312`.
- Already installed: requests 2.34.2, python-dotenv 1.2.4, RDKit 2026.09.1, pypdfium2 5.14.0, Sentence Transformers 6.2.0, rank-bm25 0.2.2, LangChain Community 0.4.2, pypdf 6.21.2, NetworkX 3.7.
- Local Ollama `http://localhost:11434` responds; exact requested model names and metadata verified. No weights were downloaded or copied by this audit.
- No `.env`, `.env.example`, `.gitignore`, README, dependency manifest, ROADMAP, PROJECT_STATE, or SESSION_LOG existed at audit start.
- No NCBI key/email is present in environment; NCBI public access remains a supported path.

## Known issues and constraints

- `app.py` is the integrated four-stage console; `main.py` remains the preserved retrieval-only console.
- Agent 1 has 589 indexed chunks; the expanded retrieval metrics pass on 18 cases but do not establish scientific correctness.
- Ten label scan pages have imperfect diagnostic OCR and remain excluded from retrieval pending proofreading.
- Four MedlinePlus PDFs share extracted text but publication-version identity is unproven.
- Some source licenses are unknown or restricted; preserve attribution and do not redistribute those files or long excerpts.
- No local `.env` or NCBI key/email is present. Public API query was live-tested; key-specific behavior is untested and optional.

## Recovery and next exact action

Before each milestone, read `ROADMAP.md`, `PROJECT_STATE.md`, and `SESSION_LOG.md`, inspect actual files/artifacts, and verify the recorded status. After each implementation stage, update all three.

**Next exact action:** review final 38-test run and 18-case report, reconcile all project-state documents with actual results, and report limits without claiming scientific accuracy.


## Current stage evidence (2026-11-01)

- Judge safeguard tests: 7 pass; orchestrator tests: 5 pass. A live Judge run returned `NEEDS_MORE_EVIDENCE` with external verification deliberately marked unavailable.
- Agent 3 API live query succeeded after read-only outbound network access was allowed. Four unique candidate metadata records returned; no full text was acquired.
- `app.py` passed one live end-to-end question; the broad scenario evaluation and expert-reviewed claim correctness remain pending.
