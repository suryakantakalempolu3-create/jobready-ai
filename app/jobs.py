from urllib.parse import quote_plus
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from .models import db, User, Job, Resume, JobRecommendation
from .utils import login_required, uid, text, api_error, serialize, to_int, user_skills

bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


def match_jobs(user_id, q="", jtype="", location="", limit=50):
    """Score every job against the student and store the result in job_recommendations."""
    user = db.session.get(User, user_id)
    profile = user.profile
    have = {s.lower() for s in user_skills(user_id)}
    resume = Resume.query.filter_by(user_id=user_id).first()
    degrees = [profile.degree or ""] + [e.get("degree", "") for e in ((resume.data or {}).get("education", []) if resume else [])]
    degree_text = " ".join(degrees).lower()
    target = (profile.target_role or "").lower()

    query = Job.query
    if jtype:
        query = query.filter(Job.job_type == jtype)
    if location:
        query = query.filter(func.lower(Job.location).contains(location.lower(), autoescape=True))
    existing = {r.job_id: r for r in JobRecommendation.query.filter_by(user_id=user_id)}

    out = []
    for j in query.all():
        if q and q.lower() not in (j.title + " " + j.company + " " + " ".join(j.skills)).lower():
            continue
        req = [s.lower() for s in j.skills]
        matched = [s for s in req if s in have]
        score = (100 * len(matched) / len(req) if req else 0) * 0.8
        if target and (target in j.title.lower() or j.title.lower() in target):
            score += 10
        if any(qual.lower() in degree_text for qual in (j.qualifications or [])):
            score += 10
        match = round(min(100, score))
        missing = [s for s in req if s not in have]
        rec = existing.get(j.id)
        if rec is None:
            rec = JobRecommendation(user_id=user_id, job_id=j.id, is_saved=False)
            db.session.add(rec)
        rec.match_score, rec.matched_skills, rec.missing_skills = match, matched, missing
        out.append({"_id": str(j.id), "id": j.id, "title": j.title, "company": j.company, "location": j.location,
                    "type": j.job_type, "salary": j.salary, "description": j.description, "skills": j.skills,
                    "match": match, "matched_skills": matched, "missing_skills": missing, "saved": bool(rec.is_saved),
                    "apply_url": f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(j.title)}&location={quote_plus(j.location.split(',')[0])}"})
    try:
        db.session.commit()
    except IntegrityError:  # a parallel request stored the same rows first; results are still correct
        db.session.rollback()
    out.sort(key=lambda x: x["match"], reverse=True)
    return out[:limit]


@bp.get("")
@login_required
def list_jobs():
    rows = match_jobs(uid(), text(request.args.get("q"), 60), text(request.args.get("type"), 20), text(request.args.get("location"), 40))
    return jsonify(serialize(rows))


@bp.post("/<jid>/save")
@login_required
def toggle_save(jid):
    n = to_int(jid)
    job = db.session.get(Job, n) if n else None
    if not job:
        return api_error("Job not found.", 404)
    rec = JobRecommendation.query.filter_by(user_id=uid(), job_id=job.id).first()
    if rec is None:
        rec = JobRecommendation(user_id=uid(), job_id=job.id, match_score=0, matched_skills=[], missing_skills=[], is_saved=False)
        db.session.add(rec)
    rec.is_saved = not rec.is_saved
    db.session.commit()
    return jsonify(saved=bool(rec.is_saved))
