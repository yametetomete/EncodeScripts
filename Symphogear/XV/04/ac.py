#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core

ts = "cap/Senki Zesshou Symphogear XV - 04 (MX).d2v"
src = core.d2v.Source(ts)
src = src.vivtc.VFM(1).vivtc.VDecimate()

ac = audiocutter.AudioCutter()

audio = ac.split(src, [(139, 1395, "Intro"), (1396, 3783, "OP"), (5462, 16826, "Part A"),
                       (18265, 35143, "Part B"), (35144, 37302, "ED")])

ac.ready_qp_and_chapters(audio)

audio.set_output(0)

if __name__ == "__main__":
	ac.cut_audio("mx_audio.m4a", audio_source="cap/mx_adjusted.m4a")
