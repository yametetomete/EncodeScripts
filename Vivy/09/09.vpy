import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix, letterbox_refix, regrain)

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubLine, HardsubSign, HardsubSignFade, HardsubMask, bounded_dehardsub

from typing import List

import os

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

WAKA_REPLACE: List[List[Range]] = [
    [(31528, 32331)],
    [],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubLine([
        (222, 2336),
        (27065, 30404),
    ], ((283, 844), (1349, 204))),
    HardsubSignFade([
        (5508, 5587),
        (33950, 34045),
    ], refframe=1),
    HardsubSignFade([
        (2385, 2505),
    ], expand=10),
    HardsubSignFade([
        (8501, 8513),
        (11701, 11716),
        (24242, 24295),
    ]),
    HardsubSign([
        (17049, 17084),
    ]),
]
NOSCALE: List[Range] = [
]
AA_NONE: List[Range] = [
]
AA_STRONGER: List[Range] = [
]
LETTERBOX: List[Range] = [
    (2853, 3737),
    (6084, 6974),
]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.dhs_source()
    wakas = [w[:11220] + w[11221:] for w in wakas]
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    src = bounded_dehardsub(waka, ref, SIGNS_RU, wakas)
    src.set_output(1)
    return src


def filter() -> vs.VideoNode:
    src = filter_basic()
    den = denoise(src)
    rescale = fsrcnnx_rescale(den, NOSCALE)
    edgefix = letterbox_edgefix(rescale, LETTERBOX)
    deb = deband(edgefix)
    aa = antialias(deb, stronger=AA_STRONGER, noaa=AA_NONE)
    refix = letterbox_refix(aa, deb, LETTERBOX)
    grain = regrain(refix)
    final = finalize(grain)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, filter_basic)
else:
    filter()
