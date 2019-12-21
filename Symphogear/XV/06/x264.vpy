import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import adjust
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 32768

opstart, edstart = 1726, 31888

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 06 [1080p].mkv")
src = core.fmtc.bitdepth(src, bits=16)
deblock = core.deblock.Deblock(src, quant=16)
Y, U, V = kgf.split(deblock)
Y = kgf.inverse_scale(Y, height=872, kernel="bicubic", b=1/3, c=1/3, mask_detail=True,
	 descale_mask_zones=f"[{opstart} {opstart+3000}] [{edstart} {edstart+2159}]")
Y = nnedi3_rpow2(Y).resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.ShufflePlanes([Y, U, V], planes=[0], colorfamily=vs.YUV)

dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.20, cont=1.20)

undim = fvf.rfs(scaled, dim1, mappings=f"[{opstart+1613} {opstart+1659}]]")
undim = fvf.rfs(undim, dim2, mappings=f"[{opstart+1665} {opstart+1693}] [25567 26014]")
undim = fvf.rfs(undim, dim3, mappings="[26254 26283]")

denoisechroma = core.knlm.KNLMeansCL(undim, d=1, a=2, h=0.45, channels="UV", device_type='gpu', device_id=0)
denoiseluma = core.knlm.KNLMeansCL(undim, d=3, a=2, h=0.4, channels="Y", device_type='gpu', device_id=0)
denoise = core.std.ShufflePlanes([denoiseluma, denoisechroma], planes=[0, 1, 2], colorfamily=vs.YUV)
taa = vstaa.TAAmbk(denoise,aatype='Nnedi3')
db = taa.f3kdb.Deband(range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(denoise)
final = core.std.MaskedMerge(db, taa, mask)
final = kgf.adaptive_grain(final)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()

#vspipe -y "x264.vpy" - | ffmpeg -i pipe: -c:v libx264 -tune animation -crf 16 -preset slower -aq-mode 3 -pix_fmt yuv420p10le -x264-params no-dct-decimate:no-fast-pskip -y "x264.mp4"