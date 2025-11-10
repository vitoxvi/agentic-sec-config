#!/usr/bin/env bash
set -euo pipefail

echo "==> Checking uv ..."
if ! command -v uv >/dev/null 2>&1; then
  echo "   uv not found. Installing with Homebrew (fallback to pipx)..."
  if command -v brew >/dev/null 2>&1; then
    brew install uv || true
  fi
  if ! command -v uv >/dev/null 2>&1; then
    pipx install uv
  fi
fi
uv --version

echo "==> Syncing deps ..."
uv sync

echo "==> Preparing .env ..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "   Created .env (fill in OPENAI_API_KEY if needed)."
fi

echo "==> Done! Try:"
echo "   uv run python -m src.mcp_servers.fs_server hello"
echo "   uv run python -m src.agents.main_auditor audit --dry-run"
