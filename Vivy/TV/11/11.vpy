import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix, letterbox_refix, regrain)

from yt_common.automation import SelfRunner
from yt_common.chapters import Chapter
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubLine, HardsubSignFade, HardsubMask, bounded_dehardsub

from typing import List

import os

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 4221),
    Chapter("Part A", 6379),
    Chapter("Part B", 11820),
    Chapter("ED", 31528),
    Chapter("PV", 33686),
]

WAKA_REPLACE: List[List[Range]] = [
    [(31528, 32331)],
    [],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubLine([
        (4227, 6341),
    ], ((283, 844), (1349, 204))),
    HardsubLine([
        (3242, 3290),
    ]),
    HardsubSignFade([
        (33949, 34045),
        (22337, 22403),
        (22500, 22583),
    ]),
    HardsubSignFade([
        (6402, 6522),
    ], expand=9),
]

PIXELSHIT: List[Range] = [
    (1466, 1507),
    (11820, 12005),
    (17270, 17329),
]
NOSCALE: List[Range] = [
]
NOSCALE += PIXELSHIT
AA_NONE: List[Range] = [
]
AA_NONE += PIXELSHIT
AA_STRONGER: List[Range] = [
]
LETTERBOX: List[Range] = [
]
LETTERBOX_FADES: List[Range] = [
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
    den = denoise(src)
    rescale = fsrcnnx_rescale(den, NOSCALE)
    edgefix = letterbox_edgefix(rescale, crops=LETTERBOX, fades=LETTERBOX_FADES)
    deb = deband(edgefix)
    aa = antialias(deb, stronger=AA_STRONGER, noaa=AA_NONE)
    refix = letterbox_refix(aa, deb, LETTERBOX)
    grain = regrain(refix)
    final = finalize(grain)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, filter_basic, chapters=CHAPTERS)
else:
    filter()
