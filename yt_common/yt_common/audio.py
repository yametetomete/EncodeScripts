from abc import ABC, abstractmethod
from subprocess import call
from typing import List, NamedTuple

from .util import get_temp_filename


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
