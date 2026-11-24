from io import BytesIO
from flask import Blueprint, jsonify, request, current_app
from pypdf import PdfReader
from .models import db, Resume, ResumeAnalysis
from .utils import login_required, uid, text, api_error, serialize, get_json, record_progress
from .services.scoring import analyze_text, ROLE_SKILLS
from .services.pdfgen import resume_to_text

bp = Blueprint("analyzer", __name__, url_prefix="/api")


def run_analysis(content, role, filename, resume_id=None):
    base = analyze_text(content, role if role in ROLE_SKILLS else "Software Developer")
    score, source = base["heuristic_score"], "offline"
    summary = ""
    improvements, strengths, missing = base["improvements"], base["strengths"], base["missing_skills"]
    ai_res = current_app.ai.complete_json(
        f"Act as an ATS and recruiter. Analyze this resume for the role <data>{role}</data>.\n<resume>{content[:9000]}</resume>\n"
        'Return JSON: {"ats_score":0-100,"summary":"2 sentences","strengths":[3-5 strings],'
        '"improvements":[4-6 specific actionable strings],"missing_skills":[up to 8 skills relevant to the role not on the resume]}', 1800)
    if isinstance(ai_res, dict) and isinstance(ai_res.get("ats_score"), (int, float)):
        score = round((base["heuristic_score"] + max(0, min(100, ai_res["ats_score"]))) / 2)
        summary = text(ai_res.get("summary"), 500)
        strengths = [text(s, 250) for s in ai_res.get("strengths", [])][:6] or strengths
        improvements = [text(s, 300) for s in ai_res.get("improvements", [])][:8] or improvements
        missing = [text(s, 40) for s in ai_res.get("missing_skills", [])][:10] or missing
        source = "ai"
    if not summary:
        summary = (f"Your resume scores {score}/100 for {role}. " +
                   ("It is in good shape — polish the details below." if score >= 70 else "Focus on the improvements below to pass ATS filters."))
    row = ResumeAnalysis(user_id=uid(), resume_id=resume_id, filename=filename, role=role[:60], score=score,
                         summary=summary, breakdown=base["breakdown"], found_skills=base["found_skills"],
                         missing_skills=missing, strengths=strengths, improvements=improvements,
                         word_count=base["word_count"], source=source)
    db.session.add(row)
    record_progress(uid(), "resume_score", score, filename)
    db.session.commit()
    return analysis_dict(row)


def analysis_dict(r, full=True):
    d = {"_id": str(r.id), "id": r.id, "filename": r.filename, "role": r.role, "score": r.score,
         "source": r.source, "created_at": r.created_at}
    if full:
        d.update(summary=r.summary, breakdown=r.breakdown, found_skills=r.found_skills, missing_skills=r.missing_skills,
                 strengths=r.strengths, improvements=r.improvements, word_count=r.word_count)
    return serialize(d)


@bp.post("/analyze")
@login_required
def analyze_pdf():
    f = request.files.get("resume")
    role = text(request.form.get("role"), 60) or "Software Developer"
    if not f or not f.filename:
        return api_error("Please choose a PDF file to upload.")
    if not f.filename.lower().endswith(".pdf"):
        return api_error("Only PDF files are supported.")
    raw = f.read()
    if not raw.startswith(b"%PDF"):
        return api_error("That file doesn't look like a valid PDF.")
    try:
        reader = PdfReader(BytesIO(raw))
        if reader.is_encrypted:
            return api_error("This PDF is password protected. Remove the password and try again.")
        content = "\n".join((p.extract_text() or "") for p in reader.pages[:6]).strip()
    except Exception:
        return api_error("We couldn't read that PDF. Try exporting it again.")
    if len(content) < 80:
        return api_error("We couldn't find readable text. Scanned/image PDFs aren't supported — export a text-based PDF.")
    return jsonify(run_analysis(content, role, text(f.filename, 100)))


@bp.post("/analyze/builder")
@login_required
def analyze_builder():
    row = Resume.query.filter_by(user_id=uid()).first()
    if not row:
        return api_error("Build and save a resume first.", 404)
    role = text(get_json().get("role"), 60) or "Software Developer"
    return jsonify(run_analysis(resume_to_text(row.data), role, "Resume Builder resume", resume_id=row.id))


@bp.get("/analyses")
@login_required
def history():
    rows = (ResumeAnalysis.query.filter_by(user_id=uid())
            .order_by(ResumeAnalysis.created_at.desc(), ResumeAnalysis.id.desc()).limit(10).all())
    return jsonify([analysis_dict(r, full=False) for r in rows])
