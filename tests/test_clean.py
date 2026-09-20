"""Cleaner tests: kind classification, inheritance, notes, normalization."""

from tolstoy.ingest.clean import (
    clean_volume,
    normalize_text,
    section_count,
    work_list,
    work_word_count,
)
from tolstoy.ingest.epub import Heading, SectionRaw, VolumeRaw


def _raw(sections: list[SectionRaw]) -> VolumeRaw:
    return VolumeRaw(
        path="x.epub",
        filename="Толстой Л.Н-Том 1..epub",
        volume_no=1,
        titles=["Том 1"],
        creator="Лев Николаевич Толстой",
        language="ru",
        publisher="Художественная литература",
        pub_year="1978",
        sections=sections,
    )


def _section(index: int, heads: list[tuple[str, str]], paragraphs: list[str]) -> SectionRaw:
    return SectionRaw(
        spine_index=index,
        idref=f"s{index}",
        href=f"Text/section{index}.xhtml",
        headings=[Heading(level=level, text=text) for level, text in heads],
        paragraphs=paragraphs,
    )


def test_editorial_tagged_not_indexed() -> None:
    raw = _raw(
        [
            _section(0, [("h2", "От издательства")], ["Текст издательства."]),
            _section(1, [("h2", "Детство")], []),
            _section(
                2,
                [("h3", "Глава I"), ("h3", "Учитель")],
                ["Проза Толстого здесь."],
            ),
        ]
    )
    clean = clean_volume(raw)
    kinds = [(section.work, section.chapter, section.kind) for section in clean.sections]
    assert kinds == [
        ("", "", "editorial"),
        ("Детство", "Глава I — Учитель", "work"),
    ]


def test_chapter_inherits_work() -> None:
    raw = _raw(
        [
            _section(0, [("h2", "Отрочество")], []),
            _section(1, [("h3", "Глава I")], ["Первая глава."]),
            _section(2, [("h3", "Глава II")], ["Вторая глава."]),
        ]
    )
    clean = clean_volume(raw)
    assert [(s.work, s.chapter) for s in clean.sections] == [
        ("Отрочество", "Глава I"),
        ("Отрочество", "Глава II"),
    ]


def test_numbered_notes_go_to_sidecar() -> None:
    raw = _raw(
        [
            _section(0, [("h2", "Примечания")], ["Заголовок раздела."]),
            _section(1, [("h2", "1")], ["Текст примечания первого."]),
        ]
    )
    clean = clean_volume(raw)
    assert len(clean.notes) == 1
    assert clean.notes[0].head == "1"
    assert clean.notes[0].text == "Текст примечания первого."
    assert all(section.kind == "editorial" for section in clean.sections)


def test_title_page_skipped_but_tracker_updated() -> None:
    raw = _raw(
        [
            _section(0, [("h2", "Собрание сочинений в двадцати двух томах")], []),
            _section(1, [("h2", "Юность")], []),
            _section(2, [("h3", "Глава I")], ["Текст."]),
        ]
    )
    clean = clean_volume(raw)
    assert len(clean.sections) == 1
    assert clean.sections[0].work == "Юность"


def test_normalize_joins_hyphenation_and_blanks() -> None:
    assert normalize_text("сло-\nво") == "слово"
    assert normalize_text("а\n\n\n\nб") == "а\n\nб"
    assert normalize_text("  лишние   пробелы  ") == "лишние пробелы"
    assert normalize_text("тире — и «кавычки»") == "тире — и «кавычки»"


def test_counts_cover_only_work() -> None:
    raw = _raw(
        [
            _section(0, [("h2", "От издательства")], ["Раз два три."]),
            _section(1, [("h3", "Глава")], ["Четыре пять."]),
        ]
    )
    clean = clean_volume(raw)
    assert section_count(clean) == 1
    assert work_word_count(clean) == 2
    assert work_list(clean) == []
