"""Read research sources into provenance-bearing page/section documents.

Original files remain read-only. Extraction reports are derived artifacts and
must never be treated as scientific validation of their contents.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)


@dataclass
class SourceDocument:
    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(root: Path) -> dict[str, dict[str, str]]:
    manifest = root / "SOURCE_MANIFEST.csv"
    if not manifest.exists():
        return {}
    with manifest.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        return {
            row.get("local_filename", "").replace("\\", "/"): row
            for row in rows
            if row.get("local_filename")
        }


def _metadata(root: Path, path: Path, manifest: dict[str, dict[str, str]],
              *, page: int | None, extractor: str, quality: str) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    source = manifest.get(relative, {})
    return {
        "source_id": source.get("source_id") or "",
        "source": path.name,
        "local_path": relative,
        "source_url": source.get("source_url") or "",
        "title": source.get("title") or "",
        "authors": source.get("authors") or "",
        "doi": source.get("doi") or "",
        "pmid": source.get("pmid") or "",
        "pmcid": source.get("pmcid") or "",
        "license_reuse": source.get("license_reuse") or "",
        "version_date": source.get("publication_or_update_date") or "",
        "page": page,
        "extractor": extractor,
        "quality_status": quality,
        "sha256": sha256_file(path),
    }


def _xml_text(path: Path) -> Iterable[tuple[str, str]]:
    """Yield non-empty JATS sections/paragraphs with section headings."""
    tree = ET.parse(path)
    root = tree.getroot()

    def text_of(element: ET.Element) -> str:
        return " ".join("".join(element.itertext()).split())

    title = next((text_of(e) for e in root.iter() if e.tag.split("}")[-1] == "article-title"), "")
    abstract = next((e for e in root.iter() if e.tag.split("}")[-1] == "abstract"), None)
    if abstract is not None and text_of(abstract):
        yield "Abstract", text_of(abstract)

    body = next((e for e in root.iter() if e.tag.split("}")[-1] == "body"), None)
    if body is None:
        return
    parents = {child: parent for parent in body.iter() for child in parent}
    for section in (e for e in body.iter() if e.tag.split("}")[-1] == "sec"):
        heading = next((text_of(child) for child in section if child.tag.split("}")[-1] == "title"), "")
        paragraphs = []
        for paragraph in (e for e in section.iter() if e.tag.split("}")[-1] == "p"):
            ancestor = parents.get(paragraph)
            while ancestor is not None and ancestor is not section and ancestor.tag.split("}")[-1] != "sec":
                ancestor = parents.get(ancestor)
            if ancestor is section:
                paragraphs.append(text_of(paragraph))
        content = "\n\n".join(p for p in paragraphs if p)
        if content:
            yield heading or title or "Body", content


def _rendered_page_ocr(document: Any, page_index: int, tesseract: str,
                       prior_pages: dict[str, int], timeout: int = 60) -> tuple[str, str, str]:
    """Render a full page, then OCR it; return text, status, and rendered hash."""
    try:
        image = document[page_index].render(scale=2).to_pil().convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        render_hash = hashlib.sha256(image_bytes).hexdigest()
        if render_hash in prior_pages:
            return "", f"duplicate_render_of_page_{prior_pages[render_hash]}", render_hash
        prior_pages[render_hash] = page_index + 1
        proc = subprocess.run([tesseract, "stdin", "stdout", "--psm", "6"],
                              input=image_bytes, capture_output=True, timeout=timeout, check=False)
        if proc.returncode != 0:
            return "", "ocr_failed", render_hash
        return proc.stdout.decode("utf-8", errors="replace").strip(), "ocr_unverified_visual_review_required", render_hash
    except Exception as exc:
        return "", f"render_or_ocr_failed:{type(exc).__name__}", ""


def ingest_file(root: Path, path: Path, manifest: dict[str, dict[str, str]],
                *, use_ocr: bool = True) -> tuple[list[SourceDocument], list[dict[str, Any]]]:
    suffix = path.suffix.lower()
    docs: list[SourceDocument] = []
    page_report: list[dict[str, Any]] = []
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pdf_meta = reader.metadata
        render_doc = None
        if use_ocr and any(not (p.extract_text() or "").strip() for p in reader.pages):
            try:
                import pypdfium2 as pdfium
                render_doc = pdfium.PdfDocument(str(path))
            except (ImportError, OSError, ValueError):
                render_doc = None
        render_hash_pages: dict[str, int] = {}
        for number, page in enumerate(reader.pages, start=1):
            content = (page.extract_text() or "").strip()
            method, quality = "pypdf", "text_extracted" if content else "no_extractable_text"
            ocr_status = "not_run" if not content else "not_needed"
            render_hash = ""
            rendered_duplicate_page = None
            ocr_text = ""
            if not content and use_ocr:
                tesseract = shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                if render_doc is None:
                    ocr_status = "pdf_renderer_missing"
                elif Path(tesseract).exists():
                    ocr_text, quality, render_hash = _rendered_page_ocr(render_doc, number - 1, tesseract, render_hash_pages)
                    ocr_status = quality
                    method = "pypdfium2+Tesseract"
                    if quality.startswith("duplicate_render_of_page_"):
                        rendered_duplicate_page = int(quality.rsplit("_", 1)[-1])
                else:
                    ocr_status = "tesseract_missing"
            metadata = _metadata(root, path, manifest, page=number, extractor=method, quality=quality)
            metadata.update({
                "pdf_title": str(getattr(pdf_meta, "title", "") or ""),
                "pdf_author": str(getattr(pdf_meta, "author", "") or ""),
                "pdf_creation_date": str(getattr(pdf_meta, "creation_date", "") or ""),
                "pdf_modified_date": str(getattr(pdf_meta, "modification_date", "") or ""),
                "pdf_page_count": len(reader.pages),
                "ocr_status": ocr_status,
                "render_sha256": render_hash,
                "render_duplicate_page": rendered_duplicate_page,
            })
            page_report.append({**metadata, "character_count": len(content),
                                "ocr_character_count": len(ocr_text), "ocr_text": ocr_text})
            if content and quality != "ocr_unverified_visual_review_required":
                docs.append(SourceDocument(content, metadata))
    elif suffix == ".txt":
        content = path.read_text(encoding="utf-8", errors="replace").strip()
        if content:
            metadata = _metadata(root, path, manifest, page=None,
                                 extractor="utf-8 text", quality="text_extracted")
            metadata["section"] = "plain text document"
            docs.append(SourceDocument(content, metadata))
    elif suffix == ".xml":
        for section, content in _xml_text(path):
            metadata = _metadata(root, path, manifest, page=None, extractor="JATS XML / ElementTree",
                                 quality="xml_parsed")
            metadata["section"] = section
            docs.append(SourceDocument(content, metadata))
    return docs, page_report


def ingest_corpus(root: Path | str, *, use_ocr: bool = True,
                  include_text_derivatives: bool = False) -> tuple[list[SourceDocument], dict[str, Any]]:
    """Ingest PDFs, XML and TXT from a paracetamol corpus, preserving provenance.

    The article TXT derivative duplicates its source XML and is omitted by
    default to prevent duplicate evidence; original TXT files remain intact.
    """
    root = Path(root).resolve()
    corpus = root / "data" / "research" / "paracetamol"
    manifest = load_manifest(root)
    paths = sorted(p for p in corpus.rglob("*") if p.is_file() and p.suffix.lower() in {".pdf", ".txt", ".xml"})
    docs: list[SourceDocument] = []
    reports: list[dict[str, Any]] = []
    for path in paths:
        if not include_text_derivatives and path.name.endswith("_extracted.txt"):
            continue
        try:
            file_docs, pages = ingest_file(root, path, manifest, use_ocr=use_ocr)
            docs.extend(file_docs)
            reports.extend(pages)
        except Exception as exc:
            reports.append({"local_path": path.relative_to(root).as_posix(),
                            "quality_status": f"ingestion_failed:{type(exc).__name__}",
                            "error": str(exc)})
    # Four MedlinePlus captures were audited as identical extracted content.
    # Exclude duplicate copies from indexing, while retaining source aliases.
    medline = [d for d in docs if "MedlinePlus Drug Information" in str(d.metadata.get("title", ""))]
    by_file: dict[str, list[SourceDocument]] = {}
    for doc in medline:
        by_file.setdefault(doc.metadata["local_path"], []).append(doc)
    by_text: dict[str, list[str]] = {}
    for name, file_docs in by_file.items():
        file_docs.sort(key=lambda d: d.metadata.get("page") or 0)
        joined = " ".join(" ".join(d.page_content.lower().split()) for d in file_docs)
        by_text.setdefault(hashlib.sha256(joined.encode()).hexdigest(), []).append(name)
    aliases = []
    for names in by_text.values():
        if len(names) > 1:
            names.sort()
            aliases.append({"duplicate_group": hashlib.sha256("\n".join(names).encode()).hexdigest()[:12],
                            "canonical_path": names[0], "duplicate_paths": names[1:],
                            "assessment": "same extracted text; distinct PDF hashes/creation dates; version identity unproven"})
            duplicates = set(names[1:])
            docs[:] = [d for d in docs if d.metadata.get("local_path") not in duplicates]
    render_groups: dict[str, list[int]] = {}
    for item in reports:
        if item.get("render_sha256"):
            render_groups.setdefault(item["render_sha256"], []).append(item["page"])
    repeated_render_groups = [
        {"render_sha256": key, "pages": pages, "canonical_page": pages[0],
         "duplicate_pages": pages[1:]}
        for key, pages in render_groups.items() if len(pages) > 1
    ]
    report = {"files_seen": len(paths), "documents_indexed": len(docs), "page_checks": reports,
              "exact_text_duplicate_groups": aliases,
              "repeated_render_groups": repeated_render_groups,
              "pages_needing_visual_review": [r for r in reports if r.get("quality_status") == "ocr_unverified_visual_review_required"]}
    return docs, report


def write_extraction_report(report: dict[str, Any], target: Path | str) -> None:
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
