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
BDMV: str = "../bdmv/[BDMV][210526][Tensei Shitara Slime Datta Ken 2nd Season][Vol.2]/BDMV/STREAM"
SOURCE: TenSuraS2BDSource = TenSuraS2BDSource(
    FileTrim(os.path.join(BDMV, "00007.m2ts"), (None, -51))
)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 3237),
    Chapter("Part A", 5395),
    Chapter("Part B", 16255),
    Chapter("ED", 31767),
    Chapter("Next", 33925),
]

NOD3: List[Range] = [
    (20345, 20471),
    (23716, 23971),
    (26714, 26869),
    (33925, 34044),
]

ZONES: List[Zone] = [
]

ZONES += [Zone(r, 0.75) for r in NOD3 if isinstance(r, tuple)]

AA_STRONG: List[Range] = [
    (8606, 8677),
    (26138, 26245),
]

SANGNOM: List[Tuple[Range, List[BoundingBox]]] = [
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
