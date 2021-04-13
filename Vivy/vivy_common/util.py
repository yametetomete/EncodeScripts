import vapoursynth as vs

import glob
import vsutil

from typing import Tuple, Union

core = vs.core

Range = Union[int, Tuple[int, int]]

FUNI_FILENAME: str = "[SubsPlease] Vivy - Fluorite Eye's Song - {epnum:02d} (1080p) [$CRC].mkv"
FUNI_INTRO: int = 289
WAKA_FILENAME: str = "Vivy_{epnum:02d}_RU_HD.mp4"


def glob_crc(pattern: str) -> str:
    res = glob.glob(glob.escape(pattern).replace("$CRC", "*"))
    if len(res) == 0:
        raise FileNotFoundError(f"File matching \"{pattern}\" not found!")
    return res[0]


def source(epnum: int) -> Tuple[vs.VideoNode, vs.VideoNode]:
    waka = vsutil.depth(core.ffms2.Source(WAKA_FILENAME.format(epnum=epnum)), 16)
    funi = vsutil.depth(core.ffms2.Source(glob_crc(FUNI_FILENAME.format(epnum=epnum))), 16)[FUNI_INTRO:]
    return waka, funi
