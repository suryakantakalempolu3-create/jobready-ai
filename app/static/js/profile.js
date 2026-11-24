const f = $("#profileForm");
(async () => {
  try {
    const d = await api("/api/profile");
    f.name.value = d.name; f.email.value = d.email;
    for (const k of ["phone", "location", "college", "degree", "target_role", "headline"]) if (f[k]) f[k].value = d.profile[k] || "";
    f.skills.value = (d.profile.skills || []).join(", ");
  } catch (e) { toast(e.message, "err"); }
})();
f.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (f.name.value.trim().length < 2) return toast("Please enter your name.", "err");
  const body = Object.fromEntries(new FormData(f)); delete body.email;
  await withLoading(f.querySelector("button"), async () => { await api("/api/profile", { method: "PUT", body }); toast("Profile saved", "ok"); });
});
