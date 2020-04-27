import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 32768

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 03 [1080p].mkv")
src = fvf.Depth(src, 16)
scaled = kgf.inverse_scale(src, height=872, kernel="lanczos", taps=5, mask_detail=True)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
denoise = kgf.hybriddenoise(scaled, knl=0.5, sigma=1, radius1=0)
taa = vstaa.TAAmbk(denoise,aatype='Nnedi3')
db = taa.f3kdb.Deband(range=12, y=60, cb=40, cr=40, grainy=15, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(denoise)
final = core.std.MaskedMerge(db, taa, mask)
final = kgf.adaptive_grain(final)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()