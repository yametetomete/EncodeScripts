import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix, regrain)

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubLineFade, HardsubLine, HardsubSignFade, HardsubMask, bounded_dehardsub
from vsutil import Range as CRange

from typing import List

import os

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

WAKA_REPLACE: List[List[Range]] = [
    [],
    [],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubLine([
        (1878, 2034),
        (2045, 2230),
        (2342, 2493),
        (2716, 2840),
        (3102, 3220),
        (3225, 3360),
        (3366, 3483),
        (3487, 3634),
        (3673, 3716),
        (3740, 3890),
        (3899, 3943),
        (3947, 4090),
        (4094, 4206),
        (4211, 4348),
        (4359, 4468),
        (4480, 4599),
        (4605, 4709),
        (4713, 4830),
        (8722, 8825),
        (8831, 9017),
        (9036, 9087),
        (18822, 18885),
        (19935, 19992),
        (21046, 21138),
        (21801, 21867),
        (25730, 25847),
        (25851, 25994),
        (25999, 26124),
        (26128, 26243),
        (26249, 26290),
        (26314, 26358),
        (26379, 26539),
        (26544, 26596),
        (26605, 26741),
        (26747, 26865),
        (26870, 27010),
        (27016, 27143),
        (27147, 27262),
        (27268, 27380),
        (27385, 27492),
        (28681, 28802),
        (28806, 28974),
        (28978, 29067),
        (29076, 29219),
        (29223, 29371),
        (29376, 29523),
        (29527, 29652),
        (29656, 29774),
        (29779, 29891),
        (29896, 30018),
    ], ((300, 840), (1313, 185))),
    HardsubLineFade([
        (30519, 30541),
        (30541, 30589),
        (30590, 30637),
        (30638, 30685),
        (30686, 30733),
        (30734, 30781),
        (30782, 30829),
        (30830, 30901),
        (30902, 30973),
        (30974, 31045),
    ], ((333, 50), (1361, 167))),
    HardsubLineFade([
        (31046, 31117),
        (31118, 31189),
    ], ((9, 70), (1239, 149))),
    HardsubSignFade([
        (4890, 5010),
        (15951, 16054),
        (16055, 16120),
        (16121, 16202),
        (29617, 29628),
        (33949, 34045),
    ]),
]
NOSCALE: List[Range] = []
AA_NONE: List[Range] = [(33870, 33873)]

LETTERBOX: List[Range] = [(0, 2150), (8791, 10693), (13427, 15153), (27878, 28006)]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.dhs_source()
    wakas = [w[:33669] + w.std.BlankClip(length=17) + w[33669:] for w in wakas]
    ref = ref.resize.Point(range_in=CRange.FULL, range=CRange.LIMITED) if SOURCE.ref_is_funi else ref
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
    aa = antialias(deb, noaa=AA_NONE)
    grain = regrain(aa)
    edgefix = letterbox_edgefix(grain, LETTERBOX)
    final = finalize(edgefix)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, filter_basic)
else:
    filter()
