import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix, regrain)

from yt_common.automation import SelfRunner
from yt_common.denoise import bm3d
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubLine, HardsubLineFade, HardsubSign, HardsubSignFade, HardsubMask, bounded_dehardsub
from lvsfunc.misc import replace_ranges
from vardefunc import dumb3kdb

from typing import List

import os

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

WAKA_REPLACE: List[List[Range]] = [
    [(31528, 32857)],
    [],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubSignFade([
        (2834, 2941),
        (16031, 16035),
    ]),
    HardsubSignFade([
        (33949, 34045),
    ], refframe=1, expand=9),
    HardsubSignFade([
        (21060, 21113),
    ], refframe=0),
    HardsubSignFade([
        (21107, 21132),
    ], refframe=1),
    HardsubSign([
        (7079, 7111),
    ]),
    HardsubLineFade([
        (21508, 21572),
    ]),
    HardsubLine([
        (961, 1106),
        (1111, 1252),
        (1265, 1408),
        (1414, 1502),
        (1509, 1578),
        (1583, 1657),
        (1663, 1815),
        (1862, 2006),
        (2011, 2079),
        (2084, 2171),
        (2179, 2309),
        (2313, 2382),
        (2387, 2486),
        (2491, 2556),
        (2570, 2686),
        (12150, 12261),
        (12279, 12403),
        (12413, 12525),
        (12530, 12633),
        (12637, 12783),
        (12789, 12891),
        (12896, 13049),
        (13054, 13116),
        (13121, 13255),
        (14930, 14990),
    ], ((283, 844), (1349, 204))),
]
NOSCALE: List[Range] = []
AA_NONE: List[Range] = [
    (14413, 14422),
    (15428, 15431),
]
AA_STRONGER: List[Range] = [
    (11972, 12080),
]
DB_WEAK: List[Range] = [
    (0, 579),
]

LETTERBOX: List[Range] = []


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.dhs_source()
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    src = bounded_dehardsub(waka, ref, SIGNS_RU, wakas)
    src.set_output(1)
    return src


def filter() -> vs.VideoNode:
    src = filter_basic()
    rescale = fsrcnnx_rescale(src, NOSCALE)
    den = denoise(rescale)
    deb = deband(den)
    den2 = bm3d(rescale, sigma=4, radius=1)
    deb2 = dumb3kdb(den2, radius=16, threshold=24)
    deb = replace_ranges(deb, deb2, DB_WEAK)
    aa = antialias(deb, stronger=AA_STRONGER, noaa=AA_NONE)
    grain = regrain(aa)
    edgefix = letterbox_edgefix(grain, LETTERBOX)
    final = finalize(edgefix)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, filter_basic)
else:
    filter()
