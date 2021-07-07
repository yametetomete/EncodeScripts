import vapoursynth as vs

from tensura_common import (TenSuraS2Config, TenSuraS2AODSource, antialias, deband,
                            dehalo, denoise, descale, edgefix, finalize, regrain)

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

OP: Optional[int] = 3189

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 3189),
    Chapter("Part A", 5347),
    Chapter("Part B", 17646),
    Chapter("ED", 31768),
    Chapter("Next", 33926),
]

DEHARDSUB: List[HardsubMask] = [
    HardsubASS("./ger.ass"),
]

NOD3: List[Range] = [
    (2261, 2452),
    (2481, 2816),
    (26614, 26733),
    (33926, None),
]

if OP is not None:
    NOD3 += [
        (OP+1520, OP+1576)
    ]

NODEN: List[Range] = [
]

if OP is not None:
    NODEN += [
        (OP+1385, OP+1519)
    ]

ZONES: List[Zone] = [
]

ZONES += [Zone(r, 0.75) for r in normalize_ranges(SOURCE.source(), NOD3 + NODEN)]

AA_STRONG: List[Range] = [
    (29341, 29406),
    (29698, 29829),
    (30089, 30206),
]

SANGNOM: List[Tuple[Range, List[BoundingBox]]] = [
]

core = vs.core


def filter() -> vs.VideoNode:
    aod, ref = SOURCE.dhs_source()
    src = bounded_dehardsub(aod[0], ref, DEHARDSUB)
    ef = edgefix(src)
    den = denoise(ef)
    den = replace_ranges(den, src, NODEN)
    descaled = descale(den)
    deb = deband(descaled)
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
    SelfRunner(CONFIG, SOURCE, filter, chapters=CHAPTERS, zones=ZONES)
else:
    filter()
