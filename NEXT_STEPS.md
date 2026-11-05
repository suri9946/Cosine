# Next Steps

## Current milestone ? Expanded evaluation and final acceptance

All four agents and the integrated console baseline are implemented. One live end-to-end chemical-property question passed; the 18-case retrieval/provenance evaluation and 38-test regression passed in 32.898 seconds. Scientific accuracy remains unassessed.

Completed in the current implementation stage:

- Recursive PDF, TXT, and JATS XML ingestion with manifest metadata, source identifiers, hashes, page/section, and extraction status.
- Image-page rendering and OCR diagnostics. FDA label pages 2â€“11 are pixel-identical; OCR is not trusted or indexed.
- PubChem JSON extraction and RDKit parsing/sanitization of all four SDF files.
- Retrieval metadata in results, a paracetamol evidence graph with lexical-only concept links, and a 10-case benchmark.
- Initial benchmark and unit-test run; details and actual scores are in `TEST_RESULTS.md` and `data/processed/agent1_evaluation.json`.

Current stage:

1. Record final regression, explicit compile and dependency-check results after the latest console output test.
2. Review `data/evaluation/paracetamol_system_cases.json` and its retrieval report; obtain expert-annotated claim judgments before making scientific accuracy claims.
3. Review current test/evaluation artifacts and known issues. The one live end-to-end console check passed; expand expert-reviewed scientific evaluation before using the system for research conclusions.

## Recommendations needing owner approval

- Existing source coverage is partial. Consider a focused, licensed source set for foundational mechanism studies, interactions, non-tablet formulations, and updated pharmacokinetics. No files will be downloaded until the owner approves specific candidates.
- Tesseract text for the repeated FDA label image is error-prone. A human-corrected transcription could be approved for indexing later; the original PDF and current OCR audit output are preserved.

## Owner tasks

- No user action currently blocks implementation. NCBI credentials remain optional; public API access was validated.
- Decide whether to approve the source-coverage recommendations and whether to provide a manually reviewed label transcription.
- Review the integrated application results after all acceptance checks; stop before any scope expansion.

## Latest verification and next work (2026-11-01)

The latest full regression passed 40 tests in 33.347 seconds. The 18-case retrieval/provenance evaluation passed offline using the cached embedding model. These results do not assess scientific accuracy. A current Europe PMC request returned temporary HTTP 503 and was marked as partial verification; repeat the live check when the service is available.

Next: review the test and evaluation artifacts, obtain expert-annotated claim judgments, and expand the scientific evaluation before relying on the system for research conclusions. Review the source coverage recommendations and OCR transcription limitation before any additional research acquisition.

## Latest runtime validation and remaining work (2026-11-01)

- Runtime hardening is in place for duplicate Agent 2 claims, invalid Agent 4 IDs/JSON, unavailable Judge service, and misleading failed-stage labels.
- A live four-stage formula/structure run completed. Agent 3 returned partial status due to external API connectivity; the workflow ended `NEEDS_MORE_EVIDENCE` safely. Review its audit JSON before treating the displayed claim as research output.
- 46 tests pass, 22 project Python files compile, and `pip check` is clean.
- Next: restore/confirm outbound HTTPS connectivity to PubMed and Europe PMC, then repeat a live run. Continue expert-reviewed claim validation; no software change can guarantee that remote services or generative models never fail.
