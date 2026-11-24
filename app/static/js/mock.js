let iv = null;
const show = (id, on) => ($(id).hidden = !on);
function ask(q, idx, total) {
  $("#qText").textContent = q; $("#answer").value = ""; $("#answer").focus();
  $("#progressTxt").textContent = `Question ${idx + 1} of ${total}`; $("#progressBar").style.width = (100 * idx / total) + "%";
}
$("#startBtn").addEventListener("click", (e) => withLoading(e.currentTarget, async () => {
  const role = $("#role").value; if (!role.trim()) return toast("Enter a job role.", "err");
  const d = await api("/api/mock/start", { method: "POST", body: { role, type: $("#type").value, count: +$("#count").value } });
  iv = { id: d.id, total: d.total, idx: 0 };
  $("#roleTxt").textContent = d.role; $("#feedback").innerHTML = ""; show("#setup", false); show("#session", true); show("#finalBox", false);
  $("#submitBtn").disabled = false; ask(d.question, 0, d.total);
}));
function fbHtml(f) {
  return `<div class="card fade"><div class="row between"><h3 style="margin:0">Feedback</h3><span class="badge ${f.score >= 7.5 ? "ok" : f.score >= 5 ? "warn" : "bad"}">${f.score}/10</span></div>
  <div class="small muted mt">What went well</div><ul class="clean">${f.strengths.map(s => `<li>${esc(s)}</li>`).join("")}</ul>
  <div class="small muted">How to improve</div><ul class="clean">${f.improvements.map(s => `<li>${esc(s)}</li>`).join("")}</ul>
  <details><summary>See an ideal answer</summary><p>${esc(f.ideal_answer)}</p></details></div>`;
}
$("#submitBtn").addEventListener("click", (e) => withLoading(e.currentTarget, async () => {
  const answer = $("#answer").value.trim();
  if (answer.length < 5) return toast("Please write an answer first.", "err");
  const r = await api(`/api/mock/${iv.id}/answer`, { method: "POST", body: { answer } });
  $("#feedback").insertAdjacentHTML("afterbegin", `<div class="small muted" style="margin:6px 0">Q${r.index + 1}: ${esc($("#qText").textContent)}</div>` + fbHtml(r.feedback));
  if (r.done) {
    $("#progressBar").style.width = "100%"; show("#session", false);
    $("#feedback").hidden = false;
    $("#finalBox").hidden = false;
    $("#finalBox").innerHTML = `<div class="card fade" style="text-align:center"><div class="ring" style="--p:${r.summary.avg_score * 10};margin:0 auto 12px"><div><div><b>${r.summary.avg_score}</b><br><span>out of 10</span></div></div></div><h2>${esc(r.summary.verdict)}</h2>
      <button class="btn btn-primary" onclick="location.reload()">Start another interview</button> <a class="btn btn-ghost" href="/dashboard">View dashboard</a></div>`;
    $("#session").after($("#feedback"));
  } else { iv.idx++; ask(r.next_question, iv.idx, iv.total); }
}));
(async () => {
  try {
    const rows = await api("/api/mock");
    $("#history").innerHTML = rows.map(r => `<div class="row between item"><span>${esc(r.role)} <span class="muted small">· ${esc(r.type)} · ${fmtDate(r.created_at)}</span></span>${r.status === "completed" ? `<span class="badge ${r.avg_score >= 7.5 ? "ok" : r.avg_score >= 5 ? "warn" : "bad"}">${r.avg_score}/10</span>` : '<span class="badge">unfinished</span>'}</div>`).join("") || '<div class="empty">No interviews yet. Start your first one above.</div>';
  } catch (e) { toast(e.message, "err"); }
})();
