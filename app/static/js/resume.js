const SCHEMA = {
  education: [["institution", "Institution"], ["degree", "Degree"], ["field", "Field of study"], ["grade", "Grade / CGPA"], ["start", "Start year"], ["end", "End year"]],
  experience: [["role", "Role"], ["company", "Company"], ["start", "Start"], ["end", "End"], ["description", "Bullet points (one per line)", true]],
  projects: [["name", "Project name"], ["tech", "Technologies"], ["link", "Link"], ["description", "Bullet points (one per line)", true]],
  certifications: [["name", "Certification"], ["issuer", "Issuer"], ["year", "Year"]],
};
let R = { skills: [], education: [], experience: [], projects: [], certifications: [] };

function renderLists() {
  for (const [key, fields] of Object.entries(SCHEMA)) {
    $("#list-" + key).innerHTML = R[key].map((it, i) => `<div class="item"><button class="btn btn-danger btn-sm x" data-del="${key}:${i}" aria-label="Remove">Remove</button>
      <div class="grid2">${fields.map(([f, label, area]) => `<div class="field" style="${area ? "grid-column:1/-1" : ""}"><label>${label}</label>
      ${area ? `<textarea data-l="${key}:${i}:${f}" rows="3">${esc(it[f])}</textarea><button class="btn btn-ghost btn-sm" data-imp="${key}:${i}:${f}" type="button" style="margin-top:6px">✨ Improve wording</button>` : `<input data-l="${key}:${i}:${f}" value="${esc(it[f])}">`}</div>`).join("")}</div></div>`).join("")
      || `<div class="empty small">Nothing added yet.</div>`;
  }
}
function fill() {
  $$("[data-k]").forEach(el => { const v = R[el.dataset.k]; el.value = Array.isArray(v) ? v.join(", ") : v || ""; });
  renderLists(); preview();
}
function preview() {
  const d = R, h = (t, body) => body ? `<h4>${t}</h4>${body}` : "";
  const line = (l, r) => `<div class="l"><span>${esc(l)}</span><span>${esc(r)}</span></div>`;
  const bl = (t) => `<ul class="clean" style="margin:2px 0">${String(t || "").split("\n").filter(x => x.trim()).map(x => `<li>${esc(x.replace(/^[-•*\s]+/, ""))}</li>`).join("")}</ul>`;
  $("#preview").innerHTML = `<h2>${esc(d.full_name || "Your Name")}</h2><div class="muted">${[d.email, d.phone, d.location, d.linkedin, d.github].filter(Boolean).map(esc).join(" | ")}</div>
  ${h("Summary", d.summary ? `<p>${esc(d.summary)}</p>` : "")}
  ${h("Education", d.education.map(e => line([e.degree, e.field].filter(Boolean).join(", "), [e.start, e.end].filter(Boolean).join(" - ")) + `<p>${esc([e.institution, e.grade].filter(Boolean).join(" | "))}</p>`).join(""))}
  ${h("Skills", d.skills.length ? `<p>${d.skills.map(esc).join(", ")}</p>` : "")}
  ${h("Experience", d.experience.map(e => line([e.role, e.company].filter(Boolean).join(", "), [e.start, e.end].filter(Boolean).join(" - ")) + bl(e.description)).join(""))}
  ${h("Projects", d.projects.map(p => line(p.name, p.link) + (p.tech ? `<p><i>Tech: ${esc(p.tech)}</i></p>` : "") + bl(p.description)).join(""))}
  ${h("Certifications", d.certifications.map(c => `<p>${esc([c.name, c.issuer, c.year].filter(Boolean).join(" | "))}</p>`).join(""))}`;
}
document.addEventListener("input", (e) => {
  const k = e.target.dataset.k, l = e.target.dataset.l;
  if (k) R[k] = k === "skills" ? e.target.value.split(",").map(s => s.trim()).filter(Boolean) : e.target.value;
  if (l) { const [key, i, f] = l.split(":"); R[key][+i][f] = e.target.value; }
  preview();
});
document.addEventListener("click", async (e) => {
  const add = e.target.closest("[data-add]"), del = e.target.closest("[data-del]"), imp = e.target.closest("[data-imp]");
  if (add) { const k = add.dataset.add; R[k].push(Object.fromEntries(SCHEMA[k].map(([f]) => [f, ""]))); renderLists(); preview(); }
  if (del) { const [k, i] = del.dataset.del.split(":"); R[k].splice(+i, 1); renderLists(); preview(); }
  if (imp) {
    const [k, i, f] = imp.dataset.imp.split(":");
    await withLoading(imp, async () => {
      const r = await api("/api/resume/improve", { method: "POST", body: { kind: "bullets", text: R[k][+i][f] } });
      R[k][+i][f] = r.text; renderLists(); preview(); toast(r.source === "ai" ? "Improved with AI" : "Wording tidied (offline mode)", "ok");
    });
  }
});
async function save(quiet) {
  if (!R.full_name?.trim()) throw new Error("Please enter your full name first.");
  await api("/api/resume", { method: "PUT", body: R }); if (!quiet) toast("Resume saved", "ok");
}
$("#saveBtn").addEventListener("click", (e) => withLoading(e.currentTarget, () => save()));
$("#pdfBtn").addEventListener("click", (e) => withLoading(e.currentTarget, async () => { await save(true); location.href = "/api/resume/pdf?template=" + $("#template").value; }));
$("#analyzeBtn").addEventListener("click", (e) => withLoading(e.currentTarget, async () => { await save(true); await api("/api/analyze/builder", { method: "POST", body: { role: $("#role").value } }); location.href = "/analyzer"; }));
$("#aiSummary").addEventListener("click", (e) => withLoading(e.currentTarget, async () => {
  const r = await api("/api/resume/improve", { method: "POST", body: { kind: "summary", role: $("#role").value, resume: R } });
  R.summary = r.text; fill(); toast(r.source === "ai" ? "Summary written with AI" : "Draft summary created (offline mode)", "ok");
}));
(async () => { try { const d = await api("/api/resume"); R = { ...R, ...d.data }; fill(); } catch (e) { toast(e.message, "err"); } })();
