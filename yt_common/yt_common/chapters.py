from lxml import etree
from lxml.etree import _Element

from random import getrandbits

from typing import Dict, List, NamedTuple, Optional, Set

LANGMAP: Dict[str, str] = {
    "eng": "en",
    "und": "und",
    "jpn": "ja",
}


class Chapter(NamedTuple):
    title: str
    frame: int
    end_frame: Optional[int] = None
    lang: str = "eng"


class Edition(NamedTuple):
    chapters: List[Chapter]
    default: bool = False
    ordered: bool = False


class RandMan:
    used: Set[int]

    def __init__(self) -> None:
        self.used = set()

    def get_rand(self, bits: int = 64) -> str:
        r = getrandbits(bits)
        while r in self.used:
            r = getrandbits(bits)
        self.used.add(r)
        return str(r)


rand = RandMan()


def timecode_to_timestamp(stamp: float) -> str:
    m = int(stamp // 60)
    stamp %= 60
    h = int(m // 60)
    m %= 60
    return f"{h:02d}:{m:02d}:{stamp:06.3f}000000"


def chapters_xml(chapters: List[Chapter], timecodes: List[float]) -> List[_Element]:
    atoms: List[_Element] = []

    for i, c in enumerate(chapters):
        start = timecode_to_timestamp(timecodes[c.frame])
        end = timecode_to_timestamp(timecodes[c.end_frame]) if c.end_frame else \
            timecode_to_timestamp(timecodes[chapters[i+1].frame]) if i < len(chapters) - 1 \
            else None
        atom = etree.Element("ChapterAtom")
        etree.SubElement(atom, "ChapterTimeStart").text = start
        if end is not None:
            etree.SubElement(atom, "ChapterTimeEnd").text = end
        disp = etree.SubElement(atom, "ChapterDisplay")
        etree.SubElement(disp, "ChapterString").text = c.title
        etree.SubElement(disp, "ChapLanguageIETF").text = LANGMAP[c.lang]
        etree.SubElement(disp, "ChapterLanguage").text = c.lang
        etree.SubElement(atom, "ChapterUID").text = rand.get_rand()
        atoms.append(atom)

    return atoms


def edition_xml(edition: Edition, timecodes: List[float]) -> _Element:
    ed = etree.Element("EditionEntry")
    etree.SubElement(ed, "EditionFlagOrdered").text = "1" if edition.ordered else "0"
    etree.SubElement(ed, "EditionUID").text = rand.get_rand()
    etree.SubElement(ed, "EditionFlagDefault").text = "1" if edition.default else "0"

    for x in chapters_xml(edition.chapters, timecodes):
        ed.append(x)

    return ed


def _to_edition(chapters: Optional[List[Chapter]] = None,
                editions: Optional[List[Edition]] = None) -> List[Edition]:
    if (chapters and editions) or (not chapters and not editions):
        raise ValueError("Must supply one and only one of a list of chapters or list of editions!")

    if chapters:
        editions = [Edition(chapters=chapters, default=True, ordered=False)]

    assert editions is not None
    return editions


def make_chapters(timecodes: List[float], outfile: str,
                  chapters: Optional[List[Chapter]] = None,
                  editions: Optional[List[Edition]] = None) -> None:
    editions = _to_edition(chapters=chapters, editions=editions)
    root = etree.Element("Chapters")
    for e in editions:
        root.append(edition_xml(e, timecodes))

    with open(outfile, "wb") as o:
        o.write(etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True))


def make_qpfile(qpfile: str,
                chapters: Optional[List[Chapter]] = None,
                editions: Optional[List[Edition]] = None) -> None:
    editions = _to_edition(chapters=chapters, editions=editions)
    frames = set(c.frame for e in editions for c in e.chapters)
    with open(qpfile, "w", encoding="utf-8") as qp:
        qp.writelines([f"{f} I\n" for f in sorted(list(frames))])
