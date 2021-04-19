import vapoursynth as vs

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubMask, HardsubLine, HardsubSign, bounded_dehardsub

from typing import List

import os
import sys
sys.path.append("..")

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,  # noqa: E402
                         finalize, fsrcnnx_rescale, letterbox_edgefix)

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

WAKA_REPLACE: List[List[Range]] = [
    [(29968, 30792)],
    [(31727, 31879)],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubLine((1371, 3157), ((293, 872), (1323, 162))),
    HardsubSign((3572, 3688), ((236, 860), (821, 103)), refframes=3671),
    HardsubSign((4040, 4105), ((937, 18), (811, 338))),
    HardsubSign((4040, 4105), ((132, 671), (384, 211))),
    HardsubSign((8135, 8259), ((583, 65), (744, 80))),
    HardsubSign((9571, 9596), ((573, 74), (768, 79))),
    HardsubSign((21874, 21942), ((532, 131), (445, 228)), refframes=21942, highpass=2000),
    HardsubLine((29968, 31084), ((293, 872), (1323, 182))),
    HardsubLine((32540, 32651), ((293, 872), (1323, 162))),
    HardsubSign((33948, 34044), ((267, 857), (1067, 104)), refframes=34030),
]
NOSCALE: List[Range] = []
NOAA: List[Range] = []
LETTERBOX: List[Range] = [(0, 432)]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.source()
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    src = bounded_dehardsub(waka, ref, SIGNS_RU)
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
    SelfRunner(CONFIG, filter, filter_basic)
else:
    filter()
