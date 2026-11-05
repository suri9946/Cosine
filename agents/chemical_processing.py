"""Validated, provenance-aware parsing for the existing chemical dataset."""

from __future__ import annotations

import csv
import csv
import json
from pathlib import Path
from typing import Any

from agents.document_ingestion import SourceDocument


def validate_chemical_sources(project_root: Path | str) -> dict[str, Any]:
    root = Path(project_root).resolve()
    chemical_dir = root / "data" / "research" / "paracetamol" / "chemical_data"
    manifest_path = root / "SOURCE_MANIFEST.csv"
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        manifest = {r.get("local_filename", "").replace("\\", "/"): r
                    for r in csv.DictReader(stream) if r.get("local_filename")}
    try:
        from rdkit import Chem, rdBase
        from rdkit.Chem import rdMolDescriptors
    except ImportError as exc:
        return {"status": "blocked_rdkit_missing", "error": str(exc), "records": []}

    records: list[dict[str, Any]] = []
    for path in sorted(chemical_dir.glob("*.sdf")):
        relative = path.relative_to(root).as_posix()
        meta = manifest.get(relative, {})
        supplier = Chem.SDMolSupplier(str(path), removeHs=False)
        parsed = 0
        parse_errors = 0
        for index, mol in enumerate(supplier, start=1):
            if mol is None:
                parse_errors += 1
                continue
            parsed += 1
            formula = rdMolDescriptors.CalcMolFormula(mol)
            records.append({
                "local_path": relative,
                "source_id": meta.get("source_id", ""),
                "source_url": meta.get("source_url", ""),
                "license_reuse": meta.get("license_reuse", ""),
                "sha256": meta.get("sha256", ""),
                "record_index": index,
                "parse_status": "parsed",
                "sanitized": True,
                "atom_count": mol.GetNumAtoms(),
                "bond_count": mol.GetNumBonds(),
                "formula": formula,
                "canonical_smiles": Chem.MolToSmiles(Chem.RemoveHs(mol), canonical=True),
                "has_3d_conformer": any(c.Is3D() for c in mol.GetConformers()),
                "rdkit_version": rdBase.rdkitVersion,
            })
        if not parsed:
            records.append({"local_path": relative, "source_id": meta.get("source_id", ""),
                            "source_url": meta.get("source_url", ""), "license_reuse": meta.get("license_reuse", ""),
                            "parse_status": "no_valid_records", "parsed_records": 0,
                            "parse_errors": parse_errors, "rdkit_version": rdBase.rdkitVersion})

    json_file = next(iter(sorted(chemical_dir.glob("*.json"))), None)
    json_status = "not_found"
    json_record: dict[str, Any] = {}
    if json_file:
        try:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
            json_status = "valid_json"
            json_record = {"local_path": json_file.relative_to(root).as_posix(),
                           "source_id": manifest.get(json_file.relative_to(root).as_posix(), {}).get("source_id", ""),
                           "license_reuse": manifest.get(json_file.relative_to(root).as_posix(), {}).get("license_reuse", ""),
                           "top_level_type": type(payload).__name__}
        except (OSError, json.JSONDecodeError) as exc:
            json_status = f"invalid_json:{type(exc).__name__}"
    return {"status": "validated", "rdkit_version": rdBase.rdkitVersion,
            "python_version": __import__("sys").version.split()[0], "sdf_file_count": len(list(chemical_dir.glob("*.sdf"))),
            "sdf_records": records, "json_status": json_status, "json_record": json_record}


def chemical_evidence_documents(project_root: Path | str) -> list[SourceDocument]:
    """Expose only explicit chemical properties as traceable retrieval records."""
    root = Path(project_root).resolve()
    report = validate_chemical_sources(root)
    if report.get("status") != "validated":
        return []
    records: list[SourceDocument] = []
    for row in report["sdf_records"]:
        if row.get("parse_status") != "parsed":
            continue
        path = row["local_path"]
        shape = "3D conformer" if row["has_3d_conformer"] else "2D structure"
        content = (f"Paracetamol (acetaminophen) chemical structure record: {shape}; "
                   f"molecular formula {row['formula']}; {row['atom_count']} atoms; "
                   f"{row['bond_count']} bonds; canonical SMILES {row['canonical_smiles']}. "
                   f"Structure parsed and sanitized by RDKit {row['rdkit_version']}.")
        records.append(SourceDocument(content, {
            "source_id": row.get("source_id", ""), "source": Path(path).name, "local_path": path,
            "source_url": row.get("source_url", ""), "license_reuse": row.get("license_reuse", ""),
            "sha256": row.get("sha256", ""), "page": None, "section": "RDKit-derived molecular record",
            "extractor": f"RDKit {row['rdkit_version']}", "quality_status": "rdkit_sanitized",
            "version_date": "", "molecular_formula": row["formula"],
            "canonical_smiles": row["canonical_smiles"], "has_3d_conformer": row["has_3d_conformer"],
        }))
    chemical_dir = root / "data" / "research" / "paracetamol" / "chemical_data"
    json_path = next(iter(sorted(chemical_dir.glob("*.json"))), None)
    if json_path:
        relative = json_path.relative_to(root).as_posix()
        with (root / "SOURCE_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as stream:
            metadata = next((r for r in csv.DictReader(stream)
                             if r.get("local_filename", "").replace("\\", "/") == relative), {})
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        compound = payload.get("PC_Compounds", [{}])[0]
        values: dict[str, str] = {}
        for prop in compound.get("props", []):
            urn = prop.get("urn", {})
            label, name = urn.get("label", ""), urn.get("name", "")
            value = prop.get("value", {})
            text = value.get("sval") or value.get("fval")
            if label in {"Molecular Formula", "Molecular Weight", "IUPAC Name", "InChI", "InChIKey"} and text:
                values.setdefault(f"{label} {name}".strip(), str(text))
        summary = "; ".join(f"{key}: {value}" for key, value in values.items())
        records.append(SourceDocument(f"Paracetamol (acetaminophen) PubChem CID 1983 properties: {summary}.", {
            "source_id": metadata.get("source_id", ""), "source": json_path.name, "local_path": relative,
            "source_url": metadata.get("source_url", ""), "license_reuse": metadata.get("license_reuse", ""),
            "sha256": metadata.get("sha256", ""), "page": None, "section": "PubChem compound properties",
            "extractor": "PubChem PUG JSON parser", "quality_status": "valid_json",
            "version_date": metadata.get("publication_or_update_date", ""),
        }))
    return records


def write_chemical_report(project_root: Path | str) -> Path:
    root = Path(project_root).resolve()
    result = validate_chemical_sources(root)
    output = root / "data" / "processed" / "chemical_validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return output
