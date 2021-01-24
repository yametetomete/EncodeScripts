import vapoursynth as vs

from toolz.functoolz import compose
from typing import List

import sys
sys.path.append("..")

from xv_common import FadeRange, Range, denoise, descale, deband, finalize  # noqa: E402

core = vs.core

NO_SCALE: List[Range] = []
FORCE_SCALE: List[Range] = []
FADE_RANGES: List[FadeRange] = []

DEBAND_HARD: List[Range] = []
DEBAND_HARDER: List[Range] = []

src = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00008.m2ts")[24:-24]
src = src.fmtc.bitdepth(bits=16)
den = denoise(src)

final = compose(
    finalize,
    deband(hard=DEBAND_HARD, harder=DEBAND_HARDER),
    descale(force_scale=FORCE_SCALE, no_scale=NO_SCALE, fade_ranges=FADE_RANGES)
)(den)

final.set_output()
