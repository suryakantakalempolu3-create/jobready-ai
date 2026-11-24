-- JobReady AI — MySQL 8.0+ schema
-- Run:  mysql -u root -p < schema.sql
-- Creates the database "jobready_ai" and all tables (safe to re-run: uses IF NOT EXISTS).

CREATE DATABASE IF NOT EXISTS jobready_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE jobready_ai;

-- 1. Accounts ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name          VARCHAR(80)  NOT NULL,
    email         VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,              -- salted hash (Werkzeug), never plain text
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

-- 2. Student profile (1:1 with users) ---------------------------------------
CREATE TABLE IF NOT EXISTS student_profiles (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED NOT NULL,
    phone       VARCHAR(40)  NOT NULL DEFAULT '',
    location    VARCHAR(120) NOT NULL DEFAULT '',
    college     VARCHAR(120) NOT NULL DEFAULT '',
    degree      VARCHAR(120) NOT NULL DEFAULT '',
    target_role VARCHAR(80)  NOT NULL DEFAULT 'Software Developer',
    headline    VARCHAR(120) NOT NULL DEFAULT '',
    skills      JSON         NOT NULL,                -- ["Python","SQL",...]
    PRIMARY KEY (id),
    UNIQUE KEY uq_profile_user (user_id),
    CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Resume built in the Resume Builder (1:1 with users) --------------------
CREATE TABLE IF NOT EXISTS resumes (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id    INT UNSIGNED NOT NULL,
    data       JSON         NOT NULL,                 -- education, skills, projects, certifications, ...
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_resume_user (user_id),
    CONSTRAINT fk_resume_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. ATS analysis results (uploaded PDF, or the built resume) ---------------
CREATE TABLE IF NOT EXISTS resume_analysis (
    id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id        INT UNSIGNED NOT NULL,
    resume_id      INT UNSIGNED NULL,                 -- set when the Resume Builder resume was analysed
    filename       VARCHAR(120) NOT NULL,
    role           VARCHAR(60)  NOT NULL,
    score          SMALLINT UNSIGNED NOT NULL,        -- ATS score 0-100
    summary        TEXT         NOT NULL,
    source         VARCHAR(10)  NOT NULL DEFAULT 'offline',   -- 'ai' or 'offline'
    word_count     INT UNSIGNED NOT NULL DEFAULT 0,
    breakdown      JSON         NOT NULL,
    found_skills   JSON         NOT NULL,
    missing_skills JSON         NOT NULL,
    strengths      JSON         NOT NULL,
    improvements   JSON         NOT NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_analysis_user_created (user_id, created_at),
    CONSTRAINT fk_analysis_user   FOREIGN KEY (user_id)   REFERENCES users (id)   ON DELETE CASCADE,
    CONSTRAINT fk_analysis_resume FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 5. Mock interview sessions ------------------------------------------------
CREATE TABLE IF NOT EXISTS interviews (
    id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id        INT UNSIGNED NOT NULL,
    role           VARCHAR(60)  NOT NULL,
    interview_type VARCHAR(12)  NOT NULL,             -- technical | hr | mixed
    status         VARCHAR(12)  NOT NULL DEFAULT 'in_progress',   -- in_progress | completed
    source         VARCHAR(10)  NOT NULL DEFAULT 'offline',
    avg_score      DECIMAL(4,1) NULL,                 -- filled when completed (0-10)
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at   DATETIME     NULL,
    PRIMARY KEY (id),
    KEY ix_interview_user_created (user_id, created_at),
    CONSTRAINT fk_interview_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. Questions asked in an interview ----------------------------------------
CREATE TABLE IF NOT EXISTS interview_questions (
    id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    interview_id  INT UNSIGNED NOT NULL,
    position      SMALLINT UNSIGNED NOT NULL,         -- 0-based order in the interview
    question      TEXT         NOT NULL,
    sample_answer TEXT         NOT NULL,
    keywords      JSON         NOT NULL,
    category      VARCHAR(12)  NOT NULL DEFAULT 'technical',
    PRIMARY KEY (id),
    UNIQUE KEY uq_question_position (interview_id, position),
    CONSTRAINT fk_question_interview FOREIGN KEY (interview_id) REFERENCES interviews (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. Student answer + evaluation for a question (1:1 with a question) -------
CREATE TABLE IF NOT EXISTS interview_feedback (
    id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
    question_id  INT UNSIGNED NOT NULL,
    answer       TEXT         NOT NULL,
    score        DECIMAL(4,1) NOT NULL,               -- 0-10
    strengths    JSON         NOT NULL,
    improvements JSON         NOT NULL,
    ideal_answer TEXT         NOT NULL,
    source       VARCHAR(10)  NOT NULL DEFAULT 'offline',
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_feedback_question (question_id),
    CONSTRAINT fk_feedback_question FOREIGN KEY (question_id) REFERENCES interview_questions (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. Job listings -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
    title          VARCHAR(120) NOT NULL,
    company        VARCHAR(120) NOT NULL,
    location       VARCHAR(120) NOT NULL,
    job_type       VARCHAR(20)  NOT NULL,             -- Full-time | Internship
    salary         VARCHAR(40)  NOT NULL DEFAULT '',
    description    TEXT         NOT NULL,
    skills         JSON         NOT NULL,
    qualifications JSON         NOT NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_jobs_title (title)
) ENGINE=InnoDB;

-- 9. Per-student job matches (+ saved flag) ---------------------------------
CREATE TABLE IF NOT EXISTS job_recommendations (
    id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id        INT UNSIGNED NOT NULL,
    job_id         INT UNSIGNED NOT NULL,
    match_score    SMALLINT UNSIGNED NOT NULL DEFAULT 0,   -- 0-100
    matched_skills JSON         NOT NULL,
    missing_skills JSON         NOT NULL,
    is_saved       TINYINT(1)   NOT NULL DEFAULT 0,
    updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_rec_user_job (user_id, job_id),
    CONSTRAINT fk_rec_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_rec_job  FOREIGN KEY (job_id)  REFERENCES jobs (id)  ON DELETE CASCADE
) ENGINE=InnoDB;

-- 10. Progress timeline shown on the dashboard ------------------------------
CREATE TABLE IF NOT EXISTS student_progress (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED NOT NULL,
    metric      VARCHAR(30)  NOT NULL,                -- resume_score | interview_score | resume_completeness
    value       DECIMAL(5,1) NOT NULL,
    label       VARCHAR(120) NOT NULL DEFAULT '',     -- e.g. role or file name
    recorded_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_progress_user_metric (user_id, metric, recorded_at),
    CONSTRAINT fk_progress_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;
