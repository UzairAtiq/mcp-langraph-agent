/* =========================================================
   LinkedIn Agent Dashboard — app.js
   ========================================================= */

"use strict";

// ── constants ────────────────────────────────────────────
const STATUS_POLL_MS  = 30_000;  // re-check LinkedIn status every 30 s
const POSTS_POLL_MS   = 15_000;  // re-poll posts list every 15 s

// ── badge helpers ─────────────────────────────────────────
const BADGE_STATES = {
  checking: { cls: "badge--dim",  dot: true,  pulse: true,  label: "Checking"     },
  ok:       { cls: "badge--ok",   dot: true,  pulse: false, label: "Connected"    },
  error:    { cls: "badge--err",  dot: true,  pulse: false, label: "Disconnected" },
};

function applyBadge(el, state) {
  if (!el) return;
  const cfg = BADGE_STATES[state] || BADGE_STATES.checking;
  el.className = `badge ${cfg.cls}`;
  el.innerHTML = cfg.dot
    ? `<span class="badge__dot${cfg.pulse ? " badge__dot--pulse" : ""}"></span>${cfg.label}`
    : cfg.label;
}

// ── post status → badge class ─────────────────────────────
function postBadgeCls(s) {
  if (!s) return "badge--dim";
  const map = {
    published:     "badge--ok",
    approved:      "badge--ok",
    pending:       "badge--warn",
    pending_approval: "badge--warn",
    rejected:      "badge--err",
    discarded:     "badge--err",
    publish_failed:"badge--err",
  };
  return map[s.toLowerCase()] || "badge--dim";
}

// ── DOM shortcuts & safe setters ─────────────────────────
const $ = (id) => document.getElementById(id);

function setText(id, text) {
  const el = $(id);
  if (el) el.textContent = text;
}

function safeCreateIcons() {
  if (window.lucide && typeof lucide.createIcons === "function") {
    lucide.createIcons();
  }
}

// ── skeletons & rows ──────────────────────────────────────
function showSkeletons(...ids) { ids.forEach(id => { const el = $(id); if (el) el.style.display = ""; }); }
function hideSkeletons(...ids) { ids.forEach(id => { const el = $(id); if (el) el.style.display = "none"; }); }
function showRows(...ids)      { ids.forEach(id => { const el = $(id); if (el) el.style.display = "flex"; }); }

// ── escape html ───────────────────────────────────────────
function esc(t) {
  if (!t) return "";
  return String(t)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ── format date ───────────────────────────────────────────
function fmt(dateStr) {
  if (!dateStr || dateStr === "None" || dateStr === "null") return "—";
  try {
    return new Intl.DateTimeFormat(undefined, {
      year:  "numeric", month: "short", day: "numeric",
      hour:  "2-digit", minute: "2-digit",
    }).format(new Date(dateStr));
  } catch { return dateStr; }
}

// ── LinkedIn status ───────────────────────────────────────
async function loadStatus() {
  const badge = $("linkedin-badge") || $("auth-badge");
  if (badge) applyBadge(badge, "checking");

  try {
    const [healthRes, tokenRes] = await Promise.all([
      fetch("/health"),
      fetch("/linkedin/status"),
    ]);

    if (!healthRes.ok || !tokenRes.ok) throw new Error("non-ok response");

    const health = await healthRes.json();
    const token  = await tokenRes.json();

    // hide skeletons, show real rows
    hideSkeletons("sk-urn", "sk-exp", "sk-db", "sk-uri");
    showRows("row-urn", "row-exp", "row-db", "row-uri");

    if (token.authenticated) {
      if (badge) applyBadge(badge, "ok");
      const urnText = token.person_urn || "Available";
      const expText = fmt(token.expires_at);
      setText("val-urn", urnText);
      setText("person-urn", urnText);
      setText("val-exp", expText);
      setText("token-expiry", expText);
    } else {
      if (badge) applyBadge(badge, "error");
      setText("val-urn", "Not authenticated");
      setText("person-urn", "Not authenticated");
      setText("val-exp", "—");
      setText("token-expiry", "—");
    }

    const dbText = health.database === "postgresql" ? "PostgreSQL" : "SQLite";
    const uriText = token.redirect_uri || `${window.location.origin}/linkedin/callback`;
    setText("val-db", dbText);
    setText("db-type", dbText);
    setText("val-uri", uriText);
    setText("redirect-uri", uriText);

    // animate rows in if GSAP is loaded
    if (typeof gsap !== "undefined") {
      try {
        gsap.from(["#row-urn", "#row-exp", "#row-db", "#row-uri"], {
          opacity: 0, y: 4, stagger: 0.06, duration: 0.3, ease: "power1.out",
        });
      } catch { /* optional animation */ }
    }

  } catch (err) {
    console.error("loadStatus failed:", err);
    if (badge) applyBadge(badge, "error");
    hideSkeletons("sk-urn", "sk-exp", "sk-db", "sk-uri");
    showRows("row-urn", "row-exp", "row-db", "row-uri");
    setText("val-urn", "Error fetching status");
    setText("person-urn", "Error fetching status");
    setText("val-exp", "—");
    setText("token-expiry", "—");
    setText("val-db", "—");
    setText("db-type", "—");
    setText("val-uri", "—");
    setText("redirect-uri", "—");
  }
}

// ── posts list ────────────────────────────────────────────
async function loadPosts() {
  const skeleton  = $("posts-skeleton");
  const tableWrap = $("posts-table-wrap");
  const emptyEl   = $("posts-empty") || $("empty-posts");
  const tbody     = $("posts-tbody");

  // show skeleton, hide table/empty
  if (skeleton)  skeleton.style.display  = "";
  if (tableWrap) tableWrap.style.display = "none";
  if (emptyEl)   emptyEl.style.display   = "none";

  try {
    const res  = await fetch("/posts");
    const data = await res.json();

    if (skeleton) skeleton.style.display = "none";

    const posts = data.posts || [];

    if (posts.length === 0) {
      if (emptyEl) {
        emptyEl.style.display = "";
        safeCreateIcons();
      }
      return;
    }

    if (tbody) {
      tbody.innerHTML = posts.map((post, i) => {
        const content  = post.content || "";
        const badgeCls = postBadgeCls(post.status);
        const rowId    = `post-row-${i}`;
        return `
          <tr id="${rowId}">
            <td class="post-id-cell">${esc(post.post_id)}</td>
            <td class="post-content-cell">
              <div class="post-excerpt" onclick="toggleContent(${i})" title="Click to expand">${esc(content)}</div>
              <pre id="post-full-${i}" class="post-full">${esc(content)}</pre>
              <button class="post-toggle-btn" id="toggle-btn-${i}" onclick="toggleContent(${i})">Show full text</button>
            </td>
            <td>
              <span class="badge ${badgeCls}" id="post-badge-${post.post_id}">${esc(post.status || "—")}</span>
            </td>
            <td style="white-space:nowrap;color:var(--text-secondary);font-size:12px">${fmt(post.created_at)}</td>
          </tr>`;
      }).join("");
    }

    if (tableWrap) tableWrap.style.display = "";

    // stagger-animate rows in if GSAP is loaded
    if (typeof gsap !== "undefined") {
      try {
        const rows = posts.map((_, i) => `#post-row-${i}`);
        gsap.from(rows, {
          opacity: 0, y: 6,
          stagger: 0.04, duration: 0.25, ease: "power1.out",
        });
      } catch { /* optional animation */ }
    }

    safeCreateIcons();

  } catch (err) {
    console.error("loadPosts failed:", err);
    if (skeleton) skeleton.style.display = "none";
    if (emptyEl)  { emptyEl.style.display = ""; safeCreateIcons(); }
  }
}

// ── expand/collapse post text ─────────────────────────────
function toggleContent(idx) {
  const full = $(`post-full-${idx}`);
  const btn  = $(`toggle-btn-${idx}`);
  if (!full || !btn) return;

  const open = full.style.display === "block";
  full.style.display = open ? "none" : "block";
  btn.textContent    = open ? "Show full text" : "Collapse";

  if (!open && typeof gsap !== "undefined") {
    try {
      gsap.from(full, { opacity: 0, y: -4, duration: 0.2, ease: "power1.out" });
    } catch { /* optional */ }
  }
}

// ── generate form ─────────────────────────────────────────
async function handleGenerate(event) {
  event.preventDefault();

  const topicInput = $("topic-input");
  const submitBtn  = $("generate-btn");
  const resultEl   = $("generate-result");

  if (!submitBtn) return;

  const topic = (topicInput && topicInput.value.trim()) || "AI advancements and modern software engineering";

  // loading state
  submitBtn.disabled = true;
  const originalHTML = submitBtn.innerHTML;
  submitBtn.innerHTML = `<i data-lucide="loader-2" style="width:14px;height:14px"></i> Generating...`;
  safeCreateIcons();

  if (resultEl) {
    resultEl.className = "result-msg";
    resultEl.textContent = "";
  }

  // spin icon
  const loaderEl = submitBtn.querySelector("[data-lucide='loader-2']");
  let spinTl;
  if (loaderEl && typeof gsap !== "undefined") {
    try {
      spinTl = gsap.to(loaderEl, { rotation: 360, duration: 0.9, ease: "none", repeat: -1 });
    } catch { /* optional */ }
  }

  try {
    const res  = await fetch(`/posts/generate?topic=${encodeURIComponent(topic)}`, { method: "POST" });
    const data = await res.json();

    if (resultEl) {
      if (res.ok) {
        resultEl.className   = "result-msg result-msg--ok";
        resultEl.textContent = `Post ${data.post_id} generated and sent to Slack for approval.`;
        if (typeof gsap !== "undefined") gsap.from(resultEl, { opacity: 0, y: 4, duration: 0.2 });
        loadPosts();
      } else {
        resultEl.className   = "result-msg result-msg--err";
        resultEl.textContent = data.detail || "Failed to generate post.";
        if (typeof gsap !== "undefined") gsap.from(resultEl, { opacity: 0, y: 4, duration: 0.2 });
      }
    }
  } catch (err) {
    if (resultEl) {
      resultEl.className   = "result-msg result-msg--err";
      resultEl.textContent = `Network error: ${err.message}`;
      if (typeof gsap !== "undefined") gsap.from(resultEl, { opacity: 0, y: 4, duration: 0.2 });
    }
  } finally {
    if (spinTl) spinTl.kill();
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalHTML;
    safeCreateIcons();
  }
}

// ── live post status polling ──────────────────────────────
async function pollPostStatuses() {
  try {
    const res  = await fetch("/posts");
    const data = await res.json();

    (data.posts || []).forEach((post) => {
      const badgeEl = document.getElementById(`post-badge-${post.post_id}`);
      if (!badgeEl) return;

      const newCls  = postBadgeCls(post.status);
      const newText = post.status || "—";

      if (badgeEl.textContent.trim() !== newText) {
        if (typeof gsap !== "undefined") {
          gsap.to(badgeEl, {
            opacity: 0, duration: 0.15,
            onComplete() {
              badgeEl.className   = `badge ${newCls}`;
              badgeEl.textContent = newText;
              gsap.to(badgeEl, { opacity: 1, duration: 0.15 });
            },
          });
        } else {
          badgeEl.className   = `badge ${newCls}`;
          badgeEl.textContent = newText;
        }
      }
    });
  } catch { /* silent — polling is best-effort */ }
}

// ── page load animations ──────────────────────────────────
function runEntryAnimations() {
  if (typeof gsap === "undefined") return;
  try {
    gsap.from("#site-header",   { opacity: 0, y: -10, duration: 0.4, ease: "power2.out" });
    gsap.from("#card-status",   { opacity: 0, y: 10,  duration: 0.35, delay: 0.08, ease: "power2.out" });
    gsap.from("#card-generate", { opacity: 0, y: 10,  duration: 0.35, delay: 0.14, ease: "power2.out" });
    gsap.from("#card-posts",    { opacity: 0, y: 10,  duration: 0.35, delay: 0.2,  ease: "power2.out" });
  } catch (err) {
    console.warn("Entry animations skipped:", err);
  }
}

// ── init ──────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // render icons first
  safeCreateIcons();

  // entry animations
  runEntryAnimations();

  // data load
  loadStatus();
  loadPosts();

  // form handler
  const form = $("generate-form");
  if (form) form.addEventListener("submit", handleGenerate);

  // polling loops
  setInterval(loadStatus,        STATUS_POLL_MS);
  setInterval(loadPosts,         POSTS_POLL_MS);
  setInterval(pollPostStatuses,  POSTS_POLL_MS);
});

