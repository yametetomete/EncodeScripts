import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix)

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubSign, HardsubMask, bounded_dehardsub

from typing import List

import os

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

WAKA_REPLACE: List[List[Range]] = [
    [],
    []
]
SIGNS_RU: List[HardsubMask] = [
    HardsubSign((5283, 5403), ((226, 786), (1214, 102)), highpass=2000),
    HardsubSign((6778, 6888), ((588, 454), (434, 63)), highpass=2000),
    HardsubSign((9017, 9070), ((975, 301), (157, 24)), highpass=2000),
    HardsubSign((22276, 22350), ((480, 75), (959, 66)), highpass=2000),
    HardsubSign((25715, 25904), ((623, 73), (681, 67)), highpass=2000),
    HardsubSign((35223, 36108), ((775, 866), (1138, 211)), highpass=2000),
    HardsubSign((37572, 37666), ((259, 856), (987, 103)), highpass=2000),
]
CREDITS: List[Range] = [(35151, 37306)]
PIXELSHIT: List[Range] = [
    (2534, 2605),
    (1937, 2021),
    (6607, 6762),
    (14160, 14227),
    (16609, 16674),
    (20112, 20558),
]
NOSCALE: List[Range] = CREDITS + PIXELSHIT
NOAA: List[Range] = PIXELSHIT
LETTERBOX: List[Range] = [
    (659, 14071)
]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.dhs_source()
    wakas = [waka[:37301] + core.std.BlankClip(waka, length=6) + waka[37301:] for waka in wakas]
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    src = bounded_dehardsub(waka, ref, SIGNS_RU, wakas)
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
