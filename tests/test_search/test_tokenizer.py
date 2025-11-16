"""
Tests for the tokenizer module.
"""


from alavista.search.tokenizer import DEFAULT_STOPWORDS, normalize_unicode, tokenize


class TestNormalizeUnicode:
    """Test unicode normalization."""

    def test_normalize_nfc(self):
        """Test NFC normalization."""
        # Combining characters
        text = "café"  # e with combining acute
        normalized = normalize_unicode(text)
        assert normalized == "café"

    def test_already_normalized(self):
        """Test text that's already normalized."""
        text = "hello world"
        normalized = normalize_unicode(text)
        assert normalized == text

    def test_empty_string(self):
        """Test empty string."""
        assert normalize_unicode("") == ""


class TestTokenize:
    """Test tokenization functionality."""

    def test_basic_tokenization(self):
        """Test basic word splitting."""
        tokens = tokenize("hello world")
        assert tokens == ["hello", "world"]

    def test_punctuation_removal(self):
        """Test that punctuation is removed."""
        tokens = tokenize("Hello, world!")
        assert tokens == ["hello", "world"]

    def test_multiple_punctuation(self):
        """Test multiple punctuation marks."""
        tokens = tokenize("Hello... world!!! How are you?")
        assert tokens == ["hello", "world", "how", "are", "you"]

    def test_lowercase_conversion(self):
        """Test lowercase conversion."""
        tokens = tokenize("HELLO World")
        assert tokens == ["hello", "world"]

    def test_no_lowercase(self):
        """Test with lowercase=False."""
        tokens = tokenize("HELLO World", lowercase=False)
        assert tokens == ["HELLO", "World"]

    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        tokens = tokenize("Python 3.11 is great")
        assert tokens == ["python", "3", "11", "is", "great"]

    def test_unicode_text(self):
        """Test unicode text handling."""
        tokens = tokenize("café résumé")
        assert tokens == ["café", "résumé"]

    def test_empty_string(self):
        """Test empty string."""
        tokens = tokenize("")
        assert tokens == []

    def test_whitespace_only(self):
        """Test whitespace-only string."""
        tokens = tokenize("   \t\n  ")
        assert tokens == []

    def test_stopword_removal(self):
        """Test stopword removal."""
        tokens = tokenize("the quick brown fox", remove_stopwords=True)
        assert tokens == ["quick", "brown", "fox"]
        assert "the" not in tokens

    def test_no_stopword_removal(self):
        """Test without stopword removal."""
        tokens = tokenize("the quick brown fox", remove_stopwords=False)
        assert tokens == ["the", "quick", "brown", "fox"]

    def test_custom_stopwords(self):
        """Test custom stopword list."""
        custom_stops = ["quick", "brown"]
        tokens = tokenize("the quick brown fox", remove_stopwords=True, stopwords=custom_stops)
        assert tokens == ["the", "fox"]

    def test_all_stopwords(self):
        """Test text with only stopwords."""
        tokens = tokenize("the and of", remove_stopwords=True)
        assert tokens == []

    def test_hyphenated_words(self):
        """Test hyphenated words are split."""
        tokens = tokenize("state-of-the-art")
        assert "state" in tokens
        assert "of" in tokens
        assert "the" in tokens
        assert "art" in tokens

    def test_apostrophes(self):
        """Test words with apostrophes."""
        tokens = tokenize("don't can't won't")
        # Apostrophes are treated as word boundaries
        assert "don" in tokens
        assert "t" in tokens
        assert "can" in tokens
        assert "won" in tokens

    def test_determinism(self):
        """Test that tokenization is deterministic."""
        text = "Hello, world! How are you?"
        tokens1 = tokenize(text)
        tokens2 = tokenize(text)
        assert tokens1 == tokens2


class TestDefaultStopwords:
    """Test default stopwords set."""

    def test_stopwords_exist(self):
        """Test that default stopwords are defined."""
        assert len(DEFAULT_STOPWORDS) > 0

    def test_common_stopwords(self):
        """Test that common stopwords are included."""
        assert "the" in DEFAULT_STOPWORDS
        assert "a" in DEFAULT_STOPWORDS
        assert "and" in DEFAULT_STOPWORDS
        assert "of" in DEFAULT_STOPWORDS

    def test_stopwords_lowercase(self):
        """Test that stopwords are lowercase."""
        for word in DEFAULT_STOPWORDS:
            assert word == word.lower()
