"""Paper sources: top-tier venue search, Hugging Face, arXiv, arxiv-txt, Semantic Scholar.

All functions are synchronous, return plain dicts / strings, and raise on network errors
so callers (CLI, MCP server) decide how to surface failures.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import logging
import os
import re
import time

import httpx

logging.getLogger("httpx").setLevel(logging.WARNING)  # keep MCP stderr quiet

USER_AGENT = "paperpal/0.2 (+https://github.com/jerpint/paperpal)"
TIMEOUT = 60.0


def _strip_version(arxiv_id: str) -> str:
    return re.sub(r"v\d+$", "", arxiv_id)


RETRY_STATUS = {406, 429, 500, 502, 503, 504}  # arXiv returns sporadic 406s; S2 rate-limits with 429


# Polite per-host spacing (arXiv asks for ~1 request / 3 s; S2's shared unauthenticated pool is tight).
MIN_INTERVAL = {"export.arxiv.org": 3.0, "api.semanticscholar.org": 1.5}
_last_call: dict[str, float] = {}


class SourceError(RuntimeError):
    """A short, readable network/API error."""


def _throttle(url: str) -> None:
    host = httpx.URL(url).host
    gap = MIN_INTERVAL.get(host, 0.0)
    if gap:
        wait = _last_call.get(host, 0.0) + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_call[host] = time.monotonic()


def _get(url: str, params: dict | None = None, timeout: float = TIMEOUT, headers: dict | None = None,
         retries: int = 3) -> httpx.Response:
    h = {"User-Agent": USER_AGENT, **(headers or {})}
    for attempt in range(retries + 1):
        _throttle(url)
        r = httpx.get(url, params=params, headers=h, timeout=timeout, follow_redirects=True)
        if r.status_code < 400:
            return r
        if r.status_code not in RETRY_STATUS or attempt == retries:
            hint = " (set S2_API_KEY for a higher limit)" if "semanticscholar" in url and r.status_code == 429 else ""
            raise SourceError(f"{httpx.URL(url).host} returned HTTP {r.status_code}{hint}")
        wait = float(r.headers.get("Retry-After", 0) or 0) or 3 * 2 ** attempt
        time.sleep(min(wait, 30))
    raise SourceError("unreachable")


# ── top-tier venues (paperz.vercel.app) ──────────────────────────────────────
# The site server-renders results into its Next.js RSC payload; we parse that.

def search_top_tier(query: str, n: int = 10) -> list[dict]:
    """Semantic search over papers from top-tier venues (NeurIPS, ICML, ICLR, AISTATS, …)."""
    html = _get("https://paperz.vercel.app/", params={"search": query}).text
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.S)
    if not chunks:
        return []
    payload = json.loads('"' + "".join(chunks).replace("\n", "\\n") + '"')
    refs = dict(re.findall(r'(?:^|\n)([0-9a-f]+):T[0-9a-f]+,(.*?)(?=\n[0-9a-f]+:|\Z)', payload, re.S))
    m = re.search(r'"papers":\[', payload)
    if not m:
        return []
    start = m.end() - 1
    depth = 0
    for i, ch in enumerate(payload[start:]):
        depth += ch == "["
        depth -= ch == "]"
        if depth == 0:
            papers = json.loads(payload[start:start + i + 1])
            break
    else:
        return []
    out = []
    for p in papers[:n]:
        abstract = p.get("abstract") or ""
        if isinstance(abstract, str) and abstract.startswith("$"):
            abstract = refs.get(abstract[1:], "")
        abstract = re.split(r"[0-9a-f]+:T[0-9a-f]+,", abstract)[0].strip()
        out.append({
            "title": p.get("title", ""),
            "venue": p.get("abbrev"),
            "year": p.get("year"),
            "authors": p.get("authors") or [],
            "url": p.get("arxiv_url") or p.get("pdf_url"),
            "code_url": p.get("code_url"),
            "abstract": abstract,
            "source": "paperz",
        })
    return out


# ── Hugging Face ─────────────────────────────────────────────────────────────

def search_hf(query: str, n: int = 10) -> list[dict]:
    """Hugging Face papers search (arXiv-backed, with community upvotes)."""
    data = _get("https://huggingface.co/api/papers/search", params={"q": query}).json()
    out = []
    for item in data[:n]:
        p = item.get("paper", item)
        out.append({
            "title": (p.get("title") or "").replace("\n", " "),
            "venue": "arXiv",
            "year": (p.get("publishedAt") or "")[:4],
            "authors": [a.get("name") for a in p.get("authors", [])],
            "url": f"https://arxiv.org/abs/{p.get('id')}",
            "arxiv_id": p.get("id"),
            "upvotes": p.get("upvotes"),
            "abstract": (p.get("summary") or "").replace("\n", " "),
            "source": "huggingface",
        })
    return out


def daily_papers(n: int = 20) -> list[dict]:
    """Today's Hugging Face daily papers, sorted by upvotes."""
    data = _get("https://huggingface.co/api/daily_papers", params={"limit": 50}).json()
    rows = [{"title": d["paper"]["title"], "arxiv_id": d["paper"]["id"], "upvotes": d["paper"].get("upvotes", 0),
             "url": f"https://arxiv.org/abs/{d['paper']['id']}"} for d in data]
    return sorted(rows, key=lambda r: -r["upvotes"])[:n]


def trending_models(n: int = 20) -> list[dict]:
    """Trending models on the Hugging Face Hub."""
    data = _get("https://huggingface.co/api/models", params={"sort": "trendingScore", "limit": n}).json()
    return [{"id": m["id"], "task": m.get("pipeline_tag"), "likes": m.get("likes"),
             "created": (m.get("createdAt") or "")[:10], "url": f"https://huggingface.co/{m['id']}"} for m in data]


# ── arXiv API ────────────────────────────────────────────────────────────────

def hf_paper(arxiv_id: str) -> dict:
    """Basic metadata from the Hugging Face papers API (fallback when arXiv is rate-limiting)."""
    p = _get(f"https://huggingface.co/api/papers/{_strip_version(arxiv_id)}").json()
    return {"arxiv_id": p.get("id"), "title": (p.get("title") or "").replace("\n", " "), "published": (p.get("publishedAt") or "")[:10],
            "updated": "", "authors": [a.get("name") for a in p.get("authors", [])], "comment": "", "journal_ref": "",
            "url": f"https://arxiv.org/abs/{p.get('id')}", "source": "huggingface (arXiv unavailable: no venue hints)"}


def arxiv_meta(ids: list[str]) -> list[dict]:
    """Authors, dates, and venue hints (comment / journal_ref) from the arXiv API.
    Falls back to Hugging Face metadata (without venue hints) if arXiv keeps refusing."""
    try:
        return _arxiv_meta(ids)
    except SourceError:
        out = []
        for i in ids:
            try:
                out.append(hf_paper(i))
            except SourceError:
                out.append(txt_paper(i))
        return out


def parse_abs_text(txt: str) -> dict:
    """Parse arxiv-txt.org /abs markdown (# Title, # Authors, # Abstract, # Categories, # Publication Details, # BibTeX)."""
    sec: dict[str, list[str]] = {}
    cur = None
    for line in txt.splitlines():
        if line.startswith("# "):
            cur = line[2:].strip().lower()
            sec[cur] = []
        elif cur:
            sec[cur].append(line)
    get = lambda k: "\n".join(sec.get(k, [])).strip()
    details = get("publication details")
    pub = re.search(r"Published:\s*(.+)", details)
    aid = re.search(r"arXiv ID:\s*(\S+)", details)
    published = ""
    if pub:
        try:
            published = dt.datetime.strptime(pub.group(1).strip(), "%B %d, %Y").date().isoformat()
        except ValueError:
            published = pub.group(1).strip()
    return {"title": get("title"), "authors": [a.strip() for a in get("authors").split(",") if a.strip()],
            "abstract": get("abstract"), "categories": get("categories"), "published": published,
            "arxiv_id": aid.group(1) if aid else "", "bibtex": get("bibtex")}


def txt_paper(arxiv_id: str) -> dict:
    """Basic metadata parsed from arxiv-txt.org (last-resort fallback)."""
    d = parse_abs_text(abstract(arxiv_id))
    return {"arxiv_id": d["arxiv_id"] or arxiv_id, "title": d["title"], "published": d["published"], "updated": "",
            "authors": d["authors"], "comment": "", "journal_ref": "", "url": f"https://arxiv.org/abs/{_strip_version(arxiv_id)}",
            "source": "arxiv-txt (arXiv unavailable: no venue hints)"}


def _arxiv_meta(ids: list[str]) -> list[dict]:
    xml = _get("https://export.arxiv.org/api/query", params={"id_list": ",".join(ids), "max_results": 100}).text
    out = []
    for e in xml.split("<entry>")[1:]:
        def g(k: str) -> str:
            m = re.search(f"<{k}[^>]*>(.*?)</{k}>", e, re.S)
            return html.unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else ""
        full_id = g("id").split("/abs/")[-1]
        out.append({
            "arxiv_id": full_id,
            "title": g("title"),
            "published": g("published")[:10],
            "updated": g("updated")[:10],
            "authors": re.findall(r"<name>(.*?)</name>", e),
            "comment": g("arxiv:comment"),
            "journal_ref": g("arxiv:journal_ref"),
            "url": "https://arxiv.org/abs/" + _strip_version(full_id),
        })
    return out


# ── arxiv-txt.org (LLM-friendly arXiv text) ──────────────────────────────────

def abstract(arxiv_id: str) -> str:
    """Title, authors, abstract, categories and BibTeX as markdown text."""
    return _get(f"https://arxiv-txt.org/abs/{arxiv_id}").text


def full_text(arxiv_id: str, grep: str | None = None, context: int = 250) -> str:
    """Full paper text; with `grep`, only regex matches with surrounding context."""
    txt = _get(f"https://arxiv-txt.org/pdf/{arxiv_id}", timeout=120).text
    if not grep:
        return txt
    pat = re.compile(grep, re.I)
    hits = ["…" + txt[max(0, m.start() - context):m.end() + context].replace("\n", " ") + "…" for m in pat.finditer(txt)]
    return "\n\n".join(hits) if hits else f"(no matches for /{grep}/)"


# ── Semantic Scholar ─────────────────────────────────────────────────────────

S2_FIELDS = "title,venue,year,publicationVenue,citationCount,influentialCitationCount,externalIds,authors,url"


def s2_lookup(arxiv_id: str | None = None, title: str | None = None) -> dict:
    """Venue and citation counts from Semantic Scholar, by arXiv ID or title."""
    base = "https://api.semanticscholar.org/graph/v1/paper"
    key = os.environ.get("S2_API_KEY")  # optional; unauthenticated requests share a small rate limit
    hdr = {"x-api-key": key} if key else None
    if arxiv_id:
        return _get(f"{base}/arXiv:{_strip_version(arxiv_id)}", params={"fields": S2_FIELDS}, headers=hdr).json()
    if title:
        return _get(f"{base}/search/match", params={"query": title, "fields": S2_FIELDS}, headers=hdr).json()
    raise ValueError("give arxiv_id or title")


def format_rows(rows: list[dict], with_abstract: bool = False) -> str:
    """Compact, human- and LLM-readable listing."""
    lines = []
    for r in rows:
        au = ", ".join((r.get("authors") or [])[:3]) + (" et al." if len(r.get("authors") or []) > 3 else "")
        up = f" ▲{r['upvotes']}" if r.get("upvotes") is not None else ""
        lines.append(f"- [{r.get('venue')} {r.get('year')}]{up} {r.get('title')} ({au})\n  {r.get('url')}")
        if with_abstract and r.get("abstract"):
            lines.append("  " + r["abstract"][:600])
    return "\n".join(lines) if lines else "(no results)"


__all__ = ["search_top_tier", "search_hf", "daily_papers", "trending_models", "arxiv_meta",
           "abstract", "full_text", "s2_lookup", "format_rows"]
