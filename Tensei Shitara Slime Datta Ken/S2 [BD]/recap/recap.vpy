import vapoursynth as vs

from tensura_common import (TenSuraS2BDConfig, antialias, deband, denoise, descale,
                            edgefix, finalize, megurumono_scenefilter, regrain)

from yt_common.automation import SelfRunner, Zone
from yt_common.chapters import Chapter
from yt_common.source import FileTrim, SimpleSource

from lvsfunc.mask import BoundingBox
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

from typing import List, Tuple

import os

DESC: str = os.path.basename(os.path.splitext(__file__)[0])
CONFIG: TenSuraS2BDConfig = TenSuraS2BDConfig(DESC)
BDMV: str = "../bdmv/[BDMV][210326][Tensei Shitara Slime Datta Ken 2nd Season][Vol.1]/BDMV/STREAM"
SOURCE: SimpleSource = SimpleSource(
    FileTrim(os.path.join(BDMV, "00013.m2ts"), (24, -24))
)

MEGURUMONO: Tuple[int, int] = (2873, 5034)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", MEGURUMONO[0]),
    Chapter("Part A", MEGURUMONO[1]+1),
    Chapter("Part B", 22561),
    Chapter("ED", 31883),
]

NOD3: List[Range] = [
]

NODEN: List[Range] = [
    (21749, 21849),
]

ZONES: List[Zone] = [
]

ZONES += [Zone(r, 0.75) for r in NOD3 + NODEN if isinstance(r, tuple)]

AA_STRONG: List[Range] = [
]

SANGNOM: List[Tuple[Range, List[BoundingBox]]] = [
]

DEBAND_STRONG: List[Range] = [
    (0, 500),
    (11519, 11615),
    (14845, 14906),
    (15137, 15234),
    (15667, 15817),
    (18848, 19536),
    (19897, 20004),
    (20749, 20814),
    (21013, 21340),
    (21485, 21748),
    (22812, 22894),
    (26719, 26769),
    (31307, 31426),
    (31596, 31882),
]

DEBAND_NUCLEAR: List[Range] = [
]

core = vs.core


def filter() -> vs.VideoNode:
    src = SOURCE.source()
    ef = edgefix(src)
    den = denoise(ef)
    den = replace_ranges(den, src, NODEN)
    descaled = descale(den)
    deb = deband(descaled, strong=DEBAND_STRONG, nuclear=DEBAND_NUCLEAR)
    deb = replace_ranges(deb, src, NOD3)
    aa = antialias(deb, strong=AA_STRONG, sangnom=SANGNOM)
    grain = regrain(aa)
    scenefilter = grain
    if MEGURUMONO:
        megurumono = megurumono_scenefilter(src, MEGURUMONO[0])
        scenefilter = replace_ranges(scenefilter, megurumono, MEGURUMONO)
    final = finalize(scenefilter)
    src.set_output(1)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, chapters=CHAPTERS, zones=ZONES)
else:
    filter()
