from yt_common import Config, FunimationSource

import os

from typing import List

TITLE: str = "Vivy"
TITLE_LONG: str = f"{TITLE} - Fluorite Eye's Song"
RESOLUTION: int = 1080
SUBGROUP: str = "YameteTomete"
DATAPATH: str = os.path.dirname(__file__)

WAKA_RU_FILENAME: str = f"{TITLE}_{{epnum:02d}}_RU_HD.mp4"
WAKA_FR_FILENAME: str = f"{TITLE}_{{epnum:02d}}_FR_HD.mp4"
WAKA_DE_FILENAME: str = f"{TITLE} - Fluorite Eyes Song E{{epnum:02d}} [1080p][AAC][JapDub][GerSub][Web-DL].mkv"


class VivyConfig(Config):
    def __init__(self, epnum: int) -> None:
        super().__init__(
            epnum,
            TITLE,
            TITLE_LONG,
            RESOLUTION,
            DATAPATH
        )


class VivySource(FunimationSource):
    def get_waka_filenames(self) -> List[str]:
        return [self.config.format_filename(f) for f in [
            WAKA_RU_FILENAME,
            WAKA_FR_FILENAME,
            WAKA_DE_FILENAME,
        ]]
