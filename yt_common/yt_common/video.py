import vapoursynth as vs
import os
import string
import subprocess

from lvsfunc.render import clip_async_render

from typing import BinaryIO, List, NamedTuple, Optional, Sequence, Tuple, cast

from .logging import log
from .util import bin_to_plat


class Zone(NamedTuple):
    r: Tuple[int, int]
    b: float


class VideoEncoder():
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
