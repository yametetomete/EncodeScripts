import vapoursynth as vs

from tensura_common import TenSuraS2BDConfig, antialias, deband, denoise, descale, edgefix, finalize, regrain

from yt_common.automation import SelfRunner
from yt_common.chapters import Chapter
from yt_common.source import FileTrim, SimpleSource

from lvsfunc.mask import BoundingBox
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

from typing import List, Tuple

import os

EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: TenSuraS2BDConfig = TenSuraS2BDConfig(EPNUM)
BDMV: str = "../bdmv/[BDMV][210526][Tensei Shitara Slime Datta Ken 2nd Season][Vol.2]/BDMV/STREAM"
SOURCE: SimpleSource = SimpleSource(
    FileTrim(os.path.join(BDMV, "00008.m2ts"), (None, -50))
)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 384),
    Chapter("Part A", 2542),
    Chapter("Part B", 17766),
    Chapter("ED", 31768),
    Chapter("Next", 33926),
]

NOD3: List[Range] = [
    (33926, 34045),
]

AA_STRONG: List[Range] = [
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
    SelfRunner(CONFIG, SOURCE, filter, chapters=CHAPTERS)
else:
    filter()
