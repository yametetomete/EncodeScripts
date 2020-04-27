#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core

ts = "cap/Senki Zesshou Symphogear - 07 (MX).d2v"
src = core.d2v.Source(ts)
src = src.vivtc.VFM(1).vivtc.VDecimate()

ac = audiocutter.AudioCutter()

audio = ac.split(src, [(812, 5775), (7455, 19633), (21072, 37973)])

ac.ready_qp_and_chapters(audio)

audio.set_output(0)

if __name__ == "__main__":
	ac.cut_audio("mx_audio.m4a", audio_source="cap/mx_adjusted.m4a")
