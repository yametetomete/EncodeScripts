#!/usr/bin/env python3

import vapoursynth as vs
import audiocutter

core = vs.core

ts = "cap/Senki Zesshou Symphogear XV - 11 (MX).d2v"
src = core.d2v.Source(ts)
src = src.vivtc.VFM(1).vivtc.VDecimate()

ac = audiocutter.AudioCutter()

audio = ac.split(src, [(795, 6572), (8251, 18992), (20431, 37957)])

ac.ready_qp_and_chapters(audio)

audio.set_output(0)

if __name__ == "__main__":
    ac.cut_audio("mx_audio.m4a", audio_source="cap/mx_adjusted.m4a")
