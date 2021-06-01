import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix, letterbox_refix, regrain)

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
    [(30354, 31683)],
    [],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubLine([
        (98, 189),
        (2931, 5045),
    ], ((283, 844), (1349, 204))),
    HardsubSignFade([
        (30347, 30353),
    ], refframe=1),
    HardsubSignFade([
        (5094, 5214),
        (33950, 34046),
    ]),
]
NOSCALE: List[Range] = [
]
AA_NONE: List[Range] = [
]
AA_STRONGER: List[Range] = [
]
LETTERBOX: List[Range] = [
    (11509, 13149),
    (25136, 25244),
]
LETTERBOX_FADES: List[Range] = [
]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.dhs_source()
    wakas = [w[:33687] + w[33696:] for w in wakas]
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    src = bounded_dehardsub(waka, ref, SIGNS_RU, wakas)
    src.set_output(1)
    return src


def filter() -> vs.VideoNode:
    src = filter_basic()
    den = denoise(src)
    rescale = fsrcnnx_rescale(den, NOSCALE)
    edgefix = letterbox_edgefix(rescale, crops=LETTERBOX, fades=LETTERBOX_FADES)
    deb = deband(edgefix)
    aa = antialias(deb, stronger=AA_STRONGER, noaa=AA_NONE)
    refix = letterbox_refix(aa, deb, LETTERBOX)
    grain = regrain(refix)
    final = finalize(grain)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, filter_basic)
else:
    filter()
