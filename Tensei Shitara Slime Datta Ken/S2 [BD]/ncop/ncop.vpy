import vapoursynth as vs

from tensura_common import (TenSuraS2Config, TenSuraS2BDSource, antialias, deband,
                            denoise, descale, edgefix, finalize, regrain)

from yt_common.automation import SelfRunner
from yt_common.source import FileTrim

from lvsfunc.mask import BoundingBox
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

from typing import List, Tuple

import os

DESC: str = os.path.basename(os.path.splitext(__file__)[0])
CONFIG: TenSuraS2Config = TenSuraS2Config(DESC)
BDMV: str = "../bdmv/[BDMV][210526][Tensei Shitara Slime Datta Ken 2nd Season][Vol.2]/BDMV/STREAM"
SOURCE: TenSuraS2BDSource = TenSuraS2BDSource(
    FileTrim(os.path.join(BDMV, "00014.m2ts"), (24, -24))
)

NOD3: List[Range] = [
]

NODEN: List[Range] = [
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
    den = replace_ranges(den, src, NODEN)
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
    SelfRunner(CONFIG, SOURCE, filter)
else:
    filter()
