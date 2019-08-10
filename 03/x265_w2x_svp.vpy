import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import adjust
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 32768

#source
src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 03 [1080p].mkv")
src = src.std.Trim(first=8730, last=9815)
src = src.std.AssumeFPS(fpsnum=24000, fpsden=1001)

#deblock
src = core.fmtc.bitdepth(src, bits=16)
deblock = core.deblock.Deblock(src, quant=16)

#rescale
#Y, U, V = kgf.split(deblock)
#Y = kgf.inverse_scale(Y, height=872, kernel="bicubic", b=1/3, c=1/3, mask_detail=True)
#Y = nnedi3_rpow2(Y).resize.Spline36(1920, 1080, format=vs.GRAY16)
#scaled = core.std.ShufflePlanes([Y, U, V], planes=[0], colorfamily=vs.YUV)
scaled = kgf.inverse_scale(deblock, height=872, kernel="bicubic", b=1/3, c=1/3, mask_detail=True)
scaled = core.fmtc.resample(scaled, css="420", kernel="lanczos")
scaled = core.fmtc.bitdepth(scaled, bits=16)

#denoise, let w2x do this?
#denoisechroma = core.knlm.KNLMeansCL(scaled, d=1, a=2, h=0.45, channels="UV", device_type='gpu', device_id=0)
#denoiseluma = core.knlm.KNLMeansCL(scaled, d=3, a=2, h=0.4, channels="Y", device_type='gpu', device_id=0)
#denoise = core.std.ShufflePlanes([denoiseluma, denoisechroma], planes=[0, 1, 2], colorfamily=vs.YUV)

#taa
taa = vstaa.TAAmbk(scaled,aatype='Nnedi3')

#deband
db = taa.f3kdb.Deband(range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(taa)
maskmerge = core.std.MaskedMerge(db, taa, mask)

#w2x
upscalewx = core.fmtc.bitdepth(maskmerge, bits=32)
upscalewx = core.fmtc.resample(upscalewx, css="444", kernel="lanczos")
upscalewx = core.caffe.Waifu2x(upscalewx, noise=0, scale=4, block_w=218, block_h=218, model=3, cudnn=True, processor=0, tta=False, batch=9)
upscalewx = core.fmtc.bitdepth(upscalewx, bits=16, dmode=3)
upscalewx = core.resize.Spline36(upscalewx,width=3840,height=2160)
upscalewx = core.fmtc.resample(upscalewx, css="420", kernel="lanczos")

#svp
svp = core.fmtc.bitdepth(upscalewx, bits=8, dmode=3)
svp1superparams = """{
pel:4,
gpu:1
}"""
svp1vectorsparams = """{
block: {
	w: 16,
	h: 16,
	overlap: 3
},
main: {
	coarse: {
		width: 3840,
		satd: true,
		trymany: true
	}
},
penalty: {
	lambda:	40.0,
	plevel: 4.0
},
refine: [{
	thsad:400
}]
}"""
svp2smoothparams = """{
rate: {
	num: 48,
	den: 1,
	abs: true
},
algo: 13,
mask: {
	cover: 150,
	area: 100
},
scene: {
	mode: 3
}
}"""

super  = core.svp1.Super(svp, svp1superparams)
vectors= core.svp1.Analyse(super["clip"], super["data"], svp, svp1vectorsparams)
smooth = core.svp2.SmoothFps(svp, super["clip"], super["data"], vectors["clip"], vectors["data"], svp2smoothparams)
svp = core.std.AssumeFPS(smooth, fpsnum=smooth.fps_num, fpsden=smooth.fps_den)

final = kgf.adaptive_grain(svp)
final = core.fmtc.bitdepth(final, bits=10)

final.set_output()
#vspipe -y "x265_w2x_svp.vpy" - | ffmpeg -i pipe: -c:v libx265 -tune animation -crf 17 -preset slower -x265-params aq-mode=3 -pix_fmt yuv420p10le -y "x265_w2x_svp_2.mp4"