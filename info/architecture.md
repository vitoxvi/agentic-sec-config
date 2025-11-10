# Architecture Notes

## TL;DR - Hard Facts

**Transport**: stdio (standard MCP pattern)
**Server API**: FastMCP (high-level, automatic schema generation)
**Server Structure**: `{name}_service.py` (functions) → `{name}_mcp_server.py` (MCP wrapper) → `{name}_cli.py` (CLI)
**Tool Registration**: `@mcp.tool()` decorator with automatic JSON schema from type hints
**Server Config**: `data/mcp_servers.yaml` (centralized registry)
**Client Pattern**: `stdio_client` + `ClientSession` (async context managers)
**Database**: SQLite (`data/audit.db`, gitignored)
**Package Manager**: `uv`
**Agent SDK**: OpenAI Agents SDK + MCP Sandbox SDK
**Pattern**: Manager (main-auditor) → Specialist agents (policy_interpreter, db_auditor, fixer, reporter)
**Communication**: All side effects via MCP servers (MCP-first principle)
**Schemas**: Pydantic models in `src/core/schemas.py` (Findings, ConfigPlan, AccessConfig)

## Core Principles
- Manager pattern: main-auditor -> specialist agents
- MCP-first: all side effects via servers
- Least privilege and dry-run-first
- Contracts before code: Schemas defined before implementation

## SDK Overview

To install a certain level of guardrails around our project we are using:
- https://github.com/GuardiAgent/python-mcp-sandbox-openai-sdk
  which provides an SDK to use an MCP sandbox in conjunction with the OpenAI Agent SDK.

The OpenAI Agent SDK which we are going to use is:
- https://github.com/openai/openai-agents-python

To connect components inside the project and calling external services we will use the MCP Protocol.
There's an SDK for python: https://github.com/modelcontextprotocol/python-sdk

## MCP Architecture Decisions

### Transport: stdio (Standard MCP Pattern)
- **Decision**: All MCP servers use **stdio transport** (standard MCP pattern)
- **Rationale**:
  - Simplest and most portable transport
  - Works across platforms without network configuration
  - Standard pattern for MCP servers (see MCP SDK README: "Direct Execution" section)
- **Implementation**: Servers use `mcp.run()` which defaults to stdio transport
- **Example**: `src/mcp_servers/db_server/db_mcp_server.py` uses `FastMCP` with `mcp.run()`

### Server Implementation: FastMCP (High-Level API)
- **Decision**: Use **FastMCP** (high-level API) instead of low-level Server API
- **Rationale**:
  - Automatic JSON schema generation from function signatures
  - Simpler tool registration with `@mcp.tool()` decorator
  - Built-in structured output support for Pydantic models
  - Less boilerplate code
- **Reference**: MCP SDK README "Quickstart" and "Tools" sections

### Server Structure Pattern
Each MCP server follows this structure:
```
src/mcp_servers/{server_name}/
  {server_name}_service.py      # Core functions (reusable, importable)
  {server_name}_mcp_server.py    # MCP server wrapper (FastMCP, stdio transport)
  {server_name}_cli.py           # CLI interface (optional, for manual testing)
```

**Example**: `db_server/`
- `db_service.py`: Functions `list_tables()`, `get_privileges()`, `who_can()`
- `db_mcp_server.py`: FastMCP server wrapping functions as MCP tools
- `db_cli.py`: CLI for manual testing

**Rationale**:
- Separation of concerns: functions vs MCP wrapper vs CLI
- Clear naming: `_service.py` = business logic, `_mcp_server.py` = MCP interface, `_cli.py` = CLI
- Functions can be imported directly (for tests, CLI, or other code)
- MCP server imports functions from `_service.py` (DRY principle)
- CLI can also import functions for manual operations

### Tool Registration
- **Pattern**: Use `@mcp.tool()` decorator on functions
- **Schema Generation**: Automatic from function type hints
- **Return Types**: Can return Pydantic models for structured output
- **Example**:
  ```python
  @mcp.tool()
  def db_list_tables() -> list[str]:
      """List all tables."""
      return list_tables()
  ```

### MCP Server Configuration
- **Location**: `data/mcp_servers.yaml`
- **Purpose**: Centralized registry of available MCP servers
- **Structure**: Maps server IDs to configuration (name, description, command, tools)
- **Usage**: Agents load config to discover and connect to servers
- **Rationale**: Modular and extensible - easy to add new servers without code changes

### Client Connection Pattern
Agents connect to MCP servers using:
```python
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import ClientSession

server_params = StdioServerParameters(
    command=["python", "-m", "src.mcp_servers.db_server.db_mcp_server"],
    args=[]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("db_list_tables", {})
```

**Reference**: MCP SDK README "Writing MCP Clients" section

## Data Schemas

### Policy & Access Configuration
- **Natural Language Policy**: `data/policy/policy.txt` (business-level description)
- **Technical Config**: `data/policy/access_config.yaml` (translated to technical format)
- **Schema**: `AccessConfig` in `src/core/schemas.py`
- **Note**: Policy interpreter (Stage 2+) will translate natural language → technical config

### Findings Schema
- **Model**: `Finding` and `Findings` in `src/core/schemas.py`
- **Fields**: id, severity, type, user, resource, action, description, recommendation, affected_resources
- **Purpose**: Structured representation of audit violations

### ConfigPlan Schema
- **Model**: `Change` and `ConfigPlan` in `src/core/schemas.py`
- **Fields**: id, target, operation (GRANT/REVOKE), resource, action, rationale
- **Purpose**: Config-as-code representation of proposed changes

## Agent Architecture

### Manager Pattern
- **main-auditor**: Orchestrates specialist agents
- **Specialist agents**:
  - `policy_interpreter`: Translates natural language policy → technical config
  - `db_auditor`: Compares actual permissions vs policy
  - `fixer`: Generates ConfigPlan for remediation
  - `reporter`: Generates audit reports

### Agent Communication
- Agents communicate via **MCP protocol** (not direct function calls)
- Agents discover servers via `data/mcp_servers.yaml` configuration
- All side effects go through MCP servers (MCP-first principle)

## Environment Notes
- Use .env file to store environment variables
- Use .gitignore to avoid committing sensitive information
- Using uv manager to manage python project environment
- Using sqlite for local development database
- Database file: `data/audit.db` (gitignored)
