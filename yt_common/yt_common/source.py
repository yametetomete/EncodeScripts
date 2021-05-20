import vapoursynth as vs

from acsuite.types import Trim

from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range
from vsutil import depth

import glob
import os

from abc import ABC, abstractmethod
from typing import Any, List, NamedTuple, Optional, Tuple, Union

from .config import Config
from .logging import log

core = vs.core

SUBSPLS_FILENAME: str = "[SubsPlease] {title_long} - {epnum} ({resolution}p) [$GLOB].mkv"
ER_FILENAME: str = "[Erai-raws] {title_long} - {epnum} [v0][{resolution}p]$GLOB.mkv"
FUNI_INTRO: int = 289
AMAZON_FILENAME_CBR: str = "{title_long} - {epnum} (Amazon Prime CBR {resolution}p).mkv"
AMAZON_FILENAME_VBR: str = "{title_long} - {epnum} (Amazon Prime VBR {resolution}p).mkv"


class FileTrim(NamedTuple):
    path: str
    trim: Optional[Trim]

    def apply_trim(self, clip: vs.VideoNode) -> vs.VideoNode:
        if self.trim is None:
            return clip
        s, e = self.trim
        if s is None and e is None:
            return clip
        if s is None:
            return clip[:e]
        if e is None:
            return clip[s:]
        return clip[s:e]


def waka_replace(src: vs.VideoNode, wakas: List[vs.VideoNode], ranges: List[List[Range]]
                 ) -> Tuple[vs.VideoNode, List[vs.VideoNode]]:
    if len(wakas) == 0:
        return src, wakas
    new_wakas = []
    for waka, r in zip(wakas, ranges):
        tmp = src
        src = replace_ranges(src, waka, r)
        new_wakas.append(replace_ranges(waka, tmp, r))

    return src, new_wakas


def glob_filename(pattern: str) -> str:
    res = glob.glob(glob.escape(pattern).replace("$GLOB", "*"))
    if len(res) == 0:
        raise FileNotFoundError(f"File matching \"{pattern}\" not found!")
    return res[0]


class FileSource(ABC):
    def _open(self, path: str) -> vs.VideoNode:
        return depth(core.lsmas.LWLibavSource(path), 16) if path.lower().endswith(".m2ts") \
            else depth(core.ffms2.Source(path), 16)

    @abstractmethod
    def get_audio(self) -> List[FileTrim]:
        pass

    @abstractmethod
    def source(self) -> vs.VideoNode:
        pass


class SimpleSource(FileSource):
    src: List[FileTrim]

    def __init__(self, src: Union[FileTrim, List[FileTrim]]) -> None:
        self.src = src if isinstance(src, list) else [src]

    def get_audio(self) -> List[FileTrim]:
        return self.src

    def source(self) -> vs.VideoNode:
        return core.std.Splice([s.apply_trim(self._open(s.path)) for s in self.src])


class DehardsubFileFinder(FileSource):
    config: Config

    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    def get_waka_filenames(self) -> List[str]:
        pass

    @abstractmethod
    def get_ref(self) -> vs.VideoNode:
        pass

    def source(self) -> vs.VideoNode:
        return self.get_ref()

    def dhs_source(self) -> Tuple[List[vs.VideoNode], vs.VideoNode]:
        wakas: List[vs.VideoNode] = []
        for f in [self.config.format_filename(f) for f in self.get_waka_filenames()]:
            if not os.path.isfile(f):
                log.warn("Missing a waka!")
                continue
            wakas.append(self._open(f))
        ref = self.get_ref()
        return wakas, ref


class FunimationSource(DehardsubFileFinder):
    ref_is_funi: bool

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.ref_is_funi = False
        super().__init__(*args, **kwargs)

    def get_audio(self) -> List[FileTrim]:
        if self.ref_is_funi:
            return [FileTrim(self.get_funi_filename(), (FUNI_INTRO, None))]

        if os.path.isfile(self.config.format_filename(AMAZON_FILENAME_CBR)):
            return [FileTrim(self.config.format_filename(AMAZON_FILENAME_CBR), None)]

        if os.path.isfile(self.config.format_filename(AMAZON_FILENAME_VBR)):
            return [FileTrim(self.config.format_filename(AMAZON_FILENAME_VBR), None)]

        raise FileNotFoundError("Failed to find audio that should exist!")

    def get_amazon(self) -> vs.VideoNode:
        if not os.path.isfile(self.config.format_filename(AMAZON_FILENAME_CBR)):
            log.warn("Amazon not found, falling back to Funimation")
            raise FileNotFoundError()
        log.success("Found Amazon video")
        return self._open(self.config.format_filename(AMAZON_FILENAME_CBR))

    def get_funi_filename(self) -> str:
        try:
            return glob_filename(self.config.format_filename(ER_FILENAME))
        except FileNotFoundError:
            pass

        try:
            return glob_filename(self.config.format_filename(SUBSPLS_FILENAME))
        except FileNotFoundError:
            log.error("Could not find funimation video")
            raise

    def get_funi(self) -> vs.VideoNode:
        return self._open(self.get_funi_filename())[FUNI_INTRO:]

    def get_ref(self) -> vs.VideoNode:
        try:
            return self.get_amazon()
        except FileNotFoundError:
            self.ref_is_funi = True
            return self.get_funi()
