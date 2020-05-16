import vapoursynth as vs

from toolz.functoolz import compose
from typing import List, Optional, Tuple

import sys
sys.path.append("..")

from xv_common import (FadeRange, Range, denoise, descale, w2x, deband,
                       mask_oped, mask_logo, finalize)  # noqa: E402

core = vs.core
core.max_cache_size = 1024

OP: Optional[Tuple[int, int]] = (1750, 4148)
ED: Optional[Tuple[int, int]] = (31339, 33495)
LOGO: Range = (17724, 17874)
NO_SCALE: List[Range] = [(34477, 34563)]
FORCE_SCALE: List[Range] = [(8369, 9325)]
FADE_RANGES: List[FadeRange] = [
    FadeRange(ref=4211, range_=(4150, 4231)),
]

W2X_DENOISE: List[Range] = [
    (21562, 21729),  # noise from the pink shit
    (21882, 21951),  # more pink shit
    (23087, 23252),  # big zoom with lots of lights
]
if OP is not None:
    W2X_DENOISE.append(
        (OP[0]+1859, OP[0]+1896),  # flashy OP scene
    )

DEBAND_HARD: List[Range] = []
DEBAND_HARDER: List[Range] = []

# ep2 has the wrong OP, stolen from varde
src_ep = core.lsmas.LWLibavSource("../bdmv/KIXA_90888/BDMV/STREAM/00005.m2ts")
src_pv = core.lsmas.LWLibavSource("../bdmv/KIXA_90888/BDMV/STREAM/00006.m2ts")[:-24]
src_oped = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00003.m2ts")
src_op = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00007.m2ts")[24:-24]
src_ed = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00008.m2ts")[24:-24]
src_logo = core.lsmas.LWLibavSource("../bdmv/KIXA_90890/BDMV/STREAM/00005.m2ts")[18416]
op = src_oped[744:3141]
src = src_ep[:1750] + op + src_ep[4147:4150] + src_ep[4149+1:] + src_pv
src = src.fmtc.bitdepth(bits=16)
den = denoise(src)

final = compose(
    finalize,
    mask_logo(src=den, src_logo=src_logo, range=LOGO),
    mask_oped(src=den, op=OP, ed=ED, src_op=src_op, src_ed=src_ed),
    deband(hard=DEBAND_HARD, harder=DEBAND_HARDER),
    w2x(w2x_range=W2X_DENOISE),
    descale(force_scale=FORCE_SCALE, no_scale=NO_SCALE, fade_ranges=FADE_RANGES)
)(den)

final.set_output()
