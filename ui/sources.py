"""COSIN Scientific Sources & Corpus Viewer.

Displays:
- Preserved research corpus files (PDF, JATS XML, TXT, SDF, JSON).
- Source manifest metadata, SHA-256 hashes, and license/reuse conditions.
- Evidence graph and extraction statistics.
"""

import csv
from pathlib import Path
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "SOURCE_MANIFEST.csv"


def load_manifest() -> list[dict[str, str]]:
    """Read the source manifest CSV."""
    if not MANIFEST_PATH.exists():
        return []
    records = []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def render_sources_page() -> None:
    """Render the scientific sources inventory."""
    st.markdown("### Scientific Corpus & Source Manifest")
    st.caption("Immutable local literature and molecular data records with cryptographic SHA-256 provenance.")

    manifest = load_manifest()
    if not manifest:
        st.warning("No `SOURCE_MANIFEST.csv` found in project root.")
        return

    st.markdown(f"**Total Tracked Scientific Sources:** {len(manifest)}")

    search = st.text_input("Filter sources by title, author, or identifier:", placeholder="e.g. PubChem, FDA, MedlinePlus...")
    filtered = manifest
    if search:
        s_lower = search.lower()
        filtered = [
            m for m in manifest
            if any(s_lower in str(v).lower() for v in m.values())
        ]

    for idx, item in enumerate(filtered, 1):
        source_id = item.get("source_id", "N/A")
        title = item.get("source_title", "Untitled Source")
        filename = item.get("filename", "")
        file_hash = item.get("sha256", "")
        url = item.get("source_url", "")
        license_terms = item.get("license_reuse", "Unspecified")
        doc_type = item.get("document_type", "document")

        with st.expander(f"{idx}. [{source_id}] {title or filename}"):
            st.markdown(f"**File:** `{filename}` | **Type:** `{doc_type}`")
            if url:
                st.markdown(f"**Source URL:** [{url}]({url})")
            st.markdown(f"**SHA-256 Checksum:** `{file_hash}`")
            st.markdown(f"**License & Reuse:** *{license_terms}*")

