"""Evidence card: gather the raw facts needed to score a paper's credibility.

The card collects; it does not judge. `suggest_band` gives a *starting* 1–5 band from simple,
transparent rules (see METHODOLOGY.md §4); a human or agent assigns the final score.
"""
from __future__ import annotations

import datetime as dt
import re

from . import sources

TOP_TIER = {"NeurIPS", "ICML", "ICLR", "AISTATS", "COLT", "UAI", "CVPR", "ICCV", "ECCV", "ACL", "EMNLP", "NAACL",
            "COLM", "TMLR", "JMLR", "AAAI", "IJCAI", "KDD", "Nature", "Science"}


def _norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def _venue_hint(text: str) -> str | None:
    """Find a known venue name in an arXiv comment or journal_ref ('Accepted at ICLR 2024' → 'ICLR 2024')."""
    for v in sorted(TOP_TIER, key=len, reverse=True):
        m = re.search(rf"\b{re.escape(v)}\b\s*'?(\d{{2,4}})?", text or "", re.I)
        if m:
            return f"{v} {m.group(1) or ''}".strip()
    return None


def card(arxiv_id: str) -> dict:
    """Collect metadata, venue evidence, citations, age, code links for one arXiv paper."""
    c: dict = {"arxiv_id": arxiv_id, "errors": []}
    try:
        m = sources.arxiv_meta([arxiv_id])[0]
        if m.get("source"):
            c["errors"].append(m["source"])
        c.update(title=m["title"], authors=m["authors"], published=m["published"], updated=m["updated"],
                 url=m["url"], comment=m["comment"], journal_ref=m["journal_ref"],
                 latest_version=int(re.search(r"v(\d+)$", m["arxiv_id"]).group(1)) if re.search(r"v\d+$", m["arxiv_id"]) else None)
        c["age_days"] = (dt.date.today() - dt.date.fromisoformat(m["published"])).days if m["published"] else None
        c["venue_from_arxiv"] = _venue_hint(f"{m['comment']} {m['journal_ref']}")
    except Exception as e:
        c["errors"].append(f"arxiv: {e}")
        return c
    try:
        hits = sources.search_top_tier(c["title"], 5)
        match = next((h for h in hits if _norm(h["title"]) == _norm(c["title"])), None)
        c["venue_from_top_tier"] = f"{match['venue']} {match['year']}" if match else None
        c["top_tier_url"] = match["url"] if match else None
        c["code_url"] = match.get("code_url") if match else None
        if not c["code_url"]:
            gh = re.search(r"https?://github\.com/[\w.-]+/[\w.-]+", c.get("comment") or "")
            c["code_url"] = gh.group(0).rstrip(".") if gh else None
    except Exception as e:
        c["errors"].append(f"top-tier: {e}")
    try:
        s2 = sources.s2_lookup(arxiv_id=arxiv_id)
        c["venue_from_s2"] = (s2.get("publicationVenue") or {}).get("name") or s2.get("venue") or None
        c["citations"] = s2.get("citationCount")
        c["influential_citations"] = s2.get("influentialCitationCount")
    except Exception as e:
        c["errors"].append(f"semantic scholar: {e}")
    return c


def suggest_band(c: dict) -> tuple[str, list[str]]:
    """A starting band plus the reasons for it. Rules are deliberately simple and explicit."""
    why = []
    venue = c.get("venue_from_top_tier") or c.get("venue_from_arxiv") or c.get("venue_from_s2")
    top = bool(venue) and any(v.lower() in venue.lower() for v in TOP_TIER)
    cites = c.get("citations") or 0
    age = c.get("age_days") or 0
    if top:
        why.append(f"peer-reviewed venue: {venue}")
        band = "5" if cites >= 100 or age > 365 else "4–4.5"
    elif age < 30:
        why.append(f"preprint, {age} days old, no venue found")
        band = "2–3"
    else:
        why.append("preprint, no venue found")
        band = "3" if cites >= 50 else "2–3"
    if cites:
        why.append(f"{cites} citations ({c.get('influential_citations') or 0} influential)")
    if c.get("code_url"):
        why.append("code available")
    if len(c.get("authors") or []) == 1:
        why.append("single author (consider lowering)")
        band = {"2–3": "1.5–2", "3": "2–3"}.get(band, band)
    if (c.get("latest_version") or 1) > 1:
        why.append(f"v{c['latest_version']}: check whether the title changed since v1")
    why.append("adjust for: commercial interest, LLM-authored benchmarks, replication (see rubric)")
    return band, why


def format_card(c: dict) -> str:
    if not c.get("title"):
        return f"{c['arxiv_id']}: not enough data for a card. " + "; ".join(c.get("errors") or [])
    band, why = suggest_band(c)
    au = ", ".join((c.get("authors") or [])[:5]) + (" et al." if len(c.get("authors") or []) > 5 else "")
    lines = [
        f"{c.get('title')}  ({c.get('url')})",
        f"  authors: {au}",
        "  published: " + ", ".join(x for x in [c.get("published") or "?",
                                               f"updated {c['updated']}" if c.get("updated") else "",
                                               f"v{c['latest_version']}" if c.get("latest_version") else "",
                                               f"{c['age_days']} days old" if c.get("age_days") is not None else ""] if x),
        f"  venue: top-tier={c.get('venue_from_top_tier')} · arXiv={c.get('venue_from_arxiv')} · S2={c.get('venue_from_s2')}",
        f"  citations: {c.get('citations')} (influential {c.get('influential_citations')}) · code: {c.get('code_url')}",
        f"  suggested band: {band}. " + "; ".join(why),
    ]
    if c.get("errors"):
        lines.append("  lookup errors: " + "; ".join(c["errors"]))
    return "\n".join(lines)
