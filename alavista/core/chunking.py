"""
Text chunking utilities for Alavista.

Provides deterministic chunking strategies for splitting documents into
manageable chunks for indexing and embedding.
"""

import re
from typing import NamedTuple


class ChunkInfo(NamedTuple):
    """Information about a text chunk."""

    text: str
    start_offset: int
    end_offset: int


def normalize_text(text: str) -> str:
    """
    Normalize text for consistent processing.

    Args:
        text: Raw input text

    Returns:
        Normalized text with consistent whitespace
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize multiple spaces but preserve single newlines
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize multiple newlines (3+ becomes 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def chunk_text(
    text: str,
    min_chunk_size: int = 500,
    max_chunk_size: int = 1500,
    overlap: int = 0,
) -> list[ChunkInfo]:
    """
    Split text into chunks using paragraph and sentence boundaries.

    Strategy:
    1. Normalize the text
    2. Split by paragraphs (double newlines)
    3. If a paragraph is too large, split by sentences
    4. If a sentence is too large, split by character count
    5. Combine small chunks to reach min_chunk_size where possible

    Args:
        text: Text to chunk
        min_chunk_size: Minimum target chunk size in characters
        max_chunk_size: Maximum chunk size in characters
        overlap: Number of characters to overlap between chunks (future use)

    Returns:
        List of ChunkInfo tuples with text and offsets
    """
    if not text or not text.strip():
        return []

    normalized = normalize_text(text)

    # Split by paragraphs (double newlines or more)
    paragraphs = re.split(r"\n\n+", normalized)

    chunks: list[ChunkInfo] = []
    current_offset = 0

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            # Track empty paragraphs for offset calculation
            current_offset += len(paragraph) + 2  # Account for the split delimiter
            continue

        # If paragraph is within bounds, use it as-is
        if len(paragraph) <= max_chunk_size:
            chunks.append(
                ChunkInfo(
                    text=paragraph,
                    start_offset=current_offset,
                    end_offset=current_offset + len(paragraph),
                )
            )
            current_offset += len(paragraph) + 2  # Account for paragraph separator
        else:
            # Split large paragraph by sentences
            sentences = _split_sentences(paragraph)
            para_offset = current_offset

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                if len(sentence) <= max_chunk_size:
                    chunks.append(
                        ChunkInfo(
                            text=sentence,
                            start_offset=para_offset,
                            end_offset=para_offset + len(sentence),
                        )
                    )
                    para_offset += len(sentence) + 1
                else:
                    # Split very long sentence by character boundaries
                    sentence_chunks = _split_by_chars(sentence, max_chunk_size)
                    for chunk_text in sentence_chunks:
                        chunks.append(
                            ChunkInfo(
                                text=chunk_text,
                                start_offset=para_offset,
                                end_offset=para_offset + len(chunk_text),
                            )
                        )
                        para_offset += len(chunk_text)

            current_offset = para_offset + 2

    # Merge small chunks to reach min_chunk_size where possible
    if min_chunk_size > 0:
        chunks = _merge_small_chunks(chunks, min_chunk_size, max_chunk_size)

    return chunks


def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentences using simple punctuation-based rules.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Split on sentence-ending punctuation followed by whitespace or end of string
    # This is a simple heuristic; more sophisticated methods could be used
    sentences = re.split(r"([.!?]+)\s+", text)

    # Recombine sentence with its punctuation
    result = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            result.append(sentences[i] + sentences[i + 1])
        else:
            result.append(sentences[i])

    # Don't forget the last part if there's no punctuation at the end
    if len(sentences) % 2 == 1 and sentences[-1]:
        result.append(sentences[-1])

    return [s for s in result if s.strip()]


def _split_by_chars(text: str, max_size: int) -> list[str]:
    """
    Split text into chunks by character count.

    Tries to split at word boundaries where possible.

    Args:
        text: Text to split
        max_size: Maximum chunk size

    Returns:
        List of text chunks
    """
    if len(text) <= max_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_size

        if end >= len(text):
            chunks.append(text[start:])
            break

        # Try to find a word boundary near the end
        boundary = text.rfind(" ", start, end)
        if boundary > start:
            end = boundary

        chunks.append(text[start:end].strip())
        start = end + 1  # Skip the space

    return chunks


def _merge_small_chunks(
    chunks: list[ChunkInfo], min_size: int, max_size: int
) -> list[ChunkInfo]:
    """
    Merge consecutive small chunks to reach minimum size.

    Args:
        chunks: List of chunks to potentially merge
        min_size: Minimum target chunk size
        max_size: Maximum chunk size (don't merge beyond this)

    Returns:
        List of merged chunks
    """
    if not chunks:
        return []

    merged: list[ChunkInfo] = []
    current_text = chunks[0].text
    current_start = chunks[0].start_offset

    for i in range(1, len(chunks)):
        # Try to merge if current chunk is small and merging won't exceed max_size
        next_chunk = chunks[i]
        combined_text = current_text + "\n\n" + next_chunk.text

        if len(current_text) < min_size and len(combined_text) <= max_size:
            # Merge
            current_text = combined_text
        else:
            # Save current and start new
            merged.append(
                ChunkInfo(
                    text=current_text,
                    start_offset=current_start,
                    end_offset=current_start + len(current_text),
                )
            )
            current_text = next_chunk.text
            current_start = next_chunk.start_offset

    # Don't forget the last chunk
    merged.append(
        ChunkInfo(
            text=current_text,
            start_offset=current_start,
            end_offset=current_start + len(current_text),
        )
    )

    return merged
