from yt_common.config import Config, FlacMixin

from typing import Union

import os

TITLE: str = "TenSura S2"
TITLE_LONG: str = "Tensei Shitara Slime Datta Ken S2"
RESOLUTION: int = 1080
DATAPATH: str = os.path.dirname(__file__)


class TenSuraConfig(FlacMixin, Config):
    def __init__(self, desc: Union[str, int]) -> None:
        super().__init__(
            desc,
            TITLE,
            TITLE_LONG,
            RESOLUTION,
            DATAPATH
        )
