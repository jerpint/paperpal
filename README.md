# paperpal

**ML literature research for agents and humans: find it, verify it, score it, cite it.**

paperpal is a plugin for coding agents (Claude Code, Codex, and any MCP client). It gives your agent a research **methodology** and the **tools** to follow it:

- **Find:** semantic search over top-tier venues (NeurIPS, ICML, ICLR, AISTATS, …), Hugging Face papers (with community upvotes), today's daily papers, trending models
- **Verify:** arXiv metadata (current title and version, venue hints), Semantic Scholar (venue, citations), and **full text** via [arxiv-txt.org](https://arxiv-txt.org) with regex grep, so numbers get quoted in context
- **Score:** an evidence card per paper (venue from three sources, citations, age, code link) with a *suggested* 1–5 credibility band. You or your agent make the final call.
- **Cite:** a barebones notes template, rendered to a static HTML page where every citation is a clickable link. Select all → paste into Google Docs, and links and tables survive.

> LLMs can still hallucinate and semantic search is never perfect. paperpal is built around making every claim checkable.

---

## Install

### Claude Code

```bash
git clone https://github.com/jerpint/paperpal
claude --plugin-dir ./paperpal
```

The plugin registers the `paperpal` skill and the `paperpal` MCP server (run with `uv`).

### Codex

paperpal ships a portable [Agent Plugins 1.0.0](https://agent-plugins.org) manifest and a local marketplace:

```bash
git clone https://github.com/jerpint/paperpal
codex plugin marketplace add ./paperpal
codex plugin add paperpal@paperpal-local
codex mcp list        # → paperpal
```

### Claude Desktop, Cursor, or any MCP client

Add the server to your client's MCP config (for Claude Desktop on macOS, that's `~/Library/Application Support/Claude/claude_desktop_config.json`; for Cursor, `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "paperpal": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/paperpal", "paperpal-mcp"]
    }
  }
}
```

### Skill only

Any agent that reads the open skills format can use the methodology without the server: copy `skills/paperpal/` into your agent's skills folder (e.g. `.agents/skills/` for Codex). The skill falls back to the CLI.

### CLI

```bash
cd paperpal && uv sync
uv run paperpal -h
```

Requires [uv](https://docs.astral.sh/uv/) and Python ≥ 3.11.

---

## Use

Ask your agent things like:

- *"Find peer-reviewed evidence that alignment training reduces output diversity, and score each source."*
- *"Was this arXiv paper accepted anywhere? Check the exact number it reports for X."*
- *"Prep research notes on small language models for a Google Doc: pointers only, every citation linked."*

Or drive it directly:

```bash
uv run paperpal top "persona consistency role-playing" --n 5    # top-tier venues
uv run paperpal hf "ternary quantization" --n 5                 # Hugging Face papers
uv run paperpal daily                                           # today's HF daily papers
uv run paperpal meta 2510.22954                                 # arXiv metadata + venue hints
uv run paperpal card 2510.22954                                 # evidence card → suggested band
uv run paperpal full 2310.11324 --grep "76 accuracy points"     # verify a number in the full text
uv run paperpal new notes.md --title "My topic"                 # start from the template
uv run paperpal render notes.md                                 # → notes.html (gdoc-pasteable)
```

### Tools

| MCP tool | CLI | what it does |
|---|---|---|
| `search_top_tier` | `top` | semantic search over top-tier venue papers ([paperz](https://paperz.vercel.app)) |
| `search_hf` | `hf` | Hugging Face papers search (recency, upvotes) |
| `daily_papers` | `daily` | today's Hugging Face daily papers |
| `trending_models` | `trending` | trending models on the Hub |
| `arxiv_meta` | `meta` | arXiv title, authors, versions, comment / journal-ref venue hints |
| `s2_lookup` | `s2` | Semantic Scholar venue and citation counts |
| `evidence_card` | `card` | credibility evidence + a suggested 1–5 band with reasons |
| `abstract` | `abs` | abstract, categories and BibTeX ([arxiv-txt](https://arxiv-txt.org)) |
| `full_text` | `full` | full paper text, or regex matches with context |
| `render_notes` | `render` | linkify citations and write static, gdoc-pasteable HTML |
| — | `new` | create a notes doc from the template |

---

## The methodology

The skill (`skills/paperpal/SKILL.md`) tells agents how to research. The full guide is [`METHODOLOGY.md`](skills/paperpal/METHODOLOGY.md), which also works standalone for humans. In short:

1. **Primary sources only.** Papers, model cards, repos, vendor posts. Blog summaries are leads, not citations.
2. **Verify every kept item:** metadata → top-tier venue → the exact number in the full text.
3. **Score credibility (1–5)** on venue, lab, public code and data, age, and replication. Build arguments on ≥4.5, hedge 3–4, and footnote or drop ≤2.
4. **Tag everything:**
   - source type: `[peer-reviewed]` `[preprint]` `[industry]` `[secondary]` `[news]`
   - status: known / inferred / unknown
5. **Pointers, not prose,** unless asked to write.
6. **Every citation is a link.** Render to static HTML before sharing.

---

## Configuration

| env var | purpose |
|---|---|
| `S2_API_KEY` | optional [Semantic Scholar API key](https://www.semanticscholar.org/product/api). Unauthenticated requests share a small rate limit. |

paperpal throttles requests per host (arXiv ≈ 1 request / 3 s), retries on 406 / 429 / 5xx, and falls back from arXiv to Hugging Face to arxiv-txt for metadata.

## Development

See [`AGENTS.md`](AGENTS.md). Quick version:

```bash
uv sync
uv run pytest -q              # offline tests
claude plugin validate .      # Claude Code manifest
```

## Roadmap

- BibTeX export (the arxiv-txt parser already captures BibTeX)
- More venue sources for the evidence card

## License

MIT
