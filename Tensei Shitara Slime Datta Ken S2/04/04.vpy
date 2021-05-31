import vapoursynth as vs

from tensura_common import TenSuraConfig, antialias, deband, denoise, descale, finalize, regrain

from yt_common.automation import SelfRunner
from yt_common.chapters import Chapter
from yt_common.source import FileTrim, SimpleSource

from lvsfunc.types import Range

from typing import List

import os

EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: TenSuraConfig = TenSuraConfig(EPNUM)
BDMV: str = "../bdmv/[BDMV][210326][Tensei Shitara Slime Datta Ken 2nd Season][Vol.1]/BDMV/STREAM"
SOURCE: SimpleSource = SimpleSource(
    FileTrim(os.path.join(BDMV, "00009.m2ts"), (None, -51))
)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 3237),
    Chapter("Part A", 5395),
    Chapter("Part B", 18484),
    Chapter("ED", 31767),
    Chapter("Next", 33925),
]

AA_STRONG: List[Range] = [
    (6038, 6117),
    (7301, 7348),
]

DEBAND_NUCLEAR: List[Range] = [
]

core = vs.core


def filter() -> vs.VideoNode:
    src = SOURCE.source()
    den = denoise(src)
    descaled = descale(den)
    deb = deband(descaled, nuclear=DEBAND_NUCLEAR)
    aa = antialias(deb, strong=AA_STRONG)
    grain = regrain(aa)
    final = finalize(grain)
    src.set_output(1)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, chapters=CHAPTERS)
else:
    filter()
