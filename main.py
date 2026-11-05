
from agents.knowledge_agent import KnowledgeAgent


def display_result(index: int, result: dict) -> None:
    print("\n" + "-" * 80)
    print(f"RESULT {index}")
    print("-" * 80)
    print(f"Source:                 {result['source']}")
    print(f"Source ID:              {result.get('source_id') or 'not recorded'}")
    print(f"Page:                   {result['page']}")
    if result.get("section"):
        print(f"Section:                {result['section']}")
    if result.get("source_url"):
        print(f"Source URL:             {result['source_url']}")
    if result.get("doi"):
        print(f"DOI:                    {result['doi']}")
    if result.get("pmid"):
        print(f"PMID:                   {result['pmid']}")
    if result.get("license_reuse"):
        print(f"Reuse terms:            {result['license_reuse']}")
    if result.get("evidence_id"):
        print(f"Evidence ID:            {result['evidence_id']}")
    if result.get("quality_status"):
        print(f"Extraction quality:     {result['quality_status']}")
    print(f"Evidence type:          {result['evidence_type']}")
    print(f"Drug match:             {result['drug_match']}")
    print(f"Topic match:            {result['topic_match']}")
    print(f"Matched topic terms:    {result['matched_terms']}")
    print(f"Semantic score:         {result['semantic_score']:.4f}")
    print(f"BM25 score:             {result['keyword_score']:.4f}")
    print(f"Hybrid score:           {result['hybrid_score']:.4f}")
    print(f"Classification reason:  {result['classification_reason']}")
    print("\nRetrieved passage:")
    print(result["text"])


def main() -> None:
    print("=" * 80)
    print("BEST LIFE AI — SCIENTIFIC KNOWLEDGE AGENT")
    print("=" * 80)
    print("Loading the local paracetamol research corpus...\n")

    agent = KnowledgeAgent()

    try:
        chunk_count = agent.load_documents()
    except Exception as exc:
        print("\nERROR: The knowledge base could not be loaded.")
        print(f"Details: {exc}")
        print(
            "\nCheck that your PDFs are in data/documents and that "
            "your virtual environment has the required packages."
        )
        return

    print(f"\nReady. Indexed {chunk_count} text chunks.")
    print("Ask a question about the local paracetamol research corpus.")
    print("Type 'exit' to quit.")

    while True:
        try:
            question = input("\nYour question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Best Life AI.")
            break

        if question.lower() in {"exit", "quit"}:
            print("Exiting Best Life AI.")
            break

        if not question:
            print("Please enter a question.")
            continue

        try:
            results = agent.search(question, top_k=5)
            assessment = agent.assess_evidence(question, results)

            print("\n" + "=" * 80)
            print("RETRIEVAL ASSESSMENT")
            print("=" * 80)
            print(f"Status:                  {assessment['status']}")
            print(f"Requested drug:          {assessment['drug']}")
            print(f"Question topic:           {assessment['topic']}")
            print(f"Direct candidates:        {assessment['direct_candidates']}")
            print(f"Drug-specific passages:   {assessment['drug_specific_context']}")
            print(f"Reason:                   {assessment['reason']}")

            if not results:
                print("\nNo passages were retrieved.")
                continue

            for index, result in enumerate(results, start=1):
                display_result(index, result)

            print("\n" + "=" * 80)
            print("IMPORTANT")
            print(
                "Retrieval labels are preliminary. They do not establish "
                "that a scientific claim is correct, clinically safe, "
                "effective, or supported by sufficient evidence."
            )
            print(
                "Verify important claims against the cited source and "
                "have qualified experts review pharmaceutical conclusions."
            )
            print("=" * 80)

        except Exception as exc:
            print(f"\nSearch error: {exc}")


if __name__ == "__main__":
    main()
