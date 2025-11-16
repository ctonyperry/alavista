"""
Tokenizer module for text preprocessing and normalization.

Provides simple tokenization for BM25 indexing and search.
"""

import re
import unicodedata
from collections.abc import Sequence

# Common English stopwords (minimal set for MVP)
DEFAULT_STOPWORDS = frozenset([
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "will", "with"
])


def normalize_unicode(text: str) -> str:
    """
    Normalize unicode text to NFC form.

    Args:
        text: Input text

    Returns:
        Unicode normalized text
    """
    return unicodedata.normalize("NFC", text)


def tokenize(text: str, lowercase: bool = True, remove_stopwords: bool = False,
             stopwords: Sequence[str] | None = None) -> list[str]:
    """
    Tokenize text into words.

    Splits on whitespace and punctuation, normalizes unicode,
    and optionally lowercases and removes stopwords.

    Args:
        text: Input text to tokenize
        lowercase: Whether to convert tokens to lowercase (default: True)
        remove_stopwords: Whether to filter out stopwords (default: False)
        stopwords: Custom stopword list (default: uses DEFAULT_STOPWORDS)

    Returns:
        List of tokens

    Examples:
        >>> tokenize("Hello, world!")
        ['hello', 'world']
        >>> tokenize("The quick brown fox", remove_stopwords=True)
        ['quick', 'brown', 'fox']
    """
    # Normalize unicode
    text = normalize_unicode(text)

    # Lowercase if requested
    if lowercase:
        text = text.lower()

    # Split on whitespace and punctuation
    # Keep alphanumeric sequences, including numbers
    tokens = re.findall(r'\w+', text)

    # Remove stopwords if requested
    if remove_stopwords:
        stop_set = set(stopwords) if stopwords else DEFAULT_STOPWORDS
        tokens = [t for t in tokens if t not in stop_set]

    return tokens
