"""Read-only PubMed and Europe PMC claim-oriented literature discovery."""

from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import requests
from dotenv import load_dotenv

from agents.ollama_client import PROJECT_ROOT


load_dotenv(PROJECT_ROOT / ".env", override=False)

NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
_STOP = {"about", "after", "against", "among", "because", "been", "being", "does", "from", "have",
         "into", "may", "more", "most", "other", "over", "should", "than", "that", "their", "there",
         "these", "this", "those", "through", "under", "using", "what", "when", "which", "while", "with",
         "the", "and", "for", "how", "is", "are", "of", "a", "an", "to", "in", "on", "at", "by",
         "it", "its", "local", "record", "records", "corpus", "listed", "describe", "described",
         "report", "reports", "review", "available", "about", "related", "paracetamol",
         "acetaminophen", "apap"}


@dataclass(frozen=True)
class LiteratureRecord:
    provider: str
    title: str
    authors: list[str]
    year: str
    journal: str
    doi: str
    pmid: str
    pmcid: str
    abstract: str
    source_url: str
    open_access: bool | None
    license: str | None
    full_text_downloaded: bool = False


@dataclass(frozen=True)
class ClaimVerification:
    claim_id: str
    status: str
    query: str
    records: list[dict[str, Any]]
    provider_errors: dict[str, str]


@dataclass(frozen=True)
class LiteratureVerificationResult:
    status: str
    claims: list[ClaimVerification]
    warnings: list[str]


class LiteratureVerificationAgent:
    """Search public indexes conservatively; discovery is not claim validation."""

    def __init__(self, *, session: requests.Session | None = None, timeout: tuple[float, float] = (5, 30),
                 max_results_per_provider: int = 5, min_interval: float | None = None) -> None:
        if max_results_per_provider < 1:
            raise ValueError("max_results_per_provider must be positive")
        self.session = session or requests.Session()
        self.timeout = timeout
        self.max_results = max_results_per_provider
        self.api_key = os.getenv("NCBI_API_KEY", "").strip()
        self.email = os.getenv("NCBI_EMAIL", "").strip()
        self.tool = os.getenv("NCBI_TOOL", "BestLifeAI").strip() or "BestLifeAI"
        self.min_interval = min_interval if min_interval is not None else (0.34 if self.api_key else 0.5)
        self._last_request = 0.0
        self._lock = threading.Lock()
        self.session.headers.update({"User-Agent": f"BestLifeAI/1.0 (literature search; tool={self.tool})"})

    @staticmethod
    def _query(text: str) -> str:
        words = re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text.lower())
        terms: list[str] = []
        for word in words:
            if word not in _STOP and word not in terms:
                terms.append(word)
            if len(terms) >= 5:
                break
        drug = '(paracetamol OR acetaminophen)'
        if not terms:
            return drug
        # A small number of representative terms avoids an unbounded query.
        return drug + " AND " + " AND ".join(f'"{term}"' for term in terms)

    def _get_json(self, url: str, params: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            wait = self.min_interval - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()
        response = self.session.get(url, params=dict(params), timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("API returned a JSON value with an unexpected shape")
        return payload

    def _ncbi_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {"tool": self.tool, "retmode": "json"}
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def _search_pubmed(self, query: str) -> list[LiteratureRecord]:
        params = self._ncbi_params()
        params.update({"db": "pubmed", "term": query, "retmax": self.max_results, "sort": "relevance"})
        search = self._get_json(f"{NCBI_EUTILS}/esearch.fcgi", params)
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        summary_params = self._ncbi_params()
        summary_params.update({"db": "pubmed", "id": ",".join(str(i) for i in ids)})
        summary = self._get_json(f"{NCBI_EUTILS}/esummary.fcgi", summary_params).get("result", {})
        records: list[LiteratureRecord] = []
        for pmid in summary.get("uids", ids):
            item = summary.get(str(pmid), {})
            if not isinstance(item, dict):
                continue
            authors = item.get("authors", [])
            records.append(LiteratureRecord(
                provider="PubMed", title=str(item.get("title", "")).strip(),
                authors=[str(a.get("name", "")) for a in authors if isinstance(a, dict) and a.get("name")],
                year=str(item.get("pubdate", ""))[:4], journal=str(item.get("fulljournalname", item.get("source", ""))),
                doi="", pmid=str(pmid), pmcid="", abstract="",
                source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", open_access=None, license=None,
            ))
        return records

    def _search_europe_pmc(self, query: str) -> list[LiteratureRecord]:
        params = {"query": query, "format": "json", "resultType": "core", "pageSize": self.max_results}
        payload = self._get_json(f"{EUROPE_PMC}/search", params)
        records: list[LiteratureRecord] = []
        for item in payload.get("resultList", {}).get("result", []):
            if not isinstance(item, dict):
                continue
            authors_text = str(item.get("authorString", ""))
            is_oa = item.get("isOpenAccess")
            records.append(LiteratureRecord(
                provider="Europe PMC", title=str(item.get("title", "")).strip(),
                authors=[a.strip() for a in authors_text.split(",") if a.strip()],
                year=str(item.get("pubYear", "")), journal=str(item.get("journalTitle", "")),
                doi=str(item.get("doi", "")), pmid=str(item.get("pmid", "")),
                pmcid=str(item.get("pmcid", "")), abstract=str(item.get("abstractText", "")),
                source_url=(f"https://europepmc.org/article/MED/{item['pmid']}" if item.get("pmid")
                            else f"https://europepmc.org/article/PMC/{item['pmcid']}" if item.get("pmcid") else ""),
                open_access=(str(is_oa).upper() in {"Y", "TRUE", "1"} if is_oa is not None else None),
                license=str(item.get("license", "")) or None,
            ))
        return records

    def verify(self, claims: Sequence[Mapping[str, Any]]) -> LiteratureVerificationResult:
        results: list[ClaimVerification] = []
        for index, claim in enumerate(claims, start=1):
            claim_id = str(claim.get("claim_id") or f"claim-{index}")
            claim_text = claim.get("text")
            if not isinstance(claim_text, str) or not claim_text.strip():
                results.append(ClaimVerification(claim_id, "INVALID_CLAIM", "", [], {"input": "claim text missing"}))
                continue
            query = self._query(claim_text)
            records: list[LiteratureRecord] = []
            errors: dict[str, str] = {}
            for provider, search in (("PubMed", self._search_pubmed), ("Europe PMC", self._search_europe_pmc)):
                try:
                    records.extend(search(query))
                except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                    # Never log request URLs here because API keys are query parameters.
                    errors[provider] = type(exc).__name__
            unique: dict[tuple[str, str, str], LiteratureRecord] = {}
            # Prefer Europe PMC on duplicate PMID because it commonly supplies
            # abstract and license metadata absent from ESummary.
            records.sort(key=lambda record: record.provider != "Europe PMC")
            for record in records:
                key = (("pmid", record.pmid, "") if record.pmid else
                       ("doi", record.doi.lower(), "") if record.doi else
                       (record.provider, "", record.title.lower()))
                unique.setdefault(key, record)
            status = ("PARTIAL" if unique and errors else "RECORDS_FOUND" if unique
                      else "PARTIAL" if errors and len(errors) < 2
                      else "UNAVAILABLE" if errors else "NO_RECORDS")
            results.append(ClaimVerification(claim_id, status, query,
                                             [asdict(r) for r in unique.values()], errors))
        overall = "COMPLETED" if results and all(not r.provider_errors for r in results) else "PARTIAL"
        return LiteratureVerificationResult(overall, results,
            ["Search results are candidate literature records; retrieval alone does not establish support or contradiction.",
             "Only indexed abstracts/metadata are returned. No full text was downloaded; verify individual reuse terms before any later retrieval."])

    def close(self) -> None:
        self.session.close()
