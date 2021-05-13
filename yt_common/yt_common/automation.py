import vapoursynth as vs

import acsuite
import argparse
import os
import random
import shutil
import string
import subprocess

from typing import Any, BinaryIO, Callable, List, Optional, Sequence, cast

from .config import Config
from .logging import log
from .source import FileSource

core = vs.core

AUDIO_ENCODE: str = "_audiogetter_encode.mka"


def bin_to_plat(binary: str) -> str:
    if os.name == "nt":
        return binary if binary.lower().endswith(".exe") else f"{binary}.exe"
    else:
        return binary if not binary.lower().endswith(".exe") else binary[:-len(".exe")]


def forward_signal(signum: int, frame: Any, process: Any) -> None:
    log.warn("Forwarding SIGINT")
    process.send_signal(signum)


class Encoder():
    clip: vs.VideoNode

    binary: str
    params: Sequence[str]
    force: bool

    out_template: str

    cleanup: List[str]

    def __init__(self, settings_path: str, binary: Optional[str] = None, force: bool = False) -> None:
        self.binary = binary if binary is not None else ""
        self.force = force
        self.cleanup = []

        self._get_encoder_settings(settings_path)

    def encode(self, clip: vs.VideoNode, filename: str, start: int = 0, end: int = 0) -> str:
        end = end if end != 0 else clip.num_frames

        outfile = self.out_template.format(filename=filename)

        if os.path.isfile(outfile) and not self.force:
            log.warn("Existing output detected, skipping encode!")
            return outfile

        params = [p.format(frames=end-start, filename=filename) for p in self.params]

        log.status("--- RUNNING ENCODE ---")

        print("+ " + " ".join([self.binary] + list(params)))

        process = subprocess.Popen([self.binary] + list(params), stdin=subprocess.PIPE)

        # i want the encoder to handle any ctrl-c so it exits properly
        # forward_to_proc = functools.partial(forward_signal, process=process)
        # signal.signal(signal.SIGINT, forward_to_proc)
        # turns out this didn't work out the way i had hoped

        clip[start:end].output(cast(BinaryIO, process.stdin), y4m=True)
        process.communicate()

        # vapoursynth should handle this itself but just in case
        if process.returncode != 0:
            log.error("--- ENCODE FAILED ---")
            raise BrokenPipeError(f"Pipe to {self.binary} broken")

        log.success("--- ENCODE FINISHED ---")
        self.cleanup.append(outfile)
        return outfile

    def _get_encoder_settings(self, settings_path: str) -> None:
        with open(settings_path, "r") as settings:
            keys = " ".join([line.strip() for line in settings if not line.strip().startswith("#")]).split(" ")

        # verify that the settings contain an output file template
        outputs = [k for k in keys[1:] if any([name == "filename" for _, name, _, _ in string.Formatter().parse(k)])]
        if not outputs or len(outputs) > 1:
            raise Exception("Failed to find unambiguous output file for encoder!")
        self.out_template = outputs[0]

        self.binary = bin_to_plat(keys[0]) if not self.binary else self.binary
        self.params = keys[1:]

    def do_cleanup(self) -> None:
        for f in self.cleanup:
            os.remove(f)
        self.cleanup = []


class AudioGetter():
    """
    TODO: really should modularize this a bit instead of assuming amazon->funi
    """
    config: Config
    src: FileSource

    audio_file: str
    audio_start: int
    video_src: Optional[vs.VideoNode]

    cleanup: List[str]

    def __init__(self, config: Config, src: FileSource) -> None:
        self.config = config
        self.src = src

        self.audio_start = 0
        self.video_src = None
        self.cleanup = []

    def trim_audio(self, ftrim: Optional[acsuite.types.Trim] = None) -> str:
        trims = self.src.get_audio()
        if not trims or len(trims) > 1:
            raise NotImplementedError("Please implement multifile trimming")
        audio_cut = acsuite.eztrim(trims[0].path, cast(acsuite.types.Trim, trims[0].trim), streams=0)[0]
        self.cleanup.append(audio_cut)

        if ftrim:
            audio_cut = acsuite.eztrim(audio_cut, ftrim, ref_clip=self.src.source())[0]
            self.cleanup.append(audio_cut)

        return audio_cut

    def encode_audio(self, path: str, args: List[str]) -> str:
        ffmpeg_args = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "panic",
            "-i", path,
            "-y",
            "-map", "0:a",
        ] + args + [AUDIO_ENCODE]
        print("+ " + " ".join(ffmpeg_args))
        subprocess.call(ffmpeg_args)

        self.cleanup.append(AUDIO_ENCODE)

        return AUDIO_ENCODE

    def do_cleanup(self) -> None:
        for f in self.cleanup:
            os.remove(f)
        self.cleanup = []


class SelfRunner():
    config: Config
    src: FileSource
    clip: vs.VideoNode

    workraw: bool

    video_file: str
    audio_file: str

    encoder: Encoder
    audio: AudioGetter

    profile: str

    def __init__(self, config: Config, source: FileSource, final_filter: Callable[[], vs.VideoNode],
                 workraw_filter: Optional[Callable[[], vs.VideoNode]] = None,
                 audio_codec: Optional[List[str]] = None) -> None:
        self.config = config
        self.src = source
        self.video_clean = False
        self.audio_clean = False

        parser = argparse.ArgumentParser(description=f"Encode {self.config.title} {self.config.desc}")
        if workraw_filter:
            parser.add_argument("-w", "--workraw", help="Encode workraw, fast x264.", action="store_true")
        parser.add_argument("-s", "--start", nargs='?', type=int, help="Start encode at frame START.")
        parser.add_argument("-e", "--end", nargs='?', type=int, help="Stop encode at frame END (inclusive).")
        parser.add_argument("-k", "--keep", help="Keep raw video", action="store_true")
        parser.add_argument("-b", "--encoder", type=str, help="Override detected encoder binary.")
        parser.add_argument("-f", "--force", help="Overwrite existing intermediaries.", action="store_true")
        parser.add_argument("-x", "--suffix", type=str, help="Change the suffix of the mux. \
                            Will be overridden by PROFILE if set.")
        parser.add_argument("-p", "--profile", type=str, help="Set the encoder profile. \
                            Overrides SUFFIX when set. Defaults to \"workraw\" when WORKRAW is set, else \"final.\"")
        parser.add_argument("-c", "--comparison", help="Output a comparison between workraw and final. \
                            Will search for the output file to include in comparison, if present.",
                            action="store_true")
        args = parser.parse_args()

        self.workraw = args.workraw if workraw_filter else False
        self.profile = "workraw" if self.workraw else "final"
        self.profile = args.profile or self.profile
        self.suffix = args.suffix if args.suffix is not None else "workraw" if self.workraw else "premux"
        self.suffix = args.profile or self.suffix

        self.clip = workraw_filter() if workraw_filter and self.workraw else final_filter()

        start = args.start if args.start is not None else 0
        if args.end is not None:
            if args.end < 0:
                end = self.clip.num_frames + args.end
            else:
                end = args.end + 1
        else:
            end = self.clip.num_frames

        if start < 0:
            raise ValueError("Start frame cannot be less than 0!")
        if start > self.clip.num_frames:
            raise ValueError("Start frame exceeds clip length!")
        if end < 0:
            raise ValueError("End frame cannot be less than 0!")
        if end > self.clip.num_frames:
            raise ValueError("End frame exceeds clip length!")
        if start >= end:
            raise ValueError("Start frame must be before end frame!")

        out_name = f"{self.config.title.lower()}_{self.config.desc}_{self.suffix}.mkv"

        if args.comparison and workraw_filter:
            log.status("Generating comparison...")
            if os.path.isfile(out_name):
                pmx = core.ffms2.Source(out_name)
                if pmx.num_frames == self.clip.num_frames:
                    pmx = pmx[start:end]
                gencomp(10, "comp", src=workraw_filter()[start:end], final=final_filter()[start:end], encode=pmx)
            else:
                gencomp(10, "comp", src=workraw_filter()[start:end], final=final_filter()[start:end])
            log.status("Comparison generated.")
            return

        settings_path = os.path.join(self.config.datapath, f"{self.profile}-settings")
        if not os.path.isfile(settings_path):
            raise FileNotFoundError(f"Failed to find {settings_path}!")

        self.encoder = Encoder(settings_path, args.encoder, args.force)
        self.video_file = self.encoder.encode(self.clip, f"{self.config.desc}_{self.suffix}_{start}_{end}",
                                              start, end)

        log.status("--- LOOKING FOR AUDIO ---")
        self.audio = AudioGetter(self.config, self.src)

        log.status("--- TRIMMING AUDIO ---")
        self.audio_file = self.audio.trim_audio((start, end))
        if audio_codec:
            log.status("--- TRANSCODING AUDIO ---")
            self.audio_file = self.audio.encode_audio(self.audio_file, audio_codec)

        try:
            log.status("--- MUXING FILE ---")
            if self._mux(out_name, start == 0 and end == self.clip.num_frames) != 0:
                raise Exception("mkvmerge failed")
        except Exception:
            log.error("--- MUXING FAILED ---")
            self.audio.do_cleanup()
            raise

        log.success("--- MUXING SUCCESSFUL ---")

        self.audio.do_cleanup()

        if not args.keep:
            self.encoder.do_cleanup()

        log.success("--- ENCODE COMPLETE ---")

    def _mux(self, name: str, chapters: bool = True) -> int:
        mkvtoolnix_args = [
            "mkvmerge",
            "--output", name,
            "--no-chapters", "--no-track-tags", "--no-global-tags", "--track-name", "0:",
            "--default-track", "0:yes",
            "(", self.video_file, ")",
            "--no-chapters", "--no-track-tags", "--no-global-tags", "--track-name", "0:",
            "--default-track", "0:yes", "--language", "0:jpn",
            "(", self.audio_file, ")",
            "--track-order", "0:0,0:1",
        ]
        if chapters:
            chap = [f for f in [f"{self.config.desc}.xml", "chapters.xml"] if os.path.isfile(f)]
            if len(chap) != 0:
                mkvtoolnix_args += [
                    "--chapters", chap[0],
                ]

        print("+ " + " ".join(mkvtoolnix_args))
        return subprocess.call(mkvtoolnix_args)


def gencomp(num: int = 10, path: str = "comp", matrix: str = "709",
            firstnum: int = 1, **clips: vs.VideoNode) -> None:
    lens = set(c.num_frames for c in clips.values())
    if len(lens) != 1:
        raise ValueError("gencomp: 'Clips must be equal length!'")

    frames = sorted(random.sample(range(lens.pop()), num))
    print("Sample frames: " + str(frames))

    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)

    for name, clip in clips.items():
        log.status(f"Rendering clip {name}")
        splice = clip[frames[0]]
        for f in frames[1:]:
            splice += clip[f]
        splice = splice.resize.Bicubic(format=vs.RGB24, matrix_in_s=matrix) \
            .imwri.Write("PNG", os.path.join(path, f"{name}%0{len(str(num))}d.png"), firstnum=firstnum)
        [splice.get_frame(f) for f in range(splice.num_frames)]
