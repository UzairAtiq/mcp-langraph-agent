# Cloud Deployment Guide (Render)

This repository includes a declarative infrastructure blueprint (`render.yaml`) for 1-click zero-downtime deployment on Render with managed PostgreSQL.

---

## 1. Automated 1-Click Deployment

1. Click the **Deploy to Render** button or navigate to Render Blueprint creation:
   [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/UzairAtiq/mcp-langraph-agent)
2. Render reads `render.yaml` from repository root and automatically provisions:
   * **Web Service (`linkedin-slack-agent`)**:
     * Environment: Python 3.11
     * Root Directory: `project/backend`
     * Build Command: `npm --prefix ../frontend install && npm --prefix ../frontend run build && pip install -r requirements.txt`
     * Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     * Health Check: `/health`
   * **PostgreSQL Database (`linkedin-slack-db`)**:
     * Managed PostgreSQL instance automatically linked via the `DATABASE_URL` environment variable.

---

## 2. Environment Variables Configuration

Enter your API credentials during Blueprint creation or in the Render Service settings:

| Variable | Required | Description | Source |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | **Yes** | Groq API key for LLM post drafting and judge evaluation. | [Groq Console](https://console.groq.com/keys) |
| `GROQ_MODEL` | No | LLM model name (defaults to `openai/gpt-oss-120b`). | [Groq Models Docs](https://console.groq.com/docs/models) |
| `SLACK_WEBHOOK_URL` | **Yes** | Slack incoming webhook URL for approval cards. | Slack App Management |
| `LINKEDIN_CLIENT_ID` | **Yes** | OAuth 2.0 Client ID. | LinkedIn Developer Portal |
| `LINKEDIN_CLIENT_SECRET` | **Yes** | OAuth 2.0 Client Secret. | LinkedIn Developer Portal |
| `DATABASE_URL` | Auto | Managed PostgreSQL connection string. | Linked automatically from `linkedin-slack-db` |
| `LINKEDIN_REDIRECT_URI` | No | Callback URL (auto-detected if omitted on Render). | `https://<service-name>.onrender.com/linkedin/callback` |
| `LANGFUSE_SECRET_KEY` | No | Secret key for telemetry tracing. | [Langfuse Cloud](https://cloud.langfuse.com/) |
| `LANGFUSE_PUBLIC_KEY` | No | Public key for telemetry tracing. | [Langfuse Cloud](https://cloud.langfuse.com/) |
| `LANGFUSE_BASE_URL` | No | Langfuse host URL (defaults to `https://cloud.langfuse.com`). | Langfuse Cloud |

---

## 3. How to Update Environment Variables in Render Dashboard

1. Open the [Render Dashboard](https://dashboard.render.com/).
2. Select your Web Service (`linkedin-slack-agent`).
3. In the sidebar, click the **Environment** tab.
4. Click **Add Environment Variable** or **Bulk Edit**.
5. Save changes. Render triggers a zero-downtime redeployment with the new values.

---

## 4. Post-Deployment Checklist

Once the deployment finishes and your service URL is live (e.g. `https://linkedin-slack-agent.onrender.com`):

1. **Update LinkedIn Developer App**:
   * Add `https://<your-service-name>.onrender.com/linkedin/callback` to **Authorized redirect URLs**.
2. **Update Slack Interactivity**:
   * Set **Request URL** in Slack App settings to `https://<your-service-name>.onrender.com/slack/interactions`.
3. **Connect Your LinkedIn Account**:
   * Visit `https://<your-service-name>.onrender.com/` and click **Connect LinkedIn** to complete initial OAuth authentication.
4. **Verify Health Endpoint**:
   * Visit `https://<your-service-name>.onrender.com/health` to confirm database connectivity and authentication state.
