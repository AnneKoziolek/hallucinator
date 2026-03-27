import os
import sys
import pytest

# Add hallucinator directory to sys.path so tests can import the scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def test_pdf_path():
    return os.path.join(os.path.dirname(__file__), '..', 'papers', 'Dehghani_MODELS26_Branching-5.pdf')


@pytest.fixture
def sample_verified_result():
    """A single verified result entry matching the results.json schema."""
    return {
        "title": "Deep Learning for Software Engineering",
        "authors": ["John Smith", "Jane Doe"],
        "year": "2023",
        "doi": None,
        "pdf": "papers/test.pdf",
        "original_verification": {},
        "hallucinator_check": {
            "status": "verified",
            "source": "CrossRef",
            "found_title": "Deep Learning for Software Engineering",
            "found_authors": ["John Smith", "Jane Doe"],
            "publication_year": 2023,
            "openalex_url": None
        }
    }


@pytest.fixture
def sample_not_found_result():
    """A not_found result entry for testing classification."""
    return {
        "title": "A Completely Fabricated Paper Title",
        "authors": ["Fake Author", "Another Fake"],
        "year": "2024",
        "doi": None,
        "pdf": "papers/test.pdf",
        "original_verification": {},
        "hallucinator_check": {
            "status": "not_found",
            "source": None,
            "found_title": None,
            "found_authors": None,
            "publication_year": None,
            "openalex_url": None
        }
    }


@pytest.fixture
def sample_results(sample_verified_result, sample_not_found_result):
    """A list of mixed results for pipeline testing."""
    return [
        sample_verified_result,
        sample_not_found_result,
        {
            "title": "IEEE Standard for Systems Architecture",
            "authors": ["IEEE"],
            "year": "2020",
            "doi": None,
            "pdf": "papers/test.pdf",
            "original_verification": {},
            "hallucinator_check": {
                "status": "not_found",
                "source": None,
                "found_title": None,
                "found_authors": None,
                "publication_year": None,
                "openalex_url": None
            }
        },
    ]
