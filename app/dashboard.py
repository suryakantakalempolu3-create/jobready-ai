from flask import Blueprint, jsonify
from .models import db, User, Resume, ResumeAnalysis, Interview, StudentProgress
from .utils import login_required, uid, serialize, user_skills
from .services.scoring import ROLE_SKILLS
from .resume import completeness
from .jobs import match_jobs

bp = Blueprint("dashboard", __name__, url_prefix="/api")


def _history(user_id, metric, n=8):
    rows = (StudentProgress.query.filter_by(user_id=user_id, metric=metric)
            .order_by(StudentProgress.recorded_at.desc(), StudentProgress.id.desc()).limit(n).all())
    return list(reversed(rows))


@bp.get("/dashboard")
@login_required
def dashboard():
    user_id = uid()
    user = db.session.get(User, user_id)
    role = user.profile.target_role or "Software Developer"
    resume = Resume.query.filter_by(user_id=user_id).first()
    n_analyses = ResumeAnalysis.query.filter_by(user_id=user_id).count()
    score_hist = _history(user_id, "resume_score")
    iv_hist = _history(user_id, "interview_score")
    completed = Interview.query.filter_by(user_id=user_id, status="completed").all()

    have = {s.lower() for s in user_skills(user_id)}
    wanted = ROLE_SKILLS.get(role, ROLE_SKILLS["Software Developer"])
    skills = [{"skill": s, "have": s in have} for s in wanted]
    coverage = round(100 * sum(1 for s in skills if s["have"]) / len(skills))

    by_type = {}
    for iv in completed:
        by_type.setdefault(iv.interview_type, []).append(float(iv.avg_score))
    by_type = {k: round(sum(v) / len(v), 1) for k, v in by_type.items()}
    avg_iv = round(sum(float(i.avg_score) for i in completed) / len(completed), 1) if completed else None

    missing = [s["skill"] for s in skills if not s["have"]]
    comp = completeness(resume.data) if resume else 0
    latest = int(score_hist[-1].value) if score_hist else None
    steps = []
    if not resume or comp < 80:
        steps.append({"text": "Complete your resume to improve your profile strength.", "link": "/resume"})
    if n_analyses == 0:
        steps.append({"text": "Run the ATS analyzer to get your resume score.", "link": "/analyzer"})
    elif latest is not None and latest < 75:
        steps.append({"text": "Apply the analyzer's suggestions to lift your score above 75.", "link": "/analyzer"})
    if missing:
        steps.append({"text": f"Learn or showcase: {', '.join(missing[:3])} (in demand for {role}).", "link": "/profile"})
    if len(completed) < 3:
        steps.append({"text": "Take a mock interview to build confidence.", "link": "/mock"})
    elif avg_iv is not None and avg_iv < 7:
        steps.append({"text": "Review sample answers in Interview Prep and retry a mock interview.", "link": "/prep"})
    if not steps:
        steps.append({"text": "You're doing great — start applying to your top job matches!", "link": "/jobs"})

    return jsonify(serialize({
        "name": user.name, "target_role": role, "resume_score": latest,
        "score_history": [{"score": int(p.value), "date": p.recorded_at} for p in score_hist],
        "resume_completeness": comp,
        "interview": {"count": len(completed), "average": avg_iv, "by_type": by_type,
                      "history": [{"score": float(p.value), "role": p.label, "date": p.recorded_at} for p in iv_hist]},
        "skills": skills, "skill_coverage": coverage, "next_steps": steps[:4],
        "recommended_jobs": [{k: j[k] for k in ("_id", "title", "company", "location", "type", "match", "apply_url")}
                             for j in match_jobs(user_id, limit=4)],
    }))
