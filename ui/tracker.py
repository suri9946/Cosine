"""COSIN Stage Execution Progress Tracker.

Renders real execution progress across the four scientific stages:
Stage 1: Scientific Knowledge Retrieval
Stage 2: Chemistry & Pharmacology Analysis
Stage 3: Scientific Literature Verification
Stage 4: Scientific Quality Review
"""

from typing import Any
import streamlit as st
from ui.theme import render_status_pill


STAGE_METADATA = {
    "agent1": {
        "title": "Stage 1: Scientific Knowledge Retrieval",
        "description": "Local corpus hybrid search (BM25 + Dense Embeddings) & evidence extraction",
        "icon": "1",
    },
    "agent2": {
        "title": "Stage 2: Chemistry & Pharmacology Analysis",
        "description": "Evidence-grounded claim formulation using ChemLLM (7B Q4_K_M)",
        "icon": "2",
    },
    "agent3": {
        "title": "Stage 3: Scientific Literature Verification",
        "description": "Cross-verification against NCBI PubMed and Europe PMC repositories",
        "icon": "3",
    },
    "agent4": {
        "title": "Stage 4: Scientific Quality Review",
        "description": "Independent judgment, claim contradiction check & fail-closed rule audit",
        "icon": "4",
    },
}


def render_progress_tracker(stage_states: dict[str, dict[str, Any]]) -> None:
    """Render the four-stage vertical progress tracker.

    Args:
        stage_states: dict mapping stage id ("agent1", "agent2", "agent3", "agent4")
                      to dict with "status", "timing_ms", "details", and "error".
    """
    st.markdown("### Research Pipeline Execution")
    st.caption("Real-time telemetry from the four scientific pipeline stages.")

    for stage_id, meta in STAGE_METADATA.items():
        state = stage_states.get(stage_id, {"status": "WAITING", "timing_ms": 0, "details": {}})
        status = state.get("status", "WAITING").upper()
        timing_ms = state.get("timing_ms")
        details = state.get("details", {}) or {}
        error = state.get("error")

        css_class = status.lower()

        # Build status card
        with st.container():
            timing_str = f" • {timing_ms} ms" if timing_ms else ""
            st.markdown(
                f"""
                <div class="stage-box {css_class}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="font-weight: 600; font-size: 0.95rem; color: #1A202C;">
                                {meta['title']}
                            </div>
                            <div style="font-size: 0.8125rem; color: #5A6A80; margin-top: 0.2rem;">
                                {meta['description']}{timing_str}
                            </div>
                        </div>
                        <div>
                            {render_status_pill(status)}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Details expansion when active or completed
            if status in {"RUNNING", "COMPLETED", "NEEDS_ATTENTION", "FAILED"}:
                _render_stage_subdetails(stage_id, status, details, error)


def _render_stage_subdetails(stage_id: str, status: str, details: dict[str, Any], error: str | None) -> None:
    """Render specific stage metrics and outputs."""
    if error:
        st.error(f"Stage Exception: {error}")
        return

    if stage_id == "agent1":
        candidates = details.get("candidates_count") or len(details.get("evidence", []))
        assessment = details.get("assessment", {})
        if candidates:
            topic = assessment.get("topic", "unclassified")
            st.markdown(
                f"""
                <div style="font-size: 0.8125rem; color: #2D3748; margin-left: 0.75rem; margin-bottom: 0.75rem;">
                    <strong>Retrieved Chunks:</strong> {candidates} &nbsp;|&nbsp;
                    <strong>Inferred Topic:</strong> <code>{topic}</code> &nbsp;|&nbsp;
                    <strong>Assessment:</strong> {assessment.get('status', 'Retrieved')}
                </div>
                """,
                unsafe_allow_html=True,
            )

    elif stage_id == "agent2":
        claims = details.get("claims", [])
        if claims:
            st.markdown(
                f"""
                <div style="font-size: 0.8125rem; color: #2D3748; margin-left: 0.75rem; margin-bottom: 0.75rem;">
                    <strong>Formulated Scientific Claims:</strong> {len(claims)} claim(s) mapped to local evidence IDs.
                </div>
                """,
                unsafe_allow_html=True,
            )

    elif stage_id == "agent3":
        verification = details.get("verification", {})
        v_claims = verification.get("claims", []) if isinstance(verification, dict) else getattr(verification, "claims", [])
        record_count = sum(len(c.get("records", []) if isinstance(c, dict) else getattr(c, "records", [])) for c in v_claims)
        st.markdown(
            f"""
            <div style="font-size: 0.8125rem; color: #2D3748; margin-left: 0.75rem; margin-bottom: 0.75rem;">
                <strong>NCBI PubMed & Europe PMC:</strong> {record_count} candidate literature citation(s) retrieved.
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif stage_id == "agent4":
        judgment = details.get("judgment")
        if judgment:
            decisions = judgment.get("claims", []) if isinstance(judgment, dict) else getattr(judgment, "claims", [])
            st.markdown(
                f"""
                <div style="font-size: 0.8125rem; color: #2D3748; margin-left: 0.75rem; margin-bottom: 0.75rem;">
                    <strong>Scientific Judge Decision:</strong> {details.get('final_status', 'Evaluated')} ({len(decisions)} claims evaluated).
                </div>
                """,
                unsafe_allow_html=True,
            )

