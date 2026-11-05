# Evaluation Methodology

Agent 1 has an initial paracetamol-only benchmark in `data/evaluation/paracetamol_agent1_benchmark.json`, an evaluator in `agents/evaluate_agent1.py`, and standard-library test coverage in `tests/test_agent1_data.py`. Results are recorded in `data/processed/agent1_evaluation.json`. This measures retrieval and traceability only, not scientific accuracy.

## Agent 1 retrieval (initial evaluation complete; broader scientific validation remains future work)

- Current questions cover mechanism, pharmacology, pharmacokinetics, NAPQI/metabolism, toxicity/safety, chemical properties, molecular structure, source/page retrieval, and two intentionally absent answers.
- Current measures: expected-term relevance@5, expected-source recall@5, gold source/page retrieval@5 where the benchmark specifies a gold page, evidence provenance completeness, duplicate-source handling, and insufficient-evidence behavior.
- Current initial results: 1.00 expected-term relevance@5, 1.00 expected-source recall@5, 1.00 provenance traceability, and 2/2 absent cases marked insufficient with no direct candidates. Gold source/page recall@5 is 1.00 (one exact source/page case).
- Gold labels and query phrasing need independent domain review and broader coverage. Do not treat these retrieval metrics as scientific correctness.
- The scan-only FDA label pages 2–11 have identical rendered-image hashes. OCR text is unverified and excluded from retrieval.

## Agent 2 interpretation

- Score claim-level support, evidence citation correctness, unsupported-claim rate, uncertainty handling, and distinction between hypothesis and established evidence.
- Include contradictory and insufficient-evidence prompts; verify that no patient-specific prescribing/dosing output is produced.
- Compare model configurations on the same fixed evidence set; do not treat model confidence as calibrated.

## Agent 3 verification

- Validate identifier correctness (PMID/PMCID/DOI), publication date/type, open full-text status, and support/contradiction classification against manually reviewed records.
- Test rate-limit handling, duplicate suppression, inaccessible full-text behavior, and metadata-only results.

## Agent 4 and end-to-end

- Use seeded unsupported, partially supported, contradictory, outdated-label, and no-evidence claims.
- Measure unsupported claim rejection, appropriate abstention, citation/source traceability, conflict preservation, and false acceptance rate.
- Require human review of a sample before any scientific-quality claim.

## Completion rule

Each component needs a versioned dataset, clear acceptance thresholds chosen before evaluation, recorded failures, and passing relevant tests. If evaluation data or dependencies are missing, status stays blocked/incomplete rather than completed.
