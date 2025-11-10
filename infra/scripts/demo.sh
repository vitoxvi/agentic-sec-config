#!/usr/bin/env bash
set -euo pipefail
echo "==> Demo: stub run"
uv run python -m src.mcp_servers.fs_server hello
uv run python -m src.agents.main_auditor audit --dry-run
