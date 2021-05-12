import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix)

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubLineFade, HardsubSign, HardsubSignFade, HardsubMask, bounded_dehardsub

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
    HardsubLineFade([
        (5632, 5679),
        (10588, 10671),
        (24934, 25005),
    ]),
    HardsubSignFade([
        (4016, 4135),
        (19061, 19186),
    ]),
    HardsubSignFade([
        (33950, 34045),
    ], expand=10, thresh=0.03),
    HardsubSignFade([
        (18989, 19060),
    ], expand=15, thresh=0.02),
    HardsubSign([
        (18923, 18988),
    ]),
]
NOSCALE: List[Range] = []
NOAA: List[Range] = []
LETTERBOX: List[Range] = [(0, 1153)]


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
    aa = antialias(deb, NOAA)
    edgefix = letterbox_edgefix(aa, LETTERBOX)
    final = finalize(edgefix)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, filter_basic)
else:
    filter()
