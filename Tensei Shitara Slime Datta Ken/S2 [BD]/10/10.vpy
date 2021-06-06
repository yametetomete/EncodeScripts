import vapoursynth as vs

from tensura_common import (TenSuraS2Config, TenSuraS2BDSource, antialias, deband,
                            denoise, descale, edgefix, finalize, regrain)

from yt_common.automation import SelfRunner
from yt_common.chapters import Chapter, Edition
from yt_common.source import FileTrim
from yt_common.video import Zone

from lvsfunc.mask import BoundingBox
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

from typing import List, Tuple

import os

EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: TenSuraS2Config = TenSuraS2Config(EPNUM)
BDMV: str = "../bdmv/[BDMV][210526][Tensei Shitara Slime Datta Ken 2nd Season][Vol.2]/BDMV/STREAM"
SOURCE: TenSuraS2BDSource = TenSuraS2BDSource([
    FileTrim(os.path.join(BDMV, "00009.m2ts"), (None, None)),
    FileTrim(os.path.join(BDMV, "00010.m2ts"), (None, -49)),
    FileTrim(os.path.join(BDMV, "00016.m2ts"), (13348, 15699)),
    FileTrim(os.path.join(BDMV, "00016.m2ts"), (17721, 17982)),
], asrc=[
    # NC version has different (quieter) audio, so make sure we use the regular version
    FileTrim(os.path.join(BDMV, "00009.m2ts"), (None, None)),
    FileTrim(os.path.join(BDMV, "00010.m2ts"), (None, -49)),
    FileTrim(os.path.join(BDMV, "00010.m2ts"), (13348, 15699)),
    FileTrim(os.path.join(BDMV, "00010.m2ts"), (17721, 17982)),
])

EDITIONS: List[Edition] = [
    Edition(chapters=[
        Chapter("Intro", 0),
        Chapter("OP", 2134),
        Chapter("Part A", 4293),
        Chapter("Part B", 16065),
        Chapter("Next", 34047, 34167),
    ], default=True, ordered=True),
    Edition(chapters=[
        Chapter("Intro", 0),
        Chapter("OP", 2134),
        Chapter("Part A", 4293),
        Chapter("Part B", 16065, 29413),
        Chapter("Part B - NC", 34167, 36518),
        Chapter("Part B", 31764, 33786),
        Chapter("Part B - NC", 36518, -1),
        Chapter("Next", 34047, 34167),
    ], default=False, ordered=True),
]

NOD3: List[Range] = [
    (34047, 34166),
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
    SelfRunner(CONFIG, SOURCE, filter, editions=EDITIONS)
else:
    filter()
