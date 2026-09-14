"""ATS-safe, adaptive single-column resume exports."""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from io import BytesIO
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate

PAGE_MARGIN = 0.3 * inch
DOCX_PAGE_MARGIN = Inches(0.3)


@dataclass
class ResumeSection:
    title: str
    lines: list[str] = field(default_factory=list)


@dataclass
class ExportResumeData:
    """Normalized resume content shared by the DOCX and PDF renderers."""
    name: str
    contact: str = ""
    sections: list[ResumeSection] = field(default_factory=list)
    tailored_bullets: list[str] = field(default_factory=list)


SECTION_NAMES = {
    "SUMMARY": "Professional Summary",
    "PROFESSIONAL SUMMARY": "Professional Summary",
    "PROFILE": "Professional Summary",
    "SKILLS": "Skills",
    "TECHNICAL SKILLS": "Skills",
    "EXPERIENCE": "Experience",
    "WORK EXPERIENCE": "Experience",
    "PROFESSIONAL EXPERIENCE": "Experience",
    "INTERNSHIP": "Experience",
    "INTERNSHIPS": "Experience",
    "PROJECTS": "Projects",
    "PERSONAL PROJECTS": "Projects",
    "EDUCATION": "Education",
    "OPEN SOURCE CONTRIBUTION": "Open Source Contribution",
    "OPEN SOURCE CONTRIBUTIONS": "Open Source Contribution",
    "ACHIEVEMENTS": "Achievements",
    "CERTIFICATIONS": "Certifications",
}

SECTION_ORDER = {
    "Professional Summary": 1,
    "Skills": 2,
    "Experience": 3,
    "Open Source Contribution": 4,
    "Projects": 5,
    "Education": 6,
    "Certifications": 7,
    "Achievements": 8,
}


def _clean_line(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u2022", "").strip())


def _heading_key(value: str) -> str:
    return re.sub(r"[^A-Z ]", "", value.strip().upper()).strip()


def _is_section_heading(value: str) -> bool:
    key = _heading_key(value)
    return key in SECTION_NAMES or (value.strip().isupper() and 2 <= len(value.split()) <= 5)


def _is_bullet(value: str) -> bool:
    return value.lstrip().startswith(("-", "*", "\u2022")) or bool(re.match(r"^\d+[.)]\s", value))


def parse_resume_text(
    raw_resume: str,
    tailored_bullets: list[str] | None = None,
    candidate_name: str | None = None,
) -> ExportResumeData:
    """Extract common resume sections while retaining unknown content."""
    lines = [_clean_line(line) for line in raw_resume.splitlines() if _clean_line(line)]
    if not lines:
        return ExportResumeData(name=candidate_name or "Candidate")

    name = candidate_name or lines[0]
    contact = ""
    start = 1
    if len(lines) > 1 and ("@" in lines[1] or re.search(r"\+?\d[\d ()-]{7,}", lines[1])):
        contact = lines[1]
        start = 2

    sections: list[ResumeSection] = []
    current: ResumeSection | None = None
    for line in lines[start:]:
        if _is_section_heading(line):
            title = SECTION_NAMES.get(_heading_key(line), line.title())
            current = ResumeSection(title)
            sections.append(current)
        else:
            if current is None:
                current = ResumeSection("Professional Summary")
                sections.append(current)
            current.lines.append(line)

    if tailored_bullets:
        experience = next((item for item in sections if item.title == "Experience"), None)
        if experience is None:
            experience = ResumeSection("Experience")
            sections.insert(0, experience)
        existing = {_clean_line(line).lower() for line in experience.lines}
        additions = [f"- {bullet}" for bullet in tailored_bullets if _clean_line(bullet).lower() not in existing]
        experience.lines = additions + experience.lines

    sections.sort(key=lambda item: SECTION_ORDER.get(item.title, 9))
    return ExportResumeData(name=name, contact=contact, sections=sections, tailored_bullets=tailored_bullets or [])


def _content_lines(data: ExportResumeData) -> list[tuple[str, str, bool]]:
    content: list[tuple[str, str, bool]] = []
    for section in data.sections:
        lines = [line for line in section.lines if _clean_line(line)]
        if not lines:
            continue
        content.append((section.title, section.title.upper(), True))
        for line in lines:
            text = _clean_line(line)
            bullet = _is_bullet(line)
            if section.title == "Projects" and not _entry_line(section.title, text, bullet):
                bullet = True
            content.append((section.title, text, bullet))
    return content


def _entry_line(section: str, text: str, bullet: bool) -> bool:
    if bullet:
        return False
    if section == "Projects":
        return "|" in text
    return section in {"Experience", "Education", "Open Source Contribution"} and (
        "|" in text or len(text) <= 90
    )


def _add_docx_border(paragraph) -> None:
    properties = paragraph._p.get_or_add_pPr()
    borders = properties.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        properties.append(borders)
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    borders.append(bottom)


def _add_docx_heading(document: Document, title: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(8)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(title.upper())
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(12)
    _add_docx_border(paragraph)


def _add_docx_line(document: Document, text: str, bullet: bool, bold: bool) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.paragraph_format.keep_together = True
    if bullet:
        paragraph.paragraph_format.left_indent = Inches(0.2)
        paragraph.paragraph_format.first_line_indent = Inches(-0.13)
    run = paragraph.add_run(f"• {text}" if bullet else text)
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(10.5)


def export_docx(
    data: ExportResumeData | None = None,
    *,
    candidate_name: str | None = None,
    bullets: list[str] | None = None,
    raw_resume: str | None = None,
) -> bytes:
    data = data or parse_resume_text(raw_resume or "", bullets, candidate_name)
    document = Document()
    section = document.sections[0]
    section.top_margin = section.bottom_margin = DOCX_PAGE_MARGIN
    section.left_margin = section.right_margin = DOCX_PAGE_MARGIN
    normal = document.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(0)

    header = document.add_paragraph()
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.paragraph_format.space_after = Pt(1)
    name_run = header.add_run(data.name)
    name_run.bold = True
    name_run.font.name = "Arial"
    name_run.font.size = Pt(16)
    if data.contact:
        contact = document.add_paragraph(data.contact)
        contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact.paragraph_format.space_after = Pt(7)
        for run in contact.runs:
            run.font.name = "Arial"
            run.font.size = Pt(9)

    for section_title, text, bullet in _content_lines(data):
        if text == section_title.upper():
            _add_docx_heading(document, section_title)
        else:
            _add_docx_line(document, text, bullet, _entry_line(section_title, text, bullet))

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _pdf_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle("ResumeName", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=16, leading=19, alignment=1, spaceAfter=2),
        "contact": ParagraphStyle("ResumeContact", parent=base["Normal"], fontName="Helvetica", fontSize=9, leading=11, alignment=1, spaceAfter=7),
        "heading": ParagraphStyle("ResumeHeading", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=14, spaceBefore=8, spaceAfter=3),
        "entry": ParagraphStyle("ResumeEntry", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=12, spaceAfter=1),
        "body": ParagraphStyle("ResumeBody", parent=base["Normal"], fontName="Helvetica", fontSize=10.5, leading=12, spaceAfter=1),
        "bullet": ParagraphStyle("ResumeBullet", parent=base["Normal"], fontName="Helvetica", fontSize=10.5, leading=12, leftIndent=14, firstLineIndent=-7, spaceAfter=1),
    }


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>") or " ", style)


def export_pdf(
    data: ExportResumeData | None = None,
    *,
    candidate_name: str | None = None,
    bullets: list[str] | None = None,
    raw_resume: str | None = None,
) -> bytes:
    data = data or parse_resume_text(raw_resume or "", bullets, candidate_name)
    styles = _pdf_styles()
    story = [_paragraph(data.name, styles["name"])]
    if data.contact:
        story.append(_paragraph(data.contact, styles["contact"]))

    for section_title, text, bullet in _content_lines(data):
        if text == section_title.upper():
            story.append(Paragraph(text, styles["heading"]))
            story.append(HRFlowable(width="100%", thickness=0.55, color="black", spaceBefore=0, spaceAfter=1))
        else:
            bold = _entry_line(section_title, text, bullet)
            style = styles["bullet"] if bullet else styles["entry"] if bold else styles["body"]
            story.append(_paragraph(f"• {text}" if bullet else text, style))

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
    )
    one_page_canvas = type("OnePageCanvas", (_OnePageCanvas, Canvas), {})
    document.build(story, canvasmaker=one_page_canvas)
    return buffer.getvalue()


class _OnePageCanvas:
    """Reject output that overflows instead of silently creating page two."""

    def showPage(self):  # noqa: N802 - ReportLab API name
        if self._pageNumber > 2:
            raise ValueError("Resume content exceeds the one-page export limit.")
        return super().showPage()
