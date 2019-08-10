import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import adjust
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 32768

src = core.ffms2.Source("[Erai-raws] Senki Zesshou Symphogear XV - 05 [1080p][Multiple Subtitle].mkv")
src = core.fmtc.bitdepth(src, bits=16)
deblock = core.deblock.Deblock(src, quant=16)
Y, U, V = kgf.split(deblock)
Y = kgf.inverse_scale(Y, height=872, kernel="bicubic", b=1/3, c=1/3, mask_detail=True)
Y = nnedi3_rpow2(Y).resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.ShufflePlanes([Y, U, V], planes=[0], colorfamily=vs.YUV)

dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.20, cont=1.20)
dim3 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
undim = fvf.rfs(scaled, dim1, mappings="[23298 23322] 23339")
undim = fvf.rfs(undim, dim2, mappings="[2888 2931]")
undim = fvf.rfs(undim, dim3, mappings="[27161 27166]")

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

#vspipe -y "x264.vpy" -s 13500 -e 13800 - | ffmpeg -i pipe: -c:v hevc_nvenc -profile:v 1 -b:v 3.5M -maxrate:v 4.5M -preset slow -rc vbr_hq -cq 1 -spatial_aq true -temporal_aq true -rc-lookahead 32 -aq-strength 12 -gpu 0 -pix_fmt p010le -y "x265_gpu.mp4"

#vspipe -y "x264.vpy" -s 13500 -e 13800 - | ffmpeg -i pipe: -c:v libx265 -tune animation -crf 16 -preset slower -x265-params aq-mode=3 -pix_fmt yuv420p10le -y "x265.mp4"

#vspipe -y "x264.vpy" -s 27900 -e 28200 - | ffmpeg -i pipe: -c:v libx264 -preset veryslow -crf 16 -g 480 -keyint_min 23 -refs 16 -bf 16 -aq-mode 3 -aq-strength 0.70 -qcomp 0.70 -psy-rd 0.72 -x264-params no-dct-decimate:no-fast-pskip -pix_fmt yuv420p10le -y "x264_newline.mp4"