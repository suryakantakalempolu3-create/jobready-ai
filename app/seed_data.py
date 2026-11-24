"""Sample data. Job listings are fictional samples for testing; 'Apply' opens a live LinkedIn search for the title."""
from datetime import timedelta
from werkzeug.security import generate_password_hash
from .models import (db, utcnow, User, StudentProfile, Resume, ResumeAnalysis, Interview, Job,
                     JobRecommendation, StudentProgress)

D = ["B.E", "B.Tech", "BCA", "MCA", "B.Sc", "M.Sc", "M.Tech"]


def J(title, company, location, type_, skills, salary, desc):
    return {"title": title, "company": company, "location": location, "type": type_, "skills": skills,
            "salary": salary, "description": desc, "qualifications": D}


JOBS = [
    J("Java Developer", "NovaSoft Technologies", "Pune, Maharashtra", "Full-time", ["java", "spring boot", "sql", "git", "rest api"], "₹4–6 LPA", "Build and maintain Spring Boot microservices for banking clients."),
    J("Java Developer Intern", "CodeBridge Labs", "Mumbai, Maharashtra", "Internship", ["java", "oop", "sql", "git"], "₹15k/month", "Six-month internship working on backend modules with senior mentors."),
    J("Junior Java Backend Engineer", "FinEdge Systems", "Hyderabad, Telangana", "Full-time", ["java", "hibernate", "mysql", "junit", "maven"], "₹5–7 LPA", "Develop REST APIs and write unit tests for payment services."),
    J("Python Developer", "Pythonic Works", "Nagpur, Maharashtra", "Full-time", ["python", "flask", "sql", "git", "rest api"], "₹4–6 LPA", "Create Flask APIs and automation scripts for logistics software."),
    J("Python Django Developer", "BrightApps", "Bengaluru, Karnataka", "Full-time", ["python", "django", "postgresql", "docker", "git"], "₹6–9 LPA", "Own features for a SaaS product built with Django and PostgreSQL."),
    J("Python Developer Intern", "DataNest", "Remote", "Internship", ["python", "pandas", "git", "sql"], "₹12k/month", "Support the data team with scripts, cleaning and reporting."),
    J("Software Developer", "Orbit Digital", "Pune, Maharashtra", "Full-time", ["data structures", "algorithms", "oop", "sql", "git"], "₹5–8 LPA", "Work across the stack on a growing e-commerce platform."),
    J("Associate Software Engineer", "Zenith IT Services", "Chhatrapati Sambhajinagar, Maharashtra", "Full-time", ["data structures", "oop", "sql", "testing", "agile"], "₹3.5–5 LPA", "Campus-hire role with structured training and mentoring."),
    J("Software Engineer Trainee", "Skyline Infotech", "Nanded, Maharashtra", "Full-time", ["oop", "sql", "git", "problem solving"], "₹3–4 LPA", "Entry-level role with training in modern development practices."),
    J("Full Stack Developer", "Pixel & Pine", "Remote", "Full-time", ["javascript", "react", "node.js", "mongodb", "git"], "₹6–10 LPA", "Build customer-facing dashboards with React and Node."),
    J("Frontend Developer", "Lumen Studio", "Mumbai, Maharashtra", "Full-time", ["html", "css", "javascript", "react", "responsive design"], "₹4–7 LPA", "Turn designs into fast, accessible, responsive interfaces."),
    J("Web Developer Intern", "WebCraft Co.", "Pune, Maharashtra", "Internship", ["html", "css", "javascript", "git"], "₹10k/month", "Learn production web development while shipping real pages."),
    J("Data Analyst", "InsightIQ Analytics", "Bengaluru, Karnataka", "Full-time", ["sql", "excel", "python", "power bi", "statistics"], "₹4–7 LPA", "Turn business data into dashboards and decisions."),
    J("Junior Data Analyst", "MetricMind", "Pune, Maharashtra", "Full-time", ["sql", "excel", "tableau", "data visualization"], "₹3.5–5 LPA", "Create weekly reports and clean datasets for retail clients."),
    J("QA Automation Engineer", "TestTrail", "Hyderabad, Telangana", "Full-time", ["testing", "python", "git", "agile", "sql"], "₹4–6 LPA", "Automate regression tests and improve release quality."),
    J("Backend Developer (MongoDB)", "CloudLeaf", "Remote", "Full-time", ["python", "mongodb", "rest api", "docker", "git"], "₹6–9 LPA", "Design APIs and data models on MongoDB for IoT products."),
]


def seed_jobs():
    if Job.query.count() == 0:
        db.session.add_all([Job(title=j["title"], company=j["company"], location=j["location"], job_type=j["type"],
                                skills=j["skills"], salary=j["salary"], description=j["description"],
                                qualifications=j["qualifications"]) for j in JOBS])
        db.session.commit()


def seed_all(reset=False):
    """Insert demo data. Must run inside an app context."""
    if reset:
        for model in (StudentProgress, JobRecommendation, Interview, ResumeAnalysis, Resume, StudentProfile, User, Job):
            model.query.delete()  # children first, so foreign keys are respected
        db.session.commit()
    seed_jobs()
    if User.query.filter_by(email="demo@jobready.ai").first():
        return
    now = utcnow()
    user = User(name="Aarav Patil", email="demo@jobready.ai", password_hash=generate_password_hash("Demo@1234"))
    user.profile = StudentProfile(phone="+91 98765 43210", location="Nanded, Maharashtra", college="SGGS Institute of Engineering",
                                  degree="B.Tech Computer Science", target_role="Python Developer",
                                  headline="Final-year CS student who loves building web apps",
                                  skills=["Python", "Flask", "SQL", "Git", "HTML", "CSS"])
    user.resume = Resume(data={
        "full_name": "Aarav Patil", "email": "demo@jobready.ai", "phone": "+91 98765 43210", "location": "Nanded, Maharashtra",
        "linkedin": "linkedin.com/in/aarav-patil", "github": "github.com/aaravpatil",
        "summary": "Final-year B.Tech student with hands-on experience building Flask web applications and REST APIs.",
        "education": [{"institution": "SGGS Institute of Engineering", "degree": "B.Tech", "field": "Computer Science", "start": "2022", "end": "2026", "grade": "CGPA 8.4"}],
        "skills": ["Python", "Flask", "SQL", "MySQL", "Git", "HTML", "CSS", "JavaScript", "REST API"],
        "experience": [{"company": "DataNest", "role": "Python Intern", "start": "Jun 2025", "end": "Aug 2025",
                        "description": "Automated weekly reports with pandas, saving 6 hours per week\nBuilt 3 REST endpoints used by 200+ internal users"}],
        "projects": [{"name": "Campus Event Portal", "tech": "Flask, MySQL, Bootstrap", "link": "github.com/aaravpatil/events",
                      "description": "Developed a full-stack event registration app with login and admin dashboard\nReduced manual paperwork by 80% for 5 college clubs"}],
        "certifications": [{"name": "Python for Everybody", "issuer": "Coursera", "year": "2024"}]})
    db.session.add(user)
    db.session.flush()
    for i, sc in enumerate([58, 66, 74]):
        when = now - timedelta(days=21 - i * 7)
        db.session.add(ResumeAnalysis(
            user_id=user.id, filename="sample_resume.pdf", role="Python Developer", score=sc, summary="Sample analysis.",
            breakdown={}, found_skills=["python", "flask"], missing_skills=["docker", "pytest"],
            strengths=["Clear structure."], improvements=["Add measurable results."], source="offline", created_at=when))
        db.session.add(StudentProgress(user_id=user.id, metric="resume_score", value=sc, label="sample_resume.pdf", recorded_at=when))
    for i, (t, sc) in enumerate([("mixed", 5.8), ("technical", 6.9), ("hr", 7.6), ("technical", 7.9)]):
        when = now - timedelta(days=16 - i * 4)
        db.session.add(Interview(user_id=user.id, role="Python Developer", interview_type=t, status="completed",
                                 avg_score=sc, source="offline", created_at=when, completed_at=when))
        db.session.add(StudentProgress(user_id=user.id, metric="interview_score", value=sc, label="Python Developer", recorded_at=when))
    db.session.commit()
