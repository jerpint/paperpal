from paperpal.render import bare_ids, linkify, to_html

A = "https://arxiv.org/abs/"


def test_linkify_forms():
    md = "x arXiv **2609.25804** y arXiv 2202.07646 z (2510.22954)"
    out = linkify(md)
    assert f"[arXiv 2609.25804]({A}2609.25804)" in out
    assert f"[arXiv 2202.07646]({A}2202.07646)" in out
    assert f"([2510.22954]({A}2510.22954))" in out


def test_linkify_idempotent():
    once = linkify("arXiv **2609.25804** and (2510.22954)")
    assert linkify(once) == once


def test_no_bare_ids_after_render():
    page = to_html(linkify("see arXiv 2404.05405 and (2405.09673)"))
    assert bare_ids(page) == []


def test_bare_ids_detected():
    assert bare_ids("<p>plain 2404.05405 here</p>") == ["2404.05405"]


def test_html_is_static():
    page = to_html("# T\n\n| a | b |\n|---|---|\n| 1 | 2 |")
    assert "<script" not in page and "<table>" in page


ABS = """# Title
User as Engram: Internalizing Per-User Memory

# Authors
Bojie Li, Ada Lovelace

# Abstract
Personal memory in a language model is two problems.

# Categories
cs.AI

# Publication Details
- Published: June 17, 2026
- arXiv ID: 2606.19172v1

# BibTeX
@misc{li2026user, title={User as Engram}}
"""


def test_parse_abs_text():
    from paperpal.sources import parse_abs_text
    d = parse_abs_text(ABS)
    assert d["title"].startswith("User as Engram")
    assert d["authors"] == ["Bojie Li", "Ada Lovelace"]
    assert d["published"] == "2026-06-17" and d["arxiv_id"] == "2606.19172v1"
    assert d["bibtex"].startswith("@misc")


def test_suggest_band_rules():
    from paperpal.evidence import suggest_band
    assert suggest_band({"venue_from_top_tier": "NeurIPS 2025", "citations": 152, "age_days": 333})[0] == "5"
    assert suggest_band({"venue_from_top_tier": "ICML 2026", "citations": 3, "age_days": 60})[0] == "4–4.5"
    assert suggest_band({"age_days": 3, "authors": ["a", "b"]})[0] == "2–3"
    assert suggest_band({"age_days": 90, "authors": ["solo"]})[0] == "1.5–2"


def test_venue_hint():
    from paperpal.evidence import _venue_hint
    assert _venue_hint("Accepted as a long paper at EMNLP 2024") == "EMNLP 2024"
    assert _venue_hint("COLM 2024; Code and data: https://github.com/x/y") == "COLM 2024"
    assert _venue_hint("33 pages, 8 figures") is None
