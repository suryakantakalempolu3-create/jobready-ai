let file = null;
const drop = $("#drop"), input = $("#file");
function pick(f) {
  if (!f) return;
  if (!f.name.toLowerCase().endsWith(".pdf")) return toast("Please choose a PDF file.", "err");
  if (f.size > 5 * 1024 * 1024) return toast("File is larger than 5 MB.", "err");
  file = f; $("#fileName").textContent = f.name; $("#goBtn").disabled = false;
}
input.addEventListener("change", () => pick(input.files[0]));
["dragover", "dragenter"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", e => pick(e.dataTransfer.files[0]));

function render(r) {
  const col = r.score >= 75 ? "ok" : r.score >= 55 ? "warn" : "bad";
  $("#result").innerHTML = `<div class="card fade"><div class="row" style="gap:28px">
    <div class="ring" style="--p:${r.score}"><div><div><b>${r.score}</b><br><span>ATS score</span></div></div></div>
    <div style="flex:1;min-width:240px"><span class="badge ${col}">${r.score >= 75 ? "Strong" : r.score >= 55 ? "Fair" : "Needs work"}</span> <span class="badge">${r.source === "ai" ? "AI + rules" : "Rule-based (offline)"}</span>
    <p>${esc(r.summary)}</p></div></div></div>
    <div class="grid g2 mt"><div class="card"><h3>Score breakdown</h3>${Object.entries(r.breakdown).map(([k, v]) => `<div class="small row between"><span>${esc(k)}</span><b>${v.score}/${v.max}</b></div><div class="bar" style="margin-bottom:10px"><i style="width:${100 * v.score / v.max}%"></i></div>`).join("")}</div>
    <div class="card"><h3>Skills</h3><div class="small muted">Found</div><div class="chips">${r.found_skills.map(s => `<span class="chip have">${esc(s)}</span>`).join("") || "None detected"}</div>
    <div class="small muted mt">Consider adding</div><div class="chips">${r.missing_skills.map(s => `<span class="chip miss">${esc(s)}</span>`).join("") || "Nothing major missing"}</div></div></div>
    <div class="grid g2 mt"><div class="card"><h3>Strengths</h3><ul class="clean">${r.strengths.map(s => `<li>${esc(s)}</li>`).join("") || "<li>Keep building your resume.</li>"}</ul></div>
    <div class="card"><h3>Suggested improvements</h3><ul class="clean">${r.improvements.map(s => `<li>${esc(s)}</li>`).join("")}</ul></div></div>`;
  $("#result").scrollIntoView({ behavior: "smooth", block: "start" });
}
async function loadHistory() {
  try {
    const rows = await api("/api/analyses");
    $("#history").innerHTML = rows.map(r => `<div class="row between item"><span>${esc(r.filename)} <span class="muted small">· ${esc(r.role)} · ${fmtDate(r.created_at)}</span></span><span class="badge ${r.score >= 75 ? "ok" : r.score >= 55 ? "warn" : "bad"}">${r.score}</span></div>`).join("") || '<div class="empty">No analyses yet. Upload your resume above.</div>';
  } catch (e) { toast(e.message, "err"); }
}
$("#goBtn").addEventListener("click", (e) => withLoading(e.currentTarget, async () => {
  const fd = new FormData(); fd.append("resume", file); fd.append("role", $("#role").value);
  render(await api("/api/analyze", { method: "POST", form: fd })); loadHistory();
}));
loadHistory();
