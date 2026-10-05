"""Render research notes: linkify citations, then write a static, Google-Docs-pasteable HTML page.

The HTML is deliberately barebones: no scripts (except KaTeX when the notes contain LaTeX), Arial, black text, underlined blue links,
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


_DISPLAY = re.compile(r"\$\$(.+?)\$\$", re.S)
_INLINE = re.compile(r"(?<![\\$\w])\$(?=\S)([^$\n]+?)(?<=\S)\$(?![\d$\w])")
KATEX = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">\n'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>\n'
         '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" '
         'onload="renderMathInElement(document.body,{delimiters:[{left:\'\\\\[\',right:\'\\\\]\',display:true},'
         '{left:\'\\\\(\',right:\'\\\\)\',display:false}],throwOnError:false})"></script>\n')


def _protect_math(md: str) -> tuple[str, list[str]]:
    """Swap $$..$$ / $..$ for placeholders so markdown doesn't eat underscores or backslashes."""
    spans: list[str] = []

    def keep(tex: str, display: bool) -> str:
        l, r = (r"\[", r"\]") if display else (r"\(", r"\)")
        spans.append(l + _html.escape(tex.strip()) + r)
        return f"PPMATH{len(spans) - 1}X"

    md = _DISPLAY.sub(lambda m: keep(m[1], True), md)
    md = _INLINE.sub(lambda m: keep(m[1], False), md)
    return md, spans


def to_html(md: str, title: str = "Research notes") -> str:
    """Static HTML. Only pages that contain LaTeX get a script: KaTeX from a CDN, to render the math."""
    md, spans = _protect_math(md)
    body = markdown.markdown(md, extensions=["tables", "sane_lists"])
    body = re.sub(r"PPMATH(\d+)X", lambda m: spans[int(m[1])], body)
    head_extra = KATEX if spans else ""
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{_html.escape(title)}</title>\n{head_extra}<style>\n{CSS}\n</style></head><body>\n{body}\n</body></html>\n")


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
