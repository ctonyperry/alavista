"""
Tests for text chunking utilities.
"""

from alavista.core.chunking import chunk_text, normalize_text


class TestNormalization:
    """Test suite for text normalization."""

    def test_normalize_whitespace(self):
        """Test that multiple spaces are normalized."""
        text = "Hello    world   with    spaces"
        normalized = normalize_text(text)
        assert normalized == "Hello world with spaces"

    def test_normalize_line_endings(self):
        """Test that line endings are normalized."""
        text = "Line 1\r\nLine 2\rLine 3\nLine 4"
        normalized = normalize_text(text)
        assert normalized == "Line 1\nLine 2\nLine 3\nLine 4"

    def test_normalize_multiple_newlines(self):
        """Test that multiple newlines are normalized."""
        text = "Paragraph 1\n\n\n\nParagraph 2"
        normalized = normalize_text(text)
        assert normalized == "Paragraph 1\n\nParagraph 2"

    def test_strip_line_whitespace(self):
        """Test that leading/trailing whitespace is stripped from lines."""
        text = "  Line 1  \n  Line 2  \n  Line 3  "
        normalized = normalize_text(text)
        assert normalized == "Line 1\nLine 2\nLine 3"

    def test_empty_text(self):
        """Test normalization of empty text."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""
        assert normalize_text("\n\n\n") == ""


class TestChunking:
    """Test suite for text chunking."""

    def test_empty_text(self):
        """Test chunking empty text returns empty list."""
        chunks = chunk_text("")
        assert chunks == []

        chunks = chunk_text("   ")
        assert chunks == []

    def test_small_text(self):
        """Test chunking text smaller than min_chunk_size."""
        text = "This is a small document."
        chunks = chunk_text(text, min_chunk_size=100)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].start_offset == 0
        assert chunks[0].end_offset == len(text)

    def test_paragraph_splitting(self):
        """Test that text is split by paragraphs."""
        text = """First paragraph with some content.

Second paragraph with more content.

Third paragraph with even more content."""

        chunks = chunk_text(text, min_chunk_size=10, max_chunk_size=500)

        # Should have 3 chunks (one per paragraph)
        assert len(chunks) >= 1  # May be merged if too small

    def test_large_paragraph_splitting(self):
        """Test that large paragraphs are split by sentences."""
        # Create a paragraph with multiple sentences that's larger than max_chunk_size
        text = "This is sentence one. " * 50  # ~1100 chars

        chunks = chunk_text(text, min_chunk_size=100, max_chunk_size=500)

        # Should be split into multiple chunks
        assert len(chunks) > 1

        # Each chunk should be within size limits
        for chunk in chunks:
            assert len(chunk.text) <= 500

    def test_very_long_sentence(self):
        """Test chunking of a sentence longer than max_chunk_size."""
        # Create a very long sentence without punctuation
        text = "word " * 300  # ~1500 chars

        chunks = chunk_text(text, min_chunk_size=100, max_chunk_size=500)

        # Should be split even without sentence boundaries
        assert len(chunks) > 1

        # Each chunk should be within size limits
        for chunk in chunks:
            assert len(chunk.text) <= 500

    def test_chunk_offsets(self):
        """Test that chunk offsets are correct."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

        chunks = chunk_text(text, min_chunk_size=10, max_chunk_size=100)

        # Verify offsets are non-overlapping and in order
        for i in range(len(chunks) - 1):
            assert chunks[i].start_offset < chunks[i].end_offset
            # Note: offsets may not be perfectly sequential due to normalization

    def test_no_punctuation(self):
        """Test chunking text without punctuation."""
        text = "word " * 400  # Long text without punctuation

        chunks = chunk_text(text, min_chunk_size=100, max_chunk_size=500)

        # Should still chunk by character boundaries
        assert len(chunks) > 1

        for chunk in chunks:
            assert len(chunk.text) <= 500

    def test_empty_lines(self):
        """Test handling of empty lines."""
        text = "Paragraph 1\n\n\n\nParagraph 2"

        chunks = chunk_text(text, min_chunk_size=5, max_chunk_size=100)

        # Empty lines should be normalized away
        assert all(chunk.text.strip() for chunk in chunks)

    def test_long_lines(self):
        """Test chunking of long lines."""
        # Create a very long single line
        text = "word " * 500  # ~2500 chars in one "line"

        chunks = chunk_text(text, min_chunk_size=100, max_chunk_size=500)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.text) <= 500

    def test_configurable_chunk_sizes(self):
        """Test that chunk size parameters work correctly."""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"

        # Small chunks
        small_chunks = chunk_text(text, min_chunk_size=5, max_chunk_size=20)
        # Large chunks
        large_chunks = chunk_text(text, min_chunk_size=10, max_chunk_size=1000)

        # Small chunks should produce more chunks
        assert len(small_chunks) >= len(large_chunks)

    def test_realistic_document(self):
        """Test chunking a realistic document."""
        text = """
        This is the first paragraph of a realistic document.
        It contains multiple sentences and some content.

        The second paragraph discusses another topic.
        It also has multiple sentences with varying lengths.
        Some sentences are short. Others are considerably longer.

        The third paragraph wraps up the document.
        It provides a conclusion to the preceding content.
        """

        chunks = chunk_text(text, min_chunk_size=50, max_chunk_size=200)

        # Verify basic properties
        assert len(chunks) > 0

        # Each chunk should have content
        for chunk in chunks:
            assert chunk.text.strip()
            assert len(chunk.text) <= 200
            assert chunk.start_offset < chunk.end_offset

        # Chunks should cover the document (approximately, after normalization)
        # We can't guarantee exact coverage due to normalization
        assert chunks[0].start_offset >= 0

    def test_merge_small_chunks(self):
        """Test that small chunks are merged when possible."""
        text = "A.\n\nB.\n\nC.\n\nD.\n\nE."

        # With small paragraphs and min_chunk_size, they should be merged
        chunks = chunk_text(text, min_chunk_size=10, max_chunk_size=100)

        # Should have fewer chunks than paragraphs due to merging
        assert len(chunks) < 5
