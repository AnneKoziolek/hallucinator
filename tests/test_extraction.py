"""Tests for PDF reference extraction logic."""

import os
import pytest

from check_hallucinated_references import (
    extract_references_with_titles_and_authors,
    extract_title_from_reference,
    extract_authors_from_reference,
    expand_ligatures,
)


class TestExtractFromPDF:
    def test_extracts_references_from_real_pdf(self, test_pdf_path):
        if not os.path.exists(test_pdf_path):
            pytest.skip("Test PDF not available")
        refs = extract_references_with_titles_and_authors(test_pdf_path)
        assert len(refs) > 0, "Should extract at least one reference"
        for title, authors, *_ in refs:
            assert isinstance(title, str)
            assert len(title) > 5, f"Title too short: {title}"
            assert isinstance(authors, list)

    def test_references_have_authors(self, test_pdf_path):
        if not os.path.exists(test_pdf_path):
            pytest.skip("Test PDF not available")
        refs = extract_references_with_titles_and_authors(test_pdf_path)
        # At least some references should have authors
        refs_with_authors = [(t, a) for t, a, *_ in refs if a]
        assert len(refs_with_authors) > 0, "At least some references should have authors"


class TestExtractTitle:
    def test_ieee_quoted_title(self):
        ref = 'J. Smith, A. Jones, "A Survey of Deep Learning," in Proc. IEEE, 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        assert title is not None
        assert "Survey" in title or "Deep Learning" in title

    def test_returns_none_for_empty(self):
        title, from_quotes = extract_title_from_reference("")
        # Should return something (possibly empty) without crashing
        assert isinstance(from_quotes, bool)


class TestExtractAuthors:
    def test_comma_separated_authors(self):
        ref = 'J. Smith, A. Jones, and C. Williams, "Some Title," in Proc. IEEE, 2023.'
        authors = extract_authors_from_reference(ref)
        assert isinstance(authors, list)

    def test_empty_input(self):
        authors = extract_authors_from_reference("")
        assert isinstance(authors, list)


class TestExpandLigatures:
    def test_fi_ligature(self):
        assert expand_ligatures("ﬁnding") == "finding"

    def test_fl_ligature(self):
        assert expand_ligatures("ﬂow") == "flow"

    def test_ffi_ligature(self):
        assert expand_ligatures("eﬃcient") == "efficient"

    def test_no_ligatures(self):
        assert expand_ligatures("normal text") == "normal text"
