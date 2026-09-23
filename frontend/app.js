// fetch and display live system and token status
async function loadStatus() {
    try {
        const [healthRes, tokenRes] = await Promise.all([
            fetch("/health"),
            fetch("/linkedin/status")
        ]);

        const health = await healthRes.json();
        const token = await tokenRes.json();

        const badgeEl = document.getElementById("auth-badge");
        const urnEl = document.getElementById("person-urn");
        const expEl = document.getElementById("token-expiry");
        const dbEl = document.getElementById("db-type");
        const redirectEl = document.getElementById("redirect-uri");

        if (token.authenticated) {
            badgeEl.className = "badge badge-success";
            badgeEl.innerText = "Connected & Active";
            urnEl.innerText = token.person_urn || "Available";
            expEl.innerText = token.expires_at || "N/A";
        } else {
            badgeEl.className = "badge badge-danger";
            badgeEl.innerText = "Not Connected";
            urnEl.innerText = "Not available";
            expEl.innerText = "None";
        }

        dbEl.innerText = health.database === "postgresql" ? "PostgreSQL" : "SQLite (data/app.db)";
        if (redirectEl) {
            redirectEl.innerText = token.redirect_uri || `${window.location.origin}/linkedin/callback`;
        }
    } catch (err) {
        console.error("failed to load status", err);
    }
}

// fetch and render saved posts table
async function loadPosts() {
    try {
        const res = await fetch("/posts");
        const data = await res.json();
        const tbody = document.getElementById("posts-tbody");
        const emptyState = document.getElementById("empty-posts");

        if (!data.posts || data.posts.length === 0) {
            tbody.innerHTML = "";
            emptyState.style.display = "block";
            return;
        }

        emptyState.style.display = "none";
        tbody.innerHTML = data.posts.map(post => {
            let statusBadge = "badge-warning";
            if (post.status === "published") statusBadge = "badge-success";
            if (post.status === "rejected" || post.status === "publish_failed") statusBadge = "badge-danger";

            return `
                <tr>
                    <td><code>${post.post_id}</code></td>
                    <td class="truncate" title="${escapeHtml(post.content)}">${escapeHtml(post.content)}</td>
                    <td><span class="badge ${statusBadge}">${post.status}</span></td>
                    <td>${new Date(post.created_at).toLocaleString()}</td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        console.error("failed to load posts", err);
    }
}

// handle post generation form submission
async function handleGenerate(event) {
    event.preventDefault();
    const topicInput = document.getElementById("topic-input");
    const submitBtn = document.getElementById("generate-btn");
    const resultMsg = document.getElementById("generate-result");

    const topic = topicInput.value.trim() || "AI advancements and modern software engineering";
    submitBtn.disabled = true;
    submitBtn.innerText = "Generating...";
    resultMsg.innerText = "";

    try {
        const res = await fetch(`/posts/generate?topic=${encodeURIComponent(topic)}`, {
            method: "POST"
        });
        const data = await res.json();

        if (res.ok) {
            resultMsg.style.color = "var(--success-color)";
            resultMsg.innerText = `Post generated (${data.post_id}) and sent to Slack! Check Slack to approve.`;
            loadPosts();
        } else {
            resultMsg.style.color = "var(--danger-color)";
            resultMsg.innerText = `Error: ${data.detail || "Failed to generate post"}`;
        }
    } catch (err) {
        resultMsg.style.color = "var(--danger-color)";
        resultMsg.innerText = `Network error: ${err.message}`;
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Generate & Send to Slack";
    }
}

// escape html entities for safe rendering
function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    loadStatus();
    loadPosts();
    const form = document.getElementById("generate-form");
    if (form) {
        form.addEventListener("submit", handleGenerate);
    }
});
