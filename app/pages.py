from flask import Blueprint, render_template, session, redirect
from .models import db, User
from .utils import login_required, uid
from .services.questions import ROLES

bp = Blueprint("pages", __name__)


def _user():
    if "uid" not in session:
        return None
    user = db.session.get(User, uid())
    if user is None:  # account was deleted: drop the stale session
        session.clear()
    return user


def render(tpl, **kw):
    return render_template(tpl, user=_user(), roles=ROLES, **kw)


@bp.get("/")
def home():
    return render("index.html")


@bp.get("/login")
def login():
    return redirect("/dashboard") if "uid" in session else render("login.html")


@bp.get("/register")
def register():
    return redirect("/dashboard") if "uid" in session else render("register.html")


def _protected(path, tpl, title):
    @login_required
    def view():
        return render(tpl, title=title, active=path.strip("/"))
    view.__name__ = "page_" + path.strip("/")
    bp.add_url_rule(path, view_func=view)


for _p, _t, _title in [("/dashboard", "dashboard.html", "Dashboard"), ("/resume", "resume.html", "Resume Builder"),
                       ("/analyzer", "analyzer.html", "Resume Analyzer"), ("/prep", "prep.html", "Interview Prep"),
                       ("/mock", "mock.html", "Mock Interview"), ("/jobs", "jobs.html", "Job Matches"),
                       ("/profile", "profile.html", "My Profile")]:
    _protected(_p, _t, _title)
