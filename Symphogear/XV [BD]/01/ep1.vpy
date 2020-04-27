import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import mvsfunc as mvf
import vsutil

from ytttfunc.adaptivegrain import adaptive_grain
from ytttfunc.replace_ranges import replace_ranges
from functools import partial

core = vs.core
core.max_cache_size = 1024

LOGO = [(20777, 20942)]
NO_SCALE = [(30836, 33230), (34463, 34553)]
FORCE_SCALE = [(4015, 5159)]

src_ep = core.lsmas.LWLibavSource("bdmv/KIXA_90888/BDMV/STREAM/00003.m2ts")
src_pv = core.lsmas.LWLibavSource("bdmv/KIXA_90888/BDMV/STREAM/00004.m2ts")[:-24]
src = src_ep + src_pv
src = src.fmtc.bitdepth(bits=16)

denoisechroma = core.knlm.KNLMeansCL(src, d=1, a=2, h=0.45, channels="UV", device_type='gpu', device_id=0)
denoiseluma = core.knlm.KNLMeansCL(src, d=3, a=2, h=0.4, channels="Y", device_type='gpu', device_id=0)
denoise = core.std.ShufflePlanes([denoiseluma, denoisechroma], planes=[0, 1, 2], colorfamily=vs.YUV)

logo_mask = core.imwri.Read("mask_2.png")
logo_mask = logo_mask.resize.Bilinear(format=src.format.id, matrix_s="709")

Y = vsutil.get_y(denoise)

def sraa_frameeval(n, clip):
	frame = clip.get_frame(n)
	if frame.height < 1080:
		rfactor = 2.5
	else:
		rfactor = 1.5
	return lvf.upscaled_sraa(clip.resize.Bicubic(frame.width, frame.height), rfactor=rfactor, h=1080, ar=16/9)

edge = kgf.retinex_edgemask(Y, .0001).std.Binarize(10000)

Ys = lvf.smart_descale(Y, [871, 872, 873], kernel="bicubic", b=1/3, c=1/3, thr=0.003)
Yf = lvf.smart_descale(Y, [871, 872, 873], kernel="bicubic", b=1/3, c=1/3, thr=0)
Yd = replace_ranges(Ys, Yf, FORCE_SCALE)
Yd = Yd.resize.Bicubic(format=vs.GRAY16)
Ysraa = Yd.std.FrameEval(partial(sraa_frameeval, clip=Yd))
Ysraa = Ysraa.resize.Spline36(1920, 1080, format=vs.GRAY16)
Yline = core.std.MaskedMerge(Y, Ysraa, edge)

scaled = core.std.ShufflePlanes([Yline, denoise], planes=[0, 1, 2], colorfamily=vs.YUV)

logo_merge = core.std.MaskedMerge(scaled, denoise, logo_mask)

scaled = replace_ranges(scaled, denoise, NO_SCALE)
scaled = replace_ranges(scaled, logo_merge, LOGO)

line = kgf.retinex_edgemask(scaled).std.Binarize(9500).rgvs.RemoveGrain(3).std.Inflate()
deband = scaled.neo_f3kdb.Deband(range=18, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16, sample_mode=4)
deband = core.std.MaskedMerge(deband, scaled, line)

final = deband
final = adaptive_grain(final, 0.3)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()