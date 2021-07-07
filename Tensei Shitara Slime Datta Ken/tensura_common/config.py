import vapoursynth as vs

from acsuite.types import Trim

from yt_common.audio import AudioStream, CodecPassthrough, CodecOpus, CodecFlac
from yt_common.config import Config
from yt_common.source import DehardsubFileFinder, FileTrim, SimpleSource, glob_filename

from typing import List, Optional, Tuple, Union

import os

core = vs.core

RESOLUTION: int = 1080
DATAPATH: str = os.path.dirname(__file__)


def apply_trim(clip: vs.VideoNode, trim: Optional[Trim]) -> vs.VideoNode:
    if trim is None:
        return clip
    s, e = trim
    if s is None and e is None:
        return clip
    if s is None:
        return clip[:e]
    if e is None:
        return clip[s:]
    return clip[s:e]


class TenSuraS1BDConfig(Config):
    def __init__(self, desc: Union[str, int]) -> None:
        super().__init__(
            desc,
            "TenSura",
            "Tensei Shitara Slime Datta Ken",
            RESOLUTION,
            DATAPATH
        )


class TenSuraS1BDSource(SimpleSource):
    def audio_streams(self) -> List[AudioStream]:
        return [AudioStream(0, CodecOpus())]


class TenSuraS2Config(Config):
    def __init__(self, desc: Union[str, int]) -> None:
        super().__init__(
            desc,
            "TenSura S2",
            "Tensei Shitara Slime Datta Ken S2",
            RESOLUTION,
            DATAPATH
        )


class TenSuraS2Source(SimpleSource):
    def audio_streams(self) -> List[AudioStream]:
        return [AudioStream(0, CodecPassthrough())]


class TenSuraS2AODSource(DehardsubFileFinder):
    trims: List[Trim]

    def __init__(self, config: Config, trims: Optional[List[Trim]] = None) -> None:
        self.trims = trims or [(None, None)]
        super().__init__(config)

    def get_waka_filenames(self) -> List[str]:
        return [f"Tensei Shitara Slime Datta Ken S2 - {int(self.config.desc)} (AoD 1080p+).mkv"]

    def get_ref(self) -> vs.VideoNode:
        ref = self._open(glob_filename("[SubsPlease] Tensei Shitara Slime Datta Ken - "
                         f"{int(self.config.desc)+24} (1080p) [$GLOB].mkv"))
        return core.std.Splice([apply_trim(ref, t) for t in self.trims]) if self.trims else ref

    def dhs_source(self) -> Tuple[List[vs.VideoNode], vs.VideoNode]:
        hs = self._open(self.get_waka_filenames()[0])
        hs = core.std.Splice([apply_trim(hs, t) for t in self.trims]) if self.trims else hs
        ref = self.get_ref()
        return [hs], ref

    def audio_src(self) -> List[FileTrim]:
        return [FileTrim(self.get_waka_filenames()[0], t) for t in self.trims]
        # return [FileTrim("Tensei Shitara Slime Datta Ken S2 - 13 (AoD 1080p+).mkv", (24, -24))]
        # return [FileTrim("[SubsPlease] Tensei Shitara Slime Datta Ken - 37 (1080p) [1FE9B194].mkv", (24, -24))]


class TenSuraS2BDSource(SimpleSource):
    def audio_streams(self) -> List[AudioStream]:
        return [AudioStream(0, CodecFlac())]
