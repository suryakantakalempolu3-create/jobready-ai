import re
import secrets
from flask import Blueprint, jsonify, session
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, StudentProfile
from .utils import api_error, get_json, text, EMAIL_RE, login_required, uid

bp = Blueprint("auth", __name__, url_prefix="/api")


def _start_session(user_id):
    """New session (prevents fixation) with a fresh CSRF token."""
    session.clear()
    session["uid"] = int(user_id)
    session["csrf"] = secrets.token_hex(16)
    session.permanent = True


def _valid_password(pw):
    return len(pw) >= 8 and re.search(r"[A-Za-z]", pw) and re.search(r"\d", pw)


@bp.post("/auth/register")
def register():
    d = get_json()
    name, email, pw = text(d.get("name"), 80), text(d.get("email"), 120).lower(), str(d.get("password") or "")
    if len(name) < 2:
        return api_error("Please enter your full name.")
    if not EMAIL_RE.match(email):
        return api_error("Please enter a valid email address.")
    if not _valid_password(pw) or len(pw) > 128:
        return api_error("Password must be 8+ characters and include a letter and a number.")
    if User.query.filter_by(email=email).first():
        return api_error("An account with this email already exists.", 409)
    user = User(name=name, email=email, password_hash=generate_password_hash(pw))  # salted hash, never plain text
    user.profile = StudentProfile(skills=[])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:  # two simultaneous signups with the same email
        db.session.rollback()
        return api_error("An account with this email already exists.", 409)
    _start_session(user.id)
    return jsonify(ok=True, redirect="/dashboard"), 201


@bp.post("/auth/login")
def login():
    d = get_json()
    email, pw = text(d.get("email"), 120).lower(), str(d.get("password") or "")
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, pw):
        return api_error("Incorrect email or password.", 401)
    _start_session(user.id)
    return jsonify(ok=True, redirect="/dashboard")


@bp.post("/auth/logout")
def logout():
    session.clear()
    session["csrf"] = secrets.token_hex(16)
    return jsonify(ok=True, redirect="/")


@bp.get("/profile")
@login_required
def get_profile():
    u = db.session.get(User, uid())
    p = u.profile
    return jsonify(name=u.name, email=u.email, profile={
        "phone": p.phone, "location": p.location, "college": p.college, "degree": p.degree,
        "target_role": p.target_role, "headline": p.headline, "skills": p.skills or []})


@bp.put("/profile")
@login_required
def update_profile():
    d = get_json()
    name = text(d.get("name"), 80)
    if len(name) < 2:
        return api_error("Name must be at least 2 characters.")
    skills = d.get("skills", [])
    if isinstance(skills, str):
        skills = skills.split(",")
    skills = [text(s, 40) for s in skills if text(s, 40)][:40]
    u = db.session.get(User, uid())
    u.name = name
    p = u.profile
    for k in ("phone", "location", "college", "degree", "headline"):
        setattr(p, k, text(d.get(k), 120))
    p.target_role = text(d.get("target_role"), 80) or "Software Developer"
    p.skills = skills
    db.session.commit()
    return jsonify(ok=True)
