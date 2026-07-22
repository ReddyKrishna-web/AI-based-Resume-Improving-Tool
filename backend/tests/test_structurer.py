"""
Tests for the resume structurer service.

These test the section identification and entity extraction logic
using synthetic resume texts (no real PDFs needed).
"""

from app.models.schemas import EducationEntry
from app.services.structurer import (
    _extract_contact,
    _split_into_sections,
    _parse_education,
    _parse_skills,
    structure_resume,
)


class TestContactExtraction:
    """Test email, phone, and LinkedIn extraction."""

    def test_extract_email(self):
        text = "john.doe@example.com\nPhone: 555-1234"
        contact = _extract_contact(text)
        assert contact.email == "john.doe@example.com"

    def test_extract_phone(self):
        text = "Email: john@example.com\n(555) 123-4567"
        contact = _extract_contact(text)
        assert contact.phone in ["(555) 123-4567", "555-123-4567"] or "555" in contact.phone

    def test_extract_linkedin(self):
        text = "https://linkedin.com/in/johndoe\njohn@example.com"
        contact = _extract_contact(text)
        assert contact.linkedin and "linkedin" in contact.linkedin.lower()

    def test_no_contact_info(self):
        text = "This is just a paragraph without any contact details."
        contact = _extract_contact(text)
        assert contact.email is None
        assert contact.phone is None


class TestSectionSplitting:
    """Test that section headings are correctly identified."""

    def test_basic_sections(self):
        text = """John Doe
john@example.com

SUMMARY
Experienced developer.

EDUCATION
Bachelor of Science in CS

EXPERIENCE
Led a team at Google.

SKILLS
Python, React, TypeScript
"""
        lines = text.split("\n")
        # We need to normalize first
        from app.utils.text_cleaning import normalize_whitespace
        normalized = normalize_whitespace(text)
        lines = normalized.split("\n")

        resume = structure_resume(text)
        assert resume.education and len(resume.education) > 0
        assert len(resume.skills) > 0
        assert resume.summary != ""

    def test_no_sections(self):
        text = "Just some random text without any clear section headers."
        resume = structure_resume(text)
        # Should not crash, should return empty or minimal structure
        assert resume.education == []
        assert resume.skills == []

    def test_education_parsing(self):
        lines = [
            "Bachelor of Science in Computer Science",
            "University of California, Berkeley",
            "2016 - 2020",
        ]
        education = _parse_education(lines)
        assert len(education) > 0

    def test_skills_parsing(self):
        lines = ["Python, JavaScript, React, TypeScript, PostgreSQL"]
        skills = _parse_skills(lines)
        assert len(skills) >= 4
        assert "Python" in skills


class TestFullPipeline:
    """Test the full structure_resume pipeline with realistic data."""

    def test_simple_resume(self):
        text = """john.doe@example.com | (555) 123-4567

PROFESSIONAL SUMMARY
Full-stack developer with 5 years of experience.

SKILLS
Python, JavaScript, React, PostgreSQL, Docker, AWS

EXPERIENCE
Senior Developer | Tech Corp
2020 - Present
• Led migration of legacy system to microservices
• Reduced deployment time by 40% using CI/CD
• Mentored 3 junior developers

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley
2014 - 2018
"""
        resume = structure_resume(text)
        assert resume.contact.email == "john.doe@example.com"
        assert len(resume.experience) > 0
        assert len(resume.skills) >= 3
        assert resume.summary != ""
