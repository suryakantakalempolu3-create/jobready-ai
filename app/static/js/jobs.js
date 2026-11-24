let timer;
async function load() {
  const p = new URLSearchParams({ q: $("#q").value, type: $("#type").value, location: $("#loc").value });
  $("#list").innerHTML = '<div class="skeleton"></div><div class="skeleton"></div>';
  try {
    const jobs = await api("/api/jobs?" + p);
    $("#list").innerHTML = jobs.map(j => `<div class="card"><div class="row between"><h3 style="margin:0">${esc(j.title)}</h3><span class="badge ${j.match >= 60 ? "ok" : j.match >= 35 ? "blue" : "warn"}">${j.match}% match</span></div>
      <div class="small muted">${esc(j.company)} · ${esc(j.location)} · ${esc(j.type)} · ${esc(j.salary)}</div><p class="small">${esc(j.description)}</p>
      <div class="chips">${j.matched_skills.map(s => `<span class="chip have">✓ ${esc(s)}</span>`).join("")}${j.missing_skills.map(s => `<span class="chip miss">${esc(s)}</span>`).join("")}</div>
      <div class="row mt"><a class="btn btn-primary btn-sm" target="_blank" rel="noopener" href="${esc(j.apply_url)}">Apply</a>
      <button class="btn btn-ghost btn-sm" data-save="${esc(j._id)}">${j.saved ? "★ Saved" : "☆ Save"}</button></div></div>`).join("") || '<div class="card empty">No jobs match these filters.</div>';
  } catch (e) { toast(e.message, "err"); }
}
$("#list").addEventListener("click", async (e) => {
  const b = e.target.closest("[data-save]"); if (!b) return;
  await withLoading(b, async () => { const r = await api(`/api/jobs/${b.dataset.save}/save`, { method: "POST" }); b.textContent = r.saved ? "★ Saved" : "☆ Save"; toast(r.saved ? "Job saved" : "Removed from saved", "ok"); });
});
for (const id of ["#q", "#loc"]) $(id).addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(load, 300); });
$("#type").addEventListener("change", load);
load();
