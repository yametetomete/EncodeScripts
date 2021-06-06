import vapoursynth as vs

from tensura_common import (TenSuraS2Config, TenSuraS2BDSource, antialias, deband,
                            denoise, descale, edgefix, finalize, regrain)

from yt_common.automation import SelfRunner
from yt_common.chapters import Chapter
from yt_common.source import FileTrim
from yt_common.video import Zone

from lvsfunc.mask import BoundingBox
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

from typing import List, Tuple

import os

EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: TenSuraS2Config = TenSuraS2Config(EPNUM)
BDMV: str = "../bdmv/[BDMV][210326][Tensei Shitara Slime Datta Ken 2nd Season][Vol.1]/BDMV/STREAM"
SOURCE: TenSuraS2BDSource = TenSuraS2BDSource(
    FileTrim(os.path.join(BDMV, "00010.m2ts"), (None, -24))
)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 2086),
    Chapter("Part A", 4245),
    Chapter("Part B", 13141),
    Chapter("ED", 31770),
    Chapter("Next", 33928),
]

NOD3: List[Range] = [
    (33928, 34047),
]

AA_STRONG: List[Range] = [
]

SANGNOM: List[Tuple[Range, List[BoundingBox]]] = [
    ((11212, 11301), [
        BoundingBox((463, 945), (223, 135)),
        BoundingBox((932, 1052), (33, 28)),
        BoundingBox((0, 0), (346, 272)),
        BoundingBox((529, 758), (72, 42)),
        BoundingBox((503, 569), (81, 54)),
    ]),
    ((14864, 14924), [
        BoundingBox((36, 805), (670, 225)),
        BoundingBox((1028, 899), (109, 143)),
        BoundingBox((1280, 817), (640, 174)),
    ]),
    ((16570, 16790), [
        BoundingBox((836, 873), (46, 188)),
    ]),
]

DEBAND_NUCLEAR: List[Range] = [
]

core = vs.core


def filter() -> vs.VideoNode:
    src = SOURCE.source()
    ef = edgefix(src)
    den = denoise(ef)
    descaled = descale(den)
    deb = deband(descaled, nuclear=DEBAND_NUCLEAR)
    deb = replace_ranges(deb, src, NOD3)
    aa = antialias(deb, strong=AA_STRONG, sangnom=SANGNOM)
    grain = regrain(aa)
    final = finalize(grain)
    src.set_output(1)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, chapters=CHAPTERS)
else:
    filter()
