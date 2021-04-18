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
    HardsubSign((1371, 3157), ((293, 872), (1323, 162)), highpass=20000),
    HardsubSign((3572, 3688), ((236, 860), (821, 103)), refframe=3671),
    HardsubSign((4040, 4105), ((937, 18), (811, 338))),
    HardsubSign((4040, 4105), ((132, 671), (384, 211))),
    HardsubSign((8135, 8259), ((583, 65), (744, 80))),
    HardsubSign((9572, 9596), ((573, 74), (768, 79))),
    HardsubSign((21874, 21942), ((532, 131), (445, 228)), highpass=2000),
    HardsubSign((29968, 31084), ((293, 872), (1323, 162)), highpass=20000),
    HardsubSign((30002, 30792), ((302, 73), (1328, 142)), highpass=2000, expand=10),
    HardsubSign((31727, 31879), ((293, 872), (1323, 162)), highpass=20000),
    HardsubSign((32540, 32651), ((293, 872), (1323, 162)), highpass=20000),
    HardsubSign((33948, 34044), ((267, 857), (1067, 104)), refframe=34030),
]
NOSCALE: List[Range] = []
NOAA: List[Range] = []
LETTERBOX: List[Range] = [(0, 432)]


def filter_basic() -> vs.VideoNode:
    waka, ref = source(EPNUM)
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
