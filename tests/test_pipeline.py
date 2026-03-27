"""Tests for the end-to-end pipeline orchestrator."""

import json
import os
import pytest
from unittest.mock import patch

from run_pipeline import pdf_refs_to_dicts, run_pipeline


class TestPdfRefsToDicts:
    def test_basic_conversion(self):
        refs = [("Title One", ["Author A", "Author B"])]
        result = pdf_refs_to_dicts("test.pdf", refs)
        assert len(result) == 1
        assert result[0]["title"] == "Title One"
        assert result[0]["authors"] == ["Author A", "Author B"]
        assert result[0]["pdf"] == "test.pdf"
        assert result[0]["year"] == ""
        assert result[0]["doi"] is None
        assert result[0]["verification"] == {}

    def test_multiple_refs(self):
        refs = [
            ("Title A", ["Auth 1"]),
            ("Title B", ["Auth 2", "Auth 3"]),
        ]
        result = pdf_refs_to_dicts("paper.pdf", refs)
        assert len(result) == 2

    def test_skips_empty_title(self):
        refs = [("", ["Author"]), ("Real Title", ["Author"])]
        result = pdf_refs_to_dicts("test.pdf", refs)
        assert len(result) == 1
        assert result[0]["title"] == "Real Title"

    def test_skips_empty_authors(self):
        refs = [("Title", []), ("Real Title", ["Author"])]
        result = pdf_refs_to_dicts("test.pdf", refs)
        assert len(result) == 1

    def test_empty_input(self):
        result = pdf_refs_to_dicts("test.pdf", [])
        assert result == []


class TestRunPipeline:
    def test_no_pdfs_in_directory(self, tmp_path):
        """Pipeline should handle empty directory gracefully."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        # Should not raise
        run_pipeline(str(empty_dir), output_dir=str(tmp_path / "output"))
        # No output dir created since pipeline exits early
        assert not (tmp_path / "output" / "results.json").exists()

    def test_pipeline_writes_results_json(self, tmp_path):
        """Pipeline should write results.json with correct schema."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "test.pdf").touch()
        output_dir = tmp_path / "output"

        mock_refs = [("Title One", ["Auth A"]), ("Title Two", ["Auth B"])]
        mock_results = [
            {
                "title": "Title One",
                "authors": ["Auth A"],
                "year": "",
                "doi": None,
                "pdf": str(pdf_dir / "test.pdf"),
                "original_verification": {},
                "hallucinator_check": {
                    "status": "verified",
                    "source": "CrossRef",
                    "found_title": "Title One",
                    "found_authors": ["Auth A"],
                    "publication_year": None,
                    "openalex_url": None,
                },
            },
            {
                "title": "Title Two",
                "authors": ["Auth B"],
                "year": "",
                "doi": None,
                "pdf": str(pdf_dir / "test.pdf"),
                "original_verification": {},
                "hallucinator_check": {
                    "status": "not_found",
                    "source": None,
                    "found_title": None,
                    "found_authors": None,
                    "publication_year": None,
                    "openalex_url": None,
                },
            },
        ]

        with patch(
            "run_pipeline.extract_references_with_titles_and_authors",
            return_value=mock_refs,
        ), patch(
            "run_pipeline.verify_references",
            return_value=mock_results,
        ):
            run_pipeline(str(pdf_dir), output_dir=str(output_dir))

        # Check results.json was written with correct content
        results_path = output_dir / "results.json"
        assert results_path.exists()
        data = json.loads(results_path.read_text())
        assert len(data) == 2
        assert data[0]["hallucinator_check"]["status"] == "verified"
        assert data[1]["hallucinator_check"]["status"] == "not_found"

    def test_pipeline_runs_postprocessing(self, tmp_path):
        """Pipeline should produce postprocessed output files."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "test.pdf").touch()
        output_dir = tmp_path / "output"

        mock_refs = [("Scholarly Paper", ["John Smith"])]
        mock_results = [
            {
                "title": "Scholarly Paper",
                "authors": ["John Smith"],
                "year": "",
                "doi": None,
                "pdf": str(pdf_dir / "test.pdf"),
                "original_verification": {},
                "hallucinator_check": {
                    "status": "not_found",
                    "source": None,
                    "found_title": None,
                    "found_authors": None,
                    "publication_year": None,
                    "openalex_url": None,
                },
            },
        ]

        with patch(
            "run_pipeline.extract_references_with_titles_and_authors",
            return_value=mock_refs,
        ), patch(
            "run_pipeline.verify_references",
            return_value=mock_results,
        ):
            run_pipeline(str(pdf_dir), output_dir=str(output_dir))

        # Postprocessing outputs
        assert (output_dir / "results-postprocessed.json").exists()
        assert (output_dir / "results-filtered-postprocessed.json").exists()
        assert (output_dir / "report-postprocessed.txt").exists()

        # Filtered should contain the scholarly not_found entry
        filtered = json.loads((output_dir / "results-filtered-postprocessed.json").read_text())
        assert len(filtered) == 1
        assert filtered[0]["reference_classification"]["type"] == "scholarly_candidate"

    def test_pipeline_produces_llm_export(self, tmp_path):
        """Pipeline should produce LLM verification export when candidates exist."""
        pdf_dir = tmp_path / "pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "test_paper.pdf").touch()
        output_dir = tmp_path / "output"

        mock_refs = [("Fabricated Paper Title", ["Fake Author"])]
        mock_results = [
            {
                "title": "Fabricated Paper Title",
                "authors": ["Fake Author"],
                "year": "",
                "doi": None,
                "pdf": str(pdf_dir / "test_paper.pdf"),
                "original_verification": {},
                "hallucinator_check": {
                    "status": "not_found",
                    "source": None,
                    "found_title": None,
                    "found_authors": None,
                    "publication_year": None,
                    "openalex_url": None,
                },
            },
        ]

        with patch(
            "run_pipeline.extract_references_with_titles_and_authors",
            return_value=mock_refs,
        ), patch(
            "run_pipeline.verify_references",
            return_value=mock_results,
        ):
            run_pipeline(str(pdf_dir), output_dir=str(output_dir))

        export_path = output_dir / "hallucination-candidates-for-verification.txt"
        assert export_path.exists()
        content = export_path.read_text()
        assert "Fabricated Paper Title" in content
        assert "Fake Author" in content
