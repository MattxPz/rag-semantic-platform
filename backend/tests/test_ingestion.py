from app.services.ingestion import (
    BLOCK_SEPARATOR,
    _bboxes_in_range,
    _join_blocks_with_offsets,
    chunk_pages,
)


def test_join_blocks_tracks_offsets():
    blocks = [
        {"text": "First block.", "bbox": [0, 0, 10, 10]},
        {"text": "Second block.", "bbox": [0, 20, 10, 30]},
    ]
    text, offsets = _join_blocks_with_offsets(blocks)

    assert "First block." in text
    assert "Second block." in text
    assert BLOCK_SEPARATOR in text
    assert offsets[0]["start"] == 0
    assert offsets[0]["end"] == len("First block.")
    # Second block starts after the first block plus the separator.
    assert offsets[1]["start"] == len("First block.") + len(BLOCK_SEPARATOR)


def test_bboxes_in_range_returns_overlapping_only():
    offset_blocks = [
        {"start": 0, "end": 10, "bbox": [0, 0, 1, 1]},
        {"start": 20, "end": 30, "bbox": [0, 2, 1, 3]},
    ]
    # Range [5, 15) overlaps only the first block.
    result = _bboxes_in_range(offset_blocks, 5, 15)
    assert result == [[0, 0, 1, 1]]


def test_chunk_pages_preserves_page_numbers():
    pages = [
        {"page_number": 1, "blocks": [{"text": "Content on page one.", "bbox": [0, 0, 10, 10]}]},
        {"page_number": 2, "blocks": [{"text": "Content on page two.", "bbox": [0, 0, 10, 10]}]},
    ]
    chunks = chunk_pages(pages)

    assert len(chunks) >= 2
    page_numbers = {chunk["page_number"] for chunk in chunks}
    assert page_numbers == {1, 2}
    for chunk in chunks:
        assert "content" in chunk
        assert chunk["bbox"] is not None
