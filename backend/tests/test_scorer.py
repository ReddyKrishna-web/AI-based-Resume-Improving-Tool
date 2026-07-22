"""
Tests for the rule-based scoring engine.

The score is deterministic — these tests verify that specific
resume structures produce specific scores. This is important
for the interview narrative: "I can prove the scoring is
consistent by pointing to these tests."
"""

import pytest

from app.models.schemas import (
    BulletPoint,
    EducationEntry,
    ExperienceEntry,
    StructuredResume,
    MatchResult,
)
from app.services.scorer import (
    _score_section_completeness,
    _score_action_verbs,
    _score_quantification,
    _score_keyword_coverage,
    calculate_score,
)


class TestSectionCompleteness:
    def test_all_sections(self):
        resume = StructuredResume(
            summary="Summary",
            education=[EducationEntry(institution="MIT", degree="BS", field="CS")],
            experience=[ExperienceEntry(company="Co", title="Dev", bullets=[])],
            skills=["Python"],
        )
        score = _score_section_completeness(resume)
        assert score == 100.0

    def test_no_summary(self):
        resume = StructuredResume(
            education=[EducationEntry(institution="MIT", degree="BS", field="CS")],
            experience=[ExperienceEntry(company="Co", title="Dev", bullets=[])],
            skills=["Python"],
        )
        score = _score_section_completeness(resume)
        assert score == 85.0  # 25 + 35 + 25

    def test_only_experience(self):
        resume = StructuredResume(
            experience=[ExperienceEntry(company="Co", title="Dev", bullets=[])],
        )
        score = _score_section_completeness(resume)
        assert score == 35.0


class TestActionVerbs:
    def test_all_strong(self):
        bullets = [
            BulletPoint(text="Led a team of 5 engineers", has_metric=True, has_strong_verb=True),
            BulletPoint(text="Built a CI/CD pipeline", has_metric=False, has_strong_verb=True),
            BulletPoint(text="Designed the API architecture", has_metric=False, has_strong_verb=True),
        ]
        resume = StructuredResume(
            experience=[ExperienceEntry(company="Co", title="Dev", bullets=bullets)],
        )
        score = _score_action_verbs(resume)
        assert score == 100.0

    def test_no_bullets(self):
        resume = StructuredResume()
        score = _score_action_verbs(resume)
        assert score == 50.0  # Neutral

    def test_mixed_verbs(self):
        bullets = [
            BulletPoint(text="Built the frontend", has_metric=False, has_strong_verb=True),
            BulletPoint(text="Was responsible for testing", has_metric=False, has_strong_verb=False),
            BulletPoint(text="Helped with deployments", has_metric=False, has_strong_verb=False),
        ]
        resume = StructuredResume(
            experience=[ExperienceEntry(company="Co", title="Dev", bullets=bullets)],
        )
        score = _score_action_verbs(resume)
        assert score < 100.0


class TestQuantification:
    def test_all_metrics(self):
        bullets = [
            BulletPoint(text="Reduced costs by 30%", has_metric=True, has_strong_verb=True),
            BulletPoint(text="Managed $2M budget", has_metric=True, has_strong_verb=True),
        ]
        resume = StructuredResume(
            experience=[ExperienceEntry(company="Co", title="Dev", bullets=bullets)],
        )
        score = _score_quantification(resume)
        assert score == 100.0

    def test_no_metrics(self):
        bullets = [
            BulletPoint(text="Led the team", has_metric=False, has_strong_verb=True),
            BulletPoint(text="Built the app", has_metric=False, has_strong_verb=True),
        ]
        resume = StructuredResume(
            experience=[ExperienceEntry(company="Co", title="Dev", bullets=bullets)],
        )
        score = _score_quantification(resume)
        assert score == 0.0


class TestKeywordCoverage:
    def test_perfect_match(self):
        match = MatchResult(
            jd_provided=True,
            matched_keywords=["python", "react", "docker"],
            missing_keywords=[],
            keyword_match_pct=100.0,
        )
        score = _score_keyword_coverage(match)
        assert score == 100.0

    def test_partial_match(self):
        match = MatchResult(
            jd_provided=True,
            matched_keywords=["python"],
            missing_keywords=["react", "docker", "aws"],
            keyword_match_pct=25.0,
        )
        score = _score_keyword_coverage(match)
        assert score == 25.0

    def test_no_keywords(self):
        match = MatchResult(
            matched_keywords=[],
            missing_keywords=[],
            keyword_match_pct=0.0,
        )
        score = _score_keyword_coverage(match)
        # When both lists are empty (no keywords to match), returns neutral 50.0
        assert score == 50.0


class TestFullScore:
    def test_perfect_resume(self):
        resume = StructuredResume(
            summary="Experienced full-stack developer",
            education=[EducationEntry(institution="MIT", degree="BS", field="CS")],
            experience=[
                ExperienceEntry(
                    company="Google",
                    title="Senior Engineer",
                    bullets=[
                        BulletPoint(text="Led migration of 50 microservices", has_metric=True, has_strong_verb=True),
                        BulletPoint(text="Reduced latency by 40%", has_metric=True, has_strong_verb=True),
                        BulletPoint(text="Mentored 5 junior engineers", has_metric=True, has_strong_verb=True),
                        BulletPoint(text="Designed the system architecture", has_metric=False, has_strong_verb=True),
                    ],
                )
            ],
            skills=["Python", "React", "AWS", "Docker"],
        )
        match = MatchResult(
            jd_provided=True,
            matched_keywords=["python", "react", "aws", "microservices", "mentor"],
            missing_keywords=["kubernetes"],
            keyword_match_pct=83.3,
        )
        score = calculate_score(resume, match)
        assert score.total_score > 70  # Should be a strong score
        assert score.level.value in ("excellent", "good")
