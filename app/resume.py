import re
from flask import Blueprint, jsonify, request, Response
from .models import db, User, Resume
from .utils import login_required, uid, get_json, text, api_error, serialize, EMAIL_RE, record_progress
from .services.pdfgen import build_resume_pdf

bp = Blueprint("resume", __name__, url_prefix="/api/resume")

LIST_FIELDS = {
    "education": ["institution", "degree", "field", "start", "end", "grade"],
    "experience": ["company", "role", "start", "end", "description"],
    "projects": ["name", "tech", "description", "link"],
    "certifications": ["name", "issuer", "year"],
}


def clean_resume(d):
    out = {k: text(d.get(k), 120) for k in ("full_name", "email", "phone", "location", "linkedin", "github")}
    out["summary"] = text(d.get("summary"), 800)
    skills = d.get("skills", [])
    if isinstance(skills, str):
        skills = skills.split(",")
    out["skills"] = [text(s, 40) for s in skills if text(s, 40)][:50]
    for key, fields in LIST_FIELDS.items():
        items = d.get(key, [])
        items = items if isinstance(items, list) else []
        cleaned = []
        for it in items[:15]:
            if isinstance(it, dict):
                row = {f: text(it.get(f), 1200 if f == "description" else 150) for f in fields}
                if any(row.values()):
                    cleaned.append(row)
        out[key] = cleaned
    return out


def completeness(d):
    checks = [d.get("full_name"), d.get("email"), d.get("phone"), d.get("summary"), d.get("education"),
              len(d.get("skills", [])) >= 5, d.get("projects"), d.get("certifications"), d.get("linkedin") or d.get("github")]
    return round(100 * sum(1 for c in checks if c) / len(checks))


@bp.get("")
@login_required
def get_resume():
    row = Resume.query.filter_by(user_id=uid()).first()
    if row:
        return jsonify(serialize({"data": row.data, "updated_at": row.updated_at}))
    u = db.session.get(User, uid())
    p = u.profile
    base = clean_resume({"full_name": u.name, "email": u.email, "phone": p.phone,
                         "location": p.location, "skills": p.skills or []})
    return jsonify({"data": base, "updated_at": None})


@bp.put("")
@login_required
def save_resume():
    data = clean_resume(get_json())
    if not data["full_name"]:
        return api_error("Please enter your full name.")
    if data["email"] and not EMAIL_RE.match(data["email"]):
        return api_error("Please enter a valid email address.")
    row = Resume.query.filter_by(user_id=uid()).first()
    if row:
        row.data = data
    else:
        db.session.add(Resume(user_id=uid(), data=data))
    record_progress(uid(), "resume_completeness", completeness(data), "Resume Builder")
    db.session.commit()
    return jsonify(ok=True)


@bp.post("/improve")
@login_required
def improve():
    """AI-assisted writing: kind = 'summary' (write a professional summary) or 'bullets' (rewrite bullet points)."""
    from flask import current_app
    d = get_json()
    kind = d.get("kind")
    if kind not in ("summary", "bullets"):
        return api_error("Unknown improvement type.")
    ctx = clean_resume(d.get("resume") or {})
    role = text(d.get("role"), 60) or "Software Developer"
    ai = current_app.ai
    if kind == "summary":
        res = ai.complete_json(
            f"Write a 2-3 sentence ATS-friendly professional summary (first-person implied, no 'I') for a student applying as "
            f"<data>{role}</data>. Candidate data: <data>{ctx}</data>. Return JSON {{\"text\": str}}", 600)
        if isinstance(res, dict) and res.get("text"):
            return jsonify(text=str(res["text"])[:800], source="ai")
        skills = ", ".join(ctx["skills"][:6]) or "modern programming tools"
        edu = ctx["education"][0] if ctx["education"] else {}
        study = f"{edu.get('degree', 'technology')} student" if edu else "motivated student"
        proj = f" Built {len(ctx['projects'])} hands-on project(s)." if ctx["projects"] else ""
        return jsonify(text=f"Motivated {study} aspiring {role} with skills in {skills}.{proj} "
                            f"Eager to apply problem-solving and teamwork skills to deliver quality software.", source="offline")
    src = text(d.get("text"), 1200)
    if len(src) < 8:
        return api_error("Write a few words first, then improve them.")
    res = ai.complete_json(
        f"Rewrite these resume bullet points to be concise and impact-oriented, starting each with a strong action verb, "
        f"keeping facts unchanged and not inventing metrics. Text: <data>{src}</data> Return JSON {{\"text\": \"bullets separated by newlines\"}}", 800)
    if isinstance(res, dict) and res.get("text"):
        return jsonify(text=str(res["text"])[:1200], source="ai")
    weak = {r"^(worked on|worked with)": "Developed", r"^(made)": "Built", r"^(helped)": "Supported", r"^(did)": "Completed",
            r"^(responsible for)": "Managed"}
    lines = []
    for ln in src.splitlines():
        ln = ln.strip().lstrip("-•* ").strip()
        if not ln:
            continue
        for pat, rep in weak.items():
            ln = re.sub(pat, rep, ln, flags=re.I)
        ln = ln[0].upper() + ln[1:]
        lines.append(ln if ln.endswith(".") else ln + ".")
    return jsonify(text="\n".join(lines), source="offline")


@bp.get("/pdf")
@login_required
def download_pdf():
    row = Resume.query.filter_by(user_id=uid()).first()
    if not row:
        return api_error("Save your resume first, then download it.", 404)
    pdf = build_resume_pdf(row.data, request.args.get("template", "modern"))
    fname = re.sub(r"[^A-Za-z0-9]+", "_", row.data.get("full_name") or "resume").strip("_") or "resume"
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}_Resume.pdf"'})
