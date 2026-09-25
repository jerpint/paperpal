# paperpal research methodology

*How we do ML literature research with an AI agent: fast, traceable and honest about uncertainty. Draft v0.1, 2026-09-25.*

Use this as a standalone guide for humans, or as the operating instructions for any agent doing ML research (it's the skill half of the paperpal plugin).

---

## 1. Principles

1. **Primary sources only.** The paper, the model card, the repo, the vendor's own post, the dataset card. Blog summaries ("X explained") are leads to follow, never citations.
2. **Every claim is traceable.** Each claim gets a clickable link to where it comes from. No link, no claim.
3. **Separate what's known from what you think.** Tag every non-trivial statement as known, inferred or unknown, and never let an inference read like a finding.
4. **Numbers carry their context.** "Up to 76 points" isn't "76 points". Keep the setting (model, task, few-shot vs zero-shot, date).
5. **Credibility is explicit.** Venue, lab, reproducibility and age are shown next to the claim, not hidden in your head.
6. **Don't guess unfamiliar terms.** A new acronym (e.g. a new model class) gets searched before it's interpreted.
7. **The reader does the framing.** Default to *pointers, not prose* unless asked to write. Research notes that editorialize are harder to reuse.

## 2. Sources (and what each is good for)

| source | good for | watch out for |
|---|---|---|
| **Top-tier venue search** ([paperz.vercel.app](https://paperz.vercel.app)) | finding peer-reviewed NeurIPS / ICML / ICLR / AISTATS work; checking whether a preprint was accepted | semantic search returns *neighbours*, so match titles; coverage is partial (not found ≠ unpublished) |
| **arXiv** (API + [arxiv.org/abs/ID](https://arxiv.org)) | canonical IDs, versions, authors; `comment` / `journal_ref` often states the venue | arXiv ≠ peer-reviewed; titles change between versions |
| **Hugging Face papers** ([search API](https://huggingface.co/api/papers/search?q=), [daily papers](https://huggingface.co/papers), trending models) | what's new this week; community traction (upvotes); linked models and datasets | popularity ≠ quality |
| **Full text** ([arxiv-txt.org](https://arxiv-txt.org): `/abs/ID`, `/pdf/ID`) | checking the exact number in context; reading methods and limitations | some papers aren't available; fall back to the arXiv PDF |
| **Semantic Scholar** | venue, citation counts, influential citations | citation counts lag for new work |
| **Leaderboards** ([Artificial Analysis](https://artificialanalysis.ai), benchmark repos) | Pareto frontiers (intelligence vs cost), open vs closed comparisons | index definitions change between versions; always give the version and date |
| **Vendor primaries** (launch posts, model cards, repos) | what a system *is*; stated specs | performance claims are self-reported until replicated |
| **News** (reputable outlets) | events (launches, outages, regulation) | cite the article itself, not a summary of it |

## 3. Workflow

1. **Scope.** Write the question and the claims you need evidence for (e.g. "general models average knowledge").
2. **Search wide.** HF papers and top-tier search for each claim; the trending and daily lists for recency.
3. **Triage.** Keep papers whose abstract actually supports the claim. Drop "related but not evidence".
4. **Verify** (for every kept item):
   - `meta`: correct ID, title (current version), first authors, and any venue in the comment or journal ref.
   - `venue`: search top-tier by title; confirm acceptance.
   - `full text`: grep the exact number or phrase you'll quote; note its setting.
   - **affiliation**: from the paper if possible, otherwise mark it ≈ (unverified).
5. **Score** each item with the rubric (§4).
6. **Write** as pointers: claim → evidence → citation → tags → relevance.
7. **Link-check.** No bare IDs; every citation clickable.
8. **Before-citing list.** What still needs a primary source, a full-text check, or a hedge.

## 4. Credibility rubric (1–5)

| score | meaning | typical examples |
|---|---|---|
| **5** | peer-reviewed at a top venue or journal, established group, widely cited or replicated | Nature, NeurIPS / ICML / ICLR main track, TMLR featured |
| **4–4.5** | top venue but recent or unreplicated; or a strong lab with public code, unreviewed | a new ICML paper; a frontier-lab technical report |
| **3** | recent preprint from a credible group, public code and data, no venue yet | a week-old arXiv benchmark from a known lab |
| **2** | position paper, vendor claim, toy-model theory, or an unknown group without code | "X retains 98% quality" (vendor); a proof on a uniform-random toy model |
| **1–1.5** | single author, no venue, self-reported headline numbers, not replicated | interesting idea, not evidence |

Adjust for: **commercial interest** (−), **LLM-authored benchmarks** (−), **2023-era models only** (note it), **retitled versions** (note it), and **independent replication** (+).

**How to use scores:** build the argument on the ≥4.5 items, hedge 3–4 ("recent work suggests"), and footnote or drop anything ≤2.

## 5. Tags

- **Source type:** `[peer-reviewed]` · `[preprint]` · `[industry]` · `[secondary]` · `[news]`
- **Epistemic status:** `known` (stated in a primary source) · `inferred` (our reasoning) · `unknown` (not disclosed)
- **In plans and playbooks:** `[fact]` · `[est]` (an estimate; benchmark it) · `[decision]` (agreed with the owner)
- **Affiliation:** `≈` means unverified, from memory or secondary sources

## 6. Claim hygiene checklist

- [ ] The quote matches the full text, including qualifiers ("up to", "few-shot", "on LLaMA-2-13B").
- [ ] Preprints are hedged. Self-reported numbers are marked. Vendor interest is flagged.
- [ ] Benchmark caveats: contamination, construct validity, who wrote the items, how old the models are.
- [ ] Counterpoints are included where they exist (the strongest version of the other side).
- [ ] Any arithmetic you derived (thresholds, ratios) is recomputed.
- [ ] Dates and versions are stated for leaderboards and fast-moving claims.

## 7. Output rules

- **Default format:** a numbered pointers doc with sections by claim, a *quick map* (ask → pointer numbers), a credibility table, and a *before citing* list.
- **Links:** arXiv as `https://arxiv.org/abs/ID`; DOIs as `https://doi.org/…`; openreview and proceedings links when that's where the peer-reviewed version is.
- **Portable:** markdown as the source of truth, plus a **static HTML** render (no scripts, plain styling) so it pastes into Google Docs with links intact.
- **Standalone:** the shared doc doesn't mention the tools, agents or process that produced it. Process notes live separately.

## 8. Failure modes we've actually hit

| failure | fix |
|---|---|
| Guessed a new acronym from an older, similar one, and was wrong | search trending/primary sources before interpreting |
| Semantic search returned a similar-titled paper as a "match" | require a title match before trusting a venue |
| Treated "not in the index" as "not published" | say "venue unverified" instead |
| Quoted a number from the abstract as if it came from the results | grep the full text; note where the number appears |
| Derived a threshold from a cost matrix and got the arithmetic wrong | recompute derived numbers explicitly |
| Announced an edit as done before checking it | verify first, then report |
| A paper was retitled in a later version | cite the current title (or both) |

## 9. Tool interface (the plugin's tools)

| tool | does |
|---|---|
| `search_top_tier(query, n)` | peer-reviewed venue search (paperz) |
| `search_hf(query, n)` | Hugging Face papers search (recency, upvotes) |
| `trending(kind)` | HF trending models, or daily papers |
| `arxiv_meta(ids)` | authors, versions, comment/journal-ref venue hints |
| `abstract(id)` / `full_text(id, grep=)` | arxiv-txt text, with an optional regex search in context |
| `s2_lookup(id or title)` | venue, citation counts (set `S2_API_KEY` for reliability) |
| `evidence_card(ids)` | venue (top-tier / arXiv / S2), citations, age, code → *suggested* band; a human or agent confirms |
| `render_notes(md)` | linkify, then write a static gdoc-pasteable HTML page |
