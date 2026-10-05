---
name: paperpal
description: Do ML literature research the traceable way. Search top-tier venues, arXiv, Hugging Face and Semantic Scholar; verify numbers in full text; score credibility; and write pointer-style notes with every citation linked, rendered to gdoc-pasteable HTML. Use when asked to find papers, back a claim with citations, check whether a paper was peer-reviewed, assess a paper's credibility, or prep research notes.
---

# paperpal

Follow the full methodology in [METHODOLOGY.md](METHODOLOGY.md). The essentials are below.

## Tools

The same functions are exposed three ways; use whichever your harness has:
- **MCP** (`paperpal` server): `search_top_tier`, `search_hf`, `daily_papers`, `trending_models`, `arxiv_meta`, `s2_lookup`, `evidence_card`, `abstract`, `full_text`, `render_notes`
- **CLI**: `paperpal top|hf|daily|trending|meta|s2|card|abs|full|new|render …` (run `paperpal -h`)
- **Python**: `from paperpal import sources, render`

## Rules

1. **Primary sources only.** Papers, model cards, repos, vendor posts. Blog summaries are leads, not citations.
2. **Don't guess new terms.** Search before interpreting an unfamiliar acronym or model class.
3. **Verify every kept item:**
   - `arxiv_meta`: current title and venue hints
   - `search_top_tier` by title: peer-reviewed? It's a semantic search, so match titles.
   - `full_text(id, grep=…)`: the exact number and its qualifiers
4. **Score** credibility from 1 to 5. `evidence_card` gathers the facts and suggests a band; you assign the final score using the METHODOLOGY rubric and show it next to the claim.
5. **Tag:**
   - source type: `[peer-reviewed]` `[preprint]` `[industry]` `[secondary]` `[news]`
   - status: known / inferred / unknown
   - `≈` for unverified affiliations
6. **Pointers, not prose,** unless asked to write: claim → evidence → citation → tags → relevance.
7. **Every citation is a link.** Run `render_notes` / `paperpal render`, which should report `bare ids: none`.
8. **Standalone output:** don't mention tools, agents or process in the shared doc.
9. **Check before reporting** anything as done: recompute derived numbers and re-read edits.

## Starting a notes doc

`paperpal new notes.md --title "…"` creates a doc from the barebones template (sections by claim, quick map, credibility table, before-citing list). When it's filled in, `paperpal render notes.md` writes `notes.html`: static, no scripts, plain styling. Select all and paste into Google Docs, and links and tables survive.
