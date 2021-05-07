import vapoursynth as vs

from tanteidan_common import (PrettyConfig, PrettySource, antialias, deband,
                              denoise, finalize, regrain, stupid_op_scenefilter,
                              wd_scenefilter)

from yt_common.automation import SelfRunner
from yt_common.denoise import bm3d
from yt_common.source import waka_replace

from typing import List, Optional

from lvsfunc.dehardsub import HardsubSign, HardsubSignFade, HardsubMask, bounded_dehardsub
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

import os


core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: PrettyConfig = PrettyConfig(EPNUM)
SOURCE: PrettySource = PrettySource(CONFIG)

OP: Optional[int] = 0
WELCOMING_DAYS: Optional[int] = None

WAKA_REPLACE: List[List[Range]] = [
    [(31864, 32650)],
    [],
]

TITLECARDS: List[Range] = [
    (2609, 2704),
    (5174, 5221),
    (5738, 5773),
    (5774, 5809),
    (6920, 6967),
    (9209, 9256),
    (10223, 10270),
    (11375, 11434),
    (11627, 11674),
    (12806, 12853),
    (14649, 14732),
    (16431, 16478),
    (19516, 19563),
    (24622, 24669),
    (25618, 25665),
    (27691, 27738),
    (29957, 30004),
]

SIGNS_RU: List[HardsubMask] = [
    HardsubSignFade(TITLECARDS + [
        (2158, 2298),
        (31751, 31863),
        (5666, 5683),
        (5684, 5701),
        (5702, 5737),
        (6722, 6763),
        (6764, 6811),
        (10715, 10757),
        (12026, 12115),
        (12566, 12631),
        (12632, 12683),
        (20821, 20919),
        (20920, 21039),
    ]),
    HardsubSign([
        (2327, 2608),
    ]),
]

AA_STRONGER: List[Range] = [
    (15231, 15338),  # this fucking plant what the hell
]

AA_STRONG: List[Range] = [
]

AA_WEAK: List[Range] = [
    (13814, 14518),
]

AA_NONE: List[Range] = TITLECARDS + [  # chapter 2 title cards are insanely detailed
    (20821, 21039),
]

STUPID_DENOISE: List[Range] = [
    (11435, 11626),
    (12026, 12115),
]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.source()
    wakas = [w[0] + w for w in wakas]
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    src = bounded_dehardsub(waka, ref, SIGNS_RU, wakas)
    src.set_output(1)
    return src


def filter() -> vs.VideoNode:
    src = filter_basic()
    den = denoise(src)
    deb = deband(den)
    deb = replace_ranges(deb, bm3d(src, sigma=4, radius=1), STUPID_DENOISE)
    aa = antialias(deb, stronger=AA_STRONGER, strong=AA_STRONG, weak=AA_WEAK, noaa=AA_NONE)
    scenefilter = stupid_op_scenefilter(aa, deb, OP)
    if WELCOMING_DAYS is not None:
        scenefilter = wd_scenefilter(aa, deb, WELCOMING_DAYS)
    grain = regrain(scenefilter)
    final = finalize(grain)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, filter, filter_basic)
else:
    filter()
