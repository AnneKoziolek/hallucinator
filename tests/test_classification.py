"""Tests for reference classification logic in postprocess_results.py."""

from postprocess_results import classify_reference


class TestClassifyStandards:
    def test_ieee_in_authors(self):
        ref = {"title": "Some standard", "authors": ["IEEE"]}
        result = classify_reference(ref)
        assert result["type"] == "standard_or_spec"

    def test_iso_in_title(self):
        ref = {"title": "ISO/IEC 25010 Systems quality", "authors": ["Standards Body"]}
        result = classify_reference(ref)
        assert result["type"] == "standard_or_spec"

    def test_autosar_in_authors(self):
        ref = {"title": "Adaptive Platform", "authors": ["AUTOSAR Consortium"]}
        result = classify_reference(ref)
        assert result["type"] == "standard_or_spec"


class TestClassifyIndustryReports:
    def test_mckinsey(self):
        ref = {"title": "Digital trends report", "authors": ["McKinsey and Company"]}
        result = classify_reference(ref)
        assert result["type"] == "industry_report"

    def test_gartner(self):
        ref = {"title": "Magic Quadrant", "authors": ["Gartner Inc"]}
        result = classify_reference(ref)
        assert result["type"] == "industry_report"


class TestClassifyGreyLiterature:
    def test_url_in_title(self):
        ref = {"title": "Documentation at https://example.org/docs", "authors": ["Some Author"]}
        result = classify_reference(ref)
        assert result["type"] == "grey_spec"

    def test_version_pattern(self):
        ref = {"title": "AUTOSAR Specification R21.11", "authors": ["Some Group"]}
        result = classify_reference(ref)
        # Could be standard_or_spec or grey_spec depending on which rule fires first
        assert result["type"] in ("standard_or_spec", "grey_spec")

    def test_white_paper_keyword(self):
        ref = {"title": "A white paper on cloud computing", "authors": ["John Smith", "Jane Doe"]}
        result = classify_reference(ref)
        assert result["type"] == "grey_spec"


class TestClassifyScholarly:
    def test_default_scholarly(self):
        ref = {"title": "Deep learning for code analysis", "authors": ["John Smith", "Jane Doe"]}
        result = classify_reference(ref)
        assert result["type"] == "scholarly_candidate"

    def test_has_confidence(self):
        ref = {"title": "Some paper", "authors": ["Author"]}
        result = classify_reference(ref)
        assert "confidence" in result
        assert result["confidence"] in ("high", "medium", "low")

    def test_has_reason(self):
        ref = {"title": "Some paper", "authors": ["Author"]}
        result = classify_reference(ref)
        assert "reason" in result
        assert isinstance(result["reason"], str)
