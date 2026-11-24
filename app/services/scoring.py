"""Rule-based ATS scoring. Always runs; AI feedback is layered on top when available."""
import re

ROLE_SKILLS = {
    "Java Developer": ["java", "spring boot", "hibernate", "sql", "maven", "rest api", "junit", "git", "microservices", "mysql"],
    "Python Developer": ["python", "flask", "django", "sql", "rest api", "git", "pandas", "pytest", "docker", "mongodb"],
    "Software Developer": ["data structures", "algorithms", "oop", "git", "sql", "rest api", "testing", "agile", "docker", "system design"],
    "Web Developer": ["html", "css", "javascript", "react", "node.js", "git", "rest api", "responsive design", "typescript", "mongodb"],
    "Data Analyst": ["sql", "excel", "python", "pandas", "power bi", "tableau", "statistics", "data visualization", "numpy", "machine learning"],
}
EXTRA_SKILLS = ["c++", "c#", "c", "kotlin", "go", "aws", "azure", "linux", "angular", "vue", "bootstrap", "postgresql",
                "redis", "kubernetes", "ci/cd", "jenkins", "graphql", "oracle", "javascript", "typescript", "php", "android",
                "figma", "tensorflow", "scikit-learn", "communication", "teamwork", "problem solving", "leadership"]
SKILL_BANK = sorted({s for v in ROLE_SKILLS.values() for s in v} | set(EXTRA_SKILLS), key=len, reverse=True)

SECTIONS = {
    "summary": r"\b(summary|objective|profile|about me)\b",
    "education": r"\beducation|academic|qualification",
    "skills": r"\b(technical )?skills\b|technologies",
    "experience": r"\b(experience|internship|employment|work history)\b",
    "projects": r"\bprojects?\b",
    "certifications": r"\bcertifications?|courses|achievements\b",
}
ACTION_VERBS = ["developed", "built", "designed", "implemented", "created", "led", "managed", "optimized", "improved",
                "automated", "deployed", "integrated", "analyzed", "reduced", "increased", "launched", "engineered", "tested"]


def find_skills(text):
    low = text.lower()
    return [s for s in SKILL_BANK if re.search(r"(?<![\w+#.])" + re.escape(s) + r"(?![\w+#])", low)]


def analyze_text(text, role="Software Developer"):
    low = text.lower()
    words = len(text.split())
    breakdown, tips, strengths = {}, [], []

    # Contact details (15)
    c = 0
    c += 5 if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text) else 0
    c += 5 if re.search(r"(\+?\d[\d\s-]{8,}\d)", text) else 0
    c += 5 if ("linkedin" in low or "github" in low) else 0
    breakdown["Contact details"] = (c, 15)
    if c < 15:
        tips.append("Add a professional email, phone number and your LinkedIn/GitHub links in the header.")
    else:
        strengths.append("Complete contact details with professional links.")

    # Sections (25)
    present = [k for k, p in SECTIONS.items() if re.search(p, low)]
    s = round(25 * len(present) / len(SECTIONS))
    breakdown["Resume sections"] = (s, 25)
    for k in SECTIONS:
        if k not in present:
            tips.append(f"Add a clearly labelled “{k.title()}” section so ATS software can parse it.")
    if len(present) >= 5:
        strengths.append("Well-structured with standard section headings.")

    # Skills match (25)
    wanted = ROLE_SKILLS.get(role, ROLE_SKILLS["Software Developer"])
    found = find_skills(text)
    matched = [w for w in wanted if w in found]
    missing = [w for w in wanted if w not in found]
    k = round(25 * len(matched) / len(wanted))
    breakdown["Role keywords"] = (k, 25)
    if missing:
        tips.append(f"For {role} roles, consider adding (if you have them): {', '.join(missing[:5])}.")
    if len(matched) >= len(wanted) * 0.6:
        strengths.append(f"Strong keyword match for {role}.")

    # Impact (20)
    verbs = sum(1 for v in ACTION_VERBS if v in low)
    nums = len(re.findall(r"\b\d+(?:\.\d+)?\s?(?:%|\+|x|k|users|projects|ms|lpa)", low)) + len(re.findall(r"\b\d{2,}\b", low)) // 6
    i = min(10, verbs * 2) + min(10, nums * 3)
    breakdown["Action verbs & impact"] = (i, 20)
    if verbs < 4:
        tips.append("Start bullet points with strong action verbs (Developed, Built, Optimized, Implemented).")
    if nums < 2:
        tips.append("Quantify achievements, e.g. “reduced load time by 35%” or “used by 200+ students”.")
    else:
        strengths.append("Includes measurable achievements.")

    # Length (15)
    if 250 <= words <= 900:
        l = 15
    elif 150 <= words < 250 or 900 < words <= 1200:
        l = 9
    else:
        l = 4
    breakdown["Length & readability"] = (l, 15)
    if words < 250:
        tips.append("Your resume is short — expand projects and internships with 2-3 bullet points each.")
    elif words > 900:
        tips.append("Your resume is long — keep it to one page (fresher) or two pages at most.")

    score = c + s + k + i + l
    return {
        "heuristic_score": score,
        "breakdown": {n: {"score": a, "max": b} for n, (a, b) in breakdown.items()},
        "found_skills": found, "matched_skills": matched, "missing_skills": missing,
        "sections_found": present, "word_count": words,
        "improvements": tips, "strengths": strengths,
    }
