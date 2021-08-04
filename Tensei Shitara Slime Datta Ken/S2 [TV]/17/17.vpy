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

OP: Optional[int] = 552

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 552),
    Chapter("Part A", 2710),
    Chapter("Part B", 18678),
    Chapter("ED", 31769),
    Chapter("Next", 33927),
]

DEHARDSUB: List[HardsubMask] = [
    HardsubASS("./ger.ass"),
]

GEBBI_PLS: List[Range] = [
    (28458, 28565),
]

NOD3: List[Range] = [
    (3393, 3659),
    (4761, 5282),
    (5349, 6038),
]

if OP is not None:
    NOD3 += [
        (OP+1520, OP+1576)
    ]

NODEN: List[Range] = [
    (33927, None),
]

if OP is not None:
    NODEN += [
        (OP+1385, OP+1519)
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
