"""Cleaner: normalize text, classify kind, detect work/chapter (0002 contract).

kind is binary per contract: `work` (Tolstoy's prose, indexed) vs
`editorial` (publisher apparatus, notes, title matter — stored, excluded
from retrieval). Numbered note bodies go to a `notes` sidecar (spine
position kept; link schema is a 0002 follow-up, still open).
"""

import argparse
import json
import os
import re
from dataclasses import dataclass, field

from tolstoy.ingest import epub as epub_reader
from tolstoy.ingest.epub import VolumeRaw

#: Section headings that mark non-authorial apparatus (lowercase match).
EDITORIAL_PATTERNS = (
    "от издательства",
    "примечания",
    "комментарии",
    "содержание",
    "аннотация",
    "указатель",
)

#: Headings that mark note/comment blocks (everything after stays editorial).
NOTES_PATTERNS = ("примечания", "комментарии")

#: Title-page matter: never emitted, never indexed.
TITLE_PATTERNS = ("собрание сочинений", "толстой")

VOLUME_TITLE_RE = re.compile(r"^\s*том\s*\d+", re.IGNORECASE)
NOTE_HEAD_RE = re.compile(r"^\s*\d+\.?\s*$")
HYPHEN_BREAK_RE = re.compile(r"(\w)-\s*\n\s*(\w)")


@dataclass
class CleanSection:
    spine_index: int
    href: str
    work: str
    chapter: str
    kind: str  # work | editorial
    text: str


@dataclass
class NoteRecord:
    spine_index: int
    head: str
    text: str


@dataclass
class CleanVolume:
    volume_no: int | None
    filename: str
    title: str
    creator: str
    publisher: str
    pub_year: str
    language: str
    sections: list[CleanSection] = field(default_factory=list)
    notes: list[NoteRecord] = field(default_factory=list)


def normalize_text(raw: str) -> str:
    """Collapse whitespace per paragraph, join FB2 hyphenation breaks.

    Paragraph boundaries become exactly one blank line; Cyrillic
    punctuation is kept verbatim.
    """
    text = raw.replace("\u00ad", "")
    text = HYPHEN_BREAK_RE.sub(r"\1\2", text)
    paragraphs = [
        re.sub(r"\s+", " ", paragraph).strip() for paragraph in re.split(r"\n\s*\n", text)
    ]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _lower(text: str) -> str:
    return text.lower()


def _is_editorial_head(text: str) -> bool:
    lowered = _lower(text)
    return any(pattern in lowered for pattern in EDITORIAL_PATTERNS)


def _is_title_head(text: str) -> bool:
    lowered = _lower(text)
    return VOLUME_TITLE_RE.match(text) is not None or any(
        pattern in lowered for pattern in TITLE_PATTERNS
    )


def clean_volume(raw: VolumeRaw) -> CleanVolume:
    """Map raw spine sections to kind-tagged clean sections + note sidecars."""
    clean = CleanVolume(
        volume_no=raw.volume_no,
        filename=raw.filename,
        title=raw.titles[0] if raw.titles else "",
        creator=raw.creator,
        publisher=raw.publisher,
        pub_year=raw.pub_year,
        language=raw.language,
    )
    current_work = ""
    current_chapter = ""
    in_back_matter = False

    for section in raw.sections:
        heads = [heading.text for heading in section.headings]
        levels = [heading.level for heading in section.headings]

        if any(any(pattern in _lower(head) for pattern in NOTES_PATTERNS) for head in heads):
            in_back_matter = True

        # Work/chapter tracker updates even for sections we skip below.
        major = [text for text, level in zip(heads, levels) if level in ("h1", "h2")]
        minors = [text for text, level in zip(heads, levels) if level == "h3"]
        for head in major:
            if not _is_editorial_head(head) and not _is_title_head(head):
                current_work = head
                current_chapter = ""
        if minors and not in_back_matter:
            current_chapter = " — ".join(minors)

        text = normalize_text("\n\n".join(section.paragraphs))
        if not text:
            continue  # title page / work marker: tracker updated, nothing to store
        if len(heads) == 1 and NOTE_HEAD_RE.match(heads[0]):
            clean.notes.append(
                NoteRecord(spine_index=section.spine_index, head=heads[0], text=text)
            )
            continue
        if any(_is_title_head(head) for head in heads):
            continue

        kind = (
            "editorial"
            if in_back_matter or any(_is_editorial_head(head) for head in heads)
            else "work"
        )
        clean.sections.append(
            CleanSection(
                spine_index=section.spine_index,
                href=section.href,
                # Editorial sections carry no work/chapter: the tracker may
                # hold stale pre-back-matter values; empty is honest.
                work="" if kind == "editorial" else current_work,
                chapter="" if kind == "editorial" else current_chapter,
                kind=kind,
                text=text,
            )
        )
    return clean


def work_word_count(clean: CleanVolume) -> int:
    """Words over work sections only (the indexed corpus)."""
    return sum(len(section.text.split()) for section in clean.sections if section.kind == "work")


def section_count(clean: CleanVolume) -> int:
    return sum(1 for section in clean.sections if section.kind == "work")


def work_list(clean: CleanVolume) -> list[str]:
    works: list[str] = []
    for section in clean.sections:
        if section.kind == "work" and section.work and section.work not in works:
            works.append(section.work)
    return works


def write_clean_json(clean: CleanVolume, clean_dir: str) -> str:
    os.makedirs(clean_dir, exist_ok=True)
    name = f"vol{clean.volume_no:02d}.json" if clean.volume_no is not None else "vol??.json"
    path = os.path.join(clean_dir, name)
    payload = {
        "volume_no": clean.volume_no,
        "filename": clean.filename,
        "title": clean.title,
        "creator": clean.creator,
        "publisher": clean.publisher,
        "pub_year": clean.pub_year,
        "language": clean.language,
        "sections": [vars(section) for section in clean.sections],
        "notes": [vars(note) for note in clean.notes],
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")
    return path


def clean_file(raw_path: str, clean_dir: str) -> tuple[CleanVolume, str]:
    raw = epub_reader.read_volume(raw_path)
    clean = clean_volume(raw)
    return clean, write_clean_json(clean, clean_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean EPUB volumes to data/clean/ JSON.")
    parser.add_argument("--raw", default="data/raw")
    parser.add_argument("--clean", default="data/clean")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--volume", type=int, help="volume number, e.g. 1")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)

    targets: list[str] = []
    if args.all:
        for filename in sorted(os.listdir(args.raw)):
            if filename.lower().endswith(".epub"):
                targets.append(os.path.join(args.raw, filename))
    else:
        for filename in sorted(os.listdir(args.raw)):
            if filename.lower().endswith(".epub"):
                found = epub_reader.parse_volume_no(filename) == args.volume
                if found:
                    targets.append(os.path.join(args.raw, filename))
        if not targets:
            print(f"no EPUB found for volume {args.volume} in {args.raw}")
            return 1

    for target in targets:
        clean, out_path = clean_file(target, args.clean)
        print(
            f"{clean.filename}: vol={clean.volume_no} "
            f"work_sections={section_count(clean)} notes={len(clean.notes)} "
            f"work_words={work_word_count(clean)} -> {out_path}"
        )
    return 0
