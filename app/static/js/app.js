/* Shared helpers: API calls (with CSRF), toasts, escaping, loading state, nav. */
const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || "";

async function api(url, { method = "GET", body, form } = {}) {
  const opts = { method, headers: { "X-CSRF-Token": CSRF }, credentials: "same-origin" };
  if (form) opts.body = form;
  else if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  let res;
  try { res = await fetch(url, opts); } catch { throw new Error("Network error. Check your connection and try again."); }
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("json") ? await res.json() : null;
  if (res.status === 401 && !url.includes("/auth/")) { location.href = "/login"; throw new Error("Please log in."); }
  if (!res.ok) throw new Error((data && data.error) || "Something went wrong. Please try again.");
  return data;
}

function toast(msg, type = "") {
  const t = document.createElement("div");
  t.className = "toast " + type; t.textContent = msg;
  document.getElementById("toasts").appendChild(t);
  setTimeout(() => t.remove(), 4200);
}
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const fmtDate = (d) => new Date(d).toLocaleDateString(undefined, { day: "numeric", month: "short" });

async function withLoading(btn, fn) {
  btn.disabled = true; btn.classList.add("loading");
  try { return await fn(); } catch (e) { toast(e.message, "err"); } finally { btn.disabled = false; btn.classList.remove("loading"); }
}

/* tiny SVG line chart: points = [{label, value}], max = y max */
function lineChart(points, max = 100, color = "#7c3aed") {
  if (!points.length) return '<div class="empty">No data yet.</div>';
  const W = 400, H = 150, p = 24, step = points.length > 1 ? (W - 2 * p) / (points.length - 1) : 0;
  const xy = points.map((d, i) => [p + i * step, H - p - (d.value / max) * (H - 2 * p)]);
  const path = xy.map((c, i) => (i ? "L" : "M") + c[0].toFixed(1) + " " + c[1].toFixed(1)).join(" ");
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Trend chart">
    <line x1="${p}" y1="${H - p}" x2="${W - p}" y2="${H - p}" stroke="#e5e7f2"/>
    <path d="${path}" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    ${xy.map((c, i) => `<circle cx="${c[0]}" cy="${c[1]}" r="4.5" fill="#fff" stroke="${color}" stroke-width="3"/><text x="${c[0]}" y="${c[1] - 10}" text-anchor="middle" font-size="11" fill="#334155" font-weight="700">${points[i].value}</text><text x="${c[0]}" y="${H - 6}" text-anchor="middle" font-size="10" fill="#64748b">${esc(points[i].label)}</text>`).join("")}</svg>`;
}

document.addEventListener("DOMContentLoaded", () => {
  $("#menuBtn")?.addEventListener("click", () => $("#side").classList.toggle("open"));
  $("#logoutBtn")?.addEventListener("click", async () => { await api("/api/auth/logout", { method: "POST" }); location.href = "/"; });
});
