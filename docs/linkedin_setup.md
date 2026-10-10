# LinkedIn App & Authentication Setup Guide

This guide walks you through configuring a LinkedIn Developer Application and connecting your personal or organization account to the automation pipeline.

---

## 1. LinkedIn Developer Portal Setup

1. Navigate to the [LinkedIn Developer Portal](https://developer.linkedin.com/) and click **Create App**.
2. Complete the required fields:
   * **App Name**: e.g. `LinkedIn Post Automation`
   * **LinkedIn Page**: Associate your LinkedIn Company page or personal profile.
   * **App Logo**: Upload a logo image.
3. Agree to the legal terms and click **Create app**.

---

## 2. Request Required Product Access

In your newly created app dashboard, open the **Products** tab and request access to:

1. **Share on LinkedIn**:
   * Grants the `w_member_social` permission.
   * Required to programmatically publish text and media posts to your feed.
2. **Sign In with LinkedIn using OpenID Connect**:
   * Grants `openid`, `profile`, and `email` permissions.
   * Required to authenticate users and resolve the Member Person URN (`urn:li:person:<id>`).

> [!NOTE]
> Approval for these two products is typically instantaneous for standard development applications.

---

## 3. Configure OAuth 2.0 Credentials & Redirect URLs

Open the **Auth** tab in your app dashboard:

1. **Application Credentials**:
   * Copy the **Client ID** -> set as `LINKEDIN_CLIENT_ID` in `.env` or Render environment variables.
   * Copy the **Client Secret** -> set as `LINKEDIN_CLIENT_SECRET` in `.env` or Render environment variables.
2. **OAuth 2.0 settings**:
   * Under **Authorized redirect URLs for your app**, add:
     * **Local Development**:
       ```
       http://localhost:8000/linkedin/callback
       ```
     * **Cloud Deployment (Render)**:
       ```
       https://<your-service-name>.onrender.com/linkedin/callback
       ```
   * Click **Update** to save the redirect URLs.

---

## 4. Connect Your Account (1-Click Automated Flow)

Once your server is running (locally or deployed to Render):

1. Open the dashboard homepage (`http://localhost:8000/` or your Render service URL).
2. Look at the **LinkedIn Connection Status** card in the dashboard.
3. Click **Connect LinkedIn**.
4. You will be redirected to LinkedIn's official OAuth consent screen. Sign in and click **Allow**.
5. Once authorized, LinkedIn redirects back to `/linkedin/callback`:
   * The backend exchanges the authorization code for an OAuth 2.0 access token and refresh token.
   * The backend queries `/v2/userinfo` to automatically determine your Person URN (`urn:li:person:...`).
   * Tokens and profile metadata are securely stored in your PostgreSQL / SQLite database.
   * The frontend updates to show an **Active** status badge with your profile ID and token expiry countdown.

---

## 5. Automated Token Refresh & Security

* **60-Day Access Tokens**: LinkedIn issues access tokens valid for 60 days.
* **Proactive Auto-Refresh**: Whenever a post is approved or when the `/auth/refresh` endpoint is triggered, the backend inspects token expiration. If the token expires within 24 hours, it automatically refreshes the token using LinkedIn's OAuth refresh endpoint without requiring manual re-authentication.
* **Token Storage**: Tokens are stored in the database `linkedin_tokens` table. In local environments without PostgreSQL, they are persisted to `project/backend/data/app.db` and backed up to `.linkedin_token`.

> [!WARNING]
> `.linkedin_token` is a sensitive secret file containing your active token. It must never be committed to git. Verify it is listed in `.gitignore`.
