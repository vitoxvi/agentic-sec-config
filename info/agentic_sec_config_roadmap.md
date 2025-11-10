# Agentic Security Audit – Developer Roadmap

## Guiding Principles
- **KISS & YAGNI:** Keep the system as small as possible; add only what the current stage requires.
- **Manager pattern:** `main-auditor` orchestrates specialist agents (policy-interpreter, db-auditor, fixer, reporter).
- **MCP-first + Sandbox:** All side effects exposed via MCP servers and executed through the MCP Sandbox OpenAI SDK wrapper. No direct raw I/O from agents.
- **Least privilege, dry-run by default:** Readers by default; explicit gated apply when needed.
- **Contracts before code:** Define JSON schemas for `Policy`, `Findings`, and `ChangePlan`/`ConfigPlan` before agent logic.
- **Reproducible demos:** Seeds, error injections, and reports are deterministic and scripted.
- **Student scope:** Ship simple CLI + Markdown/PDF reports; no heavy GUI unless time allows.

---

## Repo Skeleton
```
/agentic-sec-config/
  README.md
  pyproject.toml
  uv.lock
  .env.example
  /info/                      # roadmap, project-brief, grading, architecture notes
    roadmap.md
    project-brief.md
    grading-scheme.md
    architecture.md
  /src/
    /agents/
      main_auditor.py
      policy_interpreter.py
      db_auditor.py
      fixer.py
      reporter.py
    /mcp_servers/
      db_server/
      fs_server/
      email_server/
      config_server/
    /core/
      schemas.py
      policy_io.py
      seed.py
      error_injection.py
  /infra/
    docker-compose.yml
    scripts/              # macOS setup/demo scripts
  /data/
    policy/policy.yaml
    users/users.csv
  /plans/
  /reports/
  /outbox/
  /tests/
```

---

## Stage 0 — Environment & Tooling (single-dev bootstrap)
**Goal:** Clean macOS setup using `uv`, OpenAI Agent SDK, MCP python SDK, and the MCP Sandbox OpenAI SDK wrapper.

**Tasks:**
- Initialize repo structure (including `/info`) and commit `info/roadmap.md`, `info/project-brief.md`, and `info/grading-scheme.md`.
- Install `uv`; create project with `uv init`; add dependencies:
  ```bash
  uv add openai-agents mcp pydantic[dotenv] typer rich pytest
  ```
- Create `.env.example` (API key placeholders, DB URL, OUTPUT paths).
- Add style formatting (ruff/black) via Makefile targets.
- Minimal MCP hello

**Exit criteria:**
- Fresh clone: `uv sync` works on macOS.
- `uv run python -c "import agents, mcp"` prints OK.
- `/info` folder contains roadmap/brief/grading files.

---

## Stage 1 — Baseline Data & Policy Surface (single-dev bootstrap)
**Goal:** Minimal yet realistic world to audit: schema, seeds, fake AD, initial policy; all through MCP.

**Tasks:**
- Database: SQLite (YAGNI); optional Postgres in `docker-compose.yml`.
- Schema: `accounts, transactions, customers, orders, stock, procurement`.
- Seed scripts: deterministic `src/core/seed.py` populates tables.
- Fake AD: `data/users/users.csv` listing users, team, role.
- Initial Policy: `data/policy/policy.yaml` mapping teams → tables/actions.
- MCP DB server: expose `list_tables`, `get_privileges`, `who_can(table)`.
- Tests: policy schema validation + seed smoke test.

**Exit criteria:**
- `uv run python -m src.core.seed` succeeds.
- `uv run python -m src.mcp_servers.db_server.db_cli --list` shows tables.
- Policy validates.

---

## Stage 2 — Contracts & Agent Skeleton
**Goal:** Formalize interfaces, scaffold agents using the manager pattern, and expose Stage 1 functions as MCP tools.

**Tasks:**
- Define Pydantic/JSON schemas: `Findings`, `ConfigPlan` (Policy schema already done in Stage 1).
- Establish MCP tools: Wrap existing `db_server` functions (`list_tables`, `get_privileges`, `who_can`) as MCP tools using MCP Python SDK.
  - Create MCP server implementation in `src/mcp_servers/db_server/db_mcp_server.py` exposing tools with proper JSON schemas.
  - Tools should be callable via MCP protocol (not just CLI).
- Implement `main-auditor` (OpenAI Agent SDK) invoking specialists via MCP.
- Add CLI entrypoint: `uv run python -m src.agents.main_auditor audit --dry-run`.

**Exit criteria:**
- MCP tools registered: `db_server` exposes `list_tables`, `get_privileges`, `who_can` as MCP tools with schemas.
- Running `audit --dry-run` produces empty findings on a clean DB and a stub report.
- Agents can call MCP tools (verified via test or manual check).

---

## Stage 3 — Auditor MVP
**Goal:** Detect mismatches between policy and live privileges.

**Tasks:**
- Map CSV users → DB roles; compare to policy.
- Produce `Findings.json` and Markdown summary.
- Add `src/core/error_injection.py` for deterministic misconfigs.
- Tests: inject → audit → stable findings.

**Exit criteria:**
- Audit generates findings + report with stable IDs.

---

## Stage 4 — Reporting
**Goal:** Consumable report with access matrix and summaries.

**Tasks:**
- `reporter` writes `reports/audit-YYYYMMDD.md` with violations + access matrix.
- Email MCP server “sends” by writing to `/outbox`.

**Exit criteria:**
- After `audit`, `/outbox` contains a timestamped report referencing findings.

---

## Stage 5 — Fixer as Config-as-Code
**Goal:** Agent writes reviewable, versionable plan; human approves; sandboxed apply.

**Tasks:**
- `fixer` produces `plans/YYYYMMDD-changeplan.yaml` (config-as-code).
- Each item includes target, proposed change, rationale, risk, inverse op.
- `config_server` supports `plan()` and `apply(plan_path)` (gated).
- CLI prompt: `--apply` requires typing `APPROVE`.
- All changes logged.

**Exit criteria:**
- Plan files are versioned.
- Apply fixes errors; re-audit clean.
- Rollback plan generated.

---

## Stage 6 — Lifecycle (Onboarding/Offboarding)
**Goal:** Reconcile policy when users join/leave or move teams.

**Tasks:**
- Detect changes in `users.csv`; produce appropriate `ConfigPlan`.
- Test joiner/mover/leaver cases.

**Exit criteria:**
- Lifecycle events yield minimal diffs; apply + re-audit clean.

---

## Stage 7 — Extensions (Optional)
- Add new resource via MCP (e.g. bucket ACLs).
- Tiny UI (Streamlit/Gradio) for running audit → report → apply.

**Exit criteria:**
- Extra resource or UI runs full pipeline.

---

## Stage 8 — Security Proof & Grading Mapping
**Goal:** Demonstrate sandbox protections and align with grading.

**Tasks:**
- Show sandbox denials in logs.
- Secrets via `.env` only.
- `/info/architecture.md`: mapping for A1/A2, B1–B4.

**Exit criteria:**
- One-page “Security & Grading Notes” with runnable denial test.

---

## Stage 9 — Demo Runbook & Packaging
**Goal:** Simple evaluation on macOS.

**Tasks:**
- `/infra/scripts/setup.sh` and `/infra/scripts/demo.sh`.
- README: copy-paste setup commands.
- Finalize `/info/roadmap.md` with real outputs.

**Exit criteria:**
- Fresh clone to working demo with ≤3 commands.

---

## Copy-Paste Commands (after Stage 1)
**macOS**
```bash
brew install uv || pipx install uv
git clone <repo> && cd <repo>
uv sync && cp .env.example .env
uv run python -m src.core.seed
uv run python -m src.agents.main_auditor audit --dry-run
```
