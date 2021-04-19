import vapoursynth as vs

import vsutil

import glob
import os

from abc import ABC, abstractmethod
from typing import List, Tuple

from .config import Config
from .log import warn, error, success

core = vs.core

SUBSPLS_FILENAME: str = "[SubsPlease] {title_long} - {epnum:02d} ({resolution}p) [$CRC].mkv"
ER_FILENAME: str = "[Erai-raws] {title_long} - {epnum:02d} [v0][{resolution}p].mkv"
FUNI_INTRO: int = 289
AMAZON_FILENAME: str = "{title_long} - {epnum:02d} (Amazon Prime CBR {resolution}p).mkv"


def glob_crc(pattern: str) -> str:
    res = glob.glob(glob.escape(pattern).replace("$CRC", "*"))
    if len(res) == 0:
        raise FileNotFoundError(f"File matching \"{pattern}\" not found!")
    return res[0]


class DehardsubFileFinder(ABC):
    config: Config

    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    def get_waka_filenames(self) -> List[str]:
        pass

    @abstractmethod
    def get_ref(self) -> vs.VideoNode:
        pass

    def source(self) -> Tuple[List[vs.VideoNode], vs.VideoNode]:
        wakas = [vsutil.depth(core.ffms2.Source(self.config.format_filename(f)), 16)
                 for f in self.get_waka_filenames()]
        ref = vsutil.depth(self.get_ref(), 16)
        return wakas, ref


class FunimationSource(DehardsubFileFinder):
    def get_amazon(self) -> vs.VideoNode:
        if not os.path.isfile(self.config.format_filename(AMAZON_FILENAME)):
            warn("Amazon not found, falling back to Funimation")
            raise FileNotFoundError()
        success("Found Amazon video")
        return core.ffms2.Source(self.config.format_filename(AMAZON_FILENAME))

    def get_funi_filename(self) -> str:
        if os.path.isfile(self.config.format_filename(ER_FILENAME)):
            return self.config.format_filename(ER_FILENAME)

        error("Erai-raws not found, falling back to SubsPlease")
        return glob_crc(self.config.format_filename(SUBSPLS_FILENAME))

    def get_funi(self) -> vs.VideoNode:
        return core.ffms2.Source(self.get_funi_filename())[FUNI_INTRO:]

    def get_ref(self) -> vs.VideoNode:
        try:
            return self.get_amazon()
        except FileNotFoundError:
            return self.get_funi()
