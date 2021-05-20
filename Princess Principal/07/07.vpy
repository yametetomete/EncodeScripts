import vapoursynth as vs

from pripri_common import PriPriConfig, edgefix, denoise, descale, deband, antialias, regrain, scenefilter_ed, finalize

from yt_common.automation import SelfRunner
from yt_common.source import FileTrim, SimpleSource

from lvsfunc.misc import replace_ranges

from typing import Optional

import os

core = vs.core

EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: PriPriConfig = PriPriConfig(EPNUM)
SOURCE: SimpleSource = SimpleSource(
    FileTrim("../bdmv/[171222][BDMV] プリンセス・プリンシパル IV/PRINCESS_PRINCIPAL_4/BDMV/STREAM/00006.m2ts", (0, -24))
)
ED: Optional[int] = None


def filter() -> vs.VideoNode:
    src = SOURCE.source()
    if ED is not None:
        src = src.std.FreezeFrames(first=[src.num_frames-4], last=[src.num_frames-1], replacement=[src.num_frames-5])
    ef = edgefix(src)
    den = denoise(ef)
    rescale = descale(den)
    rescalem = descale(den, mask=True)
    rescale = replace_ranges(rescale, rescalem, [(31722, 34767)])
    deb = deband(rescale)
    aa = antialias(deb)
    grain = regrain(aa)
    ed = scenefilter_ed(grain, src, ED)
    final = finalize(ed)
    src.set_output(1)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, audio_codec=["-c:a", "libopus", "-b:a", "192k", "-sample_fmt", "s16"])
else:
    filter()
