"""Chunker: clean sections -> retrieval chunks (0008 step 1).

Input: `data/clean/vol{NN}.json` sections with `kind == work` only
(`editorial` is stored but never chunked in v1). Packing is paragraph
aware (~`chunk_size` chars, ~`chunk_overlap` chars of trailing-paragraph
overlap) and never merges across a section (`work`/`chapter`) boundary
or across volumes — chunking is per section, so boundaries hold by
construction. Oversized single paragraphs fall back to char windows.

Output record: {chunk_id, text, volume, work, chapter, spine_index,
kind}. chunk_id = ru-vol{NN}-{work-slug}-{spine_index}-{ordinal} is
deterministic: same clean JSON + same config -> same IDs/texts.
"""

import json
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str
    text: str
    volume: int
    work: str
    chapter: str
    spine_index: int
    kind: str = "work"

    def to_record(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "volume": self.volume,
            "work": self.work,
            "chapter": self.chapter,
            "spine_index": self.spine_index,
            "kind": self.kind,
        }


_SLUG_RE = re.compile(r"[^0-9a-zа-яё]+", re.IGNORECASE)


def slugify_work(work: str, limit: int = 40) -> str:
    """ASCII/Cyrillic-safe slug; falls back to 'untitled' on empty input."""
    slug = _SLUG_RE.sub("-", work.strip().lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:limit].strip("-") or "untitled"


def chunk_id_for(volume_no: int, work: str, spine_index: int, ordinal: int) -> str:
    return f"ru-vol{volume_no:02d}-{slugify_work(work)}-{spine_index}-{ordinal}"


def _split_long_paragraph(paragraph: str, size: int, overlap: int) -> list[str]:
    """Hard char-window split for a single paragraph longer than `size`."""
    step = max(size - overlap, 1)
    pieces = []
    start = 0
    while start < len(paragraph):
        pieces.append(paragraph[start : start + size])
        if start + size >= len(paragraph):
            break
        start += step
    return pieces


def _pack_paragraphs(paragraphs: list[str], size: int, overlap: int) -> list[str]:
    """Greedy paragraph packing with trailing-paragraph overlap carry."""
    texts: list[str] = []
    buf: list[str] = []
    buf_len = 0  # chars incl. "\n\n" separators

    def buf_text() -> str:
        return "\n\n".join(buf)

    def carry_overlap() -> None:
        """Keep trailing paragraphs covering >= overlap chars as next prefix."""
        nonlocal buf_len
        kept: list[str] = []
        kept_len = 0
        for para in reversed(buf):
            kept.append(para)
            kept_len += len(para) + 2
            if kept_len >= overlap + 2:
                break
        kept.reverse()
        buf.clear()
        buf.extend(kept)
        buf_len = sum(len(p) for p in buf) + max(2 * (len(buf) - 1), 0)

    for para in paragraphs:
        if len(para) > size:
            if buf:
                texts.append(buf_text())
                buf.clear()
                buf_len = 0
            texts.extend(_split_long_paragraph(para, size, overlap))
            continue
        add = len(para) + (2 if buf else 0)
        if buf and buf_len + add > size:
            texts.append(buf_text())
            carry_overlap()
            add = len(para) + (2 if buf else 0)
            if buf and buf_len + add > size:
                # Carried overlap + paragraph still exceeds size: drop the
                # carry and start fresh. Emitting it would duplicate the
                # just-flushed text; bounded chunks matter more for the
                # 512-token embedder than overlap at this one boundary.
                buf.clear()
                buf_len = 0
                add = len(para)
        buf.append(para)
        buf_len += add
    if buf:
        texts.append(buf_text())
    return [text for text in texts if text]


def chunk_section_text(text: str, size: int, overlap: int) -> list[str]:
    """Split one section's normalized text into chunk-sized strings."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []
    return _pack_paragraphs(paragraphs, size, overlap)


def chunk_section(
    *,
    volume_no: int,
    work: str,
    chapter: str,
    spine_index: int,
    text: str,
    size: int,
    overlap: int,
    min_chars: int = 50,
) -> list[Chunk]:
    """Chunk a single clean section (one work/chapter unit).

    Pieces shorter than `min_chars` (letter signatures like "Л. Т.",
    ornaments) are dropped: they carry no citable content and pollute
    top-k with identical tiny vectors.
    """
    pieces = [p for p in chunk_section_text(text, size, overlap) if len(p) >= min_chars]
    return [
        Chunk(
            chunk_id=chunk_id_for(volume_no, work, spine_index, ordinal),
            text=piece,
            volume=volume_no,
            work=work,
            chapter=chapter,
            spine_index=spine_index,
        )
        for ordinal, piece in enumerate(pieces)
    ]


def chunk_clean_payload(payload: dict, size: int, overlap: int, min_chars: int = 50) -> list[Chunk]:
    """Chunk every `kind == work` section of one loaded clean JSON payload."""
    volume_no = payload.get("volume_no")
    chunks: list[Chunk] = []
    for section in payload.get("sections", []):
        if section.get("kind") != "work":
            continue
        text = (section.get("text") or "").strip()
        if not text:
            continue
        chunks.extend(
            chunk_section(
                volume_no=volume_no,
                work=section.get("work", ""),
                chapter=section.get("chapter", ""),
                spine_index=section.get("spine_index", 0),
                text=text,
                size=size,
                overlap=overlap,
                min_chars=min_chars,
            )
        )
    return chunks


def chunk_file(clean_path: str, size: int, overlap: int, min_chars: int = 50) -> list[Chunk]:
    """Load one `data/clean/volNN.json` file and chunk its work sections."""
    with open(clean_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    return chunk_clean_payload(payload, size, overlap, min_chars)
