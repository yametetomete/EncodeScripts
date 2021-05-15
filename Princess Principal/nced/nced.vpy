import vapoursynth as vs

from pripri_common import PriPriConfig, scenefilter_ed, finalize

from yt_common.automation import SelfRunner
from yt_common.source import FileTrim, SimpleSource

from typing import Optional

import os

core = vs.core

DESC: str = os.path.basename(os.path.splitext(__file__)[0])
CONFIG: PriPriConfig = PriPriConfig(DESC)
SOURCE: SimpleSource = SimpleSource(
    FileTrim("../bdmv/[180223][BDMV] プリンセス・プリンシパル VI/PRINCESS_PRINCIPAL_6/BDMV/STREAM/00013.m2ts", (24, -24))
)
ED: Optional[int] = 0


def filter() -> vs.VideoNode:
    src = SOURCE.source()
    ed = scenefilter_ed(src, src, ED, mask=False)
    final = finalize(ed)
    src.set_output(1)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, audio_codec=["-c:a", "libopus", "-b:a", "192k", "-sample_fmt", "s16"])
else:
    filter()
