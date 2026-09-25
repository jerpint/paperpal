# paperpal

ML literature research for agents and humans: **find it, verify it, score it, cite it.**

- **Search:** top-tier venues (NeurIPS / ICML / ICLR / AISTATS…), Hugging Face papers (with upvotes), daily papers, trending models
- **Verify:** arXiv metadata (venue hints), Semantic Scholar (venue, citations), and full text via [arxiv-txt.org](https://arxiv-txt.org) with regex grep so you quote numbers in context
- **Write:** a barebones pointers template, then render every citation as a link into a static page that pastes into Google Docs cleanly
- **Methodology:** [`skills/paperpal/METHODOLOGY.md`](skills/paperpal/METHODOLOGY.md) covers sources, the verification loop, the 1–5 credibility rubric, tags and failure modes

One codebase, three surfaces:

| surface | entry point |
|---|---|
| Claude Code plugin | `.claude-plugin/plugin.json` + `skills/paperpal/SKILL.md` + `.mcp.json` |
| Codex plugin (portable [Agent Plugins](https://agent-plugins.org) 1.0.0) | `plugin.json` + `mcp.json` + `skills/` + `skills/paperpal/agents/openai.yaml` |
| any MCP client (Claude Desktop, Cursor…) | `uv run --directory /path/to/paperpal paperpal-mcp` |
| CLI | `uv run paperpal -h` |

## Install

**Claude Code** (local): `claude --plugin-dir /path/to/paperpal`

**Codex** (local marketplace):
```bash
codex plugin marketplace add /path/to/paperpal   # reads .agents/plugins/marketplace.json
codex plugin add paperpal@paperpal-local
codex mcp list                                   # paperpal server, cwd = plugin root
```

**Skill only** (any agent that reads the open skills format): copy `skills/paperpal/` into `.agents/skills/` (Codex) or your harness's skills folder.

## Quickstart (CLI)

```bash
uv run paperpal top "persona consistency role-playing" --n 5
uv run paperpal meta 2510.22954
uv run paperpal full 2310.11324 --grep "76 accuracy points"
uv run paperpal card 2510.22954        # evidence card → suggested credibility band
uv run paperpal new notes.md --title "My topic"
uv run paperpal render notes.md        # → notes.html (static, gdoc-pasteable)
```

## Status

`0.2.0.dev0`, a local rewrite of paperpal 0.1 (an MCP server with HF search and arXiv details).
Planned: BibTeX export (arxiv-txt already returns it; `parse_abs_text` captures it). Set `S2_API_KEY` for reliable Semantic Scholar lookups.
