"""Integrated Best Life AI research console; legacy retrieval console remains in main.py."""

from typing import Any

from agents.orchestrator import ResearchOrchestrator


def _value(item: Any, key: str, default: Any = None) -> Any:
    return item.get(key, default) if isinstance(item, dict) else getattr(item, key, default)


def display_result(result: Any) -> None:
    errors = getattr(result, "stage_errors", {}) or {}

    def stage_label(stage: str, value: Any, default: str) -> str:
        error = errors.get(stage)
        if error:
            return f"FAILED ({error})"
        return str(_value(value, "status", default))

    print(f"\nDecision: {result.status}")
    print(f"Agent 1 retrieval: {stage_label('agent1', result.retrieval_assessment, 'unavailable')}")
    print(f"Agent 2 interpretation: {stage_label('agent2', result.interpretation, 'not run')}")
    print(f"Agent 3 literature search: {stage_label('agent3', result.verification, 'not run')}")
    print(f"Agent 4 judgment: {stage_label('agent4', result.judgment, 'not run')}")
    timings = getattr(result, "stage_timings_ms", {}) or {}
    if timings:
        print("Stage timings (ms): " + ", ".join(f"{stage}={duration}" for stage, duration in timings.items()))
    claims = _value(result.interpretation, "claims", []) or []
    for warning in (_value(result.interpretation, "warnings", []) or []):
        print(f"Agent 2 note: {warning}")
    if claims:
        print("\nAgent 2 claims:")
        for claim in claims:
            refs = ", ".join(_value(claim, "evidence_ids", []) or []) or "none"
            print(f"  {_value(claim, 'claim_id', '')} [{_value(claim, 'claim_type', 'unknown')}]: "
                  f"{_value(claim, 'text', '')}")
            print(f"    Evidence IDs: {refs}")
    external = _value(result.verification, "claims", []) or []
    if external:
        print("\nAgent 3 literature candidates (not proof of claim support):")
        for item in external:
            print(f"  {_value(item, 'claim_id', '')}: {_value(item, 'status', 'unknown')}")
            for record in (_value(item, "records", []) or []):
                print(f"    {_value(record, 'provider', '')}: {_value(record, 'title', '')}")
                ids = [f"PMID {_value(record, 'pmid', '')}" if _value(record, 'pmid') else "",
                       f"PMCID {_value(record, 'pmcid', '')}" if _value(record, 'pmcid') else "",
                       f"DOI {_value(record, 'doi', '')}" if _value(record, 'doi') else ""]
                print(f"      {'; '.join(x for x in ids if x) or 'No stable identifier recorded'}")
                print(f"      URL: {_value(record, 'source_url', '') or 'not recorded'}")
    if result.answer:
        print(f"\nReviewed claims:\n{result.answer}")
    elif result.status == "ABSTAIN":
        print("\nInsufficient evidence for a reviewed answer.")
    judgments = _value(result.judgment, "claims", []) or []
    if judgments:
        print("\nAgent 4 claim decisions:")
        for item in judgments:
            print(f"  {_value(item, 'claim_id', '')}: {_value(item, 'decision', 'unknown')} — "
                  f"{_value(item, 'rationale', '')}")
            for warning in (_value(item, "warnings", []) or []):
                print(f"    Warning: {warning}")
    for item in result.evidence:
        print(f"\nEvidence {_value(item, 'evidence_id', '')}: "
              f"{_value(item, 'source_title') or _value(item, 'source')}")
        print(f"  Source ID: {_value(item, 'source_id') or 'not recorded'}")
        print(f"  URL: {_value(item, 'source_url') or 'not recorded'}")
        print(f"  Location: page {_value(item, 'page', 'unknown')} {_value(item, 'section', '')}")
    for stage, error in errors.items():
        print(f"Stage issue: {stage} ({error})")
    for reason in (_value(result.judgment, "reasons", []) or []):
        print(f"Review note: {reason}")
    print(f"Audit record: {result.audit_path or 'not written'}")
    print("Model decisions and retrieval are research aids, not scientific or clinical validation.")


def main() -> None:
    print("BEST LIFE AI — PARACETAMOL RESEARCH CONSOLE")
    print("Loads the local corpus, then runs retrieval, interpretation, literature search and review.")
    system = ResearchOrchestrator()
    try:
        count = system.retriever.load_documents()
    except Exception as exc:
        print(f"Could not load the local research corpus ({type(exc).__name__}).")
        return
    print(f"Local corpus ready ({count} chunks). Enter a question, or type 'exit'.")
    while True:
        try:
            question = input("\nQuestion: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if question.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        if not question:
            print("Enter a question to begin.")
            continue
        print("Running the four research stages...")
        result = system.run(question)
        display_result(result)


if __name__ == "__main__":
    main()
