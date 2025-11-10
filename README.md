# Agentic Security Audit

Student-sized, KISS+YAGNI agentic project demonstrating a manager-pattern auditor with MCP-wrapped tools.

## Quick Start (macOS)

```bash
# Prerequisites: Homebrew and Python 3.12+
brew install uv || pipx install uv

# Setup project
git clone <repo> && cd <repo>
uv sync
cp .env.example .env

# Verify SDKs are installed correctly
uv run python -c "import agents, mcp; print('SDKs loaded successfully')"

# Seed database
uv run python -m src.core.seed

# Run audit
uv run python -m src.agents.main_auditor audit --dry-run
```

### SDK Dependencies

This project uses three key SDKs (automatically installed via `uv sync`):

- **MCP Python SDK** (`mcp[cli]>=1.21.0`): Core MCP protocol implementation
  - Source: https://github.com/modelcontextprotocol/python-sdk
- **OpenAI Agents SDK** (`openai-agents>=0.5.0`): Agent orchestration framework
  - Source: https://github.com/openai/openai-agents-python
- **MCP Sandbox OpenAI SDK** (`mcp-sandbox-openai-sdk`): Sandbox wrapper for secure agent execution
  - Source: https://github.com/GuardiAgent/python-mcp-sandbox-openai-sdk (Git dependency)

All SDKs are configured in `pyproject.toml`. The MCP Sandbox SDK is installed from Git, so ensure you have network access and Git installed.

See `info/architecture.md` for detailed SDK documentation.

## Project Structure

```
src/
  agents/              # Manager-pattern agents (main_auditor orchestrates specialists)
  mcp_servers/         # MCP-exposed tools (db, fs, email, config)
    {name}_service.py     # Core business logic (pure functions)
    {name}_mcp_server.py  # MCP protocol wrapper
    {name}_cli.py         # CLI interface
  core/                # Schemas, policy IO, seeds, error injection
info/                  # Roadmap, project brief, grading, architecture docs
data/                  # Policy files, user CSV, MCP server config
plans/                 # Config-as-code change plans
reports/               # Audit outputs
outbox/                # "Sent" artifacts (reports, emails)
tests/                 # Test suites per stage
```

## Working with the Roadmap

This project follows a staged roadmap (`info/agentic_sec_config_roadmap.md`):

- **Stages are sequential**: Complete Stage N before starting N+1
- **Exit criteria**: Each stage has clear completion criteria
- **KISS & YAGNI**: Only build what the current stage requires
- **Contracts before code**: Schemas defined before implementation

**Current Progress**: Stage 0 ✅ | Stage 1 ✅ | Stage 2 ✅ | Stage 3+ (pending)

## Key Architectural Decisions

**MCP-First**: All side effects go through MCP servers (no direct I/O from agents)
- Transport: stdio (standard MCP pattern)
- Server API: FastMCP (automatic schema generation)
- Server structure: `{name}_service.py` → `{name}_mcp_server.py` → `{name}_cli.py`

**Manager Pattern**: `main-auditor` orchestrates specialist agents:
- `policy_interpreter`: Translates natural language → technical config
- `db_auditor`: Compares actual permissions vs policy
- `fixer`: Generates ConfigPlan for remediation
- `reporter`: Generates audit reports

**Separation of Concerns**: Service layer (`_service.py`) is independent and reusable:
- Can add REST API, web UI, or other interfaces without changing core logic
- CLI can be removed without affecting MCP server or tests
- Business logic tested independently of protocol wrappers

**Dry-Run First**: All operations default to read-only; explicit `--apply` flag required for changes.

See `info/architecture.md` for detailed architectural documentation.

## Development

```bash
# Run tests
uv run pytest

# Format code
make fmt

# Run CLI commands
uv run python -m src.mcp_servers.db_server.db_cli --help
uv run python -m src.agents.main_auditor --help
```
