"""Render research notes: linkify citations, then write a static, Google-Docs-pasteable HTML page.

The HTML is deliberately barebones: no scripts, Arial, black text, underlined blue links,
bordered tables. Select all → paste into Google Docs keeps links and tables.
"""
from __future__ import annotations

import html as _html
import re
from pathlib import Path

import markdown

ARXIV_ABS = "https://arxiv.org/abs/"
_ID = r"\d{4}\.\d{4,5}(?:v\d+)?"

CSS = """
body { font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.5; color: #000; background: #fff;
       max-width: 860px; margin: 24px auto; padding: 0 16px; }
a { color: #1155cc; text-decoration: underline; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; }
th, td { border: 1px solid #999; padding: 4px 6px; vertical-align: top; text-align: left; font-size: 13px; }
code { font-family: monospace; }
""".strip()


def linkify(md: str) -> str:
    """Turn bare arXiv IDs into links. Idempotent: already-linked IDs are left alone.

    Handles `arXiv **2609.25804**`, `arXiv 2609.25804` and `(2609.25804)`.
    """
    md = re.sub(rf"arXiv \*\*({_ID})\*\*", lambda m: f"[arXiv {m[1]}]({ARXIV_ABS}{m[1]})", md)
    md = re.sub(rf"(?<!\[)arXiv ({_ID})(?![\d\]])", lambda m: f"[arXiv {m[1]}]({ARXIV_ABS}{m[1]})", md)
    md = re.sub(rf"(?<![\[/])\(({_ID})\)", lambda m: f"([{m[1]}]({ARXIV_ABS}{m[1]}))", md)
    return md


def bare_ids(html_body: str) -> list[str]:
    """arXiv-looking IDs that are not inside a link (should be empty before sharing)."""
    unlinked = re.sub(r"<a [^>]*>.*?</a>", "", html_body, flags=re.S)
    return sorted(set(re.findall(rf"(?<![/\[\w.]){_ID}(?![\]\w/])", unlinked)))


def to_html(md: str, title: str = "Research notes") -> str:
    body = markdown.markdown(md, extensions=["tables", "sane_lists"])
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{_html.escape(title)}</title>\n<style>\n{CSS}\n</style></head><body>\n{body}\n</body></html>\n")


def render_file(src: str | Path, out_html: str | Path | None = None, title: str | None = None,
                write_back: bool = True) -> dict:
    """Linkify `src` (in place if write_back) and write the static HTML next to it (or to out_html)."""
    src = Path(src)
    md = linkify(src.read_text())
    if write_back:
        src.write_text(md)
    if title is None:
        m = re.search(r"^#\s+(.+)$", md, re.M)
        title = m.group(1).strip() if m else src.stem
    out = Path(out_html) if out_html else src.with_suffix(".html")
    page = to_html(md, title)
    out.write_text(page)
    return {"html": str(out), "links": page.count("<a href="), "bare_ids": bare_ids(page)}
