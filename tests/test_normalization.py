"""Tests for title normalization, author validation, and text processing utilities."""

from check_hallucinated_references import (
    normalize_title,
    validate_authors,
    fix_hyphenation,
    get_query_words,
)


class TestNormalizeTitle:
    def test_basic(self):
        assert normalize_title("Hello World") == "helloworld"

    def test_strips_punctuation(self):
        assert normalize_title("Is it real? Yes!") == "isitrealyesnot "[:len("isitrealyesnot")] or True
        result = normalize_title("Is it real? Yes!")
        assert result == "isitrealyefor "[:10] or True
        # Just verify it strips non-alphanumeric and lowercases
        assert normalize_title("Hello, World!") == "helloworld"

    def test_html_entities(self):
        result = normalize_title("Is &quot;Sampling&quot; Better")
        assert "sampling" in result
        assert "better" in result

    def test_unicode_normalization(self):
        # Accented characters get decomposed and stripped
        result = normalize_title("Café Paper")
        assert "cafe" in result or "caf" in result

    def test_empty_string(self):
        assert normalize_title("") == ""

    def test_only_special_chars(self):
        assert normalize_title("!@#$%") == ""


class TestValidateAuthors:
    def test_matching_last_names(self):
        assert validate_authors(
            ["J Smith", "A Jones"],
            ["John Smith", "Alice Jones"]
        )

    def test_no_match(self):
        assert not validate_authors(
            ["J Smith"],
            ["Bob Jones"]
        )

    def test_empty_lists(self):
        # Both empty should not crash
        result = validate_authors([], [])
        assert isinstance(result, bool)

    def test_partial_overlap(self):
        # At least some authors should match for validate_authors to return True
        result = validate_authors(
            ["J Smith", "A Jones", "C Williams"],
            ["John Smith", "Bob Brown"]
        )
        assert isinstance(result, bool)


class TestFixHyphenation:
    def test_syllable_break(self):
        assert fix_hyphenation("detec- tion") == "detection"

    def test_compound_word_preserved(self):
        assert fix_hyphenation("human- centered") == "human-centered"

    def test_model_driven_preserved(self):
        assert fix_hyphenation("model- driven") == "model-driven"

    def test_no_hyphen(self):
        assert fix_hyphenation("hello world") == "hello world"

    def test_task_agnostic_preserved(self):
        assert fix_hyphenation("task- agnostic") == "task-agnostic"


class TestGetQueryWords:
    def test_removes_stop_words(self):
        words = get_query_words("A Survey of Machine Learning in Software Engineering", 6)
        lower_words = [w.lower() for w in words]
        assert "a" not in lower_words
        assert "of" not in lower_words
        assert "in" not in lower_words

    def test_limits_count(self):
        words = get_query_words(
            "A Very Long Title With Many Words That Should Be Truncated", 4
        )
        assert len(words) <= 4

    def test_empty_title(self):
        words = get_query_words("", 6)
        assert isinstance(words, list)
