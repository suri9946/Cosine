# Paracetamol Research Data Inventory

Inventory/access date: 2026-11-01. Current subject scope is paracetamol (acetaminophen) only. Original local research files are preserved. No ibuprofen or other drug datasets were acquired.

## Corpus counts

| Format | Count | Details |
|---|---:|---|
| PDFs | 12 | 10 pre-existing, plus a DailyMed label from 2020 and a current product label updated 2026-07-20; total 144 pages |
| TXT | 2 | Existing `abstract_only.txt`; extracted-text derivative for CC BY PMC article |
| JATS XML | 1 | Full text from Europe PMC for PMC5744234, license checked in the XML |
| JSON | 1 | Existing PubChem CID 1983 record |
| SDF | 4 | Existing 2D/3D structures plus new separately named PubChem 2D/3D snapshots |
| **Source files total** | **20** | Excludes two metadata CSVs in `metadata/` |
| Metadata CSVs | 2 | `acquisition_log.csv` and `source_coverage.csv`; root `SOURCE_MANIFEST.csv` contains the file/source register |

`SOURCE_MANIFEST.csv` contains 22 rows: 20 retained source/derivative files plus metadata-only or deduplicated acquisition outcomes. Each retained file row includes SHA-256; acquisition result/status is explicit.

## Acquired during this milestone

1. `text/PMC5744234_Esh_2017.xml` — Europe PMC full-text XML for *Acetaminophen (Paracetamol): Use beyond Pain Management and Dose Variability* (Esh et al., 2017; DOI 10.3389/fphys.2017.01092; PMID 29312002; PMCID PMC5744234). Article XML states CC BY. The direct PMC PDF URL returned an anti-bot HTML page; that response was not saved. Europe PMC XML was used instead.
2. `text/PMC5744234_Esh_2017_extracted.txt` — locally derived text (abstract and body paragraphs/section headings) from the licensed XML, with attribution/source noted in its header. Figures are not separately extracted; the XML remains the source.
3. `pdf/labels/DailyMed_71bcfe9e_20200727.pdf` — the user-supplied candidate label; accessible PDF, historical 2020 version, 3 pages. Reuse terms were not explicit; retain as a local reference copy and do not redistribute absent permission.
4. `pdf/labels/DailyMed_Medline_500mg_20260720.pdf` — current DailyMed label for one Medline 500 mg tablet product, last updated 2026-07-20, 4 pages. It contains a ©2026 Medline notice; no separate reuse license was verified. This is product-specific labeling, not a universal label.
5. `chemical_data/PubChem_CID_1983_20261101_2D.sdf` and `..._3D.sdf` — PubChem PUG REST structures for CID 1983. Both downloaded with HTTP 200 and chemical/x-mdl-sdfile. RDKit validation now confirms each of the four existing SDF records parses and sanitizes successfully, has formula C8H9NO2, and canonicalizes to the same paracetamol SMILES. The 2D/3D coordinate flag is preserved in `data/processed/chemical_validation.json`.

The current PubChem JSON endpoint was checked and returned bytes identical to the existing JSON (same SHA-256); the extra copy was removed and the original retained. The PMC4498995 metabolism manuscript is relevant, but its license was not located; its full text was not copied. Its metadata and reason are recorded in the manifest/acquisition log.

## Corpus quality results

- All 12 PDFs opened with pypdf and yielded a page count. Total: 144 pages.
- Text extraction returned text on 134 pages; pages 2–11 in the existing 14-page FDA label PDF returned no native text. All ten were rendered with pypdfium2 and produce the same rendered-image SHA-256. Pages 2, 3, and 11 were visually inspected; Tesseract produced imperfect text from page 2, so OCR remains diagnostic and is excluded from retrieval until proofread. See `data/processed/extraction_report.json` and `data/processed/fda_scan_ocr_review.json`.
- The four existing MedlinePlus Drug Information PDFs have identical full extracted text, distinct file hashes, and different PDF creation timestamps. This supports identical captured content, but does not establish whether they are separate versions or repeated captures. Preserve all four originals; the lexically first capture (`doc10`) is indexed once with the duplicate family recorded in the extraction report.
- No byte-identical file groups were found among the 20 retained source files.
- PMC XML parses and carries CC BY license language. Derivative text contains author attribution and identifies the XML source.
- The existing PubChem JSON parses with one compound record and its molecular formula/weight and identifier properties are indexed with provenance. All four SDF files each contain one RDKit-sanitized paracetamol record; formula and canonical SMILES agree. Actual validation results and RDKit version are in `data/processed/chemical_validation.json`.
- The PubChem JSON was repeated exactly by the current endpoint; it was not retained twice.
- External PDFs and chemical files were checked for HTTP status/content type/format signature and locally reopened/inspected where applicable. Licensing restrictions are recorded per source.

## Coverage and outstanding gaps

See `data/research/paracetamol/metadata/source_coverage.csv`. Main gaps include primary/foundational mechanism studies, fully mapped ADME and interaction evidence, coverage of non-tablet formulations, currency of the older systematic review, independent source/version review, and chemical validation. The source coverage assessment is provisional and does not claim comprehensiveness.

Agent 1 now indexes 123 extracted PDF/TXT/XML documents plus five derived chemical records; text chunking produced 589 passages during the benchmark run. Original source files remain unchanged (all 20 manifest-listed source hashes matched). Extracted text and graph outputs are derived files under `data/processed/`.

Any further source acquisition should be targeted to the category gaps and follow recorded license/access checks. No additional research source was downloaded during Agent 1 implementation, and no bulk collection or unlicensed content was redistributed. Source coverage remains partial, not comprehensive.


## System evaluation artifacts (not research sources)

- `data/evaluation/paracetamol_system_cases.json` contains 18 paracetamol-only scenarios across mechanism, pharmacology, pharmacokinetics, NAPQI/metabolism, safety, chemical properties/structures, formulation, source/page traceability, absent evidence, and the intentionally incorrect AMPA/NAPQI pathway.
- `data/processed/system_retrieval_evaluation.json` records retrieval/provenance metrics only. It is not an expert-annotated scientific accuracy evaluation.
- `data/processed/runs/` contains local per-question application audit records with retrieved evidence, model outputs, external metadata results and stage decisions. These files are derived and may contain source passages; source reuse terms still apply.
- No original research PDF, TXT, XML, JSON or SDF file was modified or downloaded during the integrated Agent 2?4 work. The live literature test returned API metadata/abstracts in memory only; it did not save source documents.
