import os
import subprocess

from abc import ABC, abstractmethod
from typing import List, Union


class Config():
    desc: str
    title: str
    title_long: str
    resolution: int
    datapath: str

    def __init__(self, desc: Union[int, str], title: str, title_long: str, resolution: int, datapath: str) -> None:
        self.desc = desc if isinstance(desc, str) else f"{desc:02d}"
        self.title = title
        self.title_long = title_long
        self.resolution = resolution
        self.datapath = datapath

    def format_filename(self, filename: str) -> str:
        fname = filename.format(epnum=self.desc, title=self.title,
                                title_long=self.title_long, resolution=self.resolution)
        return os.path.join(f"../{self.desc}/", fname)

    def encode_audio(self, afile: str) -> str:
        return afile  # default: passthrough


class AudioEncoder(ABC):
    @abstractmethod
    def encode_audio(self, afile: str) -> str:
        pass


class FFAudio(AudioEncoder):
    def encode_audio(self, afile: str) -> str:
        ffmpeg_args = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "panic",
            "-i", afile,
            "-y",
            "-map", "0:a",
        ] + self.codec_args() + ["_ffaudio_encode.mka"]
        print("+ " + " ".join(ffmpeg_args))
        subprocess.call(ffmpeg_args)
        return "_ffaudio_encode.mka"

    @abstractmethod
    def codec_args(self) -> List[str]:
        pass


class OpusMixin(FFAudio):
    def codec_args(self) -> List[str]:
        return ["-c:a", "libopus", "-b:a", "192k", "-sample_fmt", "s16"]


class FdkAacMixin(FFAudio):
    def codec_args(self) -> List[str]:
        return ["-c:a", "libfdk_aac", "-b:a", "256k", "-sample_fmt", "s16"]


class FlacMixin(FFAudio):
    def codec_args(self) -> List[str]:
        return ["-c:a", "flac"]
