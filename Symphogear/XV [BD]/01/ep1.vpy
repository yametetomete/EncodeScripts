import vapoursynth as vs

from toolz.functoolz import compose
from typing import List, Optional, Tuple

import sys
sys.path.append("..")

from xv_common import (FadeRange, Range, denoise, descale, w2x, deband,
                       mask_logo, finalize)  # noqa: E402

core = vs.core
core.max_cache_size = 1024

OP: Optional[Tuple[int, int]] = None
ED: Optional[Tuple[int, int]] = None
LOGO: Range = (20777, 20942)
NO_SCALE: List[Range] = [(30836, 33230), (34463, 34553)]
FORCE_SCALE: List[Range] = [(4015, 5159)]
DETAIL_MASK: List[Range] = [(256, 1546)]
FADE_RANGES: List[FadeRange] = [
    FadeRange(ref=960, range_=(943, 1026)),
]

W2X_DENOISE: List[Range] = []
if OP is not None:
    W2X_DENOISE.append(
        (OP[0]+1859, OP[0]+1896),  # flashy OP scene
    )

DEBAND_HARD: List[Range] = [(4120, 4210)]
DEBAND_HARDER: List[Range] = [(4138, 4174)]

src_ep = core.lsmas.LWLibavSource("../bdmv/KIXA_90888/BDMV/STREAM/00003.m2ts")
src_pv = core.lsmas.LWLibavSource("../bdmv/KIXA_90888/BDMV/STREAM/00004.m2ts")[:-24]
src_logo = core.lsmas.LWLibavSource("../bdmv/KIXA_90890/BDMV/STREAM/00005.m2ts")[18416]
src = src_ep + src_pv
src = src.fmtc.bitdepth(bits=16)
den = denoise(src)

final = compose(
    finalize,
    mask_logo(src=den, src_logo=src_logo, range=LOGO),
    deband(hard=DEBAND_HARD, harder=DEBAND_HARDER),
    w2x(w2x_range=W2X_DENOISE),
    descale(force_scale=FORCE_SCALE, no_scale=NO_SCALE, fade_ranges=FADE_RANGES, detail_ranges=DETAIL_MASK)
)(den)

final.set_output()
