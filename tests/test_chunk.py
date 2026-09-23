"""Chunker tests: determinism, overlap, boundaries, editorial exclusion."""

from tolstoy.ingest.chunk import (
    chunk_clean_payload,
    chunk_id_for,
    chunk_section,
    chunk_section_text,
    slugify_work,
)


def _para(tag: str, length: int = 100) -> str:
    body = (tag + " ") * ((length // (len(tag) + 1)) + 1)
    return body[:length]


def test_chunk_ids_deterministic() -> None:
    kwargs = {
        "volume_no": 4,
        "work": "Война и мир. Том 1",
        "chapter": "Часть первая",
        "spine_index": 6,
        "text": "\n\n".join(_para(f"p{i}") for i in range(6)),
        "size": 250,
        "overlap": 50,
    }
    first = chunk_section(**kwargs)
    second = chunk_section(**kwargs)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert [c.text for c in first] == [c.text for c in second]
    assert first[0].chunk_id == chunk_id_for(4, "Война и мир. Том 1", 6, 0)
    assert first[0].chunk_id.startswith("ru-vol04-")


def test_overlap_carries_trailing_paragraph() -> None:
    text = "\n\n".join(_para(f"p{i}") for i in range(5))
    chunks = chunk_section_text(text, size=250, overlap=50)
    assert len(chunks) >= 2
    first_tail = _para("p1")
    assert chunks[0].endswith(first_tail)
    assert chunks[1].startswith(first_tail)


def test_chunks_bounded_by_size() -> None:
    text = "\n\n".join(_para(f"p{i}", length=n) for i, n in enumerate([800, 700, 850, 100]))
    chunks = chunk_section_text(text, size=900, overlap=150)
    assert chunks
    assert all(len(c) <= 900 for c in chunks)


def test_long_paragraph_hard_split_with_overlap() -> None:
    text = "слово " * 500  # single ~3000-char paragraph
    chunks = chunk_section_text(text.strip(), size=900, overlap=150)
    assert len(chunks) > 1
    assert all(len(c) <= 900 for c in chunks)
    assert chunks[1][:150] in chunks[0]  # window overlap honored


def test_no_chunk_crosses_section_boundaries() -> None:
    payload = {
        "volume_no": 1,
        "sections": [
            {
                "kind": "work",
                "work": "Детство",
                "chapter": "Глава I",
                "spine_index": 3,
                "text": "\n\n".join(_para(f"detstvo{i}", length=300) for i in range(4)),
            },
            {
                "kind": "work",
                "work": "Отрочество",
                "chapter": "Глава II",
                "spine_index": 4,
                "text": "\n\n".join(_para(f"otrochestvo{i}", length=300) for i in range(4)),
            },
        ],
    }
    chunks = chunk_clean_payload(payload, size=900, overlap=150)
    assert chunks
    for chunk in chunks:
        assert chunk.kind == "work"
        assert chunk.volume == 1
        if "detstvo" in chunk.text:
            assert chunk.work == "Детство"
            assert "otrochestvo" not in chunk.text
        else:
            assert chunk.work == "Отрочество"
            assert "detstvo" not in chunk.text


def test_editorial_sections_excluded() -> None:
    payload = {
        "volume_no": 2,
        "sections": [
            {
                "kind": "editorial",
                "work": "",
                "chapter": "",
                "spine_index": 1,
                "text": "От издательства: уникальный-маркер.",
            },
            {
                "kind": "work",
                "work": "Казаки",
                "chapter": "",
                "spine_index": 2,
                "text": "Проза Толстого здесь, достаточно длинная, чтобы пройти фильтр.",
            },
        ],
    }
    chunks = chunk_clean_payload(payload, size=900, overlap=150)
    assert len(chunks) == 1
    assert "уникальный-маркер" not in chunks[0].text
    assert chunks[0].work == "Казаки"


def test_carry_overflow_drops_overlap_never_duplicates() -> None:
    # Single near-full paragraph followed by another: the carried overlap
    # plus the new paragraph still exceeds size -> carry is dropped, never
    # re-emitted (regression: identical consecutive chunk texts).
    first = _para("alpha", length=800)
    second = _para("beta", length=800)
    chunks = chunk_section_text(f"{first}\n\n{second}", size=900, overlap=150)
    assert len(chunks) == 2
    assert len(set(chunks)) == 2
    assert all(len(c) <= 900 for c in chunks)


def test_tiny_pieces_dropped() -> None:
    chunks = chunk_section(
        volume_no=1,
        work="Письма",
        chapter="",
        spine_index=9,
        text="Длинный содержательный абзац. " * 30 + "\n\nЛ. Т.",
        size=900,
        overlap=150,
        min_chars=50,
    )
    assert chunks
    assert all(len(c.text) >= 50 for c in chunks)
    assert not any(c.text.strip() == "Л. Т." for c in chunks)


def test_slugify_fallback() -> None:
    assert slugify_work("") == "untitled"
    assert slugify_work("Война и мир. Том 1") == "война-и-мир-том-1"
