# AGENTS.md: working on paperpal

Instructions for coding agents (Codex, Claude Code, …) developing this repo. For *using* paperpal to do research, see `skills/paperpal/SKILL.md`.

## Layout
- `src/paperpal/sources.py`: all network access (paperz, HF, arXiv, arxiv-txt, Semantic Scholar). Sync, and raises `SourceError`.
- `src/paperpal/evidence.py`: the credibility evidence card and the `suggest_band` rules (keep them simple and explicit).
- `src/paperpal/render.py`: linkify, then write static gdoc-pasteable HTML. **No scripts in the output, ever.**
- `src/paperpal/cli.py` / `server.py`: thin CLI and MCP wrappers over the above. Keep them in sync: every tool exists in both.
- `src/paperpal/templates/pointers.md`: the barebones notes template.
- `skills/paperpal/`: the agent skill (`SKILL.md`, `METHODOLOGY.md`, `agents/openai.yaml`).
- Packaging:
  - `plugin.json` + `mcp.json`: portable Agent Plugins manifests (Codex and others)
  - `.claude-plugin/plugin.json` + `.mcp.json`: Claude Code
  - `.agents/plugins/marketplace.json`: local Codex marketplace

## Commands
```bash
uv sync
uv run pytest -q                      # offline tests only; no network
uv run paperpal -h                    # CLI
uv run paperpal-mcp                   # MCP server (stdio)
claude plugin validate .              # Claude Code manifest
```

## Rules
- Tests must not hit the network. Parse fixtures instead.
- Be polite to APIs: keep `MIN_INTERVAL` throttles and retries in `_get`, and never hammer arXiv (≈1 request / 3 s).
- When adding a tool, update the CLI, the MCP server, `SKILL.md` (tool list) and `METHODOLOGY.md` §9.
- Bump `version` in `pyproject.toml`, `plugin.json` and `.claude-plugin/plugin.json` together.
