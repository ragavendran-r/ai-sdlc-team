# AI SDLC Team - Multi-Agent Software Development System

[![Tests](https://github.com/YOUR-ORG/ai-sdlc-team/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR-ORG/ai-sdlc-team/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A sophisticated multi-agent AI system where specialized agents collaborate to design and scaffold complete software features from requirements through implementation.

## 🎯 Overview

The AI SDLC Team consists of 5 specialized AI agents that work together in a coordinated workflow:

- **🏢 PO Agent** - Analyzes market needs and creates detailed user stories
- **📊 EM Agent** - Plans sprints, estimates capacity, manages dependencies  
- **🎨 UX Agent** - Designs user interfaces and experience flows
- **⚙️ Backend Agent** - Designs APIs, databases, and business logic
- **💻 Frontend Agent** - Scaffolds React components and state management

Coordinated by a **Central Orchestrator** that manages events, routes data, and maintains a shared context store.

## ✨ Key Features

- **Multi-Agent Workflow**: 5 specialized agents, 59 total nodes
- **Event-Driven Architecture**: 24 event types with pub/sub pattern
- **Persistent Context Store**: Shared artifact storage with JSON backend
- **Automatic Routing**: Data flows automatically between workflows
- **Human Checkpoints**: Approval gates with rejection loops
- **Type-Safe**: 26 Pydantic schemas for all data contracts
- **Production Ready**: Docker Compose, CI/CD, monitoring integration
- **Comprehensive Tests**: 60+ test classes across all agents
- **Complete Documentation**: 10,000+ lines of guides and examples

## 🚀 Quick Start

### With Docker (Recommended)

```bash
docker-compose up -d
docker-compose run app python run_team_pipeline.py run --demo
docker-compose logs -f app
```

### Without Docker

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-your-key-here
python run_team_pipeline.py run --demo
# Starts PO (http://localhost:8001), EM (http://localhost:8002),
# UX (http://localhost:8003) web interfaces and runs the demo pipeline.
# Press Ctrl+C to stop all servers.
```

## 🖥️ Accessing each workspace

The three human-in-the-loop roles (PO, EM, UX) ship a minimal web interface
(FastAPI + Jinja2, no build step). The two developer roles stay CLI. Handoff
flows through the shared on-disk context store (`team_contracts/context-store`):
each interface writes an artifact (`backlog`, `sprint-plan`, `ux-handoff`) that
the next workspace reads — file-based handoff, since each app is its own process.

| Workspace | Interface | URL (docker-compose) | Role |
|-----------|-----------|----------------------|------|
| PO Agent | Web | http://localhost:8001 | Paste requirements → review/approve stories → publish backlog |
| EM Agent | Web | http://localhost:8002 | Read backlog → plan sprint → review/approve → publish sprint plan |
| UX Agent | Web | http://localhost:8003 | Read sprint plan → review personas/flows/wireframes → publish handoff |
| Backend Agent | CLI | — | Consumes contracts |
| Frontend Agent | CLI | — | Consumes UX handoff |

> Each web interface is a **starting point** — replace it with your team's
> preferred tool. The LangGraph workflow underneath does not change.

### Run the web workspaces together

```bash
# Bring up all three web interfaces (they share the context-store volume)
export ANTHROPIC_API_KEY=sk-your-key-here
docker compose up po_interface em_interface ux_interface
# Then open PO (8001) → publish a backlog → EM (8002) → plan a sprint → UX (8003)
```

### Run a single web workspace

```bash
# One service via Docker (PO on 8001 / EM on 8002 / UX on 8003)
docker compose up po_interface

# Or locally without Docker, from the repo root (serves http://localhost:8000)
python -m po_agent_workspace.interface.run    # or em_ / ux_agent_workspace
```

### Run the developer (CLI) workspaces

Backend and Frontend have no web UI — they consume artifacts from the context
store and run as workflows:

```bash
# Via Docker (defined as services in docker-compose.yml)
docker compose up backend_agent     # or frontend_agent

# Or locally (run from the repo root)
PYTHONPATH="$PWD" python -m backend_agent_workspace.agents.workflow
PYTHONPATH="$PWD" python -m frontend_agent_workspace.agents.workflow
```

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [QUICK_START.md](QUICK_START.md) | 5-minute getting started |
| [PROJECT_COMPLETE.md](PROJECT_COMPLETE.md) | Complete overview |
| [TEAM_ORCHESTRATOR_GUIDE.md](TEAM_ORCHESTRATOR_GUIDE.md) | Orchestrator details |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide |
| [INFRASTRUCTURE_COMPLETE.md](INFRASTRUCTURE_COMPLETE.md) | Production setup |
| [examples/README.md](examples/README.md) | Example projects |

## 🎯 Usage

```bash
# Run demo pipeline
python run_team_pipeline.py run --demo

# Check status
python run_team_pipeline.py status

# View events
python run_team_pipeline.py events

# Browse artifacts
python run_team_pipeline.py context --timeline

# Run tests
pytest . -v
```

## 📊 Statistics

- **16,535 lines** of agent code
- **60+ test classes** with comprehensive coverage
- **26 Pydantic schemas** for type-safe data
- **5 specialized agents** with 59 total nodes
- **10,000+ lines** of documentation
- **2,800 lines** of production infrastructure (Docker, CI/CD)

## 🏗️ Architecture

```
TEAM ORCHESTRATOR (Events, Store, Router)
    ├── PO Agent (User Stories)
    ├── EM Agent (Sprint Planning)
    ├── UX Agent (Component Design)
    ├── Backend Agent (API & Database)
    └── Frontend Agent (React Components)
         ↓
    CONTEXT STORE (Persistent Artifacts)
         ↓
    OUTPUT: Ready-to-implement specification
```

## 🔧 Configuration

```bash
cp .env.example .env
export ANTHROPIC_API_KEY=sk-your-key-here
```

See `.env.example` for 30+ configuration options.

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Run tests
docker-compose run app pytest . -v

# Stop services
docker-compose down
```

## 🧪 Testing

```bash
# All tests
pytest . -v

# By component (each workspace is an importable package, so no PYTHONPATH juggling)
pytest team_orchestrator/tests/ -v
pytest backend_agent_workspace/tests/ -v
pytest frontend_agent_workspace/tests/ -v

# Web interface tests
pytest po_agent_workspace/interface/tests/ -v
pytest em_agent_workspace/interface/tests/ -v
pytest ux_agent_workspace/interface/tests/ -v

# With coverage
pytest --cov --cov-report=html
```

## 📋 Example: E-Commerce Platform

```bash
python examples/ecommerce-platform/run.py
```

Demonstrates complete pipeline building user authentication:
- PO creates 3 user stories
- EM plans 6 tasks (26 story points)
- UX designs 5 components
- Backend designs 4 API endpoints + DB schema
- Frontend scaffolds 4 React components + 24 tests

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md):

```bash
git checkout -b feature/my-feature
# Make changes
pytest . -v && black . && isort .
git push origin feature/my-feature
# Create PR
```

## 📚 Learn More

1. Start: [QUICK_START.md](QUICK_START.md)
2. Explore: [examples/ecommerce-platform/](examples/ecommerce-platform/)
3. Deep dive: [PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)
4. Customize: [CONTRIBUTING.md](CONTRIBUTING.md)

## 🔐 Security

- Secrets in `.env` (never committed)
- Type-safe Pydantic validation
- CI/CD security scanning (Trivy)
- Non-root Docker containers
- Health checks on all services

## 📝 License

MIT License - See [LICENSE](LICENSE) file

## 🙋 Support

- **Docs**: See README files throughout the repo
- **Issues**: GitHub Issues
- **Examples**: [examples/](examples/) folder

---

**Built with Claude AI + LangGraph | 29,000+ lines of code, infrastructure & docs**
