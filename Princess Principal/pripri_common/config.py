from yt_common.config import Config

from typing import Union

import os

TITLE: str = "PriPri"
TITLE_LONG: str = "Princess Principal"
RESOLUTION: int = 1080
DATAPATH: str = os.path.dirname(__file__)


class PriPriConfig(Config):
    def __init__(self, desc: Union[str, int]) -> None:
        super().__init__(
            desc,
            TITLE,
            TITLE_LONG,
            RESOLUTION,
            DATAPATH
        )
