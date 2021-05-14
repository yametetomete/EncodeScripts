import vapoursynth as vs

from yt_common import source
from yt_common.config import Config
from yt_common.logging import log
from yt_common.source import AMAZON_FILENAME_VBR

import os

from typing import List

TITLE: str = "Vivy"
TITLE_LONG: str = f"{TITLE} - Fluorite Eye's Song"
RESOLUTION: int = 1080
DATAPATH: str = os.path.dirname(__file__)

WAKA_RU_FILENAME: str = f"{TITLE}_{{epnum:s}}_RU_HD.mp4"
WAKA_FR_FILENAME: str = f"{TITLE}_{{epnum:s}}_FR_HD.mp4"
WAKA_DE_FILENAME: str = f"{TITLE} - Fluorite Eyes Song E{{epnum:s}} [1080p][AAC][JapDub][GerSub][Web-DL].mkv"
AMAZON_FILENAME: str = "{title_long} - {epnum:s} (Amazon Prime VBR {resolution}p).mkv"


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
        if int(self.config.desc) < 4:
            raise FileNotFoundError()
        if not os.path.isfile(self.config.format_filename(AMAZON_FILENAME_VBR)):
            log.warn("Amazon not found, falling back to Funimation")
            raise FileNotFoundError()
        log.success("Found Amazon video")
        return self._open(self.config.format_filename(AMAZON_FILENAME_VBR))

    def get_waka_filenames(self) -> List[str]:
        return [self.config.format_filename(f) for f in [
            WAKA_RU_FILENAME,
            WAKA_FR_FILENAME,
            WAKA_DE_FILENAME,
        ]]
