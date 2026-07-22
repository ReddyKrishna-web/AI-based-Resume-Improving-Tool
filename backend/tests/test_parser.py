"""
Tests for the resume parser service.

Note: These tests use synthetic text data rather than actual
PDF/DOCX files. Full integration tests with real files would
go in a separate integration test suite.
"""

import pytest

from app.services.parser import _detect_multi_column


class TestMultiColumnDetection:
    """Test the multi-column layout heuristic."""

    def test_single_column(self):
        """Blocks in a single horizontal range should not trigger multi-column."""
        blocks = [
            (50, 100, 500, 120, "Line 1"),
            (50, 130, 500, 150, "Line 2"),
            (50, 160, 500, 180, "Line 3"),
            (50, 190, 500, 210, "Line 4"),
            (50, 220, 500, 240, "Line 5"),
        ]
        assert _detect_multi_column(blocks) is False

    def test_two_column(self):
        """Blocks split into two distinct x-ranges should trigger multi-column."""
        blocks = [
            (50, 100, 250, 120, "Left 1"),
            (50, 130, 250, 150, "Left 2"),
            (50, 160, 250, 180, "Left 3"),
            (300, 100, 500, 120, "Right 1"),
            (300, 130, 500, 150, "Right 2"),
            (300, 160, 500, 180, "Right 3"),
        ]
        assert _detect_multi_column(blocks) is True

    def test_empty_blocks(self):
        """Empty block list should not trigger multi-column."""
        assert _detect_multi_column([]) is False

    def test_single_block(self):
        """A single block should not trigger multi-column."""
        blocks = [(50, 100, 500, 120, "Only block")]
        assert _detect_multi_column(blocks) is False

    def test_three_column_not_detected(self):
        """Three-column layouts have content in the 'gap' region, so
        the heuristic correctly does NOT flag them. This is a known
        limitation — we can detect 2 columns reliably but not 3+."""
        blocks = [
            (50, 100, 150, 120, "Col 1"),
            (200, 100, 300, 120, "Col 2"),
            (350, 100, 450, 120, "Col 3"),
            (50, 130, 150, 150, "Col 1"),
            (200, 130, 300, 150, "Col 2"),
            (350, 130, 450, 150, "Col 3"),
        ]
        assert _detect_multi_column(blocks) is False


class TestEdgeCases:
    """Test edge case handling in parser logic."""

    def test_text_cleaning_normalizes_whitespace(self):
        from app.utils.text_cleaning import normalize_whitespace
        assert normalize_whitespace("hello    world") == "hello world"
        assert normalize_whitespace("  leading space") == "leading space"

    def test_has_metric_detection(self):
        from app.utils.text_cleaning import has_metric
        assert has_metric("Increased revenue by 30%") is True
        assert has_metric("Led a team of 5 engineers") is True
        assert has_metric("Managed quarterly budget") is False  # no digits or $
        assert has_metric("Reduced costs") is False
        assert has_metric("Saved $50k annually") is True
