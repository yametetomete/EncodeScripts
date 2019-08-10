import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 32768

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 04 [1080p].mkv")
src = core.fmtc.bitdepth(src, bits=16)
scaled = kgf.inverse_scale(src, height=872, kernel="lanczos", taps=5, mask_detail=True)

#upscalenn = nnedi3_rpow2(scaled).resize.Spline36(1920, 1080, format=vs.YUV420P16)
#denoise = kgf.hybriddenoise(upscalenn, knl=0.5, sigma=1, radius1=0)
#taa = vstaa.TAAmbk(denoise,aatype='Nnedi3')
#db = taa.f3kdb.Deband(range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
#mask = kgf.retinex_edgemask(denoise)
#finalnn = core.std.MaskedMerge(db, taa, mask)
#finalnn = kgf.adaptive_grain(finalnn)
#finalnn = core.fmtc.bitdepth(finalnn, bits=10, dmode=3)


upscalewx = core.fmtc.bitdepth(scaled, bits=32)
upscalewx = core.fmtc.resample(upscalewx, css="444", kernel="lanczos")
upscalewx = core.caffe.Waifu2x(upscalewx, noise=1, scale=1, block_w=387, block_h=387, model=3, cudnn=True, processor=0, tta=False, batch=7)
#upscalewx = core.resize.Spline16(upscalewx,width=1920,height=1080)
upscalewx = core.fmtc.bitdepth(upscalewx, bits=16, dmode=3)
upscalewx = nnedi3_rpow2(upscalewx).resize.Spline36(1920, 1080, format=vs.YUV444P16)
taa = vstaa.TAAmbk(upscalewx,aatype='Nnedi3')
db = taa.f3kdb.Deband(range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(upscalewx)
finalwx = core.std.MaskedMerge(db, taa, mask)
finalwx = kgf.adaptive_grain(finalwx)
finalwx = core.fmtc.resample(finalwx, css="420", kernel="lanczos")
finalwx = core.fmtc.bitdepth(finalwx, bits=10, dmode=3)


#stack1 = core.std.StackHorizontal([finalnn, finalwx])
#final = stack1
#final = core.fmtc.bitdepth(final, bits=10, dmode=3)
finalwx.set_output()

#vspipe -y "x264.vpy" - | ffmpeg -i pipe: -c:v libx264 -tune animation -crf 16 -preset slower -pix_fmt yuv420p10le -y "x264.mp4"