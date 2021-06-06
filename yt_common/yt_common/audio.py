import acsuite
import os

from abc import ABC, abstractmethod
from subprocess import call
from typing import TYPE_CHECKING, List, Set, NamedTuple, Optional

from .config import Config
from .util import get_temp_filename

if TYPE_CHECKING:
    from .source import FileSource


AUDIO_PFX: str = "_audio_temp_"


class AudioEncoder(ABC):
    @abstractmethod
    def encode_audio(self, afile: str) -> str:
        pass


class FFAudio(AudioEncoder):
    def encode_audio(self, afile: str) -> str:
        out = get_temp_filename(prefix="_ffaudio_encode_", suffix=".mka")
        ffmpeg_args = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "panic",
            "-i", afile,
            "-y",
            "-map", "0:a",
        ] + self.codec_args() + [out]
        print("+ " + " ".join(ffmpeg_args))
        call(ffmpeg_args)
        return out

    @abstractmethod
    def codec_args(self) -> List[str]:
        pass


class CodecPassthrough(AudioEncoder):
    def encode_audio(self, afile: str) -> str:
        return afile


class CodecOpus(FFAudio):
    bitrate: int

    def __init__(self, bitrate: int = 192) -> None:
        self.bitrate = bitrate

    def codec_args(self) -> List[str]:
        return ["-c:a", "libopus", "-b:a", f"{self.bitrate}k", "-sample_fmt", "s16"]


class CodecFdkAac(FFAudio):
    bitrate: int

    def __init__(self, bitrate: int = 256) -> None:
        self.bitrate = bitrate

    def codec_args(self) -> List[str]:
        return ["-c:a", "libfdk_aac", "-b:a", f"{self.bitrate}k", "-sample_fmt", "s16"]


class CodecFlac(FFAudio):
    def codec_args(self) -> List[str]:
        return ["-c:a", "flac"]


class AudioStream(NamedTuple):
    stream_index: int  # zero-indexed, ignores video streams
    codec: AudioEncoder
    name: str = ""
    language: str = "jpn"


class AudioTrimmer():
    config: Config
    src: "FileSource"
    cleanup: Set[str]

    def __init__(self, config: Config, src: "FileSource") -> None:
        self.config = config
        self.src = src
        self.cleanup = set()

    def trim_audio(self, ftrim: Optional[acsuite.types.Trim] = None) -> str:
        streams = sorted(self.src.audio_streams(), key=lambda s: s.stream_index)
        if len(streams) == 0:
            return ""
        trims = self.src.audio_src()
        ffmpeg = acsuite.ffmpeg.FFmpegAudio()

        tlist: List[str] = []
        for t in trims:
            audio_cut = acsuite.eztrim(t.path, t.trim or (0, None), ref_clip=self.src.audio_ref(),
                                       outfile=get_temp_filename(prefix=AUDIO_PFX+"cut_", suffix=".mka"),
                                       streams=[s.stream_index for s in streams])[0]
            self.cleanup.add(audio_cut)
            tlist.append(audio_cut)

        if len(tlist) > 1:
            audio_cut = ffmpeg.concat(*tlist)
            self.cleanup.add(audio_cut)

        if ftrim:
            audio_cut = acsuite.eztrim(audio_cut, ftrim, ref_clip=self.src.source(),
                                       outfile=get_temp_filename(prefix=AUDIO_PFX+"fcut_", suffix=".mka"))[0]
            self.cleanup.add(audio_cut)

        if len(streams) > 1:
            splits = [get_temp_filename(prefix=AUDIO_PFX+"split_", suffix=".mka") for _ in range(0, len(streams))]
            ffmpeg.split(audio_cut, splits)
            self.cleanup |= set(splits)
            encode = [streams[i].codec.encode_audio(f) for i, f in enumerate(splits)]
            self.cleanup |= set(encode)
            audio_cut = get_temp_filename(prefix=AUDIO_PFX+"join_", suffix=".mka")
            ffmpeg.join(audio_cut, *encode)
        else:
            audio_cut = streams[0].codec.encode_audio(audio_cut)

        self.cleanup.add(audio_cut)

        return audio_cut

    def do_cleanup(self) -> None:
        for f in self.cleanup:
            os.remove(f)
        self.cleanup.clear()
