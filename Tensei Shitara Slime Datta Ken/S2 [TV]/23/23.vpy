import vapoursynth as vs

from tensura_common import (TenSuraS2Config, TenSuraS2AODSource, antialias, cr_prefilter,
                            deband, dehalo, denoise, edgefix, finalize, regrain)

from yt_common.automation import SelfRunner
from yt_common.chapters import Chapter
from yt_common.video import Zone

from lvsfunc.mask import BoundingBox
from lvsfunc.dehardsub import HardsubASS, HardsubMask, bounded_dehardsub
from lvsfunc.types import Range
from lvsfunc.util import replace_ranges, normalize_ranges

from typing import List, Optional, Tuple

import os

DESC: str = os.path.basename(os.path.splitext(__file__)[0])
CONFIG: TenSuraS2Config = TenSuraS2Config(DESC)
SOURCE: TenSuraS2AODSource = TenSuraS2AODSource(CONFIG, [(24, -24)])

OP: Optional[int] = 0

CHAPTERS: List[Chapter] = [
    Chapter("OP", 0),
    Chapter("Part A", 2158),
    Chapter("Part B", 17023),
    Chapter("Next", 33925),
]

DEHARDSUB: List[HardsubMask] = [
    HardsubASS("./ger.ass"),
]

GEBBI_PLS: List[Range] = [
]

NOD3: List[Range] = [
]

NODEN: List[Range] = [
    (33925, None),
]

ZONES: List[Zone] = [
]

ZONES += [Zone(r, 0.75) for r in normalize_ranges(SOURCE.source(), NOD3 + NODEN)]

AA_STRONG: List[Range] = [
]

SANGNOM: List[Tuple[Range, List[BoundingBox]]] = [
]

core = vs.core


def filter_basic() -> vs.VideoNode:
    aod, ref = SOURCE.dhs_source()
    return finalize(bounded_dehardsub(aod[0], ref, DEHARDSUB))


def filter() -> vs.VideoNode:
    aod, ref = SOURCE.dhs_source()
    pre = cr_prefilter(ref)
    src = bounded_dehardsub(aod[0], pre, DEHARDSUB)
    src = replace_ranges(src, pre, GEBBI_PLS)
    ef = edgefix(src)
    den = denoise(ef)
    den = replace_ranges(den, src, NODEN)
    deb = deband(den)
    deb = replace_ranges(deb, src, NOD3)
    aa = antialias(deb, strong=AA_STRONG, sangnom=SANGNOM)
    dh = dehalo(aa)
    dh = replace_ranges(dh, aa, NOD3 + NODEN)
    grain = regrain(dh)
    final = finalize(grain)
    src.set_output(1)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, filter_basic, chapters=CHAPTERS, zones=ZONES)
else:
    filter()
