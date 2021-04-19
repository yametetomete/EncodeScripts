import vapoursynth as vs

from yt_common import source
from yt_common.logging import log
from yt_common.config import Config

import os

from typing import List

TITLE: str = "Vivy"
TITLE_LONG: str = f"{TITLE} - Fluorite Eye's Song"
RESOLUTION: int = 1080
DATAPATH: str = os.path.dirname(__file__)

WAKA_RU_FILENAME: str = f"{TITLE}_{{epnum:02d}}_RU_HD.mp4"
WAKA_FR_FILENAME: str = f"{TITLE}_{{epnum:02d}}_FR_HD.mp4"
WAKA_DE_FILENAME: str = f"{TITLE} - Fluorite Eyes Song E{{epnum:02d}} [1080p][AAC][JapDub][GerSub][Web-DL].mkv"


core = vs.core


class VivyConfig(Config):
    def __init__(self, epnum: int) -> None:
        super().__init__(
            epnum,
            TITLE,
            TITLE_LONG,
            RESOLUTION,
            DATAPATH
        )


class VivySource(source.FunimationSource):
    def get_amazon(self) -> vs.VideoNode:
        # ep1-3 have good funi video, let's just use that
        if self.config.epnum < 4:
            raise FileNotFoundError()
        if not os.path.isfile(self.config.format_filename(source.AMAZON_FILENAME)):
            log.warn("Amazon not found, falling back to Funimation")
            raise FileNotFoundError()
        log.success("Found Amazon video")
        return core.ffms2.Source(self.config.format_filename(source.AMAZON_FILENAME))

    def get_waka_filenames(self) -> List[str]:
        return [self.config.format_filename(f) for f in [
            WAKA_RU_FILENAME,
            WAKA_FR_FILENAME,
            WAKA_DE_FILENAME,
        ]]
