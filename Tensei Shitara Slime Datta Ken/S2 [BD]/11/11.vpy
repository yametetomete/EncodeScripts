import vapoursynth as vs

from tensura_common import TenSuraS2BDConfig, antialias, deband, denoise, descale, edgefix, finalize, regrain

from yt_common.automation import SelfRunner, Zone
from yt_common.chapters import Chapter, Edition
from yt_common.source import FileTrim, SimpleSource

from lvsfunc.mask import BoundingBox
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

from typing import List, Tuple

import os

EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: TenSuraS2BDConfig = TenSuraS2BDConfig(EPNUM)
BDMV: str = "../bdmv/[BDMV][210526][Tensei Shitara Slime Datta Ken 2nd Season][Vol.2]/BDMV/STREAM"
SOURCE: SimpleSource = SimpleSource([
    FileTrim(os.path.join(BDMV, "00011.m2ts"), (None, -49)),
    FileTrim(os.path.join(BDMV, "00017.m2ts"), (None, 3158)),
    FileTrim(os.path.join(BDMV, "00017.m2ts"), (33342, 33927)),
], asrc=[
    # NC version has different (quieter) audio, so make sure we use the regular version
    FileTrim(os.path.join(BDMV, "00011.m2ts"), (None, -49)),
    FileTrim(os.path.join(BDMV, "00011.m2ts"), (None, 3158)),
    FileTrim(os.path.join(BDMV, "00011.m2ts"), (33342, 33927)),
])

EDITIONS: List[Edition] = [
    Edition(chapters=[
        Chapter("Intro", 0),
        Chapter("Part A", 840),
        Chapter("Part B", 13980),
        Chapter("Next", 33927, 34047),
    ], default=True, ordered=True),
    Edition(chapters=[
        Chapter("Intro - NC", 34047),
        Chapter("Part A - NC", 34887, 37205),
        Chapter("Part A", 3158),
        Chapter("Part B", 13980, 33342),
        Chapter("Part B - NC", 37205, -1),
        Chapter("Next", 33927, 34047),
    ], default=False, ordered=True),
]

NOD3: List[Range] = [
    (4862, 5023),
    (8264, 8692),
    (10200, 10576),
    (17993, 18828),
    (33927, 34046),
]

NODEN: List[Range] = [
    (16484, 17992),
    (18829, 19528),
]

ZONES: List[Zone] = [
]

ZONES += [Zone(r, 0.75) for r in NOD3 + NODEN if isinstance(r, tuple)]

AA_STRONG: List[Range] = [
    (14544, 14588),
    (14716, 14763),
    (15493, 15633),
    (19529, 19600),
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
    replace_ranges(den, src, NODEN)
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
    SelfRunner(CONFIG, SOURCE, filter, editions=EDITIONS, zones=ZONES)
else:
    filter()
