import vapoursynth as vs

from toolz.functoolz import compose
from typing import List, Optional, Tuple

import sys
sys.path.append("..")

from xv_common import FadeRange, Range, denoise, descale, w2x, deband, finalize  # noqa: E402

core = vs.core

OP: Optional[Tuple[int, int]] = (0, 2399)
NO_SCALE: List[Range] = []
FORCE_SCALE: List[Range] = []
FADE_RANGES: List[FadeRange] = []

W2X_DENOISE: List[Range] = []
if OP is not None:
    W2X_DENOISE.append(
        (OP[0]+1859, OP[0]+1896),  # flashy OP scene
    )

DEBAND_HARD: List[Range] = []
DEBAND_HARDER: List[Range] = []

src = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00007.m2ts")[24:-24]
src = src.fmtc.bitdepth(bits=16)
den = denoise(src)

final = compose(
    finalize,
    deband(hard=DEBAND_HARD, harder=DEBAND_HARDER),
    w2x(w2x_range=W2X_DENOISE),
    descale(force_scale=FORCE_SCALE, no_scale=NO_SCALE, fade_ranges=FADE_RANGES)
)(den)

final.set_output()
