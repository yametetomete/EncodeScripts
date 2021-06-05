from yt_common.audio import AudioStream, CodecPassthrough, CodecOpus, CodecFlac
from yt_common.config import Config
from yt_common.source import SimpleSource

from typing import List, Union

import os

RESOLUTION: int = 1080
DATAPATH: str = os.path.dirname(__file__)


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


class TenSuraS2BDSource(SimpleSource):
    def audio_streams(self) -> List[AudioStream]:
        return [AudioStream(0, CodecFlac())]
