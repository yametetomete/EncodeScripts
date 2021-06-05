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
    FileTrim(os.path.join(BDMV, "00011.m2ts"), (24, -25))
)

CHAPTERS: List[Chapter] = [
    Chapter("OP", 0),
    Chapter("Part A", 2159),
    Chapter("Part B", 17311),
    Chapter("ED", 31769),
    Chapter("Next", 33927),
]

NOD3: List[Range] = [
    (8552, 8779),
    (28796, 29188),
    (33927, 34046),
]

ZONES: List[Zone] = [
]

ZONES += [Zone(r, 0.75) for r in NOD3 if isinstance(r, tuple)]

AA_STRONG: List[Range] = [
    (11640, 11685),
    (12437, 12488),
    (12745, 12754),
    (12959, 13129),
    (13130, 13193),
    (13432, 13479),
    (13662, 13700),
    (13845, 13915),
    (14619, 14642),
    (14779, 14801),
]

SANGNOM: List[Tuple[Range, List[BoundingBox]]] = [
    ((2159, 2206), [
        BoundingBox((0, 945), (1218, 135)),
    ]),
    ((7269, 7360), [
        BoundingBox((714, 481), (24, 44)),
    ]),
    ((11640, 11685), [
        BoundingBox((1449, 53), (471, 224)),
    ]),
    ((14490, 14522), [
        BoundingBox((0, 794), (1920, 170)),
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
    SelfRunner(CONFIG, SOURCE, filter, chapters=CHAPTERS, zones=ZONES)
else:
    filter()
