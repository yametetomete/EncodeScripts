#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core

ts = "cap/Senki Zesshou Symphogear XV - 03 (MX).d2v"
src = core.d2v.Source(ts)
src = src.vivtc.VFM(1).vivtc.VDecimate()

ac = audiocutter.AudioCutter()

audio = ac.split(src, [(810, 1554, "Intro"), (1555, 3951, "OP"), (5630, 18386, "Part A"),
                       (19826, 35815, "Part B"), (35816, 37973, "ED")])

ac.ready_qp_and_chapters(audio)

audio.set_output(0)

if __name__ == "__main__":
	ac.cut_audio("mx_audio.m4a", audio_source="cap/mx_adjusted.m4a")
