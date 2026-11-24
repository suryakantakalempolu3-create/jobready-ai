from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

THEMES = {"modern": colors.HexColor("#4f46e5"), "classic": colors.HexColor("#111827"), "ocean": colors.HexColor("#1d4ed8")}


def _e(v):
    return escape(str(v or ""))


def _join(*parts, sep=" | "):
    return sep.join(_e(p) for p in parts if p)


def resume_to_text(d):
    """Plain-text rendering of resume data (used for analysis and previews)."""
    out = [d.get("full_name", ""), " | ".join(x for x in (d.get("email"), d.get("phone"), d.get("location"), d.get("linkedin"), d.get("github")) if x)]
    if d.get("summary"):
        out += ["SUMMARY", d["summary"]]
    if d.get("education"):
        out.append("EDUCATION")
        out += [f"{x.get('degree', '')} {x.get('field', '')}, {x.get('institution', '')} {x.get('start', '')}-{x.get('end', '')} {x.get('grade', '')}" for x in d["education"]]
    if d.get("skills"):
        out += ["SKILLS", ", ".join(d["skills"])]
    if d.get("experience"):
        out.append("EXPERIENCE")
        out += [f"{x.get('role', '')} at {x.get('company', '')}. {x.get('description', '')}" for x in d["experience"]]
    if d.get("projects"):
        out.append("PROJECTS")
        out += [f"{x.get('name', '')} ({x.get('tech', '')}). {x.get('description', '')}" for x in d["projects"]]
    if d.get("certifications"):
        out.append("CERTIFICATIONS")
        out += [f"{x.get('name', '')} - {x.get('issuer', '')} {x.get('year', '')}" for x in d["certifications"]]
    return "\n".join(out)


def build_resume_pdf(d, template="modern"):
    accent = THEMES.get(template, THEMES["modern"])
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=15 * mm,
                            bottomMargin=15 * mm, title=f"{d.get('full_name', 'Resume')} - Resume", author=d.get("full_name", ""))
    name = ParagraphStyle("n", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=accent)
    contact = ParagraphStyle("c", fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#4b5563"))
    h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=accent, spaceBefore=9, spaceAfter=2)
    body = ParagraphStyle("b", fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#1f2937"))
    bold = ParagraphStyle("bo", parent=body, fontName="Helvetica-Bold")
    right = ParagraphStyle("r", parent=body, alignment=2, textColor=colors.HexColor("#6b7280"))
    bullet = ParagraphStyle("bu", parent=body, leftIndent=10, bulletIndent=0)

    s = [Paragraph(_e(d.get("full_name") or "Your Name"), name),
         Paragraph(_join(d.get("email"), d.get("phone"), d.get("location")), contact)]
    links = _join(d.get("linkedin"), d.get("github"))
    if links:
        s.append(Paragraph(links, contact))

    def section(title):
        s.append(Paragraph(title.upper(), h))
        s.append(HRFlowable(width="100%", thickness=0.8, color=accent, spaceAfter=4))

    def row(left, rgt):
        t = Table([[Paragraph(left, bold), Paragraph(rgt, right)]], colWidths=[None, 45 * mm])
        t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                               ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
        s.append(t)

    def bullets(txt):
        for line in str(txt or "").replace("\r", "").split("\n"):
            line = line.strip().lstrip("-•* ").strip()
            if line:
                s.append(Paragraph(_e(line), bullet, bulletText="•"))

    if d.get("summary"):
        section("Professional Summary")
        s.append(Paragraph(_e(d["summary"]), body))
    if d.get("education"):
        section("Education")
        for x in d["education"]:
            row(_join(x.get("degree"), x.get("field"), sep=", "), _e(f"{x.get('start', '')} - {x.get('end', '')}".strip(" -")))
            s.append(Paragraph(_join(x.get("institution"), x.get("grade")), body))
            s.append(Spacer(1, 3))
    if d.get("skills"):
        section("Skills")
        s.append(Paragraph(_e(", ".join(d["skills"])), body))
    if d.get("experience"):
        section("Experience & Internships")
        for x in d["experience"]:
            row(_join(x.get("role"), x.get("company"), sep=", "), _e(f"{x.get('start', '')} - {x.get('end', '')}".strip(" -")))
            bullets(x.get("description"))
            s.append(Spacer(1, 3))
    if d.get("projects"):
        section("Projects")
        for x in d["projects"]:
            row(_e(x.get("name")), _e(x.get("link")))
            if x.get("tech"):
                s.append(Paragraph(f"<i>Tech: {_e(x['tech'])}</i>", body))
            bullets(x.get("description"))
            s.append(Spacer(1, 3))
    if d.get("certifications"):
        section("Certifications")
        for x in d["certifications"]:
            s.append(Paragraph(_join(x.get("name"), x.get("issuer"), x.get("year")), body))
    doc.build(s)
    return buf.getvalue()
