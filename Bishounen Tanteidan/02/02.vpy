import vapoursynth as vs

from tanteidan_common import (PrettyConfig, PrettySource, antialias, deband,
                              denoise, finalize, regrain, stupid_op_scenefilter)

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from typing import List, Optional

from lvsfunc.dehardsub import HardsubSignFade, HardsubMask, bounded_dehardsub
from lvsfunc.types import Range

import os


core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: PrettyConfig = PrettyConfig(EPNUM)
SOURCE: PrettySource = PrettySource(CONFIG)

OP: Optional[int] = 792

WAKA_REPLACE: List[List[Range]] = [
    [(31864, 32652)],
    [],
]

TITLECARDS: List[Range] = [
    (0, 35),
    (2949, 2996),
    (6470, 6505),
    (8460, 8495),
    (8976, 9011),
    (11058, 11141),
    (13221, 13268),
    (15780, 15818),
    (19494, 19529),
    (21303, 21338),
    (24000, 24023),
    (25207, 25242),
    (26654, 26683),
    (30290, 30337),
]

SIGNS_RU: List[HardsubMask] = [
    HardsubSignFade([
        (318, 347),
        (4607, 4702),
        (6506, 6547),
        (31792, 31863),
        (3714, 3773),
        (3774, 3851),
        (4886, 4933),
        (5972, 6091),
        (12060, 12083),
        (12084, 12113),
        (18132, 18200),
        (19446, 19493),
        (24178, 24196),
        (24201, 24216),
        (26768, 26815),
        (26816, 26857),
    ]),

]

SIGNS_RU += [HardsubSignFade(tc) for tc in TITLECARDS]

AA_STRONG: List[Range] = [
    # the stars in this range respond poorly to nnedi3-clamped AAs, but fine to sraa
    (13374, 13889),
    (14022, 14270),
    (14994, 15233),
    (15540, 15779),
    (16086, 16277),
    (19530, 19805),
    (19995, 20177),
    (20190, 20669),
    (20856, 21020),
]

AA_WEAK: List[Range] = [
    (0, 35),
    (282, 347),
    (17757, 18068),
    (18069, 18440),
]

AA_WEAK += TITLECARDS

AA_NONE: List[Range] = [
    (5972, 6091),  # this is heavily stylized and i'm not touching it
]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.source()
    wakas = [w[0] + w for w in wakas]
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    src = bounded_dehardsub(waka, ref, SIGNS_RU, wakas)
    src.set_output(1)
    return src


def filter() -> vs.VideoNode:
    src = filter_basic()
    den = denoise(src)
    deb = deband(den)
    aa = antialias(deb, strong=AA_STRONG, weak=AA_WEAK, noaa=AA_NONE)
    scenefilter = stupid_op_scenefilter(aa, deb, OP)
    grain = regrain(scenefilter)
    final = finalize(grain)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, filter, filter_basic)
else:
    filter()
