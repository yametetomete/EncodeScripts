import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise, finalize,
                         fsrcnnx_rescale)

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubMask, HardsubSign, bounded_dehardsub

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
    HardsubSign((125, 245), ((220, 865), (992, 98)), refframe=143, blur=False),
    HardsubSign((865, 896), ((1173, 539), (232, 40)), highpass=2000, blur=False),
    HardsubSign((2274, 2318), ((431, 671), (1068, 142)), highpass=2000, blur=False),
    HardsubSign((2391, 2426), ((116, 62), (1471, 311)), highpass=2000, blur=False),
    HardsubSign((2427, 2452), ((317, 728), (1176, 80)), highpass=2000, blur=False),
    HardsubSign((3776, 3871), ((782, 286), (748, 76)), highpass=2000, blur=False),
    HardsubSign((3877, 3950), ((866, 524), (494, 53)), highpass=2000, blur=False),
    HardsubSign((6498, 6542), ((696, 296), (493, 31)), highpass=2000, blur=False),
    HardsubSign((7212, 7221), ((430, 666), (1066, 149)), highpass=2000, blur=False),
    HardsubSign((7222, 7233), ((317, 728), (1179, 84)), highpass=2000, blur=False),
    HardsubSign((7234, 7245), ((410, 303), (1169, 129)), highpass=2000, blur=False),
    HardsubSign((7246, 7254), ((514, 687), (807, 90)), highpass=2000, blur=False),
    HardsubSign((27488, 27630), ((778, 287), (758, 78)), highpass=2000, blur=False),
    HardsubSign((27636, 27779), ((756, 449), (792, 87)), highpass=2000, blur=False),
    HardsubSign((28907, 28934), ((758, 454), (787, 79)), highpass=2000, blur=False),
    HardsubSign((28945, 28954), ((773, 481), (758, 57)), highpass=2000, blur=False),
    HardsubSign((28986, 29019), ((621, 748), (657, 52)), highpass=2000, blur=False),
    HardsubSign((29053, 29061), ((621, 748), (657, 52)), highpass=2000, blur=False),
    HardsubSign((29062, 29077), ((649, 333), (742, 53)), highpass=2000, blur=False),
    HardsubSign((29615, 29674), ((336, 74), (1244, 76)), highpass=2000, blur=False),
    HardsubSign((29675, 29758), ((587, 68), (750, 85)), highpass=2000, blur=False),
    HardsubSign((30259, 30977), ((293, 843), (1321, 227)), highpass=2000, blur=False),
    HardsubSign((32608, 32703), ((281, 859), (890, 101)), highpass=2000, blur=False),
]
CREDITS: List[Range] = [(30152, 32343)]
PIXELSHIT: List[Range] = [
    (7255, 7278),
]
NOSCALE: List[Range] = CREDITS + PIXELSHIT
NOAA: List[Range] = PIXELSHIT


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.source()
    wakas = [waka[:32344] + waka[32349:] for waka in wakas]
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
    final = finalize(aa)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, filter, filter_basic)
else:
    filter()
