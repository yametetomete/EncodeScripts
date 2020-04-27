import os

import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import vsutil
from nnedi3_rpow2 import nnedi3_rpow2

from ytttfunc import adaptivegrain


core = vs.core
core.max_cache_size = 1024

src = core.lsmas.LWLibavSource("KIXA_90893/BDMV/Stream/00007.m2ts")[24:-24]
src = core.fmtc.bitdepth(src, bits=16)

Y = vsutil.get_y(src)

Y800 = kgf.inverse_scale(Y, height=800, kernel="bicubic", b=1/3, c=1/3, mask_detail=True)
Y800 = nnedi3_rpow2(Y800).resize.Spline36(1920, 1080, format=vs.GRAY16)

Y872 = kgf.inverse_scale(Y, height=872, kernel="bicubic", b=1/3, c=1/3, mask_detail=True)
Y872 = nnedi3_rpow2(Y872).resize.Spline36(1920, 1080, format=vs.GRAY16)

Yd = fvf.rfs(Y872, Y800, "[7944 8687]")
scaled = core.std.ShufflePlanes([Yd, src], planes=[0, 1, 2], colorfamily=vs.YUV)

final = scaled
final = adaptivegrain.adaptive_grain(final)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()
