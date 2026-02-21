# Synapse — Development Tracker

**Started:** 2026-02-19  
**Current Phase:** M2 — Canvas + Agent Config  
**Next Action:** Begin Milestone 2 — Agent node components, sidebar palette, config panel  

---

## Build Progress

### Milestone 1: Foundation ✅ Complete

| Task | Status | Notes |
|------|--------|-------|
| Initialize monorepo structure | ✅ | Root + frontend/ + backend/ + docs/ |
| docker-compose.yml (Postgres + Redis) | ✅ | Both healthy, removed deprecated `version` key |
| .env.example, .gitignore, README.md | ✅ | |
| Backend: pyproject.toml | ✅ | Fixed build-backend path for setuptools |
| Backend: Pydantic settings (config.py) | ✅ | Reads from .env, cached via lru_cache |
| Backend: Structured logging (structlog) | ✅ | JSON in prod, colored in dev |
| Backend: Custom exception hierarchy | ✅ | SynapseError base → NotFound, Provider, Execution errors |
| Backend: Security utils (Fernet encryption) | ✅ | For API key encryption at rest |
| Backend: Async DB engine + session factory | ✅ | asyncpg + SQLAlchemy async sessions |
| Backend: Base model (id, timestamps) | ✅ | UUID PK, created_at, updated_at |
| Backend: Workflow model | ✅ | Workflow, AgentNode, Edge |
| Backend: Execution models | ✅ | WorkflowExecution, AgentExecution with state enums |
| Backend: Provider config model | ✅ | Encrypted API key storage |
| Backend: models/__init__.py barrel export | ✅ | Fixed circular import between workflow↔execution |
| Backend: dependencies.py (DI providers) | ✅ | get_db, get_redis, get_config |
| Backend: FastAPI app factory (main.py) | ✅ | CORS, lifespan, exception handlers, health check |
| Backend: Alembic setup | ✅ | Fixed env.py to use create_async_engine directly |
| Database: Initial migration (6 tables) | ✅ | workflows, agent_nodes, edges, workflow_executions, agent_executions, provider_configs |
| Verify backend health check | ✅ | `curl /api/health` → `{"status":"ok"}` |
| Frontend: Vite + React + TS + Tailwind | ✅ | Vite 7, React 18, Tailwind via @tailwindcss/vite |
| Frontend: Install React Flow, Zustand, Lucide icons | ✅ | reactflow, zustand, lucide-react, axios |
| Basic React Flow canvas rendering (empty) | ✅ | 4 demo nodes with animated edges, dark theme |
| Verify full stack connects end-to-end | ✅ | Green "API Connected" indicator in header |

### Milestone 2: Canvas + Agent Config ⬜ Not Started
| Task | Status | Notes |
|------|--------|-------|
| Agent node sidebar palette (drag source) | ⬜ | |
| Custom AgentNode component for React Flow | ⬜ | |
| Custom InputNode component (workflow entry point) | ⬜ | |
| Edge connection with validation (no cycles) | ⬜ | |
| Agent configuration side panel | ⬜ | |
| Provider + model dropdown in config panel | ⬜ | |
| System prompt textarea with defaults per agent type | ⬜ | |
| Workflow CRUD API endpoints | ⬜ | |
| Save workflow (canvas → API → DB) | ⬜ | |
| Load workflow (DB → API → canvas) | ⬜ | |
| Zustand stores: workflowStore, providerStore | ⬜ | |

### Milestone 3: Execution Engine ⬜ Not Started
| Task | Status | Notes |
|------|--------|-------|
| DAG validation utility (frontend + backend) | ⬜ | |
| Topological sort for execution ordering | ⬜ | |
| BaseLLMProvider abstract class | ⬜ | |
| OpenAI provider implementation | ⬜ | |
| Anthropic provider implementation | ⬜ | |
| Provider registry + factory | ⬜ | |
| Execution engine: sequential agent runner | ⬜ | |
| WebSocket endpoint for streaming | ⬜ | |
| Frontend WebSocket hook (useWebSocket) | ⬜ | |
| Execution panel UI | ⬜ | |
| Agent output streaming display | ⬜ | |
| Node status indicators on canvas (color) | ⬜ | |
| Cancel execution (client → server) | ⬜ | |
| Error handling: provider failures, timeouts | ⬜ | |

### Milestone 4: Polish + Deploy ⬜ Not Started
| Task | Status | Notes |
|------|--------|-------|
| MCP client integration | ⬜ | |
| MCP web search tool (Brave/Tavily) | ⬜ | |
| MCP server config UI | ⬜ | |
| Provider settings page (API key management) | ⬜ | |
| API key encryption (AES-256) | ⬜ | |
| Template: Research-Write-Critique-Edit | ⬜ | |
| Template: LinkedIn Publisher | ⬜ | |
| Template gallery UI | ⬜ | |
| Loading states, error states, empty states | ⬜ | |
| Responsive layout (desktop-first, viewable on mobile) | ⬜ | |
| Deploy frontend to Vercel | ⬜ | |
| Deploy backend to Railway | ⬜ | |
| Seed demo data | ⬜ | |
| README with screenshots + architecture diagram | ⬜ | |
| .env.example files | ✅ | Root + backend |
| MIT LICENSE file | ⬜ | |

### Milestone 5: Post-Weekend ⬜ Not Started
| Task | Status | Notes |
|------|--------|-------|
| Gemini provider | ⬜ | |
| Groq provider | ⬜ | |
| DeepSeek provider | ⬜ | |
| OpenRouter provider | ⬜ | |
| Custom endpoint provider | ⬜ | |
| Template: GitHub Repo Monitor | ⬜ | |
| Template: Code Review Agent | ⬜ | |
| Execution history page | ⬜ | |
| Export workflow as Python code | ⬜ | |
| CONTRIBUTING.md | ⬜ | |
| ADDING_PROVIDERS.md guide | ⬜ | |
| Loom walkthrough video | ⬜ | |
| Open Graph meta tags for link previews | ⬜ | |
| Write LinkedIn post announcing the project | ⬜ | |

---

## Architecture Decision Log

| ID | Decision | Date | Rationale |
|----|----------|------|-----------|
| ADR-001 | React Flow for canvas | 2026-02-19 | Most mature React node-graph library, 30K+ stars |
| ADR-002 | FastAPI + WebSocket backend | 2026-02-19 | Python is AI lingua franca, native async + WS |
| ADR-003 | Provider-agnostic LLM layer | 2026-02-19 | Strategy pattern — one file per provider |
| ADR-004 | WebSocket over SSE/polling | 2026-02-19 | Bidirectional (cancel support), lower overhead |
| ADR-005 | MCP for tool access | 2026-02-19 | Emerging standard, backed by Anthropic |
| ADR-006 | DAG workflow model | 2026-02-19 | Guaranteed termination, deterministic order |
| ADR-007 | State machine for execution | 2026-02-19 | Clear lifecycle, easier debugging |

---

## Issues Encountered & Resolved

| Issue | Resolution | Date |
|-------|-----------|------|
| docker-compose `version` key deprecated warning | Removed `version: "3.9"` from docker-compose.yml | 2026-02-21 |
| `setuptools.backends._legacy` import error | Changed build-backend to `setuptools.build_meta` | 2026-02-21 |
| Python 3.14 incompatible with some deps | Switched to Python 3.12 venv | 2026-02-21 |
| Alembic migration file generated empty | Replaced script.py.mako with Alembic's built-in template | 2026-02-21 |
| Alembic autogenerate produced empty upgrade() | Rewrote env.py to use `create_async_engine` directly instead of `async_engine_from_config` | 2026-02-21 |
| Circular import: workflow.py ↔ execution.py | Removed bottom-of-file cross-imports; SQLAlchemy resolves string refs via registry | 2026-02-21 |

---

## Concepts Learned

| Concept | Where Used | Summary |
|---------|-----------|---------|
| Docker & Docker Compose | Infrastructure | Containers isolate Postgres + Redis; docker-compose manages both |
| pyproject.toml | Backend | Modern Python package config, replaces setup.py + requirements.txt |
| FastAPI | Backend | Async web framework with auto-validation, docs, WebSocket support |
| Pydantic | Backend | Data validation via type hints; used for schemas, config, responses |
| CORS | Backend middleware | Allows frontend (port 5173) to call backend (port 8000) |
| Health checks | Backend + Docker | Endpoint to verify service is alive; used by deployment platforms |
| Lifespan events | FastAPI | Startup/shutdown hooks for DB pools, Redis connections |
| SQLAlchemy ORM | Backend models | Python classes map to database tables; async with asyncpg |
| Alembic | Database migrations | Version control for DB schema; autogenerate detects model changes |
| Redis | Execution state + pub/sub | In-memory store for real-time streaming and temp state |
| Fernet encryption | API key storage | Symmetric encryption for provider API keys at rest |
| Strategy Pattern | LLM providers | One interface, many implementations — swap providers at runtime |
| DAG | Workflow model | Directed Acyclic Graph — guarantees termination, enables topo sort |
| State Machine | Execution lifecycle | Clear status transitions for workflows and agents |

---

## Feedback Log

| Date | Phase | Feedback | Action Taken |
|------|-------|----------|-------------|
| | | *(Will be filled as we build)* |

---

# File Registry

> Every file in the project, its purpose, and its status. Updated as files are created.

## Root Files
| File | Purpose | Status |
|------|---------|--------|
| `README.md` | Project overview, setup guide | ✅ Skeleton |
| `docker-compose.yml` | Local dev: PostgreSQL + Redis | ✅ |
| `.env.example` | Root env vars template | ✅ |
| `.gitignore` | Git ignore rules | ✅ |
| `LICENSE` | MIT License | ⬜ |

## Backend — `backend/`
| File | Purpose | Status |
|------|---------|--------|
| `pyproject.toml` | Python deps + metadata | ✅ |
| `alembic.ini` | Alembic migration config | ✅ |
| `.env.example` | Backend env vars template | ✅ |
| `.env` | Actual env vars (git-ignored) | ✅ |
| | | |
| **App Core — `app/`** | | |
| `__init__.py` | Package init | ✅ |
| `main.py` | FastAPI app factory | ✅ |
| `config.py` | Pydantic settings | ✅ |
| `dependencies.py` | Shared DI providers | ✅ |
| | | |
| **Core — `app/core/`** | | |
| `__init__.py` | Package init | ✅ |
| `exceptions.py` | Custom exception hierarchy | ✅ |
| `logging.py` | Structured logging (structlog) | ✅ |
| `security.py` | Fernet encryption utils | ✅ |
| | | |
| **Database — `app/db/`** | | |
| `__init__.py` | Package init | ✅ |
| `session.py` | Async engine + session factory | ✅ |
| `migrations/env.py` | Alembic environment config | ✅ |
| `migrations/script.py.mako` | Migration file template | ✅ |
| `migrations/versions/9db79cf61e01_*.py` | Initial tables migration | ✅ |
| | | |
| **Models — `app/models/`** | | |
| `__init__.py` | Barrel export of all models | ✅ |
| `base.py` | Base model (UUID, timestamps) | ✅ |
| `workflow.py` | Workflow, AgentNode, Edge | ✅ |
| `execution.py` | WorkflowExecution, AgentExecution | ✅ |
| `provider.py` | ProviderConfig | ✅ |
| | | |
| **Schemas — `app/schemas/`** | | |
| `__init__.py` | Package init | ✅ |
| | | |
| **Services — `app/services/`** | | |
| `__init__.py` | Package init | ✅ |
| | | |
| **Providers — `app/providers/`** | | |
| `__init__.py` | Package init | ✅ |
| | | |
| **MCP — `app/mcp/`** | | |
| `__init__.py` | Package init | ✅ |
| | | |
| **API Routes — `app/api/`** | | |
| `__init__.py` | Package init | ✅ |
| `v1/__init__.py` | Package init | ✅ |
| | | |
| **Tests — `tests/`** | | |
| `__init__.py` | Package init | ✅ |
| `conftest.py` | Pytest fixtures | ✅ Empty |

## Frontend — `frontend/`
| File | Purpose | Status |
|------|---------|--------|
| `package.json` | Node deps + scripts | ✅ |
| `vite.config.ts` | Vite config with API proxy + Tailwind | ✅ |
| `tsconfig.json` | TypeScript config (strict) | ✅ |
| `.env.example` | Frontend env vars template | ✅ |
| `.env` | Actual env vars (git-ignored) | ✅ |
| `src/main.tsx` | React entry point | ✅ |
| `src/index.css` | Tailwind imports + base styles | ✅ |
| `src/App.tsx` | App shell with header + React Flow canvas | ✅ |

## Documentation — `docs/`
| File | Purpose | Status |
|------|---------|--------|
| `ARCHITECTURE.md` | ⬜ Architecture overview + diagrams |
| `CONTRIBUTING.md` | ⬜ Contribution guide |
| `ADDING_PROVIDERS.md` | ⬜ How to add a new LLM provider |
| `ADDING_AGENT_TYPES.md` | ⬜ How to add a new agent type |