"""paperpal MCP server (stdio). Works with any MCP client: Claude Code, Claude Desktop, Codex, Cursor."""
from __future__ import annotations

try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from . import evidence, render, sources

mcp = _Server("paperpal")


def _safe(fn, *args, **kwargs) -> str:
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        return f"error: {e}"


@mcp.tool()
def search_top_tier(query: str, n: int = 10, with_abstract: bool = True) -> str:
    """Semantic search over peer-reviewed papers from top-tier venues (NeurIPS, ICML, ICLR, AISTATS, …).
    Semantic: results are neighbours, so match titles before trusting a venue. Not found ≠ unpublished."""
    return _safe(lambda: sources.format_rows(sources.search_top_tier(query, n), with_abstract))


@mcp.tool()
def search_hf(query: str, n: int = 10, with_abstract: bool = True) -> str:
    """Hugging Face papers search: recent arXiv work with community upvotes (a traction signal, not quality)."""
    return _safe(lambda: sources.format_rows(sources.search_hf(query, n), with_abstract))


@mcp.tool()
def daily_papers(n: int = 20) -> str:
    """Today's Hugging Face daily papers, sorted by upvotes."""
    return _safe(lambda: "\n".join(f"- ▲{r['upvotes']} {r['title']} {r['url']}" for r in sources.daily_papers(n)))


@mcp.tool()
def trending_models(n: int = 20) -> str:
    """Trending models on the Hugging Face Hub."""
    return _safe(lambda: "\n".join(f"- {r['id']} [{r['task']}] ♥{r['likes']} {r['created']} {r['url']}"
                                   for r in sources.trending_models(n)))


@mcp.tool()
def arxiv_meta(arxiv_ids: list[str]) -> str:
    """arXiv metadata: current title, authors, dates, and venue hints (comment / journal_ref)."""
    def run():
        out = []
        for r in sources.arxiv_meta(arxiv_ids):
            out.append(f"{r['arxiv_id']} | {r['title']} | {r['published']} | {', '.join(r['authors'][:8])}"
                       + (f"\n  comment: {r['comment']}" if r["comment"] else "")
                       + (f"\n  journal_ref: {r['journal_ref']}" if r["journal_ref"] else "")
                       + f"\n  {r['url']}")
        return "\n".join(out) or "(not found)"
    return _safe(run)


@mcp.tool()
def s2_lookup(arxiv_id: str = "", title: str = "") -> str:
    """Semantic Scholar: venue, year, citation and influential-citation counts (by arXiv ID or exact title)."""
    import json
    return _safe(lambda: json.dumps(sources.s2_lookup(arxiv_id or None, title or None), indent=2))


@mcp.tool()
def evidence_card(arxiv_ids: list[str]) -> str:
    """Gather credibility evidence per paper: current title/version, venue (top-tier index, arXiv comment,
    Semantic Scholar), citations, age, code link, plus a *suggested* 1–5 band with reasons.
    The band is a starting point; assign the final score yourself using the rubric."""
    return _safe(lambda: "\n\n".join(evidence.format_card(evidence.card(i)) for i in arxiv_ids))


@mcp.tool()
def abstract(arxiv_id: str) -> str:
    """Title, authors, abstract, categories and BibTeX for an arXiv paper (via arxiv-txt.org)."""
    return _safe(sources.abstract, arxiv_id)


@mcp.tool()
def full_text(arxiv_id: str, grep: str = "") -> str:
    """Full text of an arXiv paper (via arxiv-txt.org). Pass `grep` (regex) to get only matches with
    context — use this to verify an exact number before quoting it."""
    return _safe(sources.full_text, arxiv_id, grep or None)


@mcp.tool()
def render_notes(md_path: str, out_html: str = "") -> str:
    """Linkify every arXiv citation in a markdown notes file (in place) and write a static,
    Google-Docs-pasteable HTML page. Reports remaining bare IDs (should be none)."""
    def run():
        r = render.render_file(md_path, out_html or None)
        return f"wrote {r['html']} · {r['links']} links · bare ids: {r['bare_ids'] or 'none'}"
    return _safe(run)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
