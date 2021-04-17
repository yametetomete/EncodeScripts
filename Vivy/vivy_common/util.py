import vapoursynth as vs

import acsuite
import argparse
import os
import functools
import glob
import signal
import string
import subprocess
import vsutil

from typing import Any, BinaryIO, Callable, List, Optional, Sequence, Tuple, Union, cast

core = vs.core

Range = Union[int, Tuple[int, int]]

TITLE: str = "Vivy"
TITLE_LONG: str = f"{TITLE} - Fluorite Eye's Song"
RESOLUTION: int = 1080

SUBGROUP = "YameteTomete"

SUBSPLS_FILENAME: str = f"[SubsPlease] {TITLE_LONG} - {{epnum:02d}} ({RESOLUTION}p) [$CRC].mkv"
ER_FILENAME: str = f"[Erai-raws] {TITLE_LONG} - {{epnum:02d}} [{RESOLUTION}p][Multiple Subtitle].mkv"
FUNI_INTRO: int = 289
WAKA_FILENAME: str = f"{TITLE}_{{epnum:02d}}_RU_HD.mp4"
AMAZON_FILENAME: str = f"{TITLE_LONG} - {{epnum:02d}} (Amazon Prime CBR {RESOLUTION}p).mkv"

AUDIO_OVERRIDE: str = "audio.mka"
AUDIO_FMT: List[str] = [".mka", ".aac", ".wav", ".flac", ".mp3", ".ogg", ".opus", ".m4a"]
AFV_FMT: List[str] = [".mkv", ".mp4", ".webm"]
AUDIO_CUT: str = "_audiogetter_cut.mka"

STATUS: str = '\033[94m'
WARNING: str = '\033[93m'
ERROR: str = '\033[91m'
SUCCESS: str = '\033[92m'
RESET: str = '\033[0m'


def glob_crc(pattern: str) -> str:
    res = glob.glob(glob.escape(pattern).replace("$CRC", "*"))
    if len(res) == 0:
        raise FileNotFoundError(f"File matching \"{pattern}\" not found!")
    return res[0]


def get_ref(epnum: int) -> vs.VideoNode:
    if epnum >= 4:
        if os.path.isfile(AMAZON_FILENAME.format(epnum=epnum)):
            return core.ffms2.Source(AMAZON_FILENAME.format(epnum=epnum))
        else:
            print(f"{WARNING}Amazon video not found, dehardsubbing with new funi encode{RESET}")

    try:
        return core.ffms2.Source(glob_crc(SUBSPLS_FILENAME.format(epnum=epnum)))[FUNI_INTRO:]
    except FileNotFoundError:
        pass

    if not os.path.isfile(ER_FILENAME.format(epnum=epnum)):
        raise FileNotFoundError("Failed to find valid reference video")

    return core.ffms2.Source(ER_FILENAME.format(epnum=epnum))[FUNI_INTRO:]


def source(epnum: int) -> Tuple[vs.VideoNode, vs.VideoNode]:
    waka = vsutil.depth(core.ffms2.Source(WAKA_FILENAME.format(epnum=epnum)), 16)
    ref = vsutil.depth(get_ref(epnum), 16)
    return waka, ref


def bin_to_plat(binary: str) -> str:
    if os.name == "nt":
        return binary if binary.lower().endswith(".exe") else f"{binary}.exe"
    else:
        return binary if not binary.lower().endswith(".exe") else binary[:-len(".exe")]


def forward_signal(signum: int, frame: Any, process: Any) -> None:
    print(f"{WARNING}Forwarding SIGINT{RESET}")
    process.send_signal(signum)


class Encoder():
    clip: vs.VideoNode

    binary: str
    params: Sequence[str]
    force: bool

    out_template: str

    cleanup: List[str]

    def __init__(self, epnum: int, settings_path: str,
                 binary: Optional[str] = None, force: bool = False) -> None:
        self.binary = binary if binary is not None else ""
        self.force = force
        self.cleanup = []

        self._get_encoder_settings(settings_path)

    def encode(self, clip: vs.VideoNode, filename: str, start: int = 0, end: int = 0) -> str:
        end = end if end != 0 else clip.num_frames

        outfile = self.out_template.format(filename=filename)

        if os.path.isfile(outfile) and not self.force:
            print(f"{WARNING}Existing output detected, skipping encode!{RESET}")
            return outfile

        params = [p.format(frames=end-start, filename=filename) for p in self.params]

        print(f"{STATUS}--- RUNNING ENCODE ---{RESET}")

        print("+ " + " ".join([self.binary] + list(params)))

        process = subprocess.Popen([self.binary] + list(params), stdin=subprocess.PIPE)

        # i want the encoder to handle any ctrl-c so it exits properly
        forward_to_proc = functools.partial(forward_signal, process=process)
        signal.signal(signal.SIGINT, forward_to_proc)

        clip[start:end].output(cast(BinaryIO, process.stdin), y4m=True)
        process.communicate()

        # vapoursynth should handle this itself but just in case
        if process.returncode != 0:
            print(f"{ERROR}--- ENCODE FAILED ---{RESET}")
            raise BrokenPipeError(f"Pipe to {self.binary} broken")

        print(f"{SUCCESS}--- ENCODE FINISHED ---{RESET}")
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
    audio_file: str
    audio_start: int
    video_src: Optional[vs.VideoNode]

    cleanup: List[str]

    def __init__(self, epnum: int, override: Optional[str] = None) -> None:
        self.audio_start = 0
        self.video_src = None
        self.cleanup = []

        if override is not None:
            if os.path.isfile(override):
                self.audio_file = override
            else:
                raise FileNotFoundError(f"Audio file {override} not found!")

        # drop "audio.m4a" into the folder and it'll get used
        if os.path.isfile(AUDIO_OVERRIDE):
            self.audio_file = AUDIO_OVERRIDE
            return

        # look for amazon first
        if os.path.isfile(AMAZON_FILENAME.format(epnum=epnum)):
            self.audio_file = AMAZON_FILENAME.format(epnum=epnum)
            self.video_src = core.ffms2.Source(AMAZON_FILENAME.format(epnum=epnum))
            print(f"{SUCCESS}Found Amazon audio{RESET}")
            return

        # as of Ep4 SubsPlease is using new funi 128kbps aac while erai has 256kbps still
        try:
            if os.path.isfile(ER_FILENAME.format(epnum=epnum)):
                self.audio_file = ER_FILENAME.format(epnum=epnum)
                self.video_src = core.ffms2.Source(ER_FILENAME.format(epnum=epnum))
            if os.path.isfile(glob_crc(SUBSPLS_FILENAME.format(epnum=epnum))):
                self.audio_file = glob_crc(SUBSPLS_FILENAME.format(epnum=epnum))
                self.video_src = core.ffms2.Source(glob_crc(SUBSPLS_FILENAME.format(epnum=epnum)))
                if (epnum >= 4):
                    print(f"{WARNING}Using SubsPlease, audio may be worse than Erai-Raws{RESET}")
            else:
                raise FileNotFoundError()
        except FileNotFoundError:
            print(f"{ERROR}Could not find audio{RESET}")
            raise

        self.audio_start = FUNI_INTRO
        print(f"{WARNING}No Amazon audio, falling back to Funi{RESET}")

    def trim_audio(self, src: vs.VideoNode,
                   trims: Union[acsuite.Trim, List[acsuite.Trim], None] = None) -> str:
        if isinstance(trims, tuple):
            trims = [trims]

        if trims is None or len(trims) == 0:
            if self.audio_start == 0:
                trims = [(None, None)]
            else:
                trims = [(self.audio_start, None)]
        else:
            if self.audio_start != 0:
                trims = [(s+self.audio_start if s is not None and s >= 0 else s,
                          e+self.audio_start if e is not None and e > 0 else e)
                         for s, e in trims]

        if os.path.isfile(AUDIO_CUT):
            os.remove(AUDIO_CUT)

        acsuite.eztrim(self.video_src if self.video_src else src, trims,
                       self.audio_file, AUDIO_CUT, quiet=True)

        self.cleanup.append(AUDIO_CUT)

        return AUDIO_CUT

    def do_cleanup(self) -> None:
        for f in self.cleanup:
            os.remove(f)
        self.cleanup = []


class SelfRunner():
    clip: vs.VideoNode
    epnum: int

    workraw: bool

    video_file: str
    audio_file: str

    encoder: Encoder
    audio: AudioGetter

    def __init__(self, epnum: int, final_filter: Callable[[], vs.VideoNode],
                 workraw_filter: Optional[Callable[[], vs.VideoNode]] = None) -> None:
        self.epnum = epnum
        self.video_clean = False
        self.audio_clean = False

        parser = argparse.ArgumentParser(description=f"Encode {TITLE} Episode {epnum:02d}")
        if workraw_filter:
            parser.add_argument("-w", "--workraw", help="Encode workraw, fast x264", action="store_true")
        parser.add_argument("-s", "--start", nargs='?', type=int, help="Start encode at frame START")
        parser.add_argument("-e", "--end", nargs='?', type=int, help="Stop encode at frame END (inclusive)")
        parser.add_argument("-k", "--keep", help="Keep raw video", action="store_true")
        parser.add_argument("-c", "--encoder", type=str, help="Override detected encoder binary")
        parser.add_argument("-f", "--force", help="Overwrite existing intermediaries", action="store_true")
        parser.add_argument("-a", "--audio", type=str, help="Force audio file")
        parser.add_argument("-x", "--suffix", type=str, default="premux", help="Change the suffix of the mux")
        parser.add_argument("-d", "--no-metadata", help="No extra metadata in premux", action="store_true")
        args = parser.parse_args()

        self.workraw = args.workraw if workraw_filter else False
        self.suffix = args.suffix if not self.workraw else "workraw"

        self.clip = workraw_filter() if workraw_filter and self.workraw else final_filter()

        basename = "workraw-settings" if self.workraw else "final-settings"
        settings_path = os.path.join(os.path.dirname(__file__), basename)

        if not os.path.isfile(settings_path):
            raise FileNotFoundError("Failed to find {basename}!")

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

        self.encoder = Encoder(epnum, settings_path, args.encoder, args.force)
        self.video_file = self.encoder.encode(self.clip, f"{epnum:02d}_{start}_{end}", start, end)

        print(f"{STATUS}--- LOOKING FOR AUDIO ---{RESET}")
        self.audio = AudioGetter(self.epnum, args.audio)

        print(f"{STATUS}--- TRIMMING AUDIO ---{RESET}")
        self.audio_file = self.audio.trim_audio(self.clip, (start, end))

        try:
            print(f"{STATUS}--- MUXING FILE ---{RESET}")
            if self._mux(f"{TITLE.lower()}_{epnum:02d}_{args.suffix}.mkv", not args.no_metadata,
                         not args.no_metadata and start == 0 and end == self.clip.num_frames) != 0:
                raise Exception("mkvmerge failed")
        except Exception:
            print(f"{ERROR}--- MUXING FAILED ---{RESET}")
            self.audio.do_cleanup()
            raise

        print(f"{SUCCESS}--- MUXING SUCCESSFUL ---{RESET}")

        self.audio.do_cleanup()

        if not args.keep:
            self.encoder.do_cleanup()

        print(f"{SUCCESS}--- ENCODE COMPLETE ---{RESET}")

    def _mux(self, name: str, metadata: bool = True, chapters: bool = True) -> int:
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
        if metadata:
            mkvtoolnix_args += [
                "--title", f"[{SUBGROUP}] {TITLE_LONG} - {self.epnum:02d}",
            ]

        if chapters:
            chap = [f for f in ["{self.epnum:02d}.xml", "chapters.xml"] if os.path.isfile(f)]
            if len(chap) != 0:
                mkvtoolnix_args += [
                    "--chapters", chap[0],
                ]

        print("+ " + " ".join(mkvtoolnix_args))
        return subprocess.call(mkvtoolnix_args)
