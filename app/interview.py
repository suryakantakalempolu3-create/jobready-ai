from flask import Blueprint, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from .models import db, Interview, InterviewQuestion, InterviewFeedback, utcnow
from .utils import login_required, uid, get_json, text, api_error, serialize, to_int, record_progress
from .services.questions import generate_questions, evaluate_answer, HR

bp = Blueprint("interview", __name__, url_prefix="/api")
HR_TEXTS = {q["question"] for q in HR}


def _params(d, lo, hi, default):
    role = text(d.get("role"), 60) or "Software Developer"
    qtype = d.get("type", "mixed")
    if qtype not in ("technical", "hr", "mixed"):
        return None, None, None, "Choose technical, HR or mixed questions."
    try:
        count = max(lo, min(hi, int(d.get("count", default))))
    except (TypeError, ValueError):
        count = default
    return role, qtype, count, None


@bp.post("/prep/questions")
@login_required
def prep_questions():
    role, qtype, count, err = _params(get_json(), 3, 15, 8)
    if err:
        return api_error(err)
    qs, source = generate_questions(current_app.ai, role, qtype, count)
    return jsonify(role=role, source=source, questions=qs)


@bp.post("/mock/start")
@login_required
def mock_start():
    role, qtype, count, err = _params(get_json(), 3, 10, 5)
    if err:
        return api_error(err)
    qs, source = generate_questions(current_app.ai, role, qtype, count)
    iv = Interview(user_id=uid(), role=role, interview_type=qtype, source=source)
    for pos, q in enumerate(qs):
        cat = q.get("type") if q.get("type") in ("technical", "hr") else ("hr" if q["question"] in HR_TEXTS else "technical")
        iv.questions.append(InterviewQuestion(position=pos, question=q["question"], sample_answer=q.get("sample_answer", ""),
                                              keywords=q.get("keywords", []), category=cat))
    db.session.add(iv)
    db.session.commit()
    return jsonify(id=str(iv.id), role=role, total=len(qs), index=0, question=qs[0]["question"], source=source), 201


def _owned(iid):
    n = to_int(iid)
    return Interview.query.filter_by(id=n, user_id=uid()).first() if n else None


@bp.post("/mock/<iid>/answer")
@login_required
def mock_answer(iid):
    iv = _owned(iid)
    if not iv:
        return api_error("Interview not found.", 404)
    if iv.status == "completed":
        return api_error("This interview is already finished.", 409)
    answer = text(get_json().get("answer"), 4000)
    if len(answer) < 5:
        return api_error("Please write an answer before submitting.")
    qs = iv.questions
    idx = sum(1 for q in qs if q.feedback is not None)
    q = qs[idx]
    fb = evaluate_answer(current_app.ai, iv.role, {"question": q.question, "keywords": q.keywords,
                                                   "sample_answer": q.sample_answer}, answer)
    db.session.add(InterviewFeedback(question_id=q.id, answer=answer, score=fb["score"], strengths=fb["strengths"],
                                     improvements=fb["improvements"], ideal_answer=fb["ideal_answer"], source=fb["source"]))
    done = idx + 1 >= len(qs)
    resp = {"feedback": fb, "index": idx, "done": done}
    if done:
        scores = [float(x.feedback.score) for x in qs[:idx]] + [fb["score"]]
        avg = round(sum(scores) / len(scores), 1)
        iv.status, iv.avg_score, iv.completed_at = "completed", avg, utcnow()
        record_progress(uid(), "interview_score", avg, iv.role)
        resp["summary"] = {"avg_score": avg, "answered": len(scores),
                           "verdict": "Excellent — interview ready!" if avg >= 8 else "Good progress — keep practising." if avg >= 6 else "Needs work — review the sample answers and retry."}
    else:
        resp["next_question"] = qs[idx + 1].question
    try:
        db.session.commit()
    except IntegrityError:  # the same question was submitted twice at once
        db.session.rollback()
        return api_error("That answer was already submitted.", 409)
    return jsonify(resp)


@bp.get("/mock/<iid>")
@login_required
def mock_get(iid):
    iv = _owned(iid)
    if not iv:
        return api_error("Interview not found.", 404)
    answered = [q for q in iv.questions if q.feedback is not None]
    return jsonify(serialize({
        "_id": str(iv.id), "id": iv.id, "role": iv.role, "type": iv.interview_type, "status": iv.status,
        "avg_score": iv.avg_score, "created_at": iv.created_at, "total": len(iv.questions),
        "answers": [{"question": q.question, "answer": q.feedback.answer, "score": q.feedback.score,
                     "strengths": q.feedback.strengths, "improvements": q.feedback.improvements,
                     "ideal_answer": q.feedback.ideal_answer} for q in answered]}))


@bp.get("/mock")
@login_required
def mock_history():
    rows = Interview.query.filter_by(user_id=uid()).order_by(Interview.created_at.desc(), Interview.id.desc()).limit(15).all()
    return jsonify(serialize([{"_id": str(r.id), "id": r.id, "role": r.role, "type": r.interview_type, "status": r.status,
                               "avg_score": r.avg_score, "created_at": r.created_at} for r in rows]))
