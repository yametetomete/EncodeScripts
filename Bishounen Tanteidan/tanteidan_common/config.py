import vapoursynth as vs

from yt_common.config import Config
from yt_common.logging import log
from yt_common.source import FunimationSource, AMAZON_FILENAME

import os

from typing import List

TITLE: str = "Tanteidan"
TITLE_LONG: str = "Bishounen Tanteidan"
TITLE_ENG: str = "Pretty Boy Detective Club"
RESOLUTION: int = 1080
SUBGROUP: str = ""
DATAPATH: str = os.path.dirname(__file__)

WAKA_RU_FILENAME: str = f"{TITLE_ENG.replace(' ', '')}_{{epnum:02d}}_RU_HD.mp4"
WAKA_FR_FILENAME: str = f"{TITLE_ENG.replace(' ', '')}_{{epnum:02d}}_FR_HD.mp4"
WAKA_DE_FILENAME: str = f"{TITLE_ENG} E{{epnum:02d}} [{RESOLUTION}p][AAC][JapDub][GerSub][Web-DL].mkv"


core = vs.core


class PrettyConfig(Config):
    def __init__(self, epnum: int) -> None:
        super().__init__(
            epnum,
            TITLE,
            TITLE_LONG,
            RESOLUTION,
            DATAPATH
        )


class PrettySource(FunimationSource):
    def get_amazon(self) -> vs.VideoNode:
        # ep1 has good funi video, let's just use that
        if self.config.epnum < 2:
            log.success("Funi has good video for this episode, skipping Amazon.")
            raise FileNotFoundError()
        if not os.path.isfile(self.config.format_filename(AMAZON_FILENAME)):
            log.warn("Amazon not found, falling back to Funimation")
            raise FileNotFoundError()
        log.success("Found Amazon video")
        return core.ffms2.Source(self.config.format_filename(AMAZON_FILENAME))

    def get_waka_filenames(self) -> List[str]:
        return [self.config.format_filename(f) for f in [
            WAKA_RU_FILENAME,
            WAKA_FR_FILENAME,
            WAKA_DE_FILENAME,
        ]]
