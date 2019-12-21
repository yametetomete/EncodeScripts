import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 8192

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 01 [1080p].mkv")
src = fvf.Depth(src, 16)
scaled = kgf.inverse_scale(src, height=872, kernel="lanczos", taps=5, mask_detail=True)
scaled = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
scaled = kgf.hybriddenoise(scaled, knl=0.5, sigma=1, radius1=0)
db = scaled.f3kdb.Deband(range=12, y=60, cb=40, cr=40, grainy=15, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(scaled).std.Binarize(5000)
final = core.std.MaskedMerge(db, scaled, mask)
final = fvf.Depth(final, 10)
final = kgf.adaptive_grain(final)
final.set_output()

#ffmpeg
#vspipe -y "x264.vpy" - | ffmpeg -i pipe: -c:v libx264 -tune animation -crf 16 -pix_fmt yuv420p10 -preset slow -y "test1.mp4"