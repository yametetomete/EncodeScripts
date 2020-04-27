#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core

ts = "cap/Senki Zesshou Symphogear XV - 02 (MX).d2v"
src = core.d2v.Source(ts)
src = src.vivtc.VFM(1).vivtc.VDecimate()

ac = audiocutter.AudioCutter()

audio = ac.split(src, [(799, 2557, "Intro"), (2558, 4947, "OP"), (6625, 20267, "Part A"),
(21706, 35252, "Part B"), (35253, 37409, "ED"), (37410, 37963, "Part C")])

ac.ready_qp_and_chapters(audio)

audio.set_output(0)

if __name__ == "__main__":
	ac.cut_audio("mx_audio.m4a", audio_source="cap/mx_adjusted.m4a")
