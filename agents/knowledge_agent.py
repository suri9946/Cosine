
import hashlib
import re
from pathlib import Path
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from agents.document_ingestion import ingest_corpus, write_extraction_report
from agents.knowledge_graph import build_evidence_graph, write_graph
from agents.chemical_processing import chemical_evidence_documents, write_chemical_report


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "research" / "paracetamol"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
DEFAULT_TOP_K = 5
RRF_K = 60


# ============================================================
# TEXT NORMALIZATION AND TOKENIZATION
# ============================================================

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been",
    "being", "of", "to", "in", "on", "for", "and", "or", "with",
    "by", "from", "at", "as", "it", "its", "this", "that", "these",
    "those", "what", "which", "who", "how", "does", "do", "did",
    "can", "could", "would", "should", "explain", "describe",
    "tell", "me", "about", "please", "give", "show", "find",
    "according", "document", "documents", "passage", "drug", "drugs",
}

DRUG_ALIASES = {
    "paracetamol": [
        "paracetamol",
        "acetaminophen",
        "apap",
    ],
    "acetaminophen": [
        "acetaminophen",
        "paracetamol",
        "apap",
    ],
}

REFERENCE_MARKERS = {
    "references",
    "bibliography",
    "further reading",
    "suggested reading",
    "selected references",
    "reference list",
}

# Phrases that commonly indicate a passage is about a different
# drug or a different clinical topic, rather than the requested drug.
OTHER_DRUGS = {
    "baclofen",
    "tranylcypromine",
    "aprepitant",
}

# Explicit signals for common question types.
TOPIC_TERMS = {
    "pharmacology": {
        "pharmacology", "pharmacological", "analgesic", "antipyretic",
        "analgesia", "fever", "pain relief", "therapeutic effect",
    },
    "chemical_properties": {
        "molecular formula", "molecular weight", "canonical smiles", "smiles",
        "inchi", "inchikey", "chemical structure", "molecular structure",
        "structure", "3d", "2d", "atoms", "bonds",
    },
    "mechanism": {
        "mechanism",
        "action",
        "inhibits",
        "inhibit",
        "inhibition",
        "blocks",
        "block",
        "blocking",
        "activates",
        "activate",
        "activation",
        "binds",
        "binding",
        "receptor",
        "receptors",
        "enzyme",
        "enzymes",
        "transporter",
        "transporters",
        "reuptake",
        "cyclooxygenase",
        "prostaglandin",
        "prostaglandins",
        "synthesis",
        "pathway",
        "serotonin",
        "norepinephrine",
        "dopamine",
        "cox",
    },
    "pharmacokinetics": {
        "absorption",
        "distribution",
        "metabolism",
        "excretion",
        "clearance",
        "bioavailability",
        "half-life",
        "half life",
        "pharmacokinetics",
        "volume of distribution",
        "hepatic",
        "renal",
    },
    "side_effects": {
        "side effect",
        "side effects",
        "adverse effect",
        "adverse effects",
        "toxicity",
        "contraindication",
        "contraindications",
        "precaution",
        "precautions",
        "warning",
        "warnings",
        "long term",
        "long-term",
        "chronic",
        "kill",
        "fatal",
        "death",
        "liver injury",
        "overdose",
        "harm",
    },
    "solubility": {
        "solubility",
        "dissolution",
        "soluble",
        "dissolve",
        "dissolving",
        "aqueous",
        "permeability",
    },
}

# The drug must be connected to an action, target, or mechanism.
# These patterns are deliberately more specific than generic words
# such as "effect", "activity", or "treatment".
MECHANISM_PATTERNS = [
    r"\binhibits?\b",
    r"\binhibition of\b",
    r"\bblocks?\b",
    r"\bblockade of\b",
    r"\bactivates?\b",
    r"\bactivation of\b",
    r"\bbinds?\b",
    r"\bbinding to\b",
    r"\binteracts? with\b",
    r"\bantagonis(?:t|es|m)\b",
    r"\bagonis(?:t|ts|m)\b",
    r"\bprevents?\b",
    r"\breduces?\b",
    r"\bdecreases?\b",
    r"\bincreases?\b",
    r"\bimpairs?\b",
    r"\bmodulates?\b",
    r"\bmediates?\b",
    r"\bblocks? the\b",
    r"\bcyclooxygenase\b",
    r"\bprostaglandin synthesis\b",
    r"\bserotonin reuptake\b",
    r"\bnorepinephrine reuptake\b",
    r"\bmembrane pump\b",
    r"\bmechanism of action\b",
    r"\bmechanism remains unclear\b",
    r"\bmechanism is unclear\b",
    r"\bexact mechanism\b",
]

# Content signals that often indicate warnings, adverse effects,
# medication tables, or pharmacokinetics rather than mechanism.
NON_MECHANISM_HEADINGS = [
    "medication grid",
    "nursing considerations",
    "nursing interventions",
    "patient education",
    "adverse effects",
    "side effects",
    "contraindications",
    "drug interactions",
    "pharmacokinetics",
    "absorption and distribution",
    "metabolism and excretion",
    "dosage and administration",
    "dose and administration",
]


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalized_text(text: str) -> str:
    """Normalize text for case-insensitive comparison."""
    text = text.lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    """Tokenize text and remove common stop words."""
    text = normalized_text(text)
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text)

    return [
        token for token in tokens
        if token not in STOP_WORDS and len(token) > 1
    ]


def get_question_topic(question: str) -> str:
    """Infer the topic being asked about."""
    q = normalized_text(question)

    if any(term in q for term in [
        "molecular formula", "molecular weight", "canonical smiles", "smiles",
        "inchi", "molecular structure", "chemical structure", "3d structure",
        "structure of", "explain the structure", "describe the structure",
    ]):
        return "chemical_properties"

    if any(term in q for term in ["pharmacology", "pharmacological", "analgesic", "antipyretic", "analgesia"]):
        return "pharmacology"

    if any(term in q for term in [
        "mechanism of action",
        "mode of action",
        "how does",
        "how do",
        "what does it do",
        "pharmacological action",
    ]):
        return "mechanism"

    if any(term in q for term in [
        "pharmacokinetic",
        "absorption",
        "distribution",
        "metabolism",
        "excretion",
        "bioavailability",
        "half-life",
        "half life",
        "clearance",
    ]):
        return "pharmacokinetics"

    if any(term in q for term in [
        "side effect",
        "adverse effect",
        "toxicity",
        "contraindication",
        "warning",
        "precaution",
        "safety",
        "long term",
        "long-term",
        "chronic use",
        "kill humans",
        "kill a person",
        "fatal",
        "death",
        "liver injury",
        "overdose",
    ]):
        return "side_effects"

    if any(term in q for term in [
        "solubility",
        "dissolution",
        "dissolve",
        "soluble",
    ]):
        return "solubility"

    return "general"


def extract_drug_name(question: str) -> str | None:
    """
    Extract the requested drug name.

    Explicit forms such as 'drug called Zenthoral' are checked first
    so an unknown drug name is not silently replaced by another name.
    """
    q = question.strip()

    patterns = [
        r"\bdrug\s+(?:called|named)\s+([A-Za-z][A-Za-z0-9-]*)",
        r"\bmedication\s+(?:called|named)\s+([A-Za-z][A-Za-z0-9-]*)",
        r"\bmedicine\s+(?:called|named)\s+([A-Za-z][A-Za-z0-9-]*)",
        r"\b(?:mechanism|action|effects?|pharmacokinetics)\s+of\s+"
        r"([A-Za-z][A-Za-z0-9-]*)",
        r"\bhow\s+does\s+([A-Za-z][A-Za-z0-9-]*)\b",
        r"\bwhat\s+is\s+the\s+mechanism\s+of\s+([A-Za-z][A-Za-z0-9-]*)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, q, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .,:;?!")
            if candidate.lower() not in STOP_WORDS:
                return candidate

    # Handle common alias names even when the wording differs.
    q_lower = normalized_text(q)
    for canonical, aliases in DRUG_ALIASES.items():
        if any(
            re.search(r"\b" + re.escape(alias) + r"\b", q_lower)
            for alias in aliases
        ):
            return canonical

    return None


def get_drug_aliases(drug_name: str | None) -> list[str]:
    if not drug_name:
        return []

    key = normalized_text(drug_name)

    if key in DRUG_ALIASES:
        return DRUG_ALIASES[key]

    # If the extracted name is an alias of a known canonical name,
    # return the entire alias group.
    for canonical, aliases in DRUG_ALIASES.items():
        if key in aliases:
            return aliases

    return [key]


def contains_term(text: str, term: str) -> bool:
    """Match a whole term rather than a substring."""
    return bool(
        re.search(
            r"(?<![a-z0-9])" + re.escape(term.lower()) +
            r"(?![a-z0-9])",
            normalized_text(text),
        )
    )


def passage_mentions_drug(
    text: str,
    aliases: list[str],
) -> bool:
    return any(contains_term(text, alias) for alias in aliases)


def extract_question_topic_terms(question: str) -> set[str]:
    """
    Return relevant terms for the inferred topic.
    Stop words and generic question wording are excluded.
    """
    topic = get_question_topic(question)

    if topic in TOPIC_TERMS:
        return set(TOPIC_TERMS[topic])

    return set()


def get_sentences(text: str) -> list[str]:
    """Split passage text into approximate sentences."""
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]


def sentence_mentions_alias(
    sentence: str,
    aliases: list[str],
) -> bool:
    return passage_mentions_drug(sentence, aliases)


def has_mechanism_pattern(text: str) -> bool:
    text = normalized_text(text)
    return any(
        re.search(pattern, text)
        for pattern in MECHANISM_PATTERNS
    )


def is_probable_reference_passage(text: str) -> bool:
    text_normalized = normalized_text(text)

    if any(
        marker in text_normalized
        for marker in REFERENCE_MARKERS
    ):
        return True

    # Many bibliography passages contain a high density of years,
    # DOI strings, journal citations, and numbered references.
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if len(lines) < 3:
        return False

    citation_like = 0

    for line in lines:
        if (
            re.search(r"\b(19|20)\d{2}\b", line)
            and (
                re.search(r"\bdoi\b|10\.\d{4,9}/", line, re.I)
                or re.search(r"\bet al\.", line, re.I)
                or re.search(r"\bvol(?:ume)?\.?\s*\d+", line, re.I)
            )
        ):
            citation_like += 1

    return citation_like >= 3


def looks_like_non_mechanism_content(text: str) -> bool:
    """
    Avoid labelling medication tables, warnings, side-effect lists,
    or pharmacokinetics passages as direct mechanism evidence.
    """
    text_normalized = normalized_text(text)

    for heading in NON_MECHANISM_HEADINGS:
        if heading in text_normalized:
            return True

    return False


def sentence_has_requested_topic(sentence: str, topic: str) -> bool:
    """Check whether a sentence has terms relevant to the topic."""
    terms = TOPIC_TERMS.get(topic, set())

    if not terms:
        return True

    text = normalized_text(sentence)

    return any(contains_term(text, term) for term in terms)


# ============================================================
# EVIDENCE CLASSIFICATION
# ============================================================

def classify_passage(
    text: str,
    question: str,
    drug_name: str | None,
) -> dict[str, Any]:
    """
    Conservatively classify a passage.

    DIRECT_EVIDENCE_CANDIDATE is only a retrieval label. It does
    not mean that the claim has been scientifically validated.

    For mechanism questions, the requested drug must appear in
    the same sentence as a mechanism/action signal. A narrow
    exception allows a sentence pair when the text explicitly
    introduces the drug's mechanism and immediately describes
    that mechanism in the next sentence.
    """
    passage = text or ""
    passage_norm = normalized_text(passage)
    topic = get_question_topic(question)
    aliases = get_drug_aliases(drug_name)

    drug_match = passage_mentions_drug(passage, aliases)
    topic_terms = extract_question_topic_terms(question)

    matched_terms = sorted({
        term for term in topic_terms
        if contains_term(passage, term)
    })

    result = {
        "evidence_type": "WEAK_MATCH",
        "classification_reason": "No sufficiently specific evidence signal found.",
        "drug_match": drug_match,
        "topic_match": bool(matched_terms),
        "matched_terms": matched_terms,
    }

    if is_probable_reference_passage(passage):
        result["evidence_type"] = "WEAK_MATCH"
        result["classification_reason"] = (
            "Likely reference-list or bibliography text."
        )
        return result

    if topic == "mechanism":
        sentences = get_sentences(passage)

        # A warning/table/PK passage should not be promoted to
        # direct mechanism evidence simply because it mentions
        # the drug and has generic action-related words.
        non_mechanism_content = looks_like_non_mechanism_content(
            passage
        )

        direct_sentence_found = False
        direct_reason = ""

        # Strongest case: drug and mechanism signal occur together
        # in one sentence.
        for sentence in sentences:
            sentence_has_drug = sentence_mentions_alias(
                sentence, aliases
            )
            sentence_has_action = has_mechanism_pattern(sentence)
            sentence_has_topic = sentence_has_requested_topic(
                sentence, "mechanism"
            )

            # Explicitly exclude sentences whose main subject is
            # another named drug, where that is clear from the text.
            mentions_other_drug = any(
                contains_term(sentence, other_drug)
                for other_drug in OTHER_DRUGS
            )

            if (
                sentence_has_drug
                and sentence_has_action
                and sentence_has_topic
                and not mentions_other_drug
                and not non_mechanism_content
            ):
                direct_sentence_found = True
                direct_reason = (
                    "Requested drug and mechanism-related wording "
                    "occur in the same sentence."
                )
                break

        # Narrow exception for split sentences such as:
        # "The exact mechanism of acetaminophen remains unclear.
        #  It may involve the cyclooxygenase pathway..."
        #
        # The first sentence must mention the requested drug and
        # explicitly introduce its mechanism; the next sentence
        # must contain a mechanism signal. Do not use this for
        # table/warning/PK content.
        if not direct_sentence_found and not non_mechanism_content:
            for index in range(len(sentences) - 1):
                current_sentence = sentences[index]
                next_sentence = sentences[index + 1]

                current_mentions_drug = sentence_mentions_alias(
                    current_sentence, aliases
                )
                current_introduces_mechanism = bool(
                    re.search(
                        r"\b(exact\s+)?mechanism(?:\s+of\s+action)?\b",
                        normalized_text(current_sentence),
                    )
                )

                next_has_mechanism = has_mechanism_pattern(
                    next_sentence
                )
                next_has_topic = sentence_has_requested_topic(
                    next_sentence, "mechanism"
                )

                if (
                    current_mentions_drug
                    and current_introduces_mechanism
                    and next_has_mechanism
                    and next_has_topic
                ):
                    direct_sentence_found = True
                    direct_reason = (
                        "The requested drug is explicitly linked to "
                        "its mechanism in adjacent sentences."
                    )
                    break

        if direct_sentence_found:
            result["evidence_type"] = "DIRECT_EVIDENCE_CANDIDATE"
            result["classification_reason"] = direct_reason
            return result

        if drug_match:
            result["evidence_type"] = "DRUG_SPECIFIC_CONTEXT"

            if non_mechanism_content:
                result["classification_reason"] = (
                    "The requested drug appears in content that looks "
                    "like a warning, medication table, side-effect, "
                    "or pharmacokinetics passage; not direct mechanism "
                    "evidence."
                )
            else:
                result["classification_reason"] = (
                    "The requested drug is mentioned, but the passage "
                    "does not directly connect it to a mechanism."
                )

            return result

        if has_mechanism_pattern(passage) and matched_terms:
            result["evidence_type"] = "SUPPORTING_CONTEXT"
            result["classification_reason"] = (
                "The passage discusses mechanisms but does not mention "
                "the requested drug."
            )
            return result

        result["classification_reason"] = (
            "The passage does not directly establish the requested "
            "drug's mechanism of action."
        )
        return result

    # For other question types, require both a drug mention and
    # topic-specific content before considering the passage direct.
    if topic in TOPIC_TERMS:
        if drug_match and matched_terms:
            result["evidence_type"] = "DIRECT_EVIDENCE_CANDIDATE"
            result["classification_reason"] = (
                "The requested drug and topic-related terms appear "
                "in the same passage. Manual verification is required."
            )
        elif drug_match:
            result["evidence_type"] = "DRUG_SPECIFIC_CONTEXT"
            result["classification_reason"] = (
                "The requested drug appears, but the requested topic "
                "is not clearly supported."
            )
        elif matched_terms:
            result["evidence_type"] = "SUPPORTING_CONTEXT"
            result["classification_reason"] = (
                "The passage discusses the topic but does not mention "
                "the requested drug."
            )

        return result

    if drug_match:
        result["evidence_type"] = "DRUG_SPECIFIC_CONTEXT"
        result["classification_reason"] = (
            "The passage mentions the requested drug; relevance "
            "to the full question needs manual verification."
        )
    else:
        result["evidence_type"] = "SUPPORTING_CONTEXT"
        result["classification_reason"] = (
            "Potentially useful background, but no requested-drug "
            "mention was found."
        )

    return result


# ============================================================
# KNOWLEDGE AGENT
# ============================================================

class KnowledgeAgent:
    def __init__(
        self,
        documents_dir: Path | str = DOCUMENTS_DIR,
        model_name: str = MODEL_NAME,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        top_k: int = DEFAULT_TOP_K,
    ):
        self.documents_dir = Path(documents_dir)
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

        self.embedding_model = None
        self.documents = []
        self.chunks = []
        self.embeddings = None
        self.bm25 = None
        self.bm25_tokens = []

    def load_documents(self) -> int:
        """Ingest the local paracetamol corpus, split, embed, and index."""
        if not self.documents_dir.exists():
            raise FileNotFoundError(
                f"Documents folder not found: {self.documents_dir}"
            )

        corpus_root = self.documents_dir.resolve()
        chunks_cache_file = PROJECT_ROOT / "data" / "processed" / "corpus_chunks.pkl"
        if corpus_root == DOCUMENTS_DIR.resolve():
            project_root = PROJECT_ROOT
            source_records = None
            if chunks_cache_file.exists():
                try:
                    import pickle
                    with open(chunks_cache_file, "rb") as f:
                        source_records, extraction_report = pickle.load(f)
                    self.extraction_report = extraction_report
                except Exception:
                    source_records = None

            if source_records is None:
                print(f"Loading paracetamol PDF/TXT/XML sources under {corpus_root}...")
                source_records, extraction_report = ingest_corpus(project_root)
                source_records.extend(chemical_evidence_documents(project_root))
                write_chemical_report(project_root)
                self.extraction_report = extraction_report
                write_extraction_report(
                    extraction_report,
                    PROJECT_ROOT / "data" / "processed" / "extraction_report.json",
                )
                graph = build_evidence_graph(source_records)
                write_graph(graph, PROJECT_ROOT / "data" / "processed" / "evidence_graph.json")
                try:
                    import pickle
                    with open(chunks_cache_file, "wb") as f:
                        pickle.dump((source_records, extraction_report), f)
                except Exception:
                    pass
        else:
            # Preserve the legacy custom-PDF-directory entry point.
            pdf_files = sorted(corpus_root.rglob("*.pdf"))
            source_records = []
            for pdf_path in pdf_files:
                try:
                    for page in PyPDFLoader(str(pdf_path)).load():
                        page_num = int(page.metadata.get("page", 0)) + 1
                        source_records.append(Document(
                            page_content=page.page_content,
                            metadata={"source": pdf_path.name, "local_path": str(pdf_path),
                                      "page": page_num, "section": "", "source_id": "",
                                      "source_url": "", "license_reuse": "",
                                      "extractor": "PyPDFLoader", "quality_status": "legacy_custom_pdf"},
                        ))
                except Exception as exc:
                    print(f"  WARNING: Could not load {pdf_path.name}: {exc}")
            extraction_report = {"legacy_custom_pdf_directory": str(corpus_root)}
            self.extraction_report = extraction_report
        all_pages = [
            record if isinstance(record, Document) else Document(page_content=record.page_content, metadata=record.metadata)
            for record in source_records
        ]

        if not all_pages:
            raise RuntimeError(
                "No PDF/TXT/XML text could be extracted from the corpus."
            )

        self.documents = all_pages

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        self.chunks = splitter.split_documents(all_pages)

        # Remove empty chunks.
        self.chunks = [
            chunk for chunk in self.chunks
            if chunk.page_content.strip()
        ]

        if not self.chunks:
            raise RuntimeError(
                "PDFs loaded, but no non-empty text chunks were produced."
            )

        print(f"Loaded {len(all_pages)} page(s).")
        print(f"Created {len(self.chunks)} text chunk(s).")
        print(f"Loading embedding model: {self.model_name}")

        texts = [
            normalized_text(chunk.page_content)
            for chunk in self.chunks
        ]

        cache_dir = PROJECT_ROOT / 'data' / 'processed'
        cache_path = cache_dir / 'corpus_embeddings_cache.npz'
        content_hash = hashlib.sha256(''.join(texts).encode('utf-8')).hexdigest()

        loaded_from_cache = False
        if cache_path.exists():
            try:
                cached = np.load(cache_path, allow_pickle=True)
                if str(cached.get('hash', '')) == content_hash:
                    self.embeddings = cached['embeddings']
                    loaded_from_cache = True
                    print(f'Loaded {len(self.embeddings)} embeddings from persistent cache.')
            except Exception:
                loaded_from_cache = False

        self.embedding_model = SentenceTransformer(self.model_name)

        if not loaded_from_cache:
            self.embeddings = self.embedding_model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=True,
            )
            try:
                np.savez_compressed(cache_path, embeddings=self.embeddings, hash=content_hash)
            except Exception:
                pass

        self.bm25_tokens = [tokenize(text) for text in texts]
        self.bm25 = BM25Okapi(self.bm25_tokens)

        print("Knowledge base is ready.")
        return len(self.chunks)

    def _semantic_search(self, question: str) -> np.ndarray:
        query_embedding = self.embedding_model.encode(
            [normalized_text(question)],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        # Embeddings are normalized, so cosine similarity can be
        # calculated using the dot product.
        return cosine_similarity(
            query_embedding,
            self.embeddings,
        )[0]

    def _keyword_search(self, question: str) -> np.ndarray:
        query_tokens = tokenize(question)

        if not query_tokens:
            return np.zeros(len(self.chunks), dtype=float)

        scores = self.bm25.get_scores(query_tokens)
        return np.asarray(scores, dtype=float)

    def search(
        self,
        question: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Run semantic + BM25 hybrid retrieval."""
        if self.embedding_model is None or self.bm25 is None:
            raise RuntimeError(
                "Knowledge base is not loaded. Call load_documents() first."
            )

        if not question.strip():
            return []

        result_count = top_k or self.top_k

        semantic_scores = self._semantic_search(question)
        keyword_scores = self._keyword_search(question)

        semantic_ranking = np.argsort(semantic_scores)[::-1]
        keyword_ranking = np.argsort(keyword_scores)[::-1]

        semantic_ranks = np.empty(len(self.chunks), dtype=int)
        keyword_ranks = np.empty(len(self.chunks), dtype=int)

        semantic_ranks[semantic_ranking] = np.arange(
            1, len(self.chunks) + 1
        )
        keyword_ranks[keyword_ranking] = np.arange(
            1, len(self.chunks) + 1
        )

        drug_name = extract_drug_name(question)
        aliases = get_drug_aliases(drug_name)

        results = []

        for index, chunk in enumerate(self.chunks):
            text = chunk.page_content

            semantic_rank = int(semantic_ranks[index])
            keyword_rank = int(keyword_ranks[index])

            rrf_score = (
                1.0 / (RRF_K + semantic_rank)
                + 1.0 / (RRF_K + keyword_rank)
            )

            classification = classify_passage(
                text=text,
                question=question,
                drug_name=drug_name,
            )

            drug_match = classification["drug_match"]

            # Small ranking bonus for exact drug mentions. This is
            # a ranking aid, not a measure of scientific validity.
            drug_bonus = 0.0005 if drug_match else 0.0

            results.append({
                "source": chunk.metadata.get("source", "unknown"),
                "page": chunk.metadata.get("page", "unknown"),
                "source_id": chunk.metadata.get("source_id", ""),
                "source_path": chunk.metadata.get("local_path", ""),
                "source_url": chunk.metadata.get("source_url", ""),
                "source_title": chunk.metadata.get("title", ""),
                "authors": chunk.metadata.get("authors", ""),
                "doi": chunk.metadata.get("doi", ""),
                "pmid": chunk.metadata.get("pmid", ""),
                "pmcid": chunk.metadata.get("pmcid", ""),
                "license_reuse": chunk.metadata.get("license_reuse", ""),
                "version_date": chunk.metadata.get("version_date", ""),
                "section": chunk.metadata.get("section", ""),
                "extractor": chunk.metadata.get("extractor", ""),
                "quality_status": chunk.metadata.get("quality_status", ""),
                "evidence_id": hashlib.sha256(
                    (str(chunk.metadata.get("source_id", "")) + "|"
                     + str(chunk.metadata.get("local_path", "")) + "|"
                     + str(chunk.metadata.get("page", "")) + "|" + text).encode("utf-8")
                ).hexdigest()[:20],
                "semantic_score": float(semantic_scores[index]),
                "keyword_score": float(keyword_scores[index]),
                "hybrid_score": float(rrf_score),
                "adjusted_score": float(rrf_score + drug_bonus),
                "evidence_type": classification["evidence_type"],
                "classification_reason": (
                    classification["classification_reason"]
                ),
                "drug_match": classification["drug_match"],
                "topic_match": classification["topic_match"],
                "matched_terms": classification["matched_terms"],
                "text": text,
            })

        # Prioritize evidence category, then retrieval relevance.
        # These categories are provisional labels and not validated
        # scientific judgments.
        priority = {
            "DIRECT_EVIDENCE_CANDIDATE": 0,
            "DRUG_SPECIFIC_CONTEXT": 1,
            "SUPPORTING_CONTEXT": 2,
            "WEAK_MATCH": 3,
        }

        results.sort(
            key=lambda item: (
                priority.get(item["evidence_type"], 4),
                -item["adjusted_score"],
            )
        )

        return results[:result_count]

    def assess_evidence(
        self,
        question: str,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Decide whether retrieval found a candidate passage.
        This does not verify scientific truth or clinical validity.
        """
        if not results:
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "reason": "No relevant passages were retrieved.",
                "drug": extract_drug_name(question),
                "topic": get_question_topic(question),
                "direct_candidates": 0,
                "drug_specific_context": 0,
            }

        direct_candidates = [
            result for result in results
            if result["evidence_type"] == "DIRECT_EVIDENCE_CANDIDATE"
        ]

        drug_context = [
            result for result in results
            if result["evidence_type"] == "DRUG_SPECIFIC_CONTEXT"
        ]

        drug_name = extract_drug_name(question)

        if direct_candidates:
            status = "RETRIEVAL_RELEVANT_REVIEW_REQUIRED"
            reason = (
                "Potentially relevant passages were found. Review the "
                "original source and verify the claim before using it."
            )
        elif drug_context:
            status = "INSUFFICIENT_EVIDENCE"
            reason = (
                "The drug appears in retrieved material, but no passage "
                "directly establishes the requested topic. Treat as "
                "insufficient evidence and abstain from a substantive answer."
            )
        else:
            status = "INSUFFICIENT_EVIDENCE"
            reason = (
                "The retrieved passages do not sufficiently establish "
                "the requested drug-specific claim."
            )

        return {
            "status": status,
            "reason": reason,
            "drug": drug_name,
            "topic": get_question_topic(question),
            "direct_candidates": len(direct_candidates),
            "drug_specific_context": len(drug_context),
        }
