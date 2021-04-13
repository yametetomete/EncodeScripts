#!/usr/bin/env python3
import vapoursynth as vs

import acsuite
import os
import sys

from subprocess import DEVNULL, call

from vivy_common.util import FUNI_FILENAME, FUNI_INTRO, glob_crc

EPNUM: int = int(sys.argv[1])

ac = acsuite.AC()
core = vs.core

funi: str = glob_crc(os.path.join(f"{EPNUM:02d}", FUNI_FILENAME.format(epnum=EPNUM)))
src = core.ffms2.Source(funi)

if __name__ == "__main__":
    funi_audio: str = f"{EPNUM:02d}/funi.aac"
    if not os.path.exists(funi_audio):
        call(["ffmpeg",
              "-i", funi,
              "-vn",
              "-sn",
              "-map_metadata", "-1",
              "-c:a", "copy",
              funi_audio],
             stdout=DEVNULL, stderr=DEVNULL
             )
    ac.eztrim(src, (FUNI_INTRO, 0), funi_audio, f"{EPNUM:02d}/{EPNUM:02d}_cut.aac")
