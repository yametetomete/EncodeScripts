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
LOGO: Range = (15790, 15955)
NO_SCALE: List[Range] = [
    (30162, 32320),  # ending credits
]
FORCE_SCALE: List[Range] = [
    (0, 1348),  # credits in intro (if we don't descale, sraa can cause problems with the mask)
]
FADE_RANGES: List[FadeRange] = [
    # fading text elements don't like to be masked rip me
    FadeRange(ref=58, range_=(9, 92)),
    FadeRange(ref=159, range_=(129, 212)),
    FadeRange(ref=251, range_=(219, 291)),
    FadeRange(ref=346, range_=(300, 383)),
    FadeRange(ref=489, range_=(420, 491)),
    FadeRange(ref=709, range_=(666, 748)),
    FadeRange(ref=810, range_=(784, 866)),
    FadeRange(ref=927, range_=(877, 957)),
    FadeRange(ref=1036, range_=(959, 1037)),
    FadeRange(ref=1227, range_=(1167, 1250)),
    FadeRange(ref=1303, range_=(1264, 1347)),

    # title
    FadeRange(ref=1576, range_=(1508, 1591)),
]

W2X_DENOISE: List[Range] = []
if OP is not None:
    W2X_DENOISE.append(
        (OP[0]+1859, OP[0]+1896),  # flashy OP scene
    )

DEBAND_HARD: List[Range] = []
DEBAND_HARDER: List[Range] = []

src_ep = core.lsmas.LWLibavSource("../bdmv/KIXA_90893/BDMV/STREAM/00008.m2ts")
src_logo = core.lsmas.LWLibavSource("../bdmv/KIXA_90890/BDMV/STREAM/00005.m2ts")[18416]
src = src_ep
src = src.fmtc.bitdepth(bits=16)
den = denoise(src)

final = compose(
    finalize,
    mask_logo(src=den, src_logo=src_logo, range=LOGO),
    deband(hard=DEBAND_HARD, harder=DEBAND_HARDER),
    w2x(w2x_range=W2X_DENOISE),
    descale(force_scale=FORCE_SCALE, no_scale=NO_SCALE, fade_ranges=FADE_RANGES)
)(den)

final.set_output()
