import vapoursynth as vs

from tensura_common import (TenSuraS2Config, TenSuraS2Source, antialias, denoise, descale,
                            edgefix, finalize)
from tensura_common.filter import deband_tv as deband
from tensura_common.filter import regrain_tv as regrain

from yt_common.automation import SelfRunner
from yt_common.chapters import Chapter
from yt_common.source import FileTrim
from yt_common.video import Zone

from lvsfunc.mask import BoundingBox
from lvsfunc.types import Range
from lvsfunc.util import replace_ranges, normalize_ranges

from typing import List, Tuple

import os

DESC: str = os.path.basename(os.path.splitext(__file__)[0])
CONFIG: TenSuraS2Config = TenSuraS2Config(DESC)
SOURCE: TenSuraS2Source = TenSuraS2Source(
    FileTrim("./[SubsPlease] Tensei Shitara Slime Datta Ken - 36.5 (1080p) [9BF24474].mkv", (24, -24))
)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 960),
    Chapter("Part A", 3117),
    Chapter("Part B", 17407),
    Chapter("ED", 31889),
]

NOD3: List[Range] = [
    (10996, 11109),
    (17888, 20235),
    (25247, 25611),
]

NODEN: List[Range] = [
    (20236, 20920),
]

ZONES: List[Zone] = [
]

ZONES += [Zone(r, 0.75) for r in normalize_ranges(SOURCE.source(), NOD3 + NODEN)]

AA_STRONG: List[Range] = [
    (6071, 6123),
]

SANGNOM: List[Tuple[Range, List[BoundingBox]]] = [
]

core = vs.core


def filter() -> vs.VideoNode:
    src = SOURCE.source()
    ef = edgefix(src)
    den = denoise(ef)
    den = replace_ranges(den, src, NODEN)
    descaled = descale(den)
    deb = deband(descaled)
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
