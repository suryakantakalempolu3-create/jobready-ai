"""SQLAlchemy models — these mirror schema.sql (MySQL)."""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import INTEGER, SMALLINT

db = SQLAlchemy()
UInt = INTEGER(unsigned=True)
USmall = SMALLINT(unsigned=True)


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC, stored in DATETIME


def dec(prec, scale):
    return db.Numeric(prec, scale, asdecimal=False)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(UInt, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    profile = db.relationship("StudentProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    resume = db.relationship("Resume", uselist=False, back_populates="user", cascade="all, delete-orphan")
    analyses = db.relationship("ResumeAnalysis", back_populates="user", cascade="all, delete-orphan")
    interviews = db.relationship("Interview", back_populates="user", cascade="all, delete-orphan")
    recommendations = db.relationship("JobRecommendation", back_populates="user", cascade="all, delete-orphan")
    progress = db.relationship("StudentProgress", back_populates="user", cascade="all, delete-orphan")


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"
    id = db.Column(UInt, primary_key=True)
    user_id = db.Column(UInt, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    phone = db.Column(db.String(40), nullable=False, default="")
    location = db.Column(db.String(120), nullable=False, default="")
    college = db.Column(db.String(120), nullable=False, default="")
    degree = db.Column(db.String(120), nullable=False, default="")
    target_role = db.Column(db.String(80), nullable=False, default="Software Developer")
    headline = db.Column(db.String(120), nullable=False, default="")
    skills = db.Column(db.JSON, nullable=False, default=list)
    user = db.relationship("User", back_populates="profile")


class Resume(db.Model):
    __tablename__ = "resumes"
    id = db.Column(UInt, primary_key=True)
    user_id = db.Column(UInt, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    data = db.Column(db.JSON, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    user = db.relationship("User", back_populates="resume")
    analyses = db.relationship("ResumeAnalysis", back_populates="resume")


class ResumeAnalysis(db.Model):
    __tablename__ = "resume_analysis"
    id = db.Column(UInt, primary_key=True)
    user_id = db.Column(UInt, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_id = db.Column(UInt, db.ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    filename = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(60), nullable=False)
    score = db.Column(USmall, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(10), nullable=False, default="offline")
    word_count = db.Column(UInt, nullable=False, default=0)
    breakdown = db.Column(db.JSON, nullable=False)
    found_skills = db.Column(db.JSON, nullable=False)
    missing_skills = db.Column(db.JSON, nullable=False)
    strengths = db.Column(db.JSON, nullable=False)
    improvements = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    user = db.relationship("User", back_populates="analyses")
    resume = db.relationship("Resume", back_populates="analyses")


class Interview(db.Model):
    __tablename__ = "interviews"
    id = db.Column(UInt, primary_key=True)
    user_id = db.Column(UInt, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(60), nullable=False)
    interview_type = db.Column(db.String(12), nullable=False)
    status = db.Column(db.String(12), nullable=False, default="in_progress")
    source = db.Column(db.String(10), nullable=False, default="offline")
    avg_score = db.Column(dec(4, 1), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship("User", back_populates="interviews")
    questions = db.relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan",
                                order_by="InterviewQuestion.position")


class InterviewQuestion(db.Model):
    __tablename__ = "interview_questions"
    __table_args__ = (db.UniqueConstraint("interview_id", "position", name="uq_question_position"),)
    id = db.Column(UInt, primary_key=True)
    interview_id = db.Column(UInt, db.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    position = db.Column(USmall, nullable=False)
    question = db.Column(db.Text, nullable=False)
    sample_answer = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.JSON, nullable=False)
    category = db.Column(db.String(12), nullable=False, default="technical")
    interview = db.relationship("Interview", back_populates="questions")
    feedback = db.relationship("InterviewFeedback", uselist=False, back_populates="question", cascade="all, delete-orphan")


class InterviewFeedback(db.Model):
    __tablename__ = "interview_feedback"
    id = db.Column(UInt, primary_key=True)
    question_id = db.Column(UInt, db.ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False, unique=True)
    answer = db.Column(db.Text, nullable=False)
    score = db.Column(dec(4, 1), nullable=False)
    strengths = db.Column(db.JSON, nullable=False)
    improvements = db.Column(db.JSON, nullable=False)
    ideal_answer = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(10), nullable=False, default="offline")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    question = db.relationship("InterviewQuestion", back_populates="feedback")


class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(UInt, primary_key=True)
    title = db.Column(db.String(120), nullable=False, index=True)
    company = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    job_type = db.Column(db.String(20), nullable=False)
    salary = db.Column(db.String(40), nullable=False, default="")
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.JSON, nullable=False)
    qualifications = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class JobRecommendation(db.Model):
    __tablename__ = "job_recommendations"
    __table_args__ = (db.UniqueConstraint("user_id", "job_id", name="uq_rec_user_job"),)
    id = db.Column(UInt, primary_key=True)
    user_id = db.Column(UInt, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = db.Column(UInt, db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    match_score = db.Column(USmall, nullable=False, default=0)
    matched_skills = db.Column(db.JSON, nullable=False)
    missing_skills = db.Column(db.JSON, nullable=False)
    is_saved = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    user = db.relationship("User", back_populates="recommendations")
    job = db.relationship("Job")


class StudentProgress(db.Model):
    __tablename__ = "student_progress"
    id = db.Column(UInt, primary_key=True)
    user_id = db.Column(UInt, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    metric = db.Column(db.String(30), nullable=False)
    value = db.Column(dec(5, 1), nullable=False)
    label = db.Column(db.String(120), nullable=False, default="")
    recorded_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    user = db.relationship("User", back_populates="progress")
    __table_args__ = (db.Index("ix_progress_user_metric", "user_id", "metric", "recorded_at"),)
