from yt_common.config import Config, FlacMixin, OpusMixin

from typing import Union

import os

RESOLUTION: int = 1080
DATAPATH: str = os.path.dirname(__file__)


class TenSuraS1BDConfig(OpusMixin, Config):
    def __init__(self, desc: Union[str, int]) -> None:
        super().__init__(
            desc,
            "TenSura",
            "Tensei Shitara Slime Datta Ken",
            RESOLUTION,
            DATAPATH
        )


class TenSuraS2Config(Config):
    def __init__(self, desc: Union[str, int]) -> None:
        super().__init__(
            desc,
            "TenSura S2",
            "Tensei Shitara Slime Datta Ken S2",
            RESOLUTION,
            DATAPATH
        )


class TenSuraS2BDConfig(FlacMixin, TenSuraS2Config):
    pass
