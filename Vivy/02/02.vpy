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
    HardsubSign((125, 245), ((220, 865), (992, 98)), refframe=143),
    HardsubSign((865, 896), ((1173, 539), (232, 40)), highpass=2000),
    HardsubSign((2274, 2318), ((431, 671), (1068, 142)), highpass=2000),
    HardsubSign((2391, 2426), ((116, 62), (1471, 311)), highpass=2000),
    HardsubSign((2427, 2452), ((317, 728), (1176, 80)), highpass=2000),
    HardsubSign((3776, 3871), ((782, 286), (748, 76)), highpass=2000),
    HardsubSign((3877, 3950), ((866, 524), (494, 53)), highpass=2000),
    HardsubSign((6498, 6542), ((696, 296), (493, 31)), highpass=2000),
    HardsubSign((7212, 7221), ((430, 666), (1066, 149)), highpass=2000),
    HardsubSign((7222, 7233), ((317, 728), (1179, 84)), highpass=2000),
    HardsubSign((7234, 7245), ((410, 303), (1169, 129)), highpass=2000),
    HardsubSign((7246, 7254), ((514, 687), (807, 90)), highpass=2000),
    HardsubSign((27488, 27630), ((778, 287), (758, 78)), highpass=2000),
    HardsubSign((27636, 27779), ((756, 449), (792, 87)), highpass=2000),
    HardsubSign((28907, 28934), ((758, 454), (787, 79)), highpass=2000),
    HardsubSign((28945, 28954), ((773, 481), (758, 57)), highpass=2000),
    HardsubSign((28986, 29019), ((621, 748), (657, 52)), highpass=2000),
    HardsubSign((29053, 29061), ((621, 748), (657, 52)), highpass=2000),
    HardsubSign((29062, 29077), ((649, 333), (742, 53)), highpass=2000),
    HardsubSign((29615, 29674), ((336, 74), (1244, 76)), highpass=2000),
    HardsubSign((29675, 29758), ((587, 68), (750, 85)), highpass=2000),
    HardsubSign((30259, 30977), ((293, 843), (1321, 227)), highpass=2000),
    HardsubSign((32608, 32703), ((281, 859), (890, 101)), highpass=2000),
]
CREDITS: List[Range] = [(30152, 32343)]
PIXELSHIT: List[Range] = [
    (7255, 7278),
]
NOSCALE: List[Range] = CREDITS + PIXELSHIT
NOAA: List[Range] = PIXELSHIT

waka, ref = source(EPNUM)
waka = waka[:32344] + waka[32349:]

src = bounded_dehardsub(waka, ref, SIGNS_RU)
rescale = fsrcnnx_rescale(src, NOSCALE)
den = denoise(rescale)
deb = deband(den)
aa = antialias(deb, NOAA)
final = finalize(aa)
final.set_output()
