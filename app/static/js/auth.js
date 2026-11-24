const form = $("#loginForm") || $("#registerForm");
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const err = $("#formErr"); err.textContent = "";
  const body = Object.fromEntries(new FormData(form));
  const isReg = form.id === "registerForm";
  if (isReg && body.name.trim().length < 2) return (err.textContent = "Please enter your full name.");
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(body.email)) return (err.textContent = "Please enter a valid email address.");
  if (isReg && !(body.password.length >= 8 && /[A-Za-z]/.test(body.password) && /\d/.test(body.password)))
    return (err.textContent = "Password must be 8+ characters and include a letter and a number.");
  const btn = form.querySelector("button");
  btn.disabled = true; btn.classList.add("loading");
  try {
    const r = await api(isReg ? "/api/auth/register" : "/api/auth/login", { method: "POST", body });
    const next = new URLSearchParams(location.search).get("next");
    location.href = next && next.startsWith("/") && !next.startsWith("//") ? next : r.redirect;
  } catch (ex) { err.textContent = ex.message; btn.disabled = false; btn.classList.remove("loading"); }
});
