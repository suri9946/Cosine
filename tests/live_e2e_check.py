"""Live end-to-end integration test of COSIN pipeline with real Ollama and API connectors."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
from agents.orchestrator import ResearchOrchestrator


def main():
    print("=== COSIN LIVE END-TO-END SYSTEM INTEGRATION TEST ===")
    orchestrator = ResearchOrchestrator(top_k=5)
    print("Loading paracetamol corpus...")
    start_load = time.perf_counter()
    count = orchestrator.retriever.load_documents()
    print(f"Loaded {count} chunks in {time.perf_counter() - start_load:.2f}s.")

    events = []

    def on_progress(stage, status, details):
        print(f"[{stage.upper()}] Status -> {status.upper()}")
        events.append((stage, status, details))

    question = "What is the molecular formula and basic structure of paracetamol?"
    print(f"\nSubmitting research query: '{question}'")
    run = orchestrator.run(question, on_progress=on_progress)

    print("\n=== RUN COMPLETED ===")
    print(f"Request ID: {run.request_id}")
    print(f"Final Decision Status: {run.status}")
    print(f"Synthesized Answer: {run.answer}")
    print(f"Stage Timings: {run.stage_timings_ms}")
    print(f"Audit File: {run.audit_path}")

    assert run.request_id is not None
    assert run.status in {"APPROVED", "APPROVED_WITH_LIMITATIONS", "NEEDS_MORE_EVIDENCE", "PARTIAL", "ABSTAIN"}
    assert len(events) >= 4, "Expected telemetry events from all four stages"
    print("\n[PASS] Live End-to-End Test PASSED successfully!")


if __name__ == "__main__":
    main()
