import vapoursynth as vs

from pripri_common import PriPriConfig, edgefix, denoise, descale, deband, antialias, regrain, scenefilter_ed, finalize

from yt_common.automation import SelfRunner
from yt_common.source import FileTrim, SimpleSource

from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range

from typing import List, Optional

import os

core = vs.core

EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: PriPriConfig = PriPriConfig(EPNUM)
SOURCE: SimpleSource = SimpleSource(
    FileTrim("../bdmv/[180223][BDMV] プリンセス・プリンシパル VI/PRINCESS_PRINCIPAL_6/BDMV/STREAM/00007.m2ts", (0, -48))
)
ED: Optional[int] = None

DEBAND_STRONG: List[Range] = [
    (32710, 32757),
    (33104, 33388),
    (34406, 34534),
]


def filter() -> vs.VideoNode:
    src = SOURCE.source()
    if ED is not None:
        src = src.std.FreezeFrames(first=[src.num_frames-4], last=[src.num_frames-1], replacement=[src.num_frames-5])
    ef = edgefix(src)
    den = denoise(ef)
    rescale = descale(den)
    deb = deband(rescale, strong=DEBAND_STRONG)
    aa = antialias(deb)
    grain = regrain(aa)
    ed = scenefilter_ed(grain, src, ED)
    cr = replace_ranges(ed, src, [(29971, 32128)])
    final = finalize(cr)
    src.set_output(1)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, audio_codec=["-c:a", "libopus", "-b:a", "192k", "-sample_fmt", "s16"])
else:
    filter()
