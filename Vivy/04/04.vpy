import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix, regrain)

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubLine, HardsubSign, HardsubMask, bounded_dehardsub

from typing import List

import os

core = vs.core
core.num_threads = 16


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

WAKA_REPLACE: List[List[Range]] = [
    [(30119, 30969)],
    [],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubLine((1278, 3392), ((275, 918), (1356, 112))),
    HardsubSign((3452, 3572), ((232, 857), (1077, 114)), refframes=3500),
    HardsubSign((11454, 11489), ((727, 176), (440, 78))),
    HardsubSign((16803, 16841), ((135, 549), (479, 221))),
    HardsubLine((29463, 33374), ((275, 890), (1356, 140))),
    HardsubSign((33950, 34045), ((232, 857), (1077, 114)), refframes=34045),
]
NOSCALE: List[Range] = []
NOAA: List[Range] = []
LETTERBOX: List[Range] = [(0, 1151)]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.source()
    wakas = [w[:33665] + core.std.BlankClip(w, length=21) + w[33665:] for w in wakas]
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
    grain = regrain(aa)
    edgefix = letterbox_edgefix(grain, LETTERBOX)
    final = finalize(edgefix)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, filter, filter_basic)
else:
    filter()
