# LinkedIn Post Automation Agent

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/UzairAtiq/mcp-langraph-agent)

An automated pipeline that generates LinkedIn posts using Groq LLMs, sends interactive approval requests to Slack with yes/no buttons, and publishes approved posts to LinkedIn. The system is built using LangGraph, Model Context Protocol (MCP) servers, FastAPI, persistent database token management, and Langfuse tracing.

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

## Prerequisites

* Python 3.11 or 3.12
* A LinkedIn Developer Account with an approved application
* A Slack workspace where you can install apps or create incoming webhooks
* [Ngrok](https://ngrok.com/) installed on your machine (for local development only)
* A Groq API account for LLM generation
* A Render account (for cloud deployment) or a PostgreSQL/Supabase database
* (Optional) A Langfuse account for observability tracing

---

## Setup and Installation

### Option A: 1-Click Cloud Deployment on Render (Recommended)

1. Click the **Deploy to Render** button at the top of this repository:
   [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/UzairAtiq/mcp-langraph-agent)
2. Render will load `render.yaml` and create:
   * **Web Service:** `linkedin-slack-agent` (running FastAPI + Uvicorn)
   * **PostgreSQL Database:** `linkedin-slack-db` (auto-links `DATABASE_URL`)
3. Fill in your environment variables (such as `GROQ_API_KEY`, `SLACK_WEBHOOK_URL`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`).
4. Once deployed, open your Render web URL (e.g. `https://linkedin-slack-agent.onrender.com/`).
5. Update your Slack and LinkedIn settings with your Render URL (see sections below).

---

### Option B: Local Development Setup

#### 1. Clone the repository and create a virtual environment

```bash
git clone https://github.com/UzairAtiq/mcp-langraph-agent.git
cd mcp-langraph-agent

python3 -m venv .venv
source .venv/bin/activate
```

#### 2. Install dependencies

```bash
pip install -r requirements.txt
```

#### 3. Configure environment variables

Copy the example configuration:

```bash
cp .env.example .env
```

Open `.env` and fill in the values described below.

---

## Environment Variables

| Variable | Required | Description | Where to Get It |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | Yes | API key used by Groq LLM for generating posts and running judge evaluations. | [Groq Console](https://console.groq.com/keys) |
| `GROQ_MODEL` | No | Model name to use (defaults to `openai/gpt-oss-120b`). | [Groq Models Docs](https://console.groq.com/docs/models) |
| `SLACK_WEBHOOK_URL` | Yes | Incoming webhook URL to send Block Kit approval cards to your Slack channel. | Slack App Management -> Features -> Incoming Webhooks |
| `LINKEDIN_CLIENT_ID` | Yes | OAuth 2.0 Client ID from your LinkedIn Developer application. | [LinkedIn Developer Portal](https://developer.linkedin.com/) -> App -> Auth |
| `LINKEDIN_CLIENT_SECRET` | Yes | OAuth 2.0 Client Secret from your LinkedIn Developer application. | [LinkedIn Developer Portal](https://developer.linkedin.com/) -> App -> Auth |
| `LINKEDIN_REDIRECT_URI` | No | OAuth callback redirect URL (defaults to `http://localhost:8000/linkedin/callback` locally, or auto-detected on Render). | Must match the URL added in LinkedIn Developer Portal under Auth settings. |
| `DATABASE_URL` | No | PostgreSQL connection URL for token and post persistence (auto-populated by Render PostgreSQL or Supabase/Neon). If omitted, falls back to local SQLite `data/app.db`. | Render Dashboard / Supabase / Neon connection string. |
| `LINKEDIN_ACCESS_TOKEN` | No | Static fallback access token. (Not required if connecting via the web dashboard `/linkedin/login`). | Generated automatically on web OAuth login. |
| `LINKEDIN_PERSON_URN` | No | Static fallback member URN (`urn:li:person:<id>`). | Generated automatically on web OAuth login. |
| `LINKEDIN_PROFILE_ID` | No | Static fallback user profile JSON. | Generated automatically on web OAuth login. |
| `CONNECTION_STRING_SUPABASE` | No | Legacy alias for `DATABASE_URL` used by the database MCP tool to look up customer records. | Supabase Dashboard -> Project Settings -> Database -> Connection string |
| `LANGFUSE_SECRET_KEY` | No | Langfuse secret key for LLM tracing and token usage tracking. | [Langfuse Cloud](https://cloud.langfuse.com/) -> Project Settings -> API Keys |
| `LANGFUSE_PUBLIC_KEY` | No | Langfuse public key for tracing. | [Langfuse Cloud](https://cloud.langfuse.com/) -> Project Settings -> API Keys |
| `LANGFUSE_BASE_URL` | No | Host URL for Langfuse (defaults to `https://cloud.langfuse.com`). | Langfuse project settings. |
| `POSTS_STORAGE_PATH` | No | Path to fallback JSON file for posts (defaults to `data/posts.json`). | Local filesystem path. |

### Environment Variables Required on Render

When deploying on Render, the following variables should be entered during Blueprint setup or in the Environment tab:

* **`GROQ_API_KEY`** (Required): For generating LinkedIn post content.
* **`SLACK_WEBHOOK_URL`** (Required): Incoming webhook for approval cards.
* **`LINKEDIN_CLIENT_ID`** (Required): LinkedIn app Client ID.
* **`LINKEDIN_CLIENT_SECRET`** (Required): LinkedIn app Client Secret.
* **`DATABASE_URL`** (Auto-populated): Managed automatically by the linked `linkedin-slack-db` PostgreSQL service in `render.yaml`.
* **`LINKEDIN_REDIRECT_URI`** (Optional): `https://<your-service-name>.onrender.com/linkedin/callback` (Auto-detected if omitted).
* **`LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY`** (Optional): For observability tracing.

### How to Add or Edit Environment Variables in the Render Dashboard

1. Log in to the [Render Dashboard](https://dashboard.render.com/).
2. Select your Web Service (e.g. `linkedin-slack-agent`).
3. In the left-hand navigation, click the **Environment** tab.
4. Click **Add Environment Variable** (or click **Add from .env** / **Bulk Edit**).
5. Enter the **Key** and **Value** for each required variable.
6. Click **Save Changes**. Render will automatically trigger a zero-downtime redeployment with the updated environment variables.

---

## LinkedIn Flow and Authentication

### 1. LinkedIn Developer Portal Setup

1. Go to the [LinkedIn Developer Portal](https://developer.linkedin.com/) and create a new App.
2. Associate the app with your LinkedIn Company page or personal profile.
3. Under the **Products** tab, request access to:
   * **Share on LinkedIn** (provides the `w_member_social` permission).
   * **Sign In with LinkedIn using OpenID Connect** (provides `openid`, `profile`, and `email` permissions).
4. Under the **Auth** tab:
   * Copy your **Client ID** and **Client Secret** into your `.env` or Render environment variables.
   * Under **Authorized redirect URLs for your app**, add:
     * For Localhost:
       ```
       http://localhost:8000/linkedin/callback
       ```
     * For Render Deployment:
       ```
       https://<your-service-name>.onrender.com/linkedin/callback
       ```

### 2. Connect Your LinkedIn Account (1-Click Automated Flow)

1. Start your local server (`python -m api.main` or `uvicorn main:app --reload`) or open your deployed Render URL (`https://<your-service-name>.onrender.com/`).
2. Visit the web dashboard at the root URL (`/`).
3. Click the **Connect LinkedIn** button.
4. Sign in on LinkedIn and click **Allow**.
5. The application will automatically:
   * Exchange the authorization code for a 60-day access token and refresh token.
   * Fetch your person URN from `/v2/userinfo`.
   * Store tokens in your persistent PostgreSQL / SQLite database.
   * Enable automatic background token refreshing within 24 hours of expiration.

---

## Running the Project

### Running on Render (Production)

Once deployed via the Blueprint:
1. Open your web dashboard: `https://<your-service-name>.onrender.com/`
2. Configure Slack Interactivity:
   * Go to [api.slack.com/apps](https://api.slack.com/apps) -> **Interactivity & Shortcuts**.
   * Toggle Interactivity to **On**.
   * Set **Request URL** to:
     ```
     https://<your-service-name>.onrender.com/slack/interactions
     ```
   * Click **Save Changes**.
3. Use the dashboard UI to trigger post generations, view recent posts, and inspect token health.

---

### Running Locally (Development)

To run the complete interactive pipeline locally, start the components across separate terminal windows:

#### Terminal 1: Start the FastAPI Webhook Receiver

The FastAPI server serves the dashboard and receives interactive button payloads when you click Approve or Discard in Slack.

```bash
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

The server will start on `http://0.0.0.0:8000`.

#### Terminal 2: Start Ngrok Tunnel

Slack needs a public HTTPS URL to send interaction payloads to your local FastAPI server.

```bash
ngrok http 8000
```

1. Copy the public forwarding URL from ngrok (e.g. `https://1234-abcd.ngrok-free.app`).
2. Go to your [Slack API App Dashboard](https://api.slack.com/apps).
3. Navigate to **Interactivity & Shortcuts**.
4. Toggle Interactivity to **On**.
5. In the **Request URL** field, enter:
   ```
   https://1234-abcd.ngrok-free.app/slack/interactions
   ```
6. Click **Save Changes**.

#### Terminal 3: Run the LangGraph Agent

Run the main agent graph:

```bash
source .venv/bin/activate
python -m agent.graph
```

**What happens next:**
1. The agent launches the MCP servers in the background over stdio channels.
2. It generates a LinkedIn post on the requested topic via Groq.
3. It saves the post to database storage with status `pending`.
4. It sends a Slack message to your channel containing the post text and two buttons: **Yes (Approve & Post)** and **No (Discard)**.
5. When you click **Approve** in Slack, the interaction hits FastAPI, updates the record to `approved`, and the service immediately publishes the post directly to LinkedIn.

*Note: You do not need to start MCP servers manually in separate terminals. LangGraph automatically spawns them via `agent/tools.py` using `MultiServerMCPClient`.*

---

## Where to Edit Things

* **Post generation prompt**:
  * System prompt and user prompt: Edit `generate_linkedin_post_content()` in `services/groq_service.py`.
* **Agent workflow rules and instructions**:
  * Agent instructions: Edit `SYSTEM_PROMPT` in `agent/nodes.py`.
  * Interactive CLI prompt: Edit the `prompt` string in `run_agent_interactive()` inside `agent/graph.py`.
* **Slack message card format**:
  * Layout and styling: Edit `build_approval_blocks()` in `services/slack_service.py`.
* **Web dashboard and UI**:
  * Dashboard HTML and scripts: Edit `frontend/index.html`, `frontend/app.js`, and `frontend/style.css`.
* **Working directory**:
  * Always run Python commands from the repository root (`mcp-langraph-agent/`).

---

## Tests and Evaluation

The repository includes unit tests and an LLM-based evaluation suite.

### Run Unit Tests

```bash
# Test the complete post generation and storage flow
python tests/test_linkedin_post_flow.py

# Test MCP server tools in isolation
python tests/test_mcp_servers.py

# Test LangGraph agent compilation and tool binding
python tests/test_agent.py
```

### What Each Test Suite Covers

* **`tests/test_linkedin_post_flow.py`**:
  * Tests post record creation, state transitions, and updates in `data/post_storage.py`.
  * Validates Slack Block Kit structure, button actions, and value payloads.
  * Checks FastAPI health (`/health`) and post retrieval (`/posts`) endpoints.
  * Contains an optional live end-to-end Slack button flow test.
* **`tests/test_mcp_servers.py`**:
  * Verifies database customer lookup on `mcp_servers/db_server.py`.
  * Verifies Slack message posting on `mcp_servers/slack_server.py`.
  * Tests the combined customer lookup and Slack alert pipeline.
  * Validates post retrieval tools and MCP stdio connection management in `MCPClient`.
* **`tests/test_agent.py`**:
  * Verifies that `get_langgraph_tools()` loads tools from all three MCP servers.
  * Tests that the LangGraph state graph compiles with nodes and conditional routing edges.
  * Tests end-to-end agent invocation and response structure.
* **`evals/run_evals.py`**:
  * Runs benchmark scenarios from `evals/dataset.py` through the LangGraph agent.
  * Uses an LLM judge (`evals/judge.py`) to score whether the agent called the expected tools in the correct sequence.
  * Exports scored results and pass/fail reasoning to `evals/dataset.json`.

Run the evaluation benchmark with:

```bash
python evals/run_evals.py
```

---

## Project Structure

```
mcp-langraph-agent/
├── main.py                      # Unified FastAPI entrypoint (OAuth, Webhooks, Dashboard, APIs)
├── Procfile                     # Web process start command for cloud deployments
├── render.yaml                  # Render Blueprint definition (Web service + Managed PostgreSQL)
├── agent/
│   ├── graph.py                 # LangGraph builder, edge definitions, and execution entrypoint
│   ├── nodes.py                 # Agent node, system prompt, and conditional routing logic
│   ├── state.py                 # MessagesState schema
│   └── tools.py                 # MultiServerMCPClient loader and standalone MCPClient
├── config/
│   ├── constants.py             # PostStatus enum (PENDING, APPROVED, PUBLISHED, etc.)
│   └── settings.py              # Environment variable loader and path constants
├── data/
│   ├── db.py                    # Multi-tier database engine (PostgreSQL + SQLite fallback)
│   ├── token_storage.py         # OAuth token persistence, auto-refresh, and URN management
│   ├── post_storage.py          # Post lifecycle storage (PostgreSQL, SQLite, JSON fallback)
│   └── posts.json               # Local JSON fallback storage for generated posts
├── frontend/
│   ├── index.html               # Web UI dashboard
│   ├── callback.html            # OAuth success confirmation template
│   ├── error.html               # OAuth error message card template
│   ├── style.css                # Clean stylesheet
│   └── app.js                   # Dashboard status loader and post generator logic
├── evals/
│   ├── dataset.json             # Output evaluation results with judge scores
│   ├── dataset.py               # Evaluation benchmark test cases
│   ├── judge.py                 # LLM-as-a-judge evaluation scoring prompt
│   └── run_evals.py             # Benchmark test runner
├── mcp_servers/
│   ├── db_server.py             # Database lookup MCP server (psycopg / Supabase)
│   ├── linkedin_post_generator.py # LinkedIn generation and approval MCP server
│   └── slack_server.py          # Slack messaging MCP server
├── observability/
│   └── tracing.py               # Langfuse callback handler configuration
├── services/
│   ├── groq_service.py          # Groq LLM post generator with Langfuse tracing
│   ├── linkedin_service.py      # LinkedIn UGC post publisher and URN resolver
│   └── slack_service.py         # Slack Block Kit builder and decision execution
├── tests/
│   ├── linkedin_token.py        # Legacy OAuth token exchange utility
│   ├── test_agent.py            # LangGraph compilation and tool binding tests
│   ├── test_linkedin_post_flow.py # Post lifecycle, Block Kit, and API endpoint tests
│   ├── test_mcp_servers.py      # MCP server isolation and pipeline tests
│   └── test_slack.py            # Quick Slack client check
├── .env.example                 # Example environment variables template
├── .gitignore                   # Git ignore rules for secrets, virtualenv, and data
└── requirements.txt             # Python dependencies
```

