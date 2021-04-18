import vapoursynth as vs

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubSign, bounded_dehardsub

from typing import List

import os
import sys
sys.path.append("..")

from vivy_common import (SelfRunner, antialias, deband, denoise,  # noqa: E402
                         finalize, fsrcnnx_rescale, letterbox_edgefix, source)

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
SIGNS_RU: List[HardsubSign] = [
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
    waka, ref = source(EPNUM)
    waka = waka[:37301] + core.std.BlankClip(waka, length=6) + waka[37301:]
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
    SelfRunner(EPNUM, filter, filter_basic)
else:
    filter()
