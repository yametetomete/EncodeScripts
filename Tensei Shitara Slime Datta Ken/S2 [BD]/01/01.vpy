import vapoursynth as vs

from tensura_common import (TenSuraS2Config, TenSuraS2BDSource, antialias, deband,
                            denoise, descale, edgefix, finalize, regrain)

from yt_common.automation import SelfRunner, Zone
from yt_common.chapters import Chapter
from yt_common.source import FileTrim

from lvsfunc.mask import BoundingBox
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

from typing import List, Tuple

import os

EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: TenSuraS2Config = TenSuraS2Config(EPNUM)
BDMV: str = "../bdmv/[BDMV][210326][Tensei Shitara Slime Datta Ken 2nd Season][Vol.1]/BDMV/STREAM"
SOURCE: TenSuraS2BDSource = TenSuraS2BDSource(
    FileTrim(os.path.join(BDMV, "00006.m2ts"), (24, -50))
)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 6570),
    Chapter("Part A", 8726),
    Chapter("Part B", 21123),
    Chapter("ED", 31768),
    Chapter("Next", 33926),
]

NOD3: List[Range] = [
    (3885, 5948),
    (33926, 34045),
]

ZONES: List[Zone] = [
]

ZONES += [Zone(r, 0.75) for r in NOD3 if isinstance(r, tuple)]

AA_STRONG: List[Range] = [
    (15605, 15772),
]

SANGNOM: List[Tuple[Range, List[BoundingBox]]] = [
    ((25514, 25515), [
        BoundingBox((68, 0), (366, 622)),
    ]),
    (25516, [
        BoundingBox((126, 0), (340, 646)),
    ]),
    (25517, [
        BoundingBox((35, 0), (352, 617)),
    ]),
    (25518, [
        BoundingBox((84, 0), (353, 613)),
    ]),
    (25519, [
        BoundingBox((98, 0), (348, 642)),
    ]),
    (25520, [
        BoundingBox((70, 0), (351, 632)),
    ]),
    (25521, [
        BoundingBox((69, 0), (367, 616)),
    ]),
    (25522, [
        BoundingBox((84, 0), (367, 620)),
    ]),
    ((25523, 25780), [
        BoundingBox((75, 0), (359, 615)),
    ]),
]

core = vs.core


def filter() -> vs.VideoNode:
    src = SOURCE.source()
    ef = edgefix(src)
    den = denoise(ef)
    descaled = descale(den)
    deb = deband(descaled)
    deb = replace_ranges(deb, src, NOD3)
    aa = antialias(deb, strong=AA_STRONG, sangnom=SANGNOM)
    grain = regrain(aa)
    final = finalize(grain)
    src.set_output(1)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, chapters=CHAPTERS, zones=ZONES)
else:
    filter()
