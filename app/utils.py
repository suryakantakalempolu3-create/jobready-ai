import re
from datetime import datetime
from decimal import Decimal
from functools import wraps
from flask import session, jsonify, redirect, request, url_for
from .models import db, User, StudentProgress

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def api_error(msg, code=400):
    return jsonify(error=msg), code


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if "uid" not in session:
            if request.path.startswith("/api/"):
                return api_error("Please log in to continue.", 401)
            return redirect(url_for("pages.login", next=request.path))
        return fn(*a, **kw)
    return wrapper


def uid():
    return int(session["uid"])


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def text(value, max_len=200):
    """Coerce to a trimmed, length-limited string."""
    if value is None:
        return ""
    return str(value).strip()[:max_len]


def serialize(obj):
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items() if k != "password_hash"}
    if isinstance(obj, (list, tuple)):
        return [serialize(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat() + "Z"
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def get_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def record_progress(user_id, metric, value, label=""):
    """Append a point to the student_progress timeline (caller commits)."""
    db.session.add(StudentProgress(user_id=user_id, metric=metric, value=value, label=text(label, 120)))


def user_skills(user_id):
    """Union of profile skills and resume-builder skills (de-duplicated, case-insensitive)."""
    user = db.session.get(User, user_id)
    if not user:
        return []
    mine = list(user.profile.skills or []) if user.profile else []
    mine += list((user.resume.data or {}).get("skills", [])) if user.resume else []
    out, seen = [], set()
    for s in mine:
        if s and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out
