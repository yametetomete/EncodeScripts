import vapoursynth as vs
from vsutil import join, split
from lvsfunc.misc import replace_ranges

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
LOGO: Range = (11640, 11805)
NO_SCALE: List[Range] = [
    (34544, 34685),  # next episode title
    (31646, 34043),  # ending credits
]
FORCE_SCALE: List[Range] = [
    (13385, 14686),  # chris henshin
    (240, 2157),  # credits in intro (if we don't descale, sraa can cause problems with the mask)
]
FADE_RANGES: List[FadeRange] = [
    # fading text elements don't like to be masked rip me
    FadeRange(ref=291, range_=(252, 347)),
    FadeRange(ref=404, range_=(378, 473)),
    FadeRange(ref=527, range_=(502, 597)),
    FadeRange(ref=676, range_=(648, 743)),
    FadeRange(ref=870, range_=(829, 924)),
    FadeRange(ref=978, range_=(949, 1044)),
    FadeRange(ref=1207, range_=(1162, 1257)),
    FadeRange(ref=1382, range_=(1353, 1448)),
    FadeRange(ref=1546, range_=(1477, 1572)),
    FadeRange(ref=1891, range_=(1861, 1956)),
    FadeRange(ref=2016, range_=(1989, 2084)),

    # title
    FadeRange(ref=2228, range_=(2159, 2240)),
]

W2X_DENOISE: List[Range] = []
if OP is not None:
    W2X_DENOISE.append(
        (OP[0]+1859, OP[0]+1896),  # flashy OP scene
    )

DEBAND_HARD: List[Range] = [(13490, 13592)]  # chris henshin
DEBAND_HARDER: List[Range] = [(13508, 13550)]  # chris henshin

src_ep = core.lsmas.LWLibavSource("../bdmv/KIXA_90893/BDMV/STREAM/00005.m2ts")
src_pv = core.lsmas.LWLibavSource("../bdmv/KIXA_90893/BDMV/STREAM/00006.m2ts")[:-24]
src_logo = core.lsmas.LWLibavSource("../bdmv/KIXA_90890/BDMV/STREAM/00005.m2ts")[18416]
src = src_ep + src_pv
src = src.fmtc.bitdepth(bits=16)
den = denoise(src)

y, u, v = split(den)
y = y.edgefixer.Continuity(top=3, left=4)
u = u.edgefixer.Continuity(top=2, left=3)
v = v.edgefixer.Continuity(top=2, left=3)
endcardfix = join([y, u, v])
prefiltered = replace_ranges(den, endcardfix, [(31601, 31645)])

final = compose(
    finalize,
    mask_logo(src=den, src_logo=src_logo, range=LOGO),
    deband(hard=DEBAND_HARD, harder=DEBAND_HARDER),
    w2x(w2x_range=W2X_DENOISE),
    descale(force_scale=FORCE_SCALE, no_scale=NO_SCALE, fade_ranges=FADE_RANGES)
)(prefiltered)

final.set_output()
