"""EPUB reader tests: spine order, extraction, drops, footnote markers."""

import os

import ebooklib.epub as epub
import pytest

from tolstoy.ingest.epub import DROP_IDREFS, parse_volume_no, read_volume

RAW_DIR = "data/raw"
VOL1 = os.path.join(RAW_DIR, "Толстой Л.Н-Том 1..epub")
needs_vol1 = pytest.mark.skipif(not os.path.exists(VOL1), reason="local Vol. 1 EPUB not present")


def _make_epub(path: str) -> None:
    """Minimal two-section EPUB with out-of-order filenames (spine decides)."""
    book = epub.EpubBook()
    book.set_identifier("test-id")
    book.set_title("Том 9. Тест")
    book.add_author("Лев Николаевич Толстой")
    book.set_language("ru")
    first = epub.EpubHtml(title="b", file_name="z_last.xhtml", lang="ru")
    first.content = "<html><body><h2>Работа</h2><p>Текст один.</p></body></html>"
    second = epub.EpubHtml(title="a", file_name="a_first.xhtml", lang="ru")
    second.content = (
        "<html><body><h3>Глава</h3><p>Текст два <a href='n.xhtml'>[1]</a>.</p></body></html>"
    )
    book.add_item(first)
    book.add_item(second)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", first, second]
    epub.write_epub(path, book)


def test_parse_volume_no() -> None:
    assert parse_volume_no("Толстой Л.Н-Том 1..epub") == 1
    assert parse_volume_no("Толстой Л.Н-Том 22..epub") == 22
    assert parse_volume_no("something-else.epub") is None


def test_spine_order_not_filename_order(tmp_path) -> None:
    path = str(tmp_path / "test.epub")
    _make_epub(path)
    volume = read_volume(path)
    assert [section.href.split("/")[-1] for section in volume.sections] == [
        "z_last.xhtml",
        "a_first.xhtml",
    ]
    assert volume.sections[0].headings[0].text == "Работа"
    assert volume.sections[1].links == [{"href": "n.xhtml", "text": "[1]"}]


@needs_vol1
def test_vol1_metadata() -> None:
    volume = read_volume(VOL1)
    assert volume.volume_no == 1
    assert volume.creator == "Лев Николаевич Толстой"
    assert volume.language == "ru"
    assert volume.publisher == "Художественная литература"
    assert volume.pub_year == "1978"
    assert len(volume.sections) > 300  # 361 spine items minus drops


@needs_vol1
def test_vol1_chapter_section() -> None:
    volume = read_volume(VOL1)
    by_href = {section.href: section for section in volume.sections}
    section = by_href["Text/section4.xhtml"]
    assert [heading.text for heading in section.headings] == [
        "Глава I",
        "Учитель Карл Иваныч",
    ]
    assert len(section.paragraphs) == 23
    assert any(link["text"].startswith("[") for link in section.links)


@needs_vol1
def test_vol1_drops_cover_title_annotation() -> None:
    volume = read_volume(VOL1)
    idrefs = {section.idref for section in volume.sections}
    assert idrefs.isdisjoint(DROP_IDREFS)
