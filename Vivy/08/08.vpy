import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix, regrain)

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubLine, HardsubSignFade, HardsubMask, bounded_dehardsub

from typing import List

import os

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

WAKA_REPLACE: List[List[Range]] = [
    [(28651, 29454)],
    [],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubLine([
        (2806, 4962),
        (8891, 9113),
        (16528, 17014),
        (17903, 17998),
    ], ((283, 844), (1349, 204))),
    HardsubSignFade([
        (5117, 5237),
    ], refframe=0.75),
    HardsubSignFade([
        (33949, 34045),
    ], refframe=1),
]
NOSCALE: List[Range] = [
]
AA_NONE: List[Range] = [
    (24897, 24914),
]
AA_STRONGER: List[Range] = [
]
LETTERBOX: List[Range] = [
    (0, 2437),
    (30809, 33232),
    (33686, 33725),
    (33844, 33894),
]


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
