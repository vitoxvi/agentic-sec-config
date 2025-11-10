# Agentic Security Audit

Student-sized, KISS+YAGNI agentic project demonstrating a manager-pattern auditor with MCP-wrapped tools.

## Quick Start (macOS)

```bash
# 0) Prereqs: Homebrew and Python 3.10+ installed
# 1) Install uv (if missing)
brew install uv || pipx install uv

# 2) Setup project
uv sync
cp .env.example .env

# 3) Try the hello commands
uv run python -m src.agents.main_auditor --help
```

> Note: The OpenAI Agent SDK + MCP Sandbox wrapper are referenced in `pyproject.toml` under a separate optional dependency group. Enable/install them once you have access to the correct package or Git URL.

## Repo Map
- `src/agents/`: manager-pattern agents
- `src/mcp_servers/`: MCP-exposed tools (db, fs, email, config)
- `src/core/`: schemas, policy IO, seeds, error injections
- `info/`: roadmap, project brief, grading scheme, architecture
- `plans/`: config-as-code change plans
- `reports/`: audit outputs
- `outbox/`: "sent" artifacts (reports, emails)
- `infra/scripts/`: helper scripts for macOS / Windows

## Stage 0 Checklist
- [x] uv env setup
- [x] Basic folder skeleton
- [x] .env.example
- [x] Hello FS server + CLI entrypoints
- [ ] Add/verify OpenAI Agent SDK + MCP Sandbox wrapper URLs
- [ ] Commit and push

