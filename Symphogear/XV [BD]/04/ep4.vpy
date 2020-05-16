import vapoursynth as vs

from toolz.functoolz import compose
from typing import List, Optional, Tuple

import sys
sys.path.append("..")

from xv_common import (FadeRange, Range, denoise, descale, w2x, deband,
                       mask_oped, mask_logo, finalize)  # noqa: E402

core = vs.core
core.max_cache_size = 1024

OP: Optional[Tuple[int, int]] = (1248, 3644)
ED: Optional[Tuple[int, int]] = (31889, 34046)
LOGO: Range = (14927, 15092)
NO_SCALE: List[Range] = [(34461, 34547)]
FORCE_SCALE: List[Range] = [(10225, 11425), (19811, 20954)]
FADE_RANGES: List[FadeRange] = [
    FadeRange(ref=3676, range_=(3646, 3726)),  # title
]

W2X_DENOISE: List[Range] = []
if OP is not None:
    W2X_DENOISE.append(
        (OP[0]+1859, OP[0]+1896),  # flashy OP scene
    )

DEBAND_HARD: List[Range] = [(19916, 20006)]  # bikki's henshin banding
DEBAND_HARDER: List[Range] = [(19934, 19970)]

src_ep = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00005.m2ts")
src_pv = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00006.m2ts")[:-24]
src_op = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00007.m2ts")[24:-24]
src_ed = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00008.m2ts")[24:-24]
src_logo = core.lsmas.LWLibavSource("../bdmv/KIXA_90890/BDMV/STREAM/00005.m2ts")[18416]
src = src_ep + src_pv
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
