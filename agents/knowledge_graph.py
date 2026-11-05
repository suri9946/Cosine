"""Small, provenance-first graph for source and evidence navigation.

Concept links are explicit lexical matches, not extracted scientific claims.
This initial implementation has no cross-drug nodes or inferred mechanisms.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

CONCEPTS = {
    "mechanism_of_action": ("mechanism of action", "mechanism"),
    "pharmacokinetics": ("pharmacokinetics", "absorption", "distribution", "clearance"),
    "metabolism": ("metabolism", "metabolized", "metabolised"),
    "napqi": ("napqi", "n-acetyl-p-benzoquinone imine"),
    "toxicology": ("toxicology", "toxicity", "overdose", "hepatotoxicity"),
    "chemical_structure": ("molecular formula", "smiles", "inchi", "molecular weight"),
}


def build_evidence_graph(records: Iterable[Any]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {
        "drug:paracetamol": {"type": "drug", "drug_id": "paracetamol", "label": "Paracetamol (acetaminophen)"}
    }
    edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    for record in records:
        metadata = record.metadata
        source_id = str(metadata.get("source_id") or metadata.get("local_path") or "unknown")
        source_node = f"source:{source_id}"
        nodes.setdefault(source_node, {"type": "source", "source_id": source_id,
                                       "path": metadata.get("local_path", ""), "title": metadata.get("title", ""),
                                       "source_url": metadata.get("source_url", ""),
                                       "license_reuse": metadata.get("license_reuse", ""),
                                       "version_date": metadata.get("version_date", "")})
        edge = ("drug:paracetamol", source_node, "documented_in")
        if edge not in seen_edges:
            edges.append({"from": edge[0], "to": edge[1], "relation": edge[2], "basis": "corpus_membership"})
            seen_edges.add(edge)
        text = record.page_content
        evidence_key = hashlib.sha256((source_id + "|" + str(metadata.get("page")) + "|" + text).encode()).hexdigest()[:20]
        evidence_node = f"evidence:{evidence_key}"
        nodes[evidence_node] = {"type": "evidence", "evidence_id": evidence_key, "source_id": source_id,
                                "path": metadata.get("local_path", ""), "page": metadata.get("page"),
                                "section": metadata.get("section", ""), "extractor": metadata.get("extractor", ""),
                                "quality_status": metadata.get("quality_status", "")}
        edges.append({"from": source_node, "to": evidence_node, "relation": "contains_evidence",
                      "basis": "extraction", "page": metadata.get("page"), "section": metadata.get("section", "")})
        normalized = re.sub(r"\s+", " ", text.lower())
        for concept, terms in CONCEPTS.items():
            if any(term in normalized for term in terms):
                concept_node = f"concept:{concept}"
                nodes.setdefault(concept_node, {"type": "concept", "concept_id": concept, "label": concept.replace("_", " ")})
                edges.append({"from": evidence_node, "to": concept_node, "relation": "mentions_concept",
                              "basis": "lexical_match", "matched_terms": [term for term in terms if term in normalized],
                              "scientific_assertion": False})
    return {"schema_version": 1, "drug_scope": ["paracetamol"], "nodes": list(nodes.values()), "edges": edges}


def write_graph(graph: dict[str, Any], target: Path | str) -> Path:
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
