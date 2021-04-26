import vapoursynth as vs

from tanteidan_common import (PrettyConfig, PrettySource, antialias, deband, denoise, finalize, regrain)

from yt_common.automation import SelfRunner
from yt_common.source import waka_replace

from typing import List
from lvsfunc.dehardsub import HardsubLineFade, HardsubMask, HardsubSign, bounded_dehardsub
from lvsfunc.types import Range
from lvsfunc.misc import replace_ranges

import os


core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: PrettyConfig = PrettyConfig(EPNUM)
SOURCE: PrettySource = PrettySource(CONFIG)

WAKA_REPLACE: List[List[Range]] = [
    [(31865, 32653)],
    [],
]

SIGNS_RU: List[HardsubMask] = [
    HardsubLineFade([
        (6586, 6611),
        (6813, 6839),
        (6954, 6971),
        (7092, 7115),
        (7242, 7289),
        (7461, 7511),
        (7512, 7535),
        (7697, 7727),
        (8345, 8371),
        (8833, 8860),
        (9950, 10114),
        (11234, 11266),
        (11747, 11986),
        (12113, 12136),
        (28429, 28477),
        (28502, 28537),
    ], ((449, 51), (1015, 127)), refframe=0.75),  # wtf waka fr
    HardsubSign((0, 167), ((67, 71), (793, 253)), refframes=0),
    HardsubSign((349, 395), ((1492, 733), (263, 100)), refframes=395),
    HardsubSign((492, 813), ((132, 322), (664, 207)), refframes=492),
    HardsubSign((2185, 2239), ((634, 302), (641, 111)), refframes=2239),
    HardsubSign((6426, 6485), ((435, 374), (1087, 104))),
    HardsubSign((7728, 7787), ((372, 369), (1239, 109))),
    HardsubSign((8970, 9034), ((1424, 77), (383, 75)), refframes=9034),
    HardsubSign((9830, 9886), ((1397, 41), (414, 83)), refframes=9886),
    HardsubSign((10997, 11044), ((1509, 180), (284, 68)), refframes=11044),
    HardsubSign((12044, 12112), ((1484, 44), (296, 73)), refframes=12112),
    HardsubSign((13298, 13368), ((559, 375), (824, 102))),
    HardsubSign((13441, 13476), ((1464, 656), (338, 67))),
    HardsubSign((13477, 13518), ((158, 657), (323, 78))),
    HardsubSign((15577, 15648), ((1296, 806), (457, 103))),
    HardsubSign((15577, 15648), ((143, 66), (341, 103))),
    HardsubSign((16351, 16422), ((704, 370), (541, 109))),
    HardsubSign((16651, 16699), ((1058, 404), (462, 88)), refframes=16651),
    HardsubSign((17554, 17692), ((732, 100), (393, 80)), refframes=17554),
    HardsubSign((17554, 17692), ((609, 777), (393, 80)), refframes=17554),
    HardsubSign((18487, 18638), ((474, 72), (979, 90)), refframes=18615),
    HardsubSign((19099, 19152), ((667, 372), (609, 104))),
    HardsubSign((20641, 20676), ((516, 0), (1042, 65))),
    HardsubSign((21124, 21179), ((681, 378), (601, 94))),
    HardsubSign((22428, 22451), ((555, 93), (823, 135))),
    HardsubSign((31793, 31864), ((740, 176), (445, 92))),
    HardsubSign((31793, 31864), ((352, 617), (1229, 92))),
    HardsubSign((31793, 31864), ((1355, 794), (329, 92))),
]


AA_WEAK: List[Range] = [
    (6426, 6485),
    (7728, 7787),
    (13298, 13368),
    (16351, 19152),
    (20641, 20676),
    (21124, 21179),
    (23952, 24023),
]


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.source()
    wakas = [w[0] + w for w in wakas]
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    waka = replace_ranges(waka, ref, [(30497, 30556)])  # wth wakanim
    src = bounded_dehardsub(waka, ref, SIGNS_RU, wakas)
    src.set_output(1)
    return src


def filter() -> vs.VideoNode:
    src = filter_basic()
    den = denoise(src)
    deb = deband(den)
    aa = antialias(deb, weak=AA_WEAK)
    grain = regrain(aa)
    final = finalize(grain)
    final.set_output()
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, filter, filter_basic)
else:
    filter()
