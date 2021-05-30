from lxml import etree
from random import getrandbits

from typing import Dict, List, NamedTuple, Set

LANGMAP: Dict[str, str] = {
    "eng": "en",
    "und": "und",
    "jpn": "ja",
}


class Chapter(NamedTuple):
    title: str
    frame: int
    lang: str = "eng"


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


def timecode_to_timestamp(stamp: float) -> str:
    m = int(stamp // 60)
    stamp %= 60
    h = int(m // 60)
    m %= 60
    return f"{h:02d}:{m:02d}:{stamp:06.3f}000000"


def make_chapters(chapters: List[Chapter], timecodes: List[float], outfile: str) -> None:
    chapters.sort(key=lambda c: c.frame)
    rand = RandMan()

    root = etree.Element("Chapters")
    ed = etree.SubElement(root, "EditionEntry")
    etree.SubElement(ed, "EditionUID").text = rand.get_rand()

    for i, c in enumerate(chapters):
        start = timecode_to_timestamp(timecodes[c.frame])
        end = timecode_to_timestamp(timecodes[chapters[i+1].frame]) if i < len(chapters) - 1 else None
        atom = etree.SubElement(ed, "ChapterAtom")
        etree.SubElement(atom, "ChapterTimeStart").text = start
        if end is not None:
            etree.SubElement(atom, "ChapterTimeEnd").text = end
        disp = etree.SubElement(atom, "ChapterDisplay")
        etree.SubElement(disp, "ChapterString").text = c.title
        etree.SubElement(disp, "ChapLanguageIETF").text = LANGMAP[c.lang]
        etree.SubElement(disp, "ChapterLanguage").text = c.lang
        etree.SubElement(atom, "ChapterUID").text = rand.get_rand()

    with open(outfile, "wb") as o:
        o.write(etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True))
