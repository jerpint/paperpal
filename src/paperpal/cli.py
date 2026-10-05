"""paperpal CLI: the same tools as the MCP server, for any agent or human with a shell.

  paperpal top  "query" [--n 10] [--abs]      top-tier venues (semantic search)
  paperpal hf   "query" [--n 10] [--abs]      Hugging Face papers search
  paperpal daily [--n 20]                     Hugging Face daily papers
  paperpal trending [--n 20]                  trending models on the Hub
  paperpal meta ID [ID ...]                   arXiv metadata (authors, venue hints)
  paperpal s2 ID | --title "…"                Semantic Scholar venue + citations
  paperpal abs ID                             abstract + BibTeX (arxiv-txt.org)
  paperpal card ID [ID ...]                   evidence card: venue, citations, age, code → suggested 1–5 band
  paperpal full ID [--grep REGEX]             full text, or regex hits with context
  paperpal new PATH [--title "…"]             start a pointers doc from the template
  paperpal render PATH.md [--out PATH.html]   linkify + static gdoc-pasteable HTML
"""
from __future__ import annotations

import argparse
import json
import sys
from importlib import resources
from pathlib import Path

from . import evidence, render, sources


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="paperpal", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("top", "hf"):
        s = sub.add_parser(name)
        s.add_argument("query", nargs="+")
        s.add_argument("--n", type=int, default=10)
        s.add_argument("--abs", action="store_true")
    for name in ("daily", "trending"):
        sub.add_parser(name).add_argument("--n", type=int, default=20)
    sub.add_parser("meta").add_argument("ids", nargs="+")
    s = sub.add_parser("s2")
    s.add_argument("id", nargs="?")
    s.add_argument("--title")
    sub.add_parser("abs").add_argument("id")
    sub.add_parser("card").add_argument("ids", nargs="+")
    s = sub.add_parser("full")
    s.add_argument("id")
    s.add_argument("--grep")
    s = sub.add_parser("new")
    s.add_argument("path")
    s.add_argument("--title", default="Research")
    s = sub.add_parser("render")
    s.add_argument("path")
    s.add_argument("--out")
    s.add_argument("--no-write-back", action="store_true")
    a = p.parse_args(argv)

    try:
        if a.cmd in ("top", "hf"):
            fn = sources.search_top_tier if a.cmd == "top" else sources.search_hf
            print(sources.format_rows(fn(" ".join(a.query), a.n), a.abs))
        elif a.cmd == "daily":
            for r in sources.daily_papers(a.n):
                print(f"- ▲{r['upvotes']} {r['title']}\n  {r['url']}")
        elif a.cmd == "trending":
            for r in sources.trending_models(a.n):
                print(f"- {r['id']} [{r['task']}] ♥{r['likes']} {r['created']}\n  {r['url']}")
        elif a.cmd == "meta":
            for r in sources.arxiv_meta(a.ids):
                au = ", ".join(r["authors"][:6]) + (f" (+{len(r['authors']) - 6})" if len(r["authors"]) > 6 else "")
                print(f"== {r['arxiv_id']} | {r['title']}\n   {r['published']} | {au}")
                for k in ("comment", "journal_ref"):
                    if r[k]:
                        print(f"   {k}: {r[k]}")
        elif a.cmd == "s2":
            print(json.dumps(sources.s2_lookup(arxiv_id=a.id, title=a.title), indent=2))
        elif a.cmd == "card":
            print("\n\n".join(evidence.format_card(evidence.card(i)) for i in a.ids))
        elif a.cmd == "abs":
            print(sources.abstract(a.id))
        elif a.cmd == "full":
            print(sources.full_text(a.id, a.grep))
        elif a.cmd == "new":
            tpl = resources.files("paperpal").joinpath("templates/pointers.md").read_text()
            path = Path(a.path)
            if path.exists():
                print(f"refusing to overwrite {path}", file=sys.stderr)
                return 1
            path.write_text(tpl.replace("<Title>", a.title))
            print(f"created {path}")
        elif a.cmd == "render":
            r = render.render_file(a.path, a.out, write_back=not a.no_write_back)
            print(f"wrote {r['html']} · {r['links']} links · bare ids: {r['bare_ids'] or 'none'}")
    except Exception as e:  # surface network/API errors plainly
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
