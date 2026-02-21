# Synapse

**Visual Multi-Agent AI Orchestration Platform**

Design AI workflows by dragging agent nodes onto a canvas, connecting them into pipelines, and executing them with real-time streaming output. Each agent can use any LLM provider and access external tools via MCP (Model Context Protocol).

> 🚧 **Under active development** — see the [Development Tracker](./synapse-dev-tracker.md) for current status.

## Features

- 🎨 **Visual Workflow Builder** — Drag-and-drop canvas powered by React Flow
- 🤖 **Multi-Agent Pipelines** — Chain agents with different roles, prompts, and models
- 🔌 **Provider Agnostic** — OpenAI, Anthropic, Gemini, Groq, DeepSeek, OpenRouter, or any OpenAI-compatible endpoint
- ⚡ **Real-Time Streaming** — Watch agents think token-by-token via WebSocket
- 🛠️ **MCP Tool Access** — Agents can search the web, read files, call APIs via Model Context Protocol
- 📋 **Template Workflows** — Pre-built pipelines to get started in seconds

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/synapse.git
cd synapse

# 2. Start infrastructure (PostgreSQL + Redis)
docker-compose up -d

# 3. Set up backend
cd backend
cp .env.example .env          # Edit with your API keys
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head          # Run database migrations
uvicorn app.main:app --reload

# 4. Set up frontend (new terminal)
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) and start building workflows.

## Architecture

```
Frontend (React + React Flow)  ←→  WebSocket + REST  ←→  Backend (FastAPI)
                                                            ├── Execution Engine
                                                            ├── Provider Registry (OpenAI, Anthropic, ...)
                                                            ├── MCP Client (tool access)
                                                            ├── PostgreSQL (persistence)
                                                            └── Redis (state + pub/sub)
```

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for the full architecture overview.

## Adding a New LLM Provider

Synapse uses the Strategy Pattern — each provider is a single file implementing `BaseLLMProvider`. See [docs/ADDING_PROVIDERS.md](./docs/ADDING_PROVIDERS.md).

## License

MIT — see [LICENSE](./LICENSE).