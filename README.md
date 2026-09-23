# LinkedIn Post Automation Agent

An automated pipeline that generates LinkedIn posts using Groq LLMs, sends interactive approval requests to Slack with yes/no buttons, and publishes approved posts to LinkedIn. The system is built using LangGraph, Model Context Protocol (MCP) servers, FastAPI, and Langfuse tracing.

---

## Architecture Overview

```
User Prompt -> LangGraph Agent -> Groq LLM (Generates Post)
                     |
                     v
             Local Storage (posts.json) [status: pending]
                     |
                     v
             Slack Webhook (Block Kit with Approve/Discard Buttons)
                     |
                     v
             User clicks "Approve" in Slack
                     |
                     v
             Slack POST -> Ngrok -> FastAPI (/slack/interactions)
                     |
                     v
             Local Storage updated [status: approved]
                     |
                     v
             Agent polls & detects approval -> Publishes to LinkedIn API
```

---

## Prerequisites

* Python 3.11 or 3.12
* A LinkedIn Developer Account with an approved application
* A Slack workspace where you can install apps or create incoming webhooks
* [Ngrok](https://ngrok.com/) installed on your machine (to expose local webhooks to Slack)
* A Groq API account for LLM generation
* (Optional) A Supabase account for customer database lookups
* (Optional) A Langfuse account for observability tracing

---

## Setup and Installation

### 1. Clone the repository and create a virtual environment

```bash
git clone https://github.com/UzairAtiq/mcp-langraph-agent.git
cd mcp-langraph-agent

python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

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
| `LINKEDIN_REDIRECT_URI` | No | OAuth callback redirect URL (defaults to `http://localhost:8000/callback`). | Must match the URL added in LinkedIn Developer Portal under Auth settings. |
| `LINKEDIN_ACCESS_TOKEN` | Yes | LinkedIn member OAuth access token with post publishing permissions. | Generated automatically using `tests/linkedin_token.py` (see LinkedIn setup below). |
| `LINKEDIN_PERSON_URN` | No | Your LinkedIn member URN (`urn:li:person:<id>`). | Generated automatically by `tests/linkedin_token.py` or resolved at runtime. |
| `LINKEDIN_PROFILE_ID` | No | JSON string of user profile data saved by the token exchange script. | Generated automatically by `tests/linkedin_token.py`. |
| `CONNECTION_STRING_SUPABASE` | No | PostgreSQL connection URL used by the database MCP tool to look up customer records. | Supabase Dashboard -> Project Settings -> Database -> Connection string |
| `LANGFUSE_SECRET_KEY` | No | Langfuse secret key for LLM tracing and token usage tracking. | [Langfuse Cloud](https://cloud.langfuse.com/) -> Project Settings -> API Keys |
| `LANGFUSE_PUBLIC_KEY` | No | Langfuse public key for tracing. | [Langfuse Cloud](https://cloud.langfuse.com/) -> Project Settings -> API Keys |
| `LANGFUSE_BASE_URL` | No | Host URL for Langfuse (defaults to `https://cloud.langfuse.com`). | Langfuse project settings. |
| `POSTS_STORAGE_PATH` | No | Path to local JSON storage for posts (defaults to `data/posts.json`). | Local filesystem path. |

---

## LinkedIn Flow and Authentication

### 1. LinkedIn Developer Portal Setup

1. Go to the [LinkedIn Developer Portal](https://developer.linkedin.com/) and create a new App.
2. Associate the app with your LinkedIn Company page or personal profile.
3. Under the **Products** tab, request access to:
   * **Share on LinkedIn** (provides the `w_member_social` permission).
   * **Sign In with LinkedIn using OpenID Connect** (provides `openid`, `profile`, and `email` permissions).
4. Under the **Auth** tab:
   * Copy your **Client ID** and **Client Secret** into your `.env` file.
   * Under **Authorized redirect URLs for your app**, add:
     ```
     http://localhost:8000/callback
     ```

### 2. Generate Your LinkedIn Access Token

1. Construct the authorization URL in your browser (replace `<YOUR_CLIENT_ID>` with your real Client ID):
   ```
   https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=<YOUR_CLIENT_ID>&redirect_uri=http://localhost:8000/callback&scope=openid%20profile%20email%20w_member_social
   ```
2. Open that URL in your browser and click **Allow**.
3. Your browser will redirect to an address like:
   ```
   http://localhost:8000/callback?code=AQT...
   ```
4. Copy the `code` parameter from your browser's address bar.
5. Run the token exchange script:
   ```bash
   python tests/linkedin_token.py <AUTHORIZATION_CODE>
   ```
6. The script will:
   * Exchange the code with LinkedIn's OAuth server for a 60-day access token.
   * Fetch your profile from `/v2/userinfo` and resolve your `sub` ID to a Person URN (`urn:li:person:<id>`).
   * Automatically write `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, and `LINKEDIN_PROFILE_ID` into your `.env` file.
   * Save a local backup copy in `.linkedin_token`.

---

## Running the Project

To run the complete interactive pipeline, start the components in this exact order across separate terminal windows.

### Terminal 1: Start the FastAPI Webhook Receiver

The FastAPI server receives interactive button payloads when you click Approve or Discard in Slack.

```bash
source .venv/bin/activate
python -m api.main
```

The server will start on `http://0.0.0.0:8000`.

### Terminal 2: Start Ngrok Tunnel

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

### Terminal 3: Run the LangGraph Agent

Run the main agent graph:

```bash
source .venv/bin/activate
python -m agent.graph
```

**What happens next:**
1. The agent launches the MCP servers in the background over stdio channels.
2. It generates a LinkedIn post on the requested topic via Groq.
3. It saves the post to `data/posts.json` with status `pending`.
4. It sends a Slack message to your channel containing the post text and two buttons: **Yes (Approve & Post)** and **No (Discard)**.
5. The agent pauses and polls `data/posts.json` waiting for your decision.
6. When you click **Approve** in Slack, the interaction hits FastAPI, updates the record to `approved`, and the agent immediately publishes the post directly to LinkedIn.

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
├── agent/
│   ├── graph.py                 # LangGraph builder, edge definitions, and execution entrypoint
│   ├── nodes.py                 # Agent node, system prompt, and conditional routing logic
│   ├── state.py                 # MessagesState schema
│   └── tools.py                 # MultiServerMCPClient loader and standalone MCPClient
├── api/
│   └── main.py                  # FastAPI server handling Slack interactive webhook callbacks
├── config/
│   ├── constants.py             # PostStatus enum (PENDING, APPROVED, PUBLISHED, etc.)
│   └── settings.py              # Environment variable loader and path constants
├── data/
│   ├── post_storage.py          # Storage operations for posts.json
│   └── posts.json               # Local storage database for generated posts
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
│   ├── linkedin_token.py        # OAuth 2.0 authorization code to access token exchange script
│   ├── test_agent.py            # LangGraph compilation and tool binding tests
│   ├── test_linkedin_post_flow.py # Post lifecycle, Block Kit, and API endpoint tests
│   ├── test_mcp_servers.py      # MCP server isolation and pipeline tests
│   └── test_slack.py            # Quick Slack client check
├── .env.example                 # Example environment variables template
├── .gitignore                   # Git ignore rules for secrets, virtualenv, and data
└── requirements.txt             # Python dependencies
```
