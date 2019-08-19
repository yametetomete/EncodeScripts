import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import adjust
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 49152

#source
src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 07 [1080p].mkv")
src = src.std.Trim(first=30604, last=30704)
src = src.std.AssumeFPS(fpsnum=24000, fpsden=1001)

#deblock
src = core.fmtc.bitdepth(src, bits=16)
deblock = core.deblock.Deblock(src, quant=16)

#rescale
Y, U, V = kgf.split(deblock)
Y = kgf.inverse_scale(Y, height=872, kernel="bicubic", b=1/3, c=1/3, mask_detail=True)

#There is basically no difference between running taa and deband before or after w2x.
#taa
Y = core.fmtc.bitdepth(Y, bits=16)
taa = vstaa.TAAmbk(Y,aatype='Nnedi3')

#deband
db = taa.f3kdb.Deband(range=16, y=32, cb=32, cr=32, grainy=24, grainc=0, random_algo_ref=2, random_algo_grain=2, output_depth=16)
mask = kgf.retinex_edgemask(taa)
maskmerge = core.std.MaskedMerge(db, taa, mask)

#w2x
#model 3 - block size: 218/270 batch: 50, benchmark: 0.3fps
#model 5 - block size: 38 (rec), batch: 1440, benchmark: 0.0195fps
#model 6 - block size: 8, batch: 5. takes minutes to execute per frame.
yupscalewx = core.fmtc.bitdepth(maskmerge, bits=32)
yupscalewx = core.caffe.Waifu2x(yupscalewx, noise=0, scale=4, block_w=218, block_h=218, model=3, cudnn=True, processor=0, tta=False, batch=50)
yupscalewx = core.fmtc.bitdepth(yupscalewx, bits=16, dmode=3)
yupscalewx = core.resize.Spline36(yupscalewx,width=3840,height=2160)

uupscalewx = core.fmtc.bitdepth(U, bits=32)
uupscalewx = core.caffe.Waifu2x(uupscalewx, noise=0, scale=4, block_w=270, block_h=270, model=3, cudnn=True, processor=0, tta=False, batch=50)
uupscalewx = core.fmtc.bitdepth(uupscalewx, bits=16, dmode=3)

vupscalewx = core.fmtc.bitdepth(V, bits=32)
vupscalewx = core.caffe.Waifu2x(vupscalewx, noise=0, scale=4, block_w=270, block_h=270, model=3, cudnn=True, processor=0, tta=False, batch=50)
vupscalewx = core.fmtc.bitdepth(vupscalewx, bits=16, dmode=3)

scaled = core.std.ShufflePlanes([yupscalewx, uupscalewx, vupscalewx], planes=[0], colorfamily=vs.YUV)

final = kgf.adaptive_grain(scaled)
final = core.fmtc.bitdepth(final, bits=12)

final.set_output()
#vspipe -y "x265_w2x.vpy" - | ffmpeg -i pipe: -c:v libx265 -tune animation -crf 17 -preset slower -x265-params aq-mode=3 -pix_fmt yuv444p12le -y "x265_w2x.mp4"
#vspipe -y "x265_w2x.vpy" --y4m - | x265 --demuxer y4m -o Sympho5_07p.264 - --preset slower --tune animation --crf 17 --aq-mode 3 --output-depth 12 --output-csp i444