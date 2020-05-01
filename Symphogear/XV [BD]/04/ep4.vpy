import vapoursynth as vs
import lvsfunc as lvf
import kagefunc as kgf
import mvsfunc as mvf
import vardefunc as vrdf
import vsutil

from ytttfunc.adaptivegrain import adaptive_grain
from ytttfunc.replace_ranges import replace_ranges
from functools import partial

core = vs.core
core.max_cache_size = 32768

OP = (1248, 3644)
ED = (31889, 34046)
LOGO = [(14927, 15092)]
NO_SCALE = [(34461, 34547)]
FORCE_SCALE = [(10225, 11425), (19811, 20954)]
FADE_TEXT_REF = 3676
DESCALE_MASK = [(3646, 3726)]
W2X_DENOISE = [
	(OP[0]+1859, OP[0]+1896) # flashy OP scene
]
DEBAND_HARD = [(19916, 20006)] # bikki's henshin banding
DEBAND_HARDER = [(19934, 19970)]

src_ep = core.lsmas.LWLibavSource("../bd2/KIXA_90889/BDMV/STREAM/00005.m2ts")
src_pv = core.lsmas.LWLibavSource("../bd2/KIXA_90889/BDMV/STREAM/00006.m2ts")[:-24]
src_ncop = core.lsmas.LWLibavSource("../bd2/KIXA_90889/BDMV/STREAM/00007.m2ts")[24:-24]
src_nced = core.lsmas.LWLibavSource("../bd2/KIXA_90889/BDMV/STREAM/00008.m2ts")[24:-24]
src = src_ep + src_pv
src = src.fmtc.bitdepth(bits=16)

denoisechroma = core.knlm.KNLMeansCL(src, d=1, a=2, h=0.45, channels="UV", device_type='gpu', device_id=0)
denoiseluma = core.knlm.KNLMeansCL(src, d=3, a=2, h=0.4, channels="Y", device_type='gpu', device_id=0)
denoise = core.std.ShufflePlanes([denoiseluma, denoisechroma], planes=[0, 1, 2], colorfamily=vs.YUV)

logo_mask = core.imwri.Read("../common/mask_2.png")
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
text_mask = core.std.Expr([Y[FADE_TEXT_REF], Yd[FADE_TEXT_REF].resize.Bicubic(1920, 1080, filter_param_a=1/3, filter_param_b=1/3)], 'x y - abs')
text_mask = vsutil.iterate(text_mask, core.std.Maximum, 4)
text_mask = text_mask.std.Binarize(4000)
Ydmask = core.std.MaskedMerge(Yline, Y, text_mask)
Yfinal = replace_ranges(Yline, Ydmask, DESCALE_MASK)

scaled = core.std.ShufflePlanes([Yfinal, denoise], planes=[0, 1, 2], colorfamily=vs.YUV)

logo_merge = core.std.MaskedMerge(scaled, denoise, logo_mask)

scaled = replace_ranges(scaled, denoise, NO_SCALE)
scaled = replace_ranges(scaled, logo_merge, LOGO)

rgb = scaled.resize.Bicubic(1920, 1080, format=vs.RGBS, matrix_in_s="709")
w2x = rgb.w2xnvk.Waifu2x(noise=1, scale=1, model=2).resize.Bicubic(format=scaled.format.id, matrix_s="709")

bm3d = mvf.BM3D(scaled, sigma=[0, 5], ref=w2x)
bm3d = core.std.ShufflePlanes([w2x, bm3d], planes=[0, 1, 2], colorfamily=vs.YUV)
denoise_2 = replace_ranges(scaled, bm3d, W2X_DENOISE)

line = kgf.retinex_edgemask(denoise_2).std.Binarize(9500).rgvs.RemoveGrain(3).std.Inflate()
nf3kdb = denoise_2.neo_f3kdb.Deband(range=18, y=32, cb=24, cr=24, grainy=24, grainc=0, output_depth=16, sample_mode=4, keep_tv_range=True)
nf3kdb = core.std.MaskedMerge(nf3kdb, denoise_2, line)
placebo = denoise_2.placebo.Deband(iterations=3, threshold=3, radius=24, grain=4)
placebo2 = denoise_2.placebo.Deband(iterations=3, threshold=5, radius=32, grain=4)
deband = replace_ranges(nf3kdb, placebo, DEBAND_HARD)
deband = replace_ranges(deband, placebo2, DEBAND_HARDER)

# mask OP/ED credits, stolen from varde
credit_op_m = vrdf.dcm(deband, src[OP[0]:OP[1]+1], src_ncop[:OP[1]-OP[0]+1], OP[0], OP[1], 2, 2)
credit_ed_m = vrdf.dcm(deband, src[ED[0]:ED[1]+1], src_nced[:ED[1]-ED[0]+1], ED[0], ED[1], 2, 2)
credit_m = core.std.Expr([credit_op_m, credit_ed_m], 'x y +')
credit = core.std.MaskedMerge(deband, denoise, credit_m)

final = credit
final = kgf.adaptive_grain(final, 0.3)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()
