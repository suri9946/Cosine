# Project Tracker

Initial scope: **paracetamol (acetaminophen) only**. Keep future drug extension modular; do not implement multi-drug functionality now.

| Milestone | Status | Acceptance evidence | Notes |
|---|---|---|---|
| 1. Project audit and prerequisite identification | COMPLETED | Initial code/data/environment audit recorded | No application implementation changes |
| 2. Paracetamol research acquisition, corpus validation and architecture documentation | COMPLETED | Owner approved acquisition and documented four-agent architecture | Research coverage remains incomplete; no further sources acquired in this Agent 1 milestone |
| 3. Agent 1 implementation | COMPLETED | Approved Agent 1 pipeline implemented; original retrieval retained; corpus provenance, chemistry, OCR review and evidence graph integrated | Initial paracetamol-only acceptance passed; ready for owner review |
| 4. Agent 1 testing and evaluation | COMPLETED | Six regression checks and 10-case benchmark passed | Retrieval quality only; scientific accuracy not assessed |
| 5. Agent 2 implementation and evaluation | COMPLETED | Evidence-first ChemLLM contract and evaluation pass | Shared client and Agent 2 module implemented; 8 focused tests and real evidence-grounded smoke check passed |
| 6. Agent 3 implementation and evaluation | COMPLETED | Four mocked tests and read-only live query against both APIs pass | Four candidate metadata records returned; full text not downloaded |
| 7. Agent 4 Judge implementation | COMPLETED | Deterministic safeguards, seven mocked tests and live Judge call pass | Pipeline status is not a scientific accuracy finding |
| 8. System integration and evaluation | IN PROGRESS | Five orchestration tests and one live end-to-end question pass | Broader scenario and expert-reviewed evaluation remain in Milestone 8 |
| 9. User interface and additional features | COMPLETED (initial console) | Live four-stage question plus console output test pass | `app.py`; legacy console preserved in `main.py` |

## Milestone 2 completed work (owner approved)

- Acquired one CC BY Europe PMC full-text XML review plus a credited local text derivative, two DailyMed label versions (2020 historical candidate and 2026 product label), and refreshed PubChem 2D/3D SDF snapshots.
- Retained the existing PubChem JSON after its current endpoint produced an exact byte match; no redundant JSON file retained.
- Recorded source metadata/licenses/status/hashes in `SOURCE_MANIFEST.csv`; acquisition outcomes in `data/research/paracetamol/metadata/acquisition_log.csv`; category coverage in `data/research/paracetamol/metadata/source_coverage.csv`.
- Validated 12 PDFs (144 pages), 20 corpus files, text presence, XML/JSON parsing, SDF record headers, and source hashes. Ten FDA-label pages lack native text; four MedlinePlus PDFs have identical extracted text despite different file hashes.
- Documented four-agent architecture and interfaces in `ARCHITECTURE.md`, `AGENT_INTERFACES.md`, `DATA_SCHEMA.md`, `SYSTEM_WORKFLOW.md`, and `EVALUATION_METHODOLOGY.md`.
- Preserved original research files and `main.py`/`agents/knowledge_agent.py`. No application code was changed and no tests were added.

## Agent 1 implementation progress

- Four MedlinePlus captures are confirmed identical by extracted text; PDF bytes and creation dates differ, so version identity remains unproven. One canonical copy is indexed, and all originals remain intact.
- Ten FDA-label pages (2â€“11) were rendered and OCR checked. Their rendered PNG hashes match exactly; sampled pages 2, 3, and 11 were visually reviewed. Tesseract output is unverified and not indexed.
- RDKit 2026.09.1 validates all four SDF records as sanitized, equivalent paracetamol structures (C8H9NO2; same canonical SMILES). PubChem JSON parsed and is searchable.
- Six Agent 1 unit tests pass. Benchmark: answerable relevance@5 1.00, expected-source recall@5 1.00, gold source-page recall@5 1.00, provenance traceability 1.00, absent-case insufficient-evidence 1.00, and zero direct candidates for absent questions. These are retrieval measures only.
- Main console smoke test passes; it indexed 589 chunks and exited normally on `exit`.
- Agent 1 implementation and its defined initial evaluation acceptance criteria are complete for owner review. Wider expert-reviewed evidence evaluation remains a limitation; Agents 2, 3 and 4 remain unimplemented.

### Latest integrated verification update (2026-11-01)

- Regression: 40 tests passed; focused Agent 3/Judge tests: 13 passed.
- Offline retrieval evaluation: 18 cases passed with documented retrieval/provenance metrics; no scientific accuracy assessment.
- Current Europe PMC request returned HTTP 503 and was handled as partial verification. No source acquisition or model download occurred in this checkpoint.
- Stage timing data is recorded in each run audit and displayed by the integrated console. Expert-reviewed scientific evaluation and final owner review remain open.

### Runtime hardening checkpoint (2026-11-01)

- Agent 2 duplicate-claim filtering, Agent 4 constrained IDs plus one retry and safe abstention, console failure-state labels, and common structure/safety question routing are implemented.
- Regression: 46 tests passed; compilation: 22 Python files passed; `pip check` clean.
- Live local four-agent run executed all stages; Agent 3 was partial from external connectivity and the final run correctly required more evidence. Expert-reviewed scientific evaluation remains open.
