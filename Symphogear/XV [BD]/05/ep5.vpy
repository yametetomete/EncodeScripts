import vapoursynth as vs

import sys
sys.path.append("..")

from xv_common import FadeRange, denoise, descale, w2x, deband, ncop_mask, finalize
from functools import partial
from toolz.functoolz import compose

core = vs.core
core.max_cache_size = 1024

OP = (1272, 3668)
ED = (31889, 34046)
NO_SCALE = [(34514, 34600)]
FORCE_SCALE = [(22384, 23376)]
FADE_RANGES = [FadeRange(ref=3700,  range_=(3670, 3751)),   # title
               FadeRange(ref=17383, range_=(17300, 17436))  # logo
]
W2X_DENOISE = [
	(OP[0]+1859, OP[0]+1896) # flashy OP scene
]
DEBAND_HARD = []
DEBAND_HARDER = []

src_ep = core.lsmas.LWLibavSource("../bdmv/KIXA_90890/BDMV/STREAM/00003.m2ts")
src_pv = core.lsmas.LWLibavSource("../bdmv/KIXA_90890/BDMV/STREAM/00004.m2ts")[:-24]
src_op = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00007.m2ts")[24:-24]
src_ed = core.lsmas.LWLibavSource("../bdmv/KIXA_90889/BDMV/STREAM/00008.m2ts")[24:-24]
src = src_ep + src_pv
src = src.fmtc.bitdepth(bits=16)
den = denoise(src)

descale = partial(descale, force_scale=FORCE_SCALE, no_scale=NO_SCALE, fade_ranges=FADE_RANGES)
w2x = partial(w2x, w2x_range=W2X_DENOISE)
deband = partial(deband, hard=DEBAND_HARD, harder=DEBAND_HARDER)
ncop_mask = partial(ncop_mask, src=den, op=OP, ed=ED, src_op=src_op, src_ed=src_ed)
final = compose(
                finalize,
                ncop_mask,
                deband,
                w2x,
                descale
               )(den)
final.set_output()
