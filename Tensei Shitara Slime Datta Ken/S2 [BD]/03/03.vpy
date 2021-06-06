import vapoursynth as vs

from tensura_common import (TenSuraS2Config, TenSuraS2BDSource, antialias, deband,
                            denoise, descale, edgefix, finalize, regrain)

from yt_common.automation import SelfRunner
from yt_common.chapters import Chapter
from yt_common.source import FileTrim
from yt_common.video import Zone

from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

from typing import List

import os

EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: TenSuraS2Config = TenSuraS2Config(EPNUM)
BDMV: str = "../bdmv/[BDMV][210326][Tensei Shitara Slime Datta Ken 2nd Season][Vol.1]/BDMV/STREAM"
SOURCE: TenSuraS2BDSource = TenSuraS2BDSource(
    FileTrim(os.path.join(BDMV, "00008.m2ts"), (None, -50))
)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 336),
    Chapter("Part A", 2494),
    Chapter("Part B", 18198),
    Chapter("ED", 31768),
    Chapter("Next", 33926),
]

NOD3: List[Range] = [
    (8023, 8205),
    (33926, 34045),
]

ZONES: List[Zone] = [
]

ZONES += [Zone(r, 0.75) for r in NOD3 if isinstance(r, tuple)]

AA_STRONG: List[Range] = [
    (3084, 3125),
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
    aa = antialias(deb, strong=AA_STRONG)
    grain = regrain(aa)
    final = finalize(grain)
    src.set_output(1)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, chapters=CHAPTERS, zones=ZONES)
else:
    filter()
