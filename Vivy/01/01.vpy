import vapoursynth as vs

from typing import List

import os
import sys
sys.path.append("..")

from vivy_common import (HardsubSign, Range, bounded_dehardsub, antialias, deband, denoise,  # noqa: E402
                         finalize, fsrcnnx_rescale, source)

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
SIGNS_RU: List[HardsubSign] = [
    HardsubSign((5283, 5403), ((226, 786), (1214, 102))),
    HardsubSign((6778, 6888), ((588, 454), (434, 63))),
    HardsubSign((9017, 9070), ((975, 301), (157, 24))),
    HardsubSign((22276, 22350), ((480, 75), (959, 66))),
    HardsubSign((25715, 25904), ((623, 73), (681, 67))),
    HardsubSign((35223, 36108), ((775, 866), (1138, 211))),
    HardsubSign((37572, 37666), ((259, 856), (987, 103))),
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

waka, funi = source(EPNUM)
waka = waka[:37301] + core.std.BlankClip(waka, length=6) + waka[37301:]

src = bounded_dehardsub(waka, funi, SIGNS_RU)
rescale = fsrcnnx_rescale(src, NOSCALE)
den = denoise(rescale)
deb = deband(den)
aa = antialias(deb, NOAA)
final = finalize(aa)
final.set_output()
