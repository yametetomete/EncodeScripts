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

OP: Optional[int] = 0

WAKA_REPLACE: List[List[Range]] = [
    [(1852, 1965), (31864, 32661)],
    [],
]

TITLECARDS: List[Range] = [
    (5186, 5221),
    (7520, 7561),
    (10517, 10552),
    (11317, 11364),
    (12555, 12590),
    (15321, 15356),
    (17786, 17833),
    (20838, 20861),
    (22857, 22898),
    (24009, 24056),
]

SIGNS_RU: List[HardsubMask] = [
    HardsubSignFade(TITLECARDS + [
        (2158, 2217),
        (2266, 2313),
        (2947, 2988),
        (3295, 3384),
        (7004, 7084),
        (10205, 10226),
        (11059, 11124),
        (14061, 14102),
        (24059, 24116),
        (26435, 26472),
        (26759, 26863),
        (26972, 27073),
        (27140, 27259),
        (27975, 28163),
        (28377, 28460),
        (31797, 31863),
    ]),
]

AA_STRONG: List[Range] = [
    (20892, 20933),
    (20994, 21041),
]

AA_WEAK: List[Range] = TITLECARDS + [
]

AA_NONE: List[Range] = [
]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.source()
    wakas = [w[0] + w for w in wakas]
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    src = bounded_dehardsub(waka, ref, SIGNS_RU, wakas)
    src.set_output(2)
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
