"""COSIN — Scientific Drug Research and Evidence Analysis Platform.

Main Streamlit Application Entry Point.
Desktop-first, light-themed, professional scientific research workspace.
"""

from typing import Any
import streamlit as st

# Set Streamlit page config as first Streamlit call
st.set_page_config(
    page_title="COSIN — Scientific Drug Research & Evidence Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.theme import CUSTOM_CSS, render_status_pill
from ui.tracker import render_progress_tracker
from ui.report import render_scientific_report
from ui.evidence import render_evidence_panel, render_agent_details_inspection
from ui.history import render_research_history_page
from ui.system_status import render_system_status_page
from ui.sources import render_sources_page


# Inject custom styling for light scientific theme
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Initializing COSIN Scientific Knowledge Index...")
def get_system_orchestrator(top_k: int = 5):
    """Instantiate orchestrator and load the local research corpus once."""
    from agents.orchestrator import ResearchOrchestrator
    orchestrator = ResearchOrchestrator(top_k=top_k)
    orchestrator.retriever.load_documents()
    return orchestrator


def init_session_state() -> None:
    """Initialize application session state keys."""
    if "stage_states" not in st.session_state:
        st.session_state["stage_states"] = {
            "agent1": {"status": "WAITING", "timing_ms": 0, "details": {}},
            "agent2": {"status": "WAITING", "timing_ms": 0, "details": {}},
            "agent3": {"status": "WAITING", "timing_ms": 0, "details": {}},
            "agent4": {"status": "WAITING", "timing_ms": 0, "details": {}},
        }
    if "current_run" not in st.session_state:
        st.session_state["current_run"] = None
    if "is_running" not in st.session_state:
        st.session_state["is_running"] = False
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "New Research"
    if "question_input_text" not in st.session_state:
        st.session_state["question_input_text"] = ""


def reset_stage_states() -> None:
    """Reset stages to waiting state before execution."""
    st.session_state["stage_states"] = {
        "agent1": {"status": "WAITING", "timing_ms": 0, "details": {}},
        "agent2": {"status": "WAITING", "timing_ms": 0, "details": {}},
        "agent3": {"status": "WAITING", "timing_ms": 0, "details": {}},
        "agent4": {"status": "WAITING", "timing_ms": 0, "details": {}},
    }


def render_sidebar() -> str:
    """Render the application sidebar."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding-top: 0.5rem; margin-bottom: 1.25rem;">
                <div class="cosin-brand">COSIN</div>
                <div class="cosin-subtitle">Scientific Drug Research & Evidence Analysis</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_options = [
            "New Research",
            "Research History",
            "Scientific Sources",
            "System Status",
            "Settings",
        ]

        choice = st.radio(
            "Navigation",
            options=nav_options,
            index=nav_options.index(st.session_state["nav_page"]) if st.session_state["nav_page"] in nav_options else 0,
            label_visibility="collapsed",
        )
        st.session_state["nav_page"] = choice

        st.divider()

        # Scope card
        st.markdown(
            """
            <div style="font-size: 0.8125rem; color: #5A6A80; background-color: #F8F9FA; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.75rem;">
                <strong style="color: #1A202C;">Active Target Scope</strong><br/>
                Compound: <strong>Paracetamol</strong><br/>
                SMILES: <code>CC(=O)Nc1ccc(O)cc1</code><br/>
                Corpus Chunks: <strong>589 indexed</strong><br/>
                Traceability Standard: <strong>1.00</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Evidence retrieval and model assessments are scientific research aids; "
            "they do not establish clinical accuracy or medical safety."
        )

        return choice


def render_settings_page() -> None:
    """Render the settings view."""
    st.markdown("### Platform Settings & Configuration")
    st.caption("Inspect and configure evidence retrieval limits and literature connector parameters.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Retrieval & Model Configuration")
        top_k = st.slider("Top-K Evidence Candidates (Agent 1)", min_value=3, max_value=10, value=5, step=1)
        st.caption("Number of high-relevance chunks retrieved by dense + BM25 reciprocal-rank fusion.")

        st.text_input("Chemistry Model Target", value="ChemLLM-7B-Chat-GGUF:Q4_K_M", disabled=True)
        st.text_input("Quality Review Model Target", value="llama3.2:3b", disabled=True)

    with col2:
        st.markdown("#### External Literature Connectors")
        st.text_input("PubMed E-utilities Endpoint", value="https://eutils.ncbi.nlm.nih.gov", disabled=True)
        st.text_input("Europe PMC REST Endpoint", value="https://www.ebi.ac.uk/europepmc", disabled=True)
        st.markdown(
            """
            <div style="font-size: 0.8125rem; color: #5A6A80; margin-top: 0.5rem;">
                NCBI credentials are read securely from local <code>.env</code> file.<br/>
                Public rate limits (3 requests/sec) are enforced by default.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_new_research_page() -> None:
    """Render the primary question input and research execution page."""
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <div class="cosin-brand">COSIN</div>
            <div class="cosin-subtitle">Scientific Drug Research & Evidence Analysis</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Prompt suggestions
    st.markdown(
        "<span style='font-size: 0.825rem; font-weight: 600; color: #5A6A80;'>EXAMPLE SCIENTIFIC INQUIRIES:</span>",
        unsafe_allow_html=True,
    )
    s_col1, s_col2, s_col3 = st.columns([1, 1, 1.2])
    with s_col1:
        if st.button("🧪 Formula & Structure", use_container_width=True):
            st.session_state["question_input_text"] = "What is the molecular formula and basic structure of paracetamol?"
            st.rerun()
    with s_col2:
        if st.button("⚙️ Mechanism of Action", use_container_width=True):
            st.session_state["question_input_text"] = "What is the primary mechanism of action of paracetamol?"
            st.rerun()
    with s_col3:
        if st.button("⚠️ Liver Toxicity in Overdose", use_container_width=True):
            st.session_state["question_input_text"] = "How does paracetamol cause liver toxicity in overdose?"
            st.rerun()

    # Question Input
    question = st.text_area(
        "Scientific Research Question",
        value=st.session_state.get("question_input_text", ""),
        placeholder="Ask a scientific question about a drug, its chemistry, pharmacology or mechanisms...",
        height=95,
        label_visibility="collapsed",
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        submit = st.button("🔍 Submit Research", type="primary", use_container_width=True, disabled=st.session_state["is_running"])

    tracker_placeholder = st.empty()
    result_placeholder = st.empty()

    # Pre-render existing tracker state
    with tracker_placeholder.container():
        render_progress_tracker(st.session_state["stage_states"])

    # If already have a current run, render its result
    if st.session_state["current_run"] and not st.session_state["is_running"]:
        with result_placeholder.container():
            t1, t2, t3 = st.tabs([
                "📋 Research Findings & Summary",
                "📚 Evidence & Literature Provenance",
                "🛡️ Quality Review & Pipeline Telemetry",
            ])
            with t1:
                render_scientific_report(st.session_state["current_run"])
            with t2:
                render_evidence_panel(st.session_state["current_run"])
            with t3:
                render_agent_details_inspection(st.session_state["current_run"])

    # Handle submission
    if submit:
        if not question.strip():
            st.warning("Please enter a scientific research question to begin analysis.")
            return

        st.session_state["is_running"] = True
        reset_stage_states()

        tracker_placeholder.empty()
        with tracker_placeholder.container():
            render_progress_tracker(st.session_state["stage_states"])

        try:
            with st.status("🔬 Executing Four Scientific Stages...", expanded=True) as status_box:
                st.write("Initializing scientific knowledge index...")

                # Define real-time progress callback
                def on_stage_progress(stage: str, status: str, details: Any = None):
                    if stage in st.session_state["stage_states"]:
                        st.session_state["stage_states"][stage]["status"] = status
                        if details:
                            st.session_state["stage_states"][stage]["details"] = details
                            if "timing_ms" in details:
                                st.session_state["stage_states"][stage]["timing_ms"] = details["timing_ms"]

                    if stage == "agent1":
                        if status == "running":
                            st.write("🔍 **Stage 1 (Retrieval):** Searching local scientific corpus & embeddings...")
                        elif status == "completed":
                            cnt = details.get("candidates_count", 5) if details else 5
                            t_ms = details.get("timing_ms", 0) if details else 0
                            st.write(f"✅ **Stage 1 Complete:** Retrieved {cnt} relevant evidence passages in {t_ms}ms.")
                    elif stage == "agent2":
                        if status == "running":
                            st.write("🧪 **Stage 2 (Chemistry & Pharmacology):** ChemLLM formulating evidence-grounded claims...")
                        elif status == "completed":
                            claims_cnt = len(details.get("claims", [])) if details else 0
                            t_ms = details.get("timing_ms", 0) if details else 0
                            st.write(f"✅ **Stage 2 Complete:** Formulated {claims_cnt} claim(s) mapped to evidence in {t_ms}ms.")
                    elif stage == "agent3":
                        if status == "running":
                            st.write("📚 **Stage 3 (Literature Verification):** Cross-querying NCBI PubMed & Europe PMC...")
                        elif status in {"completed", "needs_attention"}:
                            t_ms = details.get("timing_ms", 0) if details else 0
                            st.write(f"✅ **Stage 3 Complete:** External literature candidates verified in {t_ms}ms.")
                    elif stage == "agent4":
                        if status == "running":
                            st.write("⚖️ **Stage 4 (Scientific Judge):** Running contradiction checks & fail-closed safety review...")
                        elif status == "completed":
                            dec = details.get("final_status", "Evaluated") if details else "Evaluated"
                            t_ms = details.get("timing_ms", 0) if details else 0
                            st.write(f"✅ **Stage 4 Complete:** Quality review decision: **{dec}** in {t_ms}ms.")

                    tracker_placeholder.empty()
                    with tracker_placeholder.container():
                        render_progress_tracker(st.session_state["stage_states"])

                orchestrator = get_system_orchestrator()
                run_result = orchestrator.run(question.strip(), on_progress=on_stage_progress)
                st.session_state["current_run"] = run_result
                status_box.update(
                    label=f"✅ Research Analysis Complete — Final Verdict: {run_result.status}",
                    state="complete",
                    expanded=False,
                )

        except Exception as exc:
            st.error(f"Research execution encountered an unhandled exception: {type(exc).__name__}: {str(exc)}")
        finally:
            st.session_state["is_running"] = False

        # Render final results
        tracker_placeholder.empty()
        with tracker_placeholder.container():
            render_progress_tracker(st.session_state["stage_states"])

        if st.session_state["current_run"]:
            result_placeholder.empty()
            with result_placeholder.container():
                t1, t2, t3 = st.tabs([
                    "📋 Research Findings & Summary",
                    "📚 Evidence & Literature Provenance",
                    "🛡️ Quality Review & Pipeline Telemetry",
                ])
                with t1:
                    render_scientific_report(st.session_state["current_run"])
                with t2:
                    render_evidence_panel(st.session_state["current_run"])
                with t3:
                    render_agent_details_inspection(st.session_state["current_run"])


def on_select_historical_run(run_data: dict[str, Any]) -> None:
    """Callback to switch view and inspect a historical run."""
    st.session_state["current_run"] = run_data
    st.session_state["nav_page"] = "New Research"
    st.rerun()


def main() -> None:
    """Application main controller."""
    init_session_state()
    nav_page = render_sidebar()

    if nav_page == "New Research":
        render_new_research_page()
    elif nav_page == "Research History":
        render_research_history_page(on_select_run=on_select_historical_run)
    elif nav_page == "Scientific Sources":
        render_sources_page()
    elif nav_page == "System Status":
        render_system_status_page()
    elif nav_page == "Settings":
        render_settings_page()


if __name__ == "__main__":
    main()

