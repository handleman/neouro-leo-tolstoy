"""EPUB reader: OPF spine order + XHTML extraction (0002 contract).

Reads volumes in OPF spine order (never filename order). Per spine item
extracts headings (h1/h2/h3) and paragraph text (inline markup flattened
to plain text). Drops non-content items (cover, title page, annotation,
images, fonts, CSS). Footnote links are recorded as markers; note bodies
are handled downstream by clean.py (sidecars, never inlined).
"""

import re
from dataclasses import dataclass, field

import ebooklib.epub as epub
from lxml import etree

XHTML_NS = {"x": "http://www.w3.org/1999/xhtml"}
XHTML_MIME = "application/xhtml+xml"

#: Spine idrefs that never hold prose (FB2-converted layout, cf. Vol. 1).
DROP_IDREFS = {"cover", "title", "annotation", "nav", "ncx"}

VOLUME_NO_RE = re.compile(r"[Тт]ом\s*(\d+)")


@dataclass
class Heading:
    level: str  # h1 | h2 | h3
    text: str


@dataclass
class SectionRaw:
    spine_index: int
    idref: str
    href: str
    headings: list[Heading] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)  # [{href, text}] footnote markers


@dataclass
class VolumeRaw:
    path: str
    filename: str
    volume_no: int | None  # parsed from filename; cross-checked vs OPF title
    titles: list[str]  # dc:title values in order
    creator: str
    language: str
    publisher: str
    pub_year: str
    sections: list[SectionRaw] = field(default_factory=list)


def _text(element: etree._Element) -> str:
    return "".join(element.itertext())


def _meta(book: epub.EpubBook, name: str) -> list[str]:
    return [value for value, _attrs in book.get_metadata("DC", name)]


def parse_volume_no(filename: str) -> int | None:
    match = VOLUME_NO_RE.search(filename)
    return int(match.group(1)) if match else None


def read_volume(path: str) -> VolumeRaw:
    """Parse one EPUB file into raw sections in spine order."""
    import os

    book = epub.read_epub(path)
    filename = os.path.basename(path)
    volume_no = parse_volume_no(filename)

    titles = _meta(book, "title")
    creators = _meta(book, "creator")
    languages = _meta(book, "language")
    publishers = _meta(book, "publisher")
    dates = [
        value
        for value, attrs in book.get_metadata("DC", "date")
        if attrs.get("{http://www.idpf.org/2007/opf}event") == "original-publication"
    ]

    volume = VolumeRaw(
        path=path,
        filename=filename,
        volume_no=volume_no,
        titles=titles,
        creator=creators[0] if creators else "",
        language=languages[0] if languages else "",
        publisher=publishers[0] if publishers else "",
        pub_year=dates[0] if dates else "",
    )

    for spine_index, (idref, _linear) in enumerate(book.spine):
        if idref in DROP_IDREFS:
            continue
        item = book.get_item_with_id(idref)
        if item is None or item.media_type != XHTML_MIME:
            continue
        root = etree.fromstring(item.get_content())
        section = SectionRaw(spine_index=spine_index, idref=idref, href=item.get_name())
        for node in root.xpath("//x:h1|//x:h2|//x:h3", namespaces=XHTML_NS):
            text = re.sub(r"\s+", " ", _text(node)).strip()
            if text:
                section.headings.append(Heading(level=node.tag.split("}")[1], text=text))
        for node in root.xpath("//x:p", namespaces=XHTML_NS):
            section.paragraphs.append(_text(node))
        for node in root.xpath("//x:a[@href]", namespaces=XHTML_NS):
            section.links.append({"href": node.get("href"), "text": _text(node).strip()})
        volume.sections.append(section)
    return volume
