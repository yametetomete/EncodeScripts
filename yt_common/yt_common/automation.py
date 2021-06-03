import vapoursynth as vs

import acsuite
import argparse
import os
import random
import shutil
import string
import subprocess
import tempfile

from lvsfunc.render import clip_async_render

from typing import Any, BinaryIO, Callable, List, NamedTuple, Optional, Sequence, Set, Tuple, cast

from .chapters import Chapter, Edition, make_chapters, make_qpfile
from .config import Config
from .logging import log
from .source import FileSource

core = vs.core

AUDIO_PFX: str = "_audiogetter_temp_"


def get_temp_filename(prefix: str = "", suffix: str = "") -> str:
    return f"{prefix}{next(tempfile._get_candidate_names())}{suffix}"  # type: ignore


def bin_to_plat(binary: str) -> str:
    if os.name == "nt":
        return binary if binary.lower().endswith(".exe") else f"{binary}.exe"
    else:
        return binary if not binary.lower().endswith(".exe") else binary[:-len(".exe")]


def forward_signal(signum: int, frame: Any, process: Any) -> None:
    log.warn("Forwarding SIGINT")
    process.send_signal(signum)


class Zone(NamedTuple):
    r: Tuple[int, int]
    b: float


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

    def encode(self, clip: vs.VideoNode, filename: str, start: int = 0, end: int = 0,
               zones: Optional[List[Zone]] = None, qpfile: Optional[str] = None,
               timecode_file: Optional[str] = None, want_timecodes: bool = False) -> Tuple[str, List[float]]:
        end = end if end != 0 else clip.num_frames
        want_timecodes = True if timecode_file else want_timecodes

        outfile = self.out_template.format(filename=filename)

        if os.path.isfile(outfile) and not self.force:
            log.warn("Existing output detected, skipping encode!")
            return outfile, []

        params: List[str] = []
        for p in self.params:
            if p == "$ZONES":
                if zones:
                    zones.sort(key=lambda z: z.r[0])
                    params.append("--zones")
                    zargs: List[str] = []
                    for z in zones:
                        if z.r[0] - start >= 0 and z.r[0] < end:
                            s = z.r[0] - start
                            e = z.r[1] - start
                            e = e if e < end - start else end - start - 1
                            zargs.append(f"{s},{e},b={z.b}")
                    params.append("/".join(zargs))
            elif p == "$QPFILE":
                if qpfile:
                    params += ["--qpfile", qpfile]
            else:
                params.append(p.format(frames=end-start, filename=filename, qpfile="qpfile.txt"))

        log.status("--- RUNNING ENCODE ---")

        print("+ " + " ".join([self.binary] + list(params)))

        process = subprocess.Popen([self.binary] + list(params), stdin=subprocess.PIPE)

        # i want the encoder to handle any ctrl-c so it exits properly
        # forward_to_proc = functools.partial(forward_signal, process=process)
        # signal.signal(signal.SIGINT, forward_to_proc)
        # turns out this didn't work out the way i had hoped

        # use the python renderer only if we need timecodes because it's slower
        timecodes: List[float] = []
        if want_timecodes:
            timecode_io = open(timecode_file, "w") if timecode_file else None
            timecodes = clip_async_render(clip[start:end], cast(BinaryIO, process.stdin), timecode_io)
        else:
            clip[start:end].output(cast(BinaryIO, process.stdin), y4m=True)
        process.communicate()

        # vapoursynth should handle this itself but just in case
        if process.returncode != 0:
            log.error("--- ENCODE FAILED ---")
            raise BrokenPipeError(f"Pipe to {self.binary} broken")

        log.success("--- ENCODE FINISHED ---")
        self.cleanup.append(outfile)
        return outfile, timecodes

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
    config: Config
    src: FileSource
    cleanup: Set[str]

    def __init__(self, config: Config, src: FileSource) -> None:
        self.config = config
        self.src = src
        self.cleanup = set()

    def trim_audio(self, ftrim: Optional[acsuite.types.Trim] = None) -> str:
        trims = self.src.audio_src()

        tlist: List[str] = []
        for t in trims:
            audio_cut = acsuite.eztrim(t.path, t.trim or (0, None), ref_clip=self.src.audio_ref(),
                                       outfile=get_temp_filename(prefix=AUDIO_PFX, suffix=".mka"),
                                       streams=0)[0]
            self.cleanup.add(audio_cut)
            tlist.append(audio_cut)

        if len(tlist) > 1:
            ffmpeg = acsuite.ffmpeg.FFmpegAudio()
            audio_cut = ffmpeg.concat(*tlist)
            self.cleanup.add(audio_cut)

        if ftrim:
            audio_cut = acsuite.eztrim(audio_cut, ftrim, ref_clip=self.src.source(),
                                       outfile=get_temp_filename(prefix=AUDIO_PFX, suffix=".mka"))[0]
            self.cleanup.add(audio_cut)

        audio_cut = self.config.encode_audio(audio_cut)
        self.cleanup.add(audio_cut)

        return audio_cut

    def do_cleanup(self) -> None:
        for f in self.cleanup:
            os.remove(f)
        self.cleanup.clear()


class SelfRunner():
    config: Config
    src: FileSource
    clip: vs.VideoNode

    workraw: bool

    video_file: str
    audio_file: str
    timecodes: List[float]
    timecode_file: Optional[str]
    qpfile: Optional[str]

    encoder: Encoder
    audio: AudioGetter

    profile: str

    def __init__(self, config: Config, source: FileSource, final_filter: Callable[[], vs.VideoNode],
                 workraw_filter: Optional[Callable[[], vs.VideoNode]] = None,
                 chapters: Optional[List[Chapter]] = None,
                 editions: Optional[List[Edition]] = None,
                 zones: Optional[List[Zone]] = None) -> None:
        self.config = config
        self.src = source
        self.video_clean = False
        self.audio_clean = False
        self.qpfile = None

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
        parser.add_argument("-a", "--audio-only", help="Only process audio, no video.", action="store_true")
        args = parser.parse_args()

        self.workraw = args.workraw if workraw_filter else False
        self.profile = "workraw" if self.workraw else "final"
        self.profile = args.profile or self.profile
        self.suffix = args.suffix if args.suffix is not None \
            else "workraw" if self.workraw \
            else args.profile if args.profile \
            else "premux"

        self.clip = workraw_filter() if workraw_filter and self.workraw else final_filter()

        start = args.start or 0
        if args.end is not None:
            if args.end < 0:
                end = self.clip.num_frames + args.end
            else:
                end = args.end + 1
        else:
            end = self.clip.num_frames
        # audio needs to be trimmed relative to source,
        # acsuite can do the conversions itself but is end-exclusive
        audio_end = args.end + 1 if args.end and args.end > 0 else args.end

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

        out_name = f"{self.config.title.lower().replace(' ', '_')}_{self.config.desc}_{self.suffix}"

        if args.audio_only:
            out_name += ".mka"
            self._do_audio(start, audio_end, out_name=out_name)
            self.audio.do_cleanup()
            log.success("--- AUDIO ENCODE COMPLETE ---")
            return

        out_name += ".mkv"

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

        if (editions or chapters) and (start == 0 and end == self.clip.num_frames):
            self.qpfile = "qpfile.txt"
            make_qpfile(self.qpfile, chapters=chapters, editions=editions)

        settings_path = os.path.join(self.config.datapath, f"{self.profile}-settings")
        if not os.path.isfile(settings_path):
            raise FileNotFoundError(f"Failed to find {settings_path}!")

        self.encoder = Encoder(settings_path, args.encoder, args.force)
        # we only want to generate timecodes if vfr, otherwise we can just calculate them
        self.timecode_file = f"{self.config.desc}_{self.suffix}_{start}_{end}_timecodes.txt" \
            if self.clip.fps_den == 0 else None
        self.video_file, self.timecodes = self.encoder.encode(self.clip,
                                                              f"{self.config.desc}_{self.suffix}_{start}_{end}",
                                                              start, end, zones, self.qpfile, self.timecode_file)

        # calculate timecodes if cfr and we didn't generate any (we shouldn'tve)
        self.timecodes = [round(float(1e9*f*(1/self.clip.fps)))/1e9 for f in range(0, self.clip.num_frames + 1)] \
            if self.clip.fps_den != 0 and len(self.timecodes) == 0 else self.timecodes

        self._do_audio(start, audio_end)

        if (editions or chapters) and (start == 0 and end == self.clip.num_frames):
            log.status("--- GENERATING CHAPTERS  ---")
            make_chapters(self.timecodes, f"{self.config.desc}.xml", chapters=chapters, editions=editions)

        try:
            log.status("--- MUXING FILE ---")
            if self._do_mux(out_name, start == 0 and end == self.clip.num_frames) != 0:
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

    def _do_audio(self, start: int, end: int, out_name: Optional[str] = None) -> None:
        log.status("--- LOOKING FOR AUDIO ---")
        self.audio = AudioGetter(self.config, self.src)

        log.status("--- TRIMMING AUDIO ---")
        self.audio_file = self.audio.trim_audio((start, end))
        if out_name:
            shutil.copy(self.audio_file, out_name)
            self.audio_file = out_name

    def _do_mux(self, name: str, chapters: bool = True) -> int:
        tcargs = ["--timecodes", f"0:{self.timecode_file}"] if self.timecode_file else []
        mkvtoolnix_args = [
            "mkvmerge",
            "--output", name,
            "--no-chapters", "--no-track-tags", "--no-global-tags", "--track-name", "0:",
            "--default-track", "0:yes",
        ] + tcargs + [
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
