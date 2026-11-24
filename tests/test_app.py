import io
import os
import re
import pathlib
import pytest
from sqlalchemy import create_engine, text
from config import mysql_uri
from reportlab.pdfgen import canvas
from app import create_app
from app.models import db, User, StudentProgress, JobRecommendation, ResumeAnalysis
from app.seed_data import seed_all

RESUME_TEXT = [
    "Aarav Patil | aarav@example.com | +91 98765 43210 | linkedin.com/in/aarav | github.com/aarav",
    "SUMMARY", "Final-year student building Python and Flask web applications.",
    "EDUCATION", "B.Tech Computer Science, SGGS Institute 2022-2026",
    "SKILLS", "Python, Flask, SQL, Git, MongoDB, REST API, Docker, pandas",
    "EXPERIENCE", "Python Intern at DataNest. Developed reporting scripts that reduced manual work by 40%.",
    "Built REST endpoints used by 200+ users. Automated weekly tests and improved performance by 30%.",
    "PROJECTS", "Campus Portal: Implemented a Flask and MongoDB app. Designed login and admin dashboards.",
    "CERTIFICATIONS", "Python for Everybody - Coursera 2024",
] * 2


TEST_DB = os.getenv("TEST_DB_NAME", "jobready_ai_test")
SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schema.sql"


def reset_test_db():
    """Drop/recreate the test database by running the project's own schema.sql against MySQL."""
    engine = create_engine(mysql_uri(""))  # no default database selected
    sql = SCHEMA.read_text().replace("jobready_ai", TEST_DB)
    sql = re.sub(r"--[^\n]*", "", sql)  # strip SQL comments
    with engine.begin() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB}"))
        for stmt in filter(None, (s.strip() for s in sql.split(";"))):
            conn.execute(text(stmt))
    engine.dispose()
    return True


def make_pdf(lines):
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for ln in lines:
        c.drawString(40, y, ln)
        y -= 14
    c.save()
    return buf.getvalue()


@pytest.fixture()
def client():
    """Fresh MySQL test database built from schema.sql for every test."""
    app = create_app({"TESTING": True, "ANTHROPIC_API_KEY": "", "AUTO_CREATE_TABLES": False,
                      "SQLALCHEMY_DATABASE_URI": mysql_uri(TEST_DB)}, seed=False) if reset_test_db() else None
    with app.app_context():
        seed_all()
    c = app.test_client()
    c.get("/login")
    yield c
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def H(client):
    with client.session_transaction() as s:
        return {"X-CSRF-Token": s["csrf"]}


def login(client, email="demo@jobready.ai", pw="Demo@1234"):
    return client.post("/api/auth/login", json={"email": email, "password": pw}, headers=H(client))


def test_pages_render(client):
    for p in ("/", "/login", "/register"):
        assert client.get(p).status_code == 200
    assert client.get("/dashboard").status_code == 302  # protected
    login(client)
    for p in ("/dashboard", "/resume", "/analyzer", "/prep", "/mock", "/jobs", "/profile"):
        assert client.get(p).status_code == 200, p
    assert client.get("/nope").status_code == 404


def test_register_validation_and_hashing(client):
    h = H(client)
    assert client.post("/api/auth/register", json={"name": "A", "email": "x", "password": "p"}, headers=h).status_code == 400
    assert client.post("/api/auth/register", json={"name": "Test User", "email": "t@x.com", "password": "short1"}, headers=h).status_code == 400
    r = client.post("/api/auth/register", json={"name": "Test User", "email": "t@x.com", "password": "Strong123"}, headers=h)
    assert r.status_code == 201
    client.post("/api/auth/logout", headers=H(client))
    assert client.post("/api/auth/register", json={"name": "Test User", "email": "t@x.com", "password": "Strong123"}, headers=H(client)).status_code == 409
    with client.application.app_context():
        user = User.query.filter_by(email="t@x.com").one()
        assert user.password_hash != "Strong123" and user.password_hash.count("$") >= 2
        assert user.profile is not None  # student_profiles row created with the user


def test_login_logout_and_csrf(client):
    assert client.post("/api/auth/login", json={"email": "demo@jobready.ai", "password": "bad"}, headers=H(client)).status_code == 401
    assert client.post("/api/auth/login", json={"email": "demo@jobready.ai", "password": "Demo@1234"}).status_code == 400  # no CSRF
    assert login(client).status_code == 200
    assert client.get("/api/profile").status_code == 200
    client.post("/api/auth/logout", headers=H(client))
    assert client.get("/api/profile").status_code == 401


def test_profile_update(client):
    login(client)
    r = client.put("/api/profile", json={"name": "Aarav P", "skills": "Python, Java", "target_role": "Java Developer"}, headers=H(client))
    assert r.status_code == 200
    assert client.get("/api/profile").get_json()["profile"]["skills"] == ["Python", "Java"]
    assert client.put("/api/profile", json={"name": ""}, headers=H(client)).status_code == 400


def test_resume_save_pdf_improve(client):
    login(client)
    d = client.get("/api/resume").get_json()["data"]
    assert d["full_name"] == "Aarav Patil"
    d["skills"] = ["Python", "SQL"]
    d["summary"] = "<b>Hello & welcome</b>"
    assert client.put("/api/resume", json=d, headers=H(client)).status_code == 200
    assert client.put("/api/resume", json={"full_name": ""}, headers=H(client)).status_code == 400
    r = client.get("/api/resume/pdf?template=ocean")
    assert r.status_code == 200 and r.data.startswith(b"%PDF")
    s = client.post("/api/resume/improve", json={"kind": "summary", "role": "Python Developer", "resume": d}, headers=H(client)).get_json()
    assert s["source"] == "offline" and "Python" in s["text"]
    b = client.post("/api/resume/improve", json={"kind": "bullets", "text": "worked on login page\nhelped team"}, headers=H(client)).get_json()
    assert b["text"].startswith("Developed login page.")


def test_analyzer(client):
    login(client)
    h = H(client)
    r = client.post("/api/analyze", data={"role": "Python Developer", "resume": (io.BytesIO(make_pdf(RESUME_TEXT)), "r.pdf")}, headers=h, content_type="multipart/form-data")
    assert r.status_code == 200, r.get_json()
    j = r.get_json()
    assert 50 <= j["score"] <= 100 and "python" in j["found_skills"] and j["improvements"] is not None
    bad = client.post("/api/analyze", data={"resume": (io.BytesIO(b"not a pdf"), "r.pdf")}, headers=h, content_type="multipart/form-data")
    assert bad.status_code == 400
    txt = client.post("/api/analyze", data={"resume": (io.BytesIO(b"hello"), "r.txt")}, headers=h, content_type="multipart/form-data")
    assert txt.status_code == 400
    assert client.post("/api/analyze/builder", json={"role": "Python Developer"}, headers=h).status_code == 200
    assert len(client.get("/api/analyses").get_json()) >= 4
    with client.application.app_context():  # rows really are in MySQL, linked by foreign keys
        assert ResumeAnalysis.query.filter(ResumeAnalysis.resume_id.isnot(None)).count() == 1
        assert StudentProgress.query.filter_by(metric="resume_score").count() >= 5


def test_prep_and_mock_interview(client):
    login(client)
    h = H(client)
    r = client.post("/api/prep/questions", json={"role": "Java Developer", "type": "technical", "count": 5}, headers=h).get_json()
    assert len(r["questions"]) == 5 and r["questions"][0]["sample_answer"]
    assert client.post("/api/prep/questions", json={"role": "X", "type": "bogus"}, headers=h).status_code == 400

    s = client.post("/api/mock/start", json={"role": "Python Developer", "type": "mixed", "count": 3}, headers=h).get_json()
    iid = s["id"]
    assert s["total"] == 3 and s["question"]
    assert client.post(f"/api/mock/{iid}/answer", json={"answer": "x"}, headers=h).status_code == 400
    last = None
    for _ in range(3):
        last = client.post(f"/api/mock/{iid}/answer", json={"answer": "A decorator wraps a function to add behaviour such as logging, for example timing a request, because it keeps code clean."}, headers=h).get_json()
        assert 0 <= last["feedback"]["score"] <= 10
    assert last["done"] and last["summary"]["avg_score"] > 0
    assert client.post(f"/api/mock/{iid}/answer", json={"answer": "again again"}, headers=h).status_code == 409
    assert client.get(f"/api/mock/{iid}").status_code == 200
    assert client.get("/api/mock/notanid").status_code == 404
    assert any(x["_id"] == iid for x in client.get("/api/mock").get_json())
    det = client.get(f"/api/mock/{iid}").get_json()
    assert len(det["answers"]) == 3 and det["status"] == "completed"
    from app.models import InterviewQuestion, InterviewFeedback
    with client.application.app_context():
        assert InterviewQuestion.query.filter_by(interview_id=int(iid)).count() == 3
        assert InterviewFeedback.query.join(InterviewQuestion).filter(InterviewQuestion.interview_id == int(iid)).count() == 3


def test_interview_isolated_between_users(client):
    login(client)
    iid = client.post("/api/mock/start", json={"role": "Software Developer", "type": "hr", "count": 3}, headers=H(client)).get_json()["id"]
    client.post("/api/auth/logout", headers=H(client))
    client.post("/api/auth/register", json={"name": "Other One", "email": "o@x.com", "password": "Strong123"}, headers=H(client))
    assert client.get(f"/api/mock/{iid}").status_code == 404


def test_jobs_and_dashboard(client):
    login(client)
    h = H(client)
    jobs = client.get("/api/jobs").get_json()
    assert len(jobs) >= 10 and jobs[0]["match"] >= jobs[-1]["match"]
    assert "python" in " ".join(jobs[0]["title"].lower().split() + jobs[0]["skills"])
    assert len(client.get("/api/jobs?type=Internship").get_json()) >= 2
    jid = jobs[0]["_id"]
    assert client.post(f"/api/jobs/{jid}/save", headers=h).get_json()["saved"] is True
    assert client.get("/api/jobs").get_json()[0]["saved"] is True
    assert client.post(f"/api/jobs/{jid}/save", headers=h).get_json()["saved"] is False
    with client.application.app_context():
        assert JobRecommendation.query.count() >= 16
    d = client.get("/api/dashboard").get_json()
    assert d["resume_score"] == 74 and d["interview"]["count"] == 4 and d["recommended_jobs"] and d["next_steps"]


def test_foreign_keys_cascade_on_user_delete(client):
    login(client)
    client.get("/api/jobs")
    with client.application.app_context():
        u = User.query.filter_by(email="demo@jobready.ai").one()
        db.session.delete(u)
        db.session.commit()
        assert StudentProgress.query.count() == 0 and ResumeAnalysis.query.count() == 0 and JobRecommendation.query.count() == 0
