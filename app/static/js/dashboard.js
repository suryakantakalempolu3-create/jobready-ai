(async function () {
  try {
    const d = await api("/api/dashboard");
    $("#roleBadge").textContent = d.target_role;
    $("#sScore").textContent = d.resume_score ?? "–";
    if (d.resume_score != null) $("#sScoreSub").textContent = d.resume_score >= 75 ? "Looking strong" : "Room to improve";
    $("#sComp").textContent = d.resume_completeness + "%"; $("#sCompBar").style.width = d.resume_completeness + "%";
    $("#sIv").textContent = d.interview.average != null ? d.interview.average + "/10" : "–";
    if (d.interview.count) $("#sIvSub").textContent = d.interview.count + " completed interview" + (d.interview.count > 1 ? "s" : "");
    $("#sCov").textContent = d.skill_coverage + "%"; $("#sCovSub").textContent = "of " + d.target_role + " skills";
    $("#scoreChart").innerHTML = lineChart(d.score_history.map(x => ({ label: fmtDate(x.date), value: x.score })), 100, "#2563eb");
    $("#ivChart").innerHTML = lineChart(d.interview.history.map(x => ({ label: fmtDate(x.date), value: x.score })), 10);
    $("#ivTypes").innerHTML = Object.entries(d.interview.by_type).map(([k, v]) => `<span class="chip">${esc(k)}: ${v}/10</span>`).join("");
    $("#skills").innerHTML = d.skills.map(s => `<span class="chip ${s.have ? "have" : "miss"}">${s.have ? "✓" : "+"} ${esc(s.skill)}</span>`).join("");
    $("#steps").innerHTML = d.next_steps.map(s => `<li><a href="${esc(s.link)}">${esc(s.text)}</a></li>`).join("");
    $("#jobs").innerHTML = d.recommended_jobs.map(j => `<div class="item" style="margin:0"><div class="row between"><b>${esc(j.title)}</b><span class="badge ${j.match >= 60 ? "ok" : "blue"}">${j.match}% match</span></div>
      <div class="small muted">${esc(j.company)} · ${esc(j.location)} · ${esc(j.type)}</div></div>`).join("") || '<div class="empty">Add skills to see matches.</div>';
  } catch (e) { toast(e.message, "err"); }
})();
