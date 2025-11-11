# Control Flow: Manager Orchestrating Specialists via MCP

This document explains how the manager agent orchestrates specialist agents via the MCP protocol in our agentic security configuration system.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Manager Agent (Python Agent Object)                       │
│  Location: src/agents/main_auditor.py                       │
│  Tools: AGENT_TOOLS + FS_TOOLS                              │
│  Role: Decides which specialists to call                    │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ Uses MCP Protocol
                    │ (via call_agent_tool)
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────────┐   ┌──────────────────┐
│ Policy Interpreter│   │  DB Auditor      │
│ Agent (MCP Server)│   │  Agent (MCP      │
│                   │   │   Server)        │
│ Tool:             │   │ Tool:            │
│ interpret_policy  │   │ audit_database   │
│                   │   │                  │
│ Uses: FS_TOOLS    │   │ Uses: DB_TOOLS + │
│       (via MCP)   │   │       FS_TOOLS   │
│                   │   │       (via MCP)  │
└──────────────────┘   └──────────────────┘
        │                       │
        │ Use MCP Tools         │ Use MCP Tools
        ▼                       ▼
┌──────────────────┐   ┌──────────────────┐
│ fs_server        │   │ db_server        │
│ (MCP Server)     │   │ (MCP Server)     │
│                  │   │                  │
│ Tools:           │   │ Tools:           │
│ - fs_read_policy │   │ - db_list_tables │
│ - fs_write_*     │   │ - db_get_*       │
│ - fs_read_*      │   │ - db_who_can    │
└──────────────────┘   └──────────────────┘
```

## Step-by-Step Flow

### Step 1: Entry Point - CLI Command

**File**: `src/agents/main_auditor.py`

```python
@app.command()
def audit(dry_run: bool = True) -> None:
    """Run security audit against database configuration."""
    task_prompt = """
    Perform a complete security audit:
    1. Translate the natural language policy from policy.txt into technical access_config.yaml format
    2. Audit the database permissions by comparing expected permissions from access_config.yaml
       with actual permissions in the database
    3. Generate Findings.json and a Markdown report summarizing all violations found

    Use the specialist agents available via MCP to complete this task.
    """

    result = asyncio.run(run_audit(task_prompt=task_prompt))
```

**What happens**: User runs `python -m src.agents.main_auditor audit`, which creates a task prompt and passes it to the manager agent.

---

### Step 2: Create Manager Agent

**File**: `src/agents/main_auditor.py:17-57`

```python
def create_manager_agent() -> Agent:
    """Create the main auditor manager agent."""
    return Agent(
        name="Main Auditor",
        instructions="""
        You are the main security auditor orchestrating the audit workflow.

        Your role is to:
        1. Discover available specialist agents using list_agent_servers()
        2. Decide which agents to call based on the task
        3. Call specialist agents via MCP using call_agent_tool()
        4. Coordinate the workflow and generate reports

        Available specialist agents (discover via list_agent_servers):
        - policy_interpreter_agent: Translates policy.txt to access_config.yaml
        - db_auditor_agent: Audits database permissions and generates Findings

        Typical workflow:
        1. Call policy_interpreter_agent with interpret_policy tool to translate policy
        2. Call db_auditor_agent with audit_database tool to audit permissions
        3. Generate reports using fs_server tools

        You decide the order and which agents are needed based on the task.
        Use call_agent_tool(agent_server_id, tool_name, input) to invoke specialist agents.
        """,
        model="gpt-4o-mini",
        tools=AGENT_TOOLS + FS_TOOLS,  # ← Key: Has agent discovery/calling tools
    )
```

**Key Points**:
- Manager is a **Python Agent object** (not an MCP server)
- Has access to `AGENT_TOOLS` (discovery/calling) and `FS_TOOLS` (reporting)
- Instructions guide it to discover and call specialists via MCP
- **Non-deterministic**: Decides which agents to call based on task

---

### Step 3: Manager Runs and Discovers Agents

**File**: `src/agents/main_auditor.py:60-101`

```python
async def run_audit(task_prompt: str | None = None) -> Findings | None:
    # Create manager agent
    manager = create_manager_agent()

    # Run manager agent - it decides which specialists to call
    result = await Runner.run(manager, input=task_prompt)
```

**What happens**: The OpenAI Agents SDK executes the manager agent. The LLM decides to first discover available agents.

#### 3.1: Manager Calls `list_agent_servers()`

**File**: `src/core/mcp_tools.py:184-203`

```python
@function_tool
def list_agent_servers() -> list[dict[str, Any]]:
    """List all agent MCP servers from mcp_servers.yaml configuration."""
    config = load_mcp_config()

    # Filter for agent servers (servers with "_agent" in their ID)
    agent_servers = []
    for server_id, server_config in config.servers.items():
        if "_agent" in server_id:
            agent_servers.append({
                "server_id": server_id,
                "name": server_config.name,
                "description": server_config.description,
                "tools": server_config.tools,
            })

    return agent_servers
```

**Returns**:
```python
[
    {
        "server_id": "policy_interpreter_agent",
        "name": "Policy Interpreter Agent",
        "description": "Translates natural language policy to technical config",
        "tools": ["interpret_policy"]
    },
    {
        "server_id": "db_auditor_agent",
        "name": "Database Auditor Agent",
        "description": "Compares policy vs actual permissions and generates Findings",
        "tools": ["audit_database"]
    }
]
```

**What happens**: Manager learns about available specialist agents from `data/mcp_servers.yaml`.

---

### Step 4: Manager Calls Specialist Agent via MCP

The manager decides to call `policy_interpreter_agent` first:

#### 4.1: Manager Calls `call_agent_tool()`

**File**: `src/core/mcp_tools.py:243-259`

```python
@function_tool
def call_agent_tool(agent_server_id: str, tool_name: str, input: str) -> dict[str, Any]:
    """Call an agent tool via MCP protocol."""
    # This calls the MCP server via stdio transport
    result = _run_async(call_mcp_tool(agent_server_id, tool_name, {"input": input}))

    # Ensure result is a dict
    if isinstance(result, dict):
        return result
    return {"result": str(result)}
```

**Manager's call**:
```python
call_agent_tool(
    agent_server_id="policy_interpreter_agent",
    tool_name="interpret_policy",
    input="Translate the natural language policy from policy.txt into technical access_config.yaml format"
)
```

#### 4.2: MCP Client Connects to Agent Server

**File**: `src/core/mcp_setup.py`

```python
async def call_mcp_tool(server_id: str, tool_name: str, arguments: dict[str, Any]) -> Any:
    async with create_mcp_server_session(server_id) as session:
        result = await session.call_tool(tool_name, arguments)
        # Extract and return result
        return result
```

**What happens**:
1. Loads server config from `mcp_servers.yaml`
2. Creates stdio connection to `policy_interpreter_agent` MCP server
3. Calls `interpret_policy` tool with input prompt
4. Returns structured output

---

### Step 5: Agent MCP Server Receives Call

**File**: `src/mcp_servers/policy_interpreter_agent/policy_interpreter_mcp_server.py`

```python
from src.core.agent_mcp_server import create_agent_mcp_server
from src.mcp_servers.policy_interpreter_agent.policy_interpreter_service import (
    create_policy_interpreter_agent,
)

# Create MCP server wrapping the policy interpreter agent
mcp = create_agent_mcp_server(
    agent_name="Policy Interpreter Agent",
    agent_factory=create_policy_interpreter_agent,  # ← Function that creates Python Agent
    tool_name="interpret_policy",
    tool_description="Translate natural language policy..."
)
```

#### 5.1: Agent MCP Server Wrapper Executes

**File**: `src/core/agent_mcp_server.py:29-42`

```python
async def agent_tool(input: str) -> dict[str, Any]:
    """Execute the agent with the given input."""
    # Create the agent instance
    agent = agent_factory()  # ← Creates Policy Interpreter Agent (Python object)

    # Run the agent
    result = await Runner.run(agent, input=input)

    # Extract structured output (AccessConfig)
    if hasattr(result.final_output, 'model_dump'):
        return result.final_output.model_dump()  # ← Returns AccessConfig as dict

    return {"result": str(result.final_output)}
```

**What happens**:
1. MCP server receives call via stdio
2. Creates Python Agent instance (`create_policy_interpreter_agent()`)
3. Runs agent with `Runner.run()` (LLM execution)
4. Extracts structured output (`AccessConfig` Pydantic model)
5. Converts to dict and returns via MCP

---

### Step 6: Specialist Agent Executes

**File**: `src/mcp_servers/policy_interpreter_agent/policy_interpreter_service.py`

```python
def create_policy_interpreter_agent() -> Agent:
    return Agent(
        name="Policy Interpreter",
        instructions="Translate natural language policy to technical config...",
        model="gpt-4o-mini",
        tools=FS_TOOLS,  # ← Has access to fs_server via MCP
        output_type=AccessConfig,
    )
```

**Agent's execution**:
1. Uses `fs_read_policy()` tool (via MCP) to read `policy.txt`
2. LLM analyzes and translates policy
3. Uses `fs_write_access_config()` tool (via MCP) to write `access_config.yaml`
4. Returns `AccessConfig` as structured output

**Flow visualization**:
```
Policy Interpreter Agent (Python Agent)
    │
    │ Uses FS_TOOLS (function_tool wrappers)
    ▼
fs_read_policy() → MCP call → fs_server → Reads policy.txt
fs_write_access_config() → MCP call → fs_server → Writes access_config.yaml
    │
    ▼
Returns AccessConfig (structured output)
```

---

### Step 7: Manager Receives Result and Continues

The manager receives the `AccessConfig` dict from `policy_interpreter_agent` and decides to call the next agent:

```python
call_agent_tool(
    agent_server_id="db_auditor_agent",
    tool_name="audit_database",
    input="Audit database permissions by comparing expected permissions from access_config.yaml with actual permissions"
)
```

#### 7.1: DB Auditor Agent Executes

**File**: `src/mcp_servers/db_auditor_agent/db_auditor_service.py`

```python
def create_db_auditor_agent() -> Agent:
    return Agent(
        name="Database Auditor",
        instructions="Compare expected vs actual permissions...",
        model="gpt-4o-mini",
        tools=DB_TOOLS + FS_TOOLS,  # ← Has access to both db_server and fs_server
        output_type=Findings,
    )
```

**Agent's execution**:
1. Uses `fs_read_access_config()` to read `access_config.yaml`
2. Uses `fs_read_users_csv()` to read `users.csv`
3. Uses `db_get_privileges(username)` for each user
4. Compares expected vs actual permissions
5. Generates `Findings` with violations
6. Returns `Findings` as structured output

---

### Step 8: Manager Generates Reports

The manager receives `Findings` and generates reports using `FS_TOOLS`:

```python
# Manager calls:
fs_write_findings_json(findings_json)  # Writes reports/findings.json
fs_write_report_markdown(markdown)     # Writes reports/audit-YYYYMMDD.md
```

**File**: `src/core/mcp_tools.py`

```python
@function_tool
def fs_write_findings_json(findings_json: str, path: str | None = None) -> str:
    """Write Findings JSON to file."""
    return _run_async(call_mcp_tool("fs_server", "fs_write_findings_json", {
        "findings_json": findings_json,
        "path": path
    }))
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CLI: python -m src.agents.main_auditor audit                │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Create Manager Agent                                        │
│    - Python Agent object                                        │
│    - Tools: AGENT_TOOLS + FS_TOOLS                             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Runner.run(manager, input=task_prompt)                      │
│    LLM decides to discover agents                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Manager calls list_agent_servers()                          │
│    Returns: [policy_interpreter_agent, db_auditor_agent]       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Manager calls call_agent_tool(                              │
│      "policy_interpreter_agent",                                │
│      "interpret_policy",                                        │
│      "Translate policy..."                                      │
│    )                                                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. MCP Client connects to policy_interpreter_agent MCP server  │
│    (via stdio transport)                                        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Agent MCP Server:                                            │
│    - Creates Python Agent (create_policy_interpreter_agent)    │
│    - Runs Runner.run(agent, input=input)                       │
│    - Returns AccessConfig as dict                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Policy Interpreter Agent executes:                           │
│    - fs_read_policy() → fs_server → Reads policy.txt          │
│    - LLM translates policy                                      │
│    - fs_write_access_config() → fs_server → Writes YAML        │
│    - Returns AccessConfig                                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. Manager receives AccessConfig, calls db_auditor_agent        │
│    call_agent_tool("db_auditor_agent", "audit_database", ...) │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. DB Auditor Agent executes:                                 │
│     - fs_read_access_config() → Reads access_config.yaml       │
│     - fs_read_users_csv() → Reads users.csv                    │
│     - db_get_privileges() → Queries database                  │
│     - Compares and generates Findings                          │
│     - Returns Findings                                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. Manager generates reports:                                  │
│     - fs_write_findings_json() → Writes findings.json          │
│     - fs_write_report_markdown() → Writes audit report          │
└─────────────────────────────────────────────────────────────────┘
```

## Key Differences: Before vs After

### Before (Deterministic Approach)

```python
async def run_audit_workflow(dry_run: bool = True) -> Findings:
    # Step 1: Direct Python function call
    access_config = await interpret_policy()  # ← Direct call

    # Step 2: Direct Python function call
    findings = await audit_database()          # ← Direct call

    # Step 3: Direct function call
    await generate_reports(findings)

    return findings
```

**Problems**:
- Fixed sequence (deterministic)
- Direct Python function calls (not via MCP)
- Manager doesn't make decisions
- Agents not discoverable

### After (Agentic MCP Approach)

```python
async def run_audit(task_prompt: str | None = None) -> Findings | None:
    # Create manager agent
    manager = create_manager_agent()

    # Run manager - it decides which specialists to call
    result = await Runner.run(manager, input=task_prompt)

    # Manager internally:
    # 1. Discovers agents via list_agent_servers()
    # 2. Calls call_agent_tool("policy_interpreter_agent", "interpret_policy", ...)
    # 3. Calls call_agent_tool("db_auditor_agent", "audit_database", ...)
    # 4. Generates reports via fs_server tools
```

**Benefits**:
- ✅ **Non-deterministic**: Manager decides order and which agents to call
- ✅ **Discoverable**: Agents registered in `mcp_servers.yaml`
- ✅ **Modular**: Specialist agents are independent MCP servers
- ✅ **Scalable**: Agents can run on different machines
- ✅ **MCP-first**: All agent-to-agent communication via MCP protocol

## Communication Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Manager Agent (Python Agent Object)                │
│ - Uses AGENT_TOOLS to discover/call specialists             │
│ - Uses FS_TOOLS to generate reports                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Function Tools (function_tool)
                            │
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: MCP Tools Wrapper (src/core/mcp_tools.py)          │
│ - call_agent_tool() → calls MCP client                       │
│ - list_agent_servers() → reads mcp_servers.yaml             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ MCP Protocol (stdio transport)
                            │
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Agent MCP Servers                                   │
│ - policy_interpreter_agent_mcp_server.py                    │
│ - db_auditor_agent_mcp_server.py                            │
│ - Wraps Python Agents as MCP servers                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Creates Python Agent
                            │
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Specialist Agents (Python Agent Objects)           │
│ - policy_interpreter_service.py                             │
│ - db_auditor_service.py                                     │
│ - Use MCP tools (FS_TOOLS, DB_TOOLS) via function_tool     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ MCP Protocol
                            │
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Service MCP Servers                                 │
│ - fs_server (file operations)                                │
│ - db_server (database queries)                               │
└─────────────────────────────────────────────────────────────┘
```

## Summary

The manager agent orchestrates specialist agents through a multi-layer MCP-based architecture:

1. **Manager Agent** (Python Agent) receives task prompt
2. **Discovers** available specialist agents via `list_agent_servers()`
3. **Decides** which agents to call and in what order (non-deterministic)
4. **Calls** specialist agents via `call_agent_tool()` (MCP protocol)
5. **Specialist Agents** (MCP servers) wrap Python Agents
6. **Python Agents** execute using MCP tools (fs_server, db_server)
7. **Manager** coordinates results and generates reports

This architecture ensures:
- **True agentic behavior**: Manager makes decisions
- **MCP-first communication**: All agent-to-agent via MCP
- **Modularity**: Agents are independent services
- **Discoverability**: Agents registered in configuration
- **Scalability**: Can distribute agents across machines
