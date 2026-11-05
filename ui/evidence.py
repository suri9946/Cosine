"""COSIN Dedicated Evidence & Agent Output Inspection Components.

Renders:
- Detailed provenance-backed evidence cards with clickable DOIs and URLs.
- Granular agent stage outputs inspection views with timing, raw structured results, and error details.
"""

from typing import Any
import streamlit as st
from ui.theme import render_status_pill


def _val(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def render_evidence_panel(result: Any) -> None:
    """Render the dedicated scientific evidence & provenance panel."""
    evidence_list = _val(result, "evidence", []) or []
    verification = _val(result, "verification")
    ext_claims = _val(verification, "claims", []) or []

    st.markdown("### Evidence & Literature Inventory")
    st.caption("Complete provenance record of local corpus extracts and external publication records.")

    tab1, tab2 = st.tabs(["Local Ingested Sources (Corpus)", "External Literature Candidates (PubMed / Europe PMC)"])

    with tab1:
        if not evidence_list:
            st.info("No local evidence passages were retrieved for this research query.")
        else:
            for idx, ev in enumerate(evidence_list, 1):
                eid = _val(ev, "evidence_id", "N/A")
                title = _val(ev, "source_title") or _val(ev, "source", "Unnamed Local Document")
                authors = _val(ev, "authors", "")
                year = _val(ev, "version_date", "")
                page = _val(ev, "page")
                section = _val(ev, "section", "")
                url = _val(ev, "source_url", "")
                pmid = _val(ev, "pmid", "")
                doi = _val(ev, "doi", "")
                text = _val(ev, "text", "")
                ev_type = _val(ev, "evidence_type", "SUPPORTING_CONTEXT")
                score = _val(ev, "hybrid_score") or _val(ev, "adjusted_score") or 0.0
                extractor = _val(ev, "extractor", "Native Parser")
                quality = _val(ev, "quality_status", "verified")

                with st.expander(f"Source #{idx}: {title} (ID: {eid[:8]})", expanded=(idx == 1)):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        if authors:
                            st.markdown(f"**Authors:** {authors}")
                        meta_items = []
                        if year:
                            meta_items.append(f"**Date:** {year}")
                        if page:
                            meta_items.append(f"**Page:** {page}")
                        if section:
                            meta_items.append(f"**Section:** {section}")
                        if meta_items:
                            st.markdown(" • ".join(meta_items))

                        link_row = []
                        if pmid:
                            link_row.append(f"PMID: [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
                        if doi:
                            link_row.append(f"DOI: [{doi}](https://doi.org/{doi})")
                        if url:
                            link_row.append(f"[Official Source URL ↗]({url})")
                        if link_row:
                            st.markdown(" | ".join(link_row))

                    with c2:
                        st.markdown(f"**Retrieval Score:** `{score:.4f}`")
                        st.markdown(f"**Classification:** `{ev_type}`")
                        st.markdown(f"**Extractor:** `{extractor}`")
                        st.markdown(f"**Integrity:** `{quality}`")

                    st.markdown("##### Extracted Source Passage")
                    st.markdown(f"> *{text}*")

                    reason = _val(ev, "classification_reason")
                    if reason:
                        st.caption(f"Relevance Note: {reason}")

    with tab2:
        has_ext = False
        for ec in ext_claims:
            cid = _val(ec, "claim_id", "")
            query = _val(ec, "query", "")
            records = _val(ec, "records", []) or []
            errors = _val(ec, "provider_errors", {}) or {}

            if errors:
                st.warning(f"Claim `{cid}` Provider Status: {', '.join(f'{k}: {v}' for k, v in errors.items())}")

            for rec in records:
                has_ext = True
                title = _val(rec, "title", "External Publication")
                provider = _val(rec, "provider", "Repository")
                journal = _val(rec, "journal", "")
                year = _val(rec, "year", "")
                authors = _val(rec, "authors", "")
                pmid = _val(rec, "pmid", "")
                pmcid = _val(rec, "pmcid", "")
                doi = _val(rec, "doi", "")
                url = _val(rec, "source_url", "")
                abstract = _val(rec, "abstract", "")

                with st.expander(f"{provider}: {title}"):
                    st.markdown(f"**Associated Claim:** `{cid}` | **Query Used:** `{query}`")
                    if authors:
                        st.markdown(f"**Authors:** {authors}")
                    meta_row = []
                    if journal:
                        meta_row.append(f"**Journal:** {journal}")
                    if year:
                        meta_row.append(f"**Year:** {year}")
                    if meta_row:
                        st.markdown(" • ".join(meta_row))

                    link_row = []
                    if pmid:
                        link_row.append(f"PMID: [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
                    if pmcid:
                        link_row.append(f"PMCID: [{pmcid}](https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/)")
                    if doi:
                        link_row.append(f"DOI: [{doi}](https://doi.org/{doi})")
                    if url:
                        link_row.append(f"[Repository Link ↗]({url})")
                    if link_row:
                        st.markdown(" | ".join(link_row))

                    if abstract:
                        st.markdown("##### Abstract Preview")
                        st.markdown(f"> *{abstract[:800]}...*")

        if not has_ext:
            st.info("No external literature records available for this query.")


def render_agent_details_inspection(result: Any) -> None:
    """Render granular inspection views for each of the four agents."""
    timings = _val(result, "stage_timings_ms", {}) or {}
    errors = _val(result, "stage_errors", {}) or {}

    st.markdown("### Granular Scientific Agent Telemetry")
    st.caption("Deep inspection of intermediate outputs, timings, model payloads, and stage errors.")

    a1, a2, a3, a4 = st.tabs([
        "1. Knowledge Retrieval",
        "2. Chemistry & Pharmacology",
        "3. Literature Verification",
        "4. Scientific Quality Review",
    ])

    with a1:
        st.markdown(f"**Stage Duration:** `{timings.get('agent1', 'N/A')} ms`")
        assessment = _val(result, "retrieval_assessment", {}) or {}
        st.json(assessment)
        if "agent1" in errors:
            st.error(f"Agent 1 Failure: {errors['agent1']}")

    with a2:
        interpretation = _val(result, "interpretation")
        st.markdown(f"**Stage Duration:** `{timings.get('agent2', 'N/A')} ms`")
        if interpretation:
            st.markdown(f"**Model:** `{_val(interpretation, 'model', 'N/A')}`")
            st.markdown(f"**Status:** `{_val(interpretation, 'status', 'N/A')}`")
            claims = _val(interpretation, "claims", []) or []
            st.markdown(f"**Claims Generated:** {len(claims)}")
            for c in claims:
                st.markdown(f"- **{_val(c, 'claim_id')}** [{_val(c, 'claim_type')}]: {_val(c, 'text')}")
                st.caption(f"Evidence References: {', '.join(_val(c, 'evidence_ids', []))}")
            warnings = _val(interpretation, "warnings", [])
            if warnings:
                st.warning("\n".join(warnings))
        if "agent2" in errors:
            st.error(f"Agent 2 Failure: {errors['agent2']}")

    with a3:
        verification = _val(result, "verification")
        st.markdown(f"**Stage Duration:** `{timings.get('agent3', 'N/A')} ms`")
        if verification:
            st.markdown(f"**Status:** `{_val(verification, 'status', 'N/A')}`")
            v_claims = _val(verification, "claims", []) or []
            for vc in v_claims:
                st.markdown(f"- **Claim:** `{_val(vc, 'claim_id')}` | **Status:** `{_val(vc, 'status')}`")
                st.caption(f"Query: `{_val(vc, 'query')}`")
            v_warns = _val(verification, "warnings", [])
            if v_warns:
                st.info("\n".join(v_warns))
        if "agent3" in errors:
            st.error(f"Agent 3 Failure: {errors['agent3']}")

    with a4:
        judgment = _val(result, "judgment")
        st.markdown(f"**Stage Duration:** `{timings.get('agent4', 'N/A')} ms`")
        if judgment:
            st.markdown(f"**Model:** `{_val(judgment, 'model', 'llama3.2:3b')}`")
            st.markdown(f"**Status:** `{_val(judgment, 'status', 'N/A')}`")
            j_claims = _val(judgment, "claims", []) or []
            for jc in j_claims:
                st.markdown(f"- **Claim:** `{_val(jc, 'claim_id')}` -> **{_val(jc, 'decision')}**")
                st.markdown(f"  *Rationale:* {_val(jc, 'rationale')}")
            reasons = _val(judgment, "reasons", [])
            if reasons:
                st.caption("Review notes:\n" + "\n".join(f"- {r}" for r in reasons))
        if "agent4" in errors:
            st.error(f"Agent 4 Failure: {errors['agent4']}")

