# Known Issues and Limitations

## Agent 1 implementation

- The ten text-empty FDA-label pages are repeated image pages: pypdfium2 rendered pages 2â€“11 to identical pixel hashes. Tesseract output for one unique page is imperfect and remains excluded from retrieval pending human proofreading.
- Four MedlinePlus PDFs have identical full extracted text, but their different byte hashes and timestamps do not prove distinct versions. All originals remain; one canonical text copy is indexed.
- Retrieval assessment is heuristic. Benchmark relevance uses expected terms and source/page metadata; it does not verify scientific claim accuracy, source quality, or clinical safety.
- The benchmark is small (8 answerable, 2 absent questions) and currently covers retrieval only. It needs broader phrasing, independently reviewed gold evidence, and contradiction cases before stronger performance claims.
- The knowledge graph records source/evidence provenance and lexical concept mentions only. It does not encode validated causal or mechanistic relations.
- Corpus coverage remains partial. See `data/research/paracetamol/metadata/source_coverage.csv`; no additional research documents were acquired during this implementation step.
- License/reuse conditions remain unknown or limited for some local reference sources. Their terms and URLs are passed through where recorded; no restricted source is redistributed.
- pypdfium2 and Tesseract can render/OCR scan pages, but OCR confidence is not used as a scientific quality score.
- Embedding generation currently runs during corpus load and can take about a minute on CPU. The model is cached locally; network access is unavailable, so evaluation was explicitly run offline.
- No persistent vector-index cache or incremental reindexing is implemented. BM25, embeddings and RRF are built in memory by the existing retrieval class.
- Advanced reranking and graph query features have not been validated; existing RRF and provisional candidate labels remain the retrieval behavior.

## Project boundaries

- Agent 1?4, orchestration and an integrated console have initial implementations. Broader system evaluation and acceptance remain in progress.
- The four-agent architecture remains the long-term target; this work does not implement multi-drug behavior.
- Agent 1 initial retrieval acceptance passed; that benchmark is not evidence of scientific correctness.

## Full-system implementation status

- Agent 2 has passed focused mocks and one live evidence-grounded call; this checks interface operation, not interpretation quality or scientific accuracy.
- Agent 3 live connectivity has been verified. Agent 4, orchestration and integrated console are implemented; integrated evaluation and acceptance remain pending.


## Agent 3 literature discovery

- Agent 3 read-only PubMed/Europe PMC search and four mocked checks are implemented. The initial restricted request failed with `ProxyError`; a later approved read-only call succeeded for both APIs and returned four metadata records. More restrictive environments can still yield partial/unavailable status.
- Public service use is designed to work without credentials; optional NCBI key/email are read from the local ignored .env. No credential was present or printed.
- Full text is not downloaded by this stage. Europe PMC candidate metadata and abstracts may be returned; open-access flags alone do not establish reuse permission, and each record's license must be checked before later text acquisition.


## Runtime resilience update — 2026-11-01

- Agent 3 depends on outbound PubMed and Europe PMC connectivity. Live requests can still time out or be blocked by the configured proxy. The system reports partial/unavailable verification and prevents global approval; API credentials do not resolve proxy/network failures.
- Local LLM output is nondeterministic. Agent 2 duplicate claims are collapsed when text and evidence IDs match. Agent 4 validates IDs, retries malformed output once, then returns an explicit safe `NEEDS_MORE_EVIDENCE` fallback rather than presenting the invalid response as a review.
- Live four-stage formula/structure run completed with Agent 3 partial and final `NEEDS_MORE_EVIDENCE`; Agent 4 did run. This is a successful resilience/plumbing check, not proof of scientific correctness.
- Retrieval intent routing now recognizes plain structure and long-term harm wording. Relevance still depends on the local corpus and conservative evidence classifier; unsupported or weakly grounded questions may correctly abstain.
- The latest live mechanism-question retest confirms both provider calls currently fail with `ProxyError`; a real successful literature-provider request requires correcting outbound proxy/network access outside the application. Local Agent 4 inference works but correctly abstains from a stronger conclusion.
