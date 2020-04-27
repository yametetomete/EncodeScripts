#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter
from subprocess import call

core = vs.core

ts = "cap/Senki Zesshou Symphogear XV - 06 (BS11).d2v"
src = core.d2v.Source(ts)
src = src.vivtc.VFM(1).vivtc.VDecimate()

ac = audiocutter.AudioCutter()

audio = ac.split(src, [(680, 4805), (6484, 20773), (22211, 37844)])

ac.ready_qp_and_chapters(audio)

audio.set_output(0)

if __name__ == "__main__":
	ac.cut_audio("bs11_audio.m4a", audio_source="cap/bs11_adjusted.m4a")
