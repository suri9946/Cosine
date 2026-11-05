"""COSIN Research History Component.

Loads, indexes, and presents past research runs from data/processed/runs/*.json.
Allows users to search, inspect past answers, and view execution telemetry.
"""

import json
from pathlib import Path
from typing import Any
import streamlit as st
from ui.theme import render_status_pill


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "data" / "processed" / "runs"


def load_research_history() -> list[dict[str, Any]]:
    """Scan and load all historical JSON audit records."""
    if not RUNS_DIR.exists():
        return []

    records = []
    for file_path in RUNS_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_file_path"] = str(file_path)
                records.append(data)
        except Exception:
            continue

    # Sort descending by creation date or request_id
    records.sort(
        key=lambda r: r.get("created_at") or r.get("request_id") or "",
        reverse=True,
    )
    return records


def render_research_history_page(on_select_run: Any = None) -> None:
    """Render the full Research History view."""
    st.markdown("### Research History & Audit Trail")
    st.caption("Immutable local records of all completed and fail-closed research executions.")

    history = load_research_history()

    if not history:
        st.info("No research history records found in `data/processed/runs/`.")
        return

    # Filter / Search
    query = st.text_input("Filter research by keyword or question:", placeholder="e.g. molecular formula, liver toxicity, mechanism...")

    filtered = history
    if query:
        q_lower = query.lower()
        filtered = [
            r for r in history
            if q_lower in r.get("question", "").lower()
            or q_lower in r.get("answer", "").lower()
            or q_lower in r.get("request_id", "").lower()
        ]

    st.markdown(f"**Showing {len(filtered)} of {len(history)} execution runs:**")

    for item in filtered:
        req_id = item.get("request_id", "unknown")
        q = item.get("question", "No question recorded")
        status = item.get("status", "UNKNOWN")
        ans = item.get("answer", "") or "No synthesized answer."
        created = item.get("created_at", "N/A")
        timings = item.get("stage_timings_ms", {}) or {}
        tot_time = f"{timings.get('total', 0) / 1000:.2f}s" if "total" in timings else "N/A"

        with st.container():
            st.markdown(
                f"""
                <div class="cosin-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <span style="font-family: monospace; font-size: 0.775rem; color: #5A6A80;">
                            ID: {req_id[:12]}... • {created} • Latency: {tot_time}
                        </span>
                        <div>{render_status_pill(status)}</div>
                    </div>
                    <div style="font-size: 1rem; font-weight: 600; color: #1A202C; margin-bottom: 0.4rem;">
                        {q}
                    </div>
                    <div style="font-size: 0.85rem; color: #4A5568; line-height: 1.5; margin-bottom: 0.5rem;">
                        {ans[:240]}{'...' if len(ans) > 240 else ''}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns([1, 5])
            with c1:
                if st.button("Inspect Run", key=f"btn_hist_{req_id}"):
                    if callable(on_select_run):
                        on_select_run(item)

