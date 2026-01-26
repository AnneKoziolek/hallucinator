"""Unit tests for citation sentence extraction functionality."""

import pytest
from check_hallucinated_references import extract_citation_sentences


class TestExtractCitationSentences:
    """Test suite for the extract_citation_sentences function."""
    
    def test_single_reference_single_sentence(self):
        """Test extraction of a single reference in a single sentence."""
        full_text = """This is the introduction.
        Machine learning has been studied extensively [1].
        
        References
        [1] A. Smith, "Deep Learning", 2020."""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 1 in citations
        assert len(citations[1]) == 1
        assert "Machine learning has been studied extensively [1]." in citations[1][0]
    
    def test_multiple_references_single_sentence(self):
        """Test extraction when multiple references appear in the same sentence."""
        full_text = """Introduction text here.
        This technique has been used in various domains [1], [2], [3].
        
        References
        [1] Author One
        [2] Author Two
        [3] Author Three"""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 1 in citations
        assert 2 in citations
        assert 3 in citations
        # All three should be in the same sentence
        assert citations[1] == citations[2] == citations[3]
    
    def test_reference_in_multiple_sentences(self):
        """Test when the same reference appears in multiple sentences."""
        full_text = """The initial study [1] showed promising results.
        Later analysis confirmed [1] the findings.
        We also noted that [1] provides a comprehensive framework.
        
        References
        [1] J. Doe, "Comprehensive Study", 2021."""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 1 in citations
        assert len(citations[1]) == 3
        assert any("initial study" in s for s in citations[1])
        assert any("Later analysis" in s for s in citations[1])
        assert any("comprehensive framework" in s for s in citations[1])
    
    def test_no_citations_in_text(self):
        """Test when a reference is not cited in the main text."""
        full_text = """This is some text without citations.
        
        References
        [1] Uncited Reference"""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        # Reference 1 should not appear in the dictionary
        assert 1 not in citations
    
    def test_skips_author_initials(self):
        """Test that author initials (M., J., etc.) don't break sentence detection."""
        full_text = """The work by M. Johnson and J. Smith [1] was groundbreaking.
        
        References
        [1] M. Johnson and J. Smith, "Title", 2020."""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 1 in citations
        assert len(citations[1]) == 1
        # The sentence should include both initials
        assert "M. Johnson and J. Smith [1]" in citations[1][0]
    
    def test_citations_at_sentence_boundaries(self):
        """Test citations at the start or end of sentences."""
        full_text = """[1] shows that this is effective.
        This approach is validated by research [2].
        
        References
        [1] First Reference
        [2] Second Reference"""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 1 in citations
        assert 2 in citations
        assert "[1] shows that this is effective." in citations[1][0]
        assert "This approach is validated by research [2]." in citations[2][0]
    
    def test_mixed_reference_numbers(self):
        """Test with non-sequential reference numbers."""
        full_text = """Some work [5] was done.
        Later, more work [10] followed.
        
        References
        [1] Unused ref
        [5] Fifth ref
        [10] Tenth ref"""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 5 in citations
        assert 10 in citations
        assert 1 not in citations  # Not cited in main text
    
    def test_duplicate_sentences_not_added(self):
        """Test that the same sentence is not added multiple times for a reference."""
        full_text = """This sentence has [1] and also [1] again.
        
        References
        [1] Reference"""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 1 in citations
        # Should only have one copy of the sentence even though [1] appears twice
        assert len(citations[1]) == 1
    
    def test_empty_text_before_references(self):
        """Test when there's no text before the references section."""
        full_text = """References
        [1] Only Reference"""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert len(citations) == 0
    
    def test_complex_multiline_sentence(self):
        """Test sentences that span multiple lines in the PDF."""
        full_text = """Recent research has shown that
        machine learning approaches [1] can
        significantly improve performance.
        
        References
        [1] ML Research Paper"""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 1 in citations
        assert len(citations[1]) == 1
        # Should capture the whole sentence across line breaks
        assert "[1]" in citations[1][0]
    
    def test_reference_in_parenthetical(self):
        """Test citations within parenthetical expressions."""
        full_text = """The system (as shown in [1]) performs well.
        
        References
        [1] System Paper"""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 1 in citations
        assert len(citations[1]) == 1
        assert "system (as shown in [1])" in citations[1][0].lower()
    
    def test_large_reference_numbers(self):
        """Test with large reference numbers (e.g., [100])."""
        full_text = """This cites reference [100] from a large bibliography.
        
        References
        ... many references ...
        [100] The 100th Reference"""
        
        ref_start = full_text.find("References")
        citations = extract_citation_sentences(full_text, ref_start)
        
        assert 100 in citations
        assert len(citations[100]) == 1
        assert "[100]" in citations[100][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
