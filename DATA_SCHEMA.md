# Proposed Data Schema

The source manifest remains CSV for reviewability. Agent 1 currently uses in-memory document records with metadata dictionaries and writes reproducible extraction, chemistry, graph, and evaluation JSON under `data/processed/`. The schema below remains the cross-agent target; it is not yet a formal Pydantic model.

## Source/document record

Required: stable `source_id`, `drug_id`, local/original filename, source URL when known, document type, category, acquisition status, SHA-256 for local files, and extraction status. Optional: title, authors, publication year/date, journal/publisher, DOI, PMID, PMCID, license, version/update date, access date, and notes.

Rules:

- `source_id` is stable across filename changes and version relations.
- A new source version receives a new source ID and may link to `supersedes_source_id`; historical versions are retained.
- Use an empty/unknown field for unknown metadata; never fabricate it.
- Hash the exact acquired bytes before parsing.
- Distinguish `acquired`, `metadata_only`, `failed`, `duplicate_not_retained`, and `restricted` statuses.
- Derivative files identify their source ID and transformation/version.

## Evidence/chunk record

```json
{
  "evidence_id": "stable-or-content-derived-id",
  "source_id": "manifest-source-id",
  "text": "extracted passage",
  "page_start": 1,
  "page_end": 1,
  "section": null,
  "char_start": null,
  "char_end": null,
  "extractor": "tool and version",
  "source_type": "review|primary_research|label|reference|other",
  "quality_flags": [],
  "processed_at": "ISO-8601 timestamp"
}
```

## Chemical record

Keep original JSON/SDF paths and hashes. Parsed derived record may contain CID, canonical/isomeric SMILES, InChI/InChIKey, formula, charge, atom/bond counts, 2D/3D designation, conformer provenance, RDKit version, and sanitization/validation errors. All calculated properties identify toolkit and version; raw values remain distinguishable from computed values.

## Claim and graph records

Claims link one or more evidence IDs and identify claim class, source direction (supports/contradicts), date, and uncertainty. Graph nodes reference immutable source/evidence/chemical identifiers; graph edges carry provenance and extraction method. Model-extracted relationships are marked as extracted interpretation and require evidence review.
