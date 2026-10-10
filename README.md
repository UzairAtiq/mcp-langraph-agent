# LinkedIn Post Automation Agent

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/UzairAtiq/mcp-langraph-agent)

An automated, human-in-the-loop pipeline that generates technical and engaging LinkedIn posts using Groq LLMs, delivers interactive approval cards to Slack with yes/no buttons, and publishes approved posts to LinkedIn.

The system is built with **LangGraph**, **Model Context Protocol (MCP)** tool servers, **FastAPI**, persistent PostgreSQL / SQLite token storage with automated token refreshes, and a **React 18 + Vite** dashboard.

---

## Architecture Overview

```
User Prompt / Web Dashboard -> LangGraph Agent -> Groq LLM (Generates Post)
                                     |
                                     v
                 Persistent Database (PostgreSQL / SQLite) [status: pending]
                                     |
                                     v
                 Slack Webhook (Block Kit with Approve/Discard Buttons)
                                     |
                                     v
                 User clicks "Approve" in Slack
                                     |
                                     v
                 Slack POST -> FastAPI (/slack/interactions)
                                     |
                                     v
                 Database updated [status: approved] -> Auto-Refreshes Token if needed
                                     |
                                     v
                 Publishes to LinkedIn API -> Replaces Slack card with confirmation
```

---

## Documentation

Comprehensive guides are organized in the [`docs/`](file:///Users/uzair/Developer/mcp-langraph-agent/docs) directory:

* **[Project Structure & Architecture](file:///Users/uzair/Developer/mcp-langraph-agent/docs/PROJECT_STRUCTURE.md)**: Full codebase directory breakdown, data flow, and file map.
* **[LinkedIn App & OAuth Setup](file:///Users/uzair/Developer/mcp-langraph-agent/docs/linkedin_setup.md)**: Developer app creation, permissions, 1-click connect, and 60-day token lifecycle.
* **[Slack App & Interactivity Setup](file:///Users/uzair/Developer/mcp-langraph-agent/docs/slack_setup.md)**: Webhooks, Block Kit approval cards, ngrok setup, and interaction callbacks.
* **[Render Cloud Deployment](file:///Users/uzair/Developer/mcp-langraph-agent/docs/deployment.md)**: 1-click Blueprint deployment, managed PostgreSQL, and environment variables.

---

## Quickstart (Local Development)

### 1. Prerequisites
* Python 3.11 or 3.12
* Node.js 18+ (for frontend dashboard)
* LinkedIn Developer App credentials
* Slack Workspace with Incoming Webhook and Interactivity enabled
* Groq API key

### 2. Setup Environment

```bash
# Clone repository
git clone https://github.com/UzairAtiq/mcp-langraph-agent.git
cd mcp-langraph-agent

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r project/backend/requirements.txt

# Configure environment variables
cp .env.example .env
```

Fill in required keys in `.env`:
* `GROQ_API_KEY`: Groq API key
* `SLACK_WEBHOOK_URL`: Slack Incoming Webhook URL
* `LINKEDIN_CLIENT_ID`: LinkedIn Developer Client ID
* `LINKEDIN_CLIENT_SECRET`: LinkedIn Developer Client Secret

### 3. Build Frontend & Run Backend

```bash
# Build React dashboard bundle
cd project/frontend
npm install
npm run build
cd ../backend

# Run FastAPI server
uvicorn main:app --reload --port 8000
```

Open `http://localhost:8000` to view the dashboard and connect your LinkedIn account.

### 4. Run LangGraph Agent

```bash
python -m agent.graph
```

---

## Repository Structure

```
mcp-langraph-agent/
├── README.md               # Main project documentation and quickstart
├── render.yaml             # Render Blueprint infrastructure configuration
├── .gitignore              # Git ignore rules
├── project/
│   ├── backend/            # FastAPI, LangGraph agent, MCP servers, data, and tests
│   │   ├── agent/          # State graph, workflow nodes, and tool adapters
│   │   ├── api/            # API entrypoints
│   │   ├── config/         # App constants and settings
│   │   ├── data/           # SQLite / PostgreSQL persistence and token store
│   │   ├── mcp_servers/    # Stdio MCP servers (db, slack, post_generator)
│   │   ├── observability/  # Langfuse tracing
│   │   ├── services/       # Integrations for Groq, LinkedIn, and Slack
│   │   ├── tests/          # Test suite
│   │   ├── main.py         # Unified FastAPI application
│   │   └── requirements.txt# Backend dependencies
│   └── frontend/           # React 18 + Vite + Tailwind dashboard
├── evals/                  # Benchmark evaluations and LLM-as-a-judge tests
├── docs/                   # Setup guides and architecture documentation
└── _notes/                 # Plans, prompts, and knowledge graph analysis
```

---

## Running Tests & Evaluations

```bash
# Run unit tests across agent and MCP servers
pytest project/backend/tests/test_agent.py
pytest project/backend/tests/test_mcp_servers.py

# Run benchmark evaluation suite
python evals/run_evals.py
```
