import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import adjust
import vsutil
from nnedi3_rpow2 import nnedi3_rpow2
from ytttfunc import descale_eval, adaptivegrain

core = vs.core
core.max_cache_size = 32768

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 13 [1080p].mkv")
src = core.fmtc.bitdepth(src, bits=16)

logo_mask = core.imwri.Read('mask_2.png')
logo_mask = core.resize.Bilinear(logo_mask, format=src.format.id, matrix_s="709")
deblock = core.deblock.Deblock(src, quant=16)

Y = vsutil.get_y(deblock)

Ycond = descale_eval.descale_range(Y, heights=list(range(870, 875)), threshold=1, debug=False, mask_detail=True)
Ycond = Ycond.resize.Point(Ycond.width, Ycond.height, format=vs.GRAY16)

scaled = core.std.ShufflePlanes([Ycond, deblock], planes=[0, 1, 2], colorfamily=vs.YUV)

scaled = fvf.rfs(scaled, src, mappings="[30162 32320]")

logo_merge = core.std.MaskedMerge(scaled, deblock, logo_mask)
scaled = fvf.rfs(scaled, logo_merge, mappings=f"[15790 15955]")

# lightarrows did it this time so it doesn't suck
dim1 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim2 = adjust.Tweak(scaled, sat=1.20, cont=1.20)
dim3 = adjust.Tweak(scaled, sat=1.05, cont=1.05)
dim4 = adjust.Tweak(scaled, sat=1.10, cont=1.10)

undim = fvf.rfs(scaled, dim1, mappings="[1870 1938] [2011 2136] [2441 2670] [2719 2730] [5157 5697] [6482 6571] [6591 7079] [7140 7222] [7274 7842] [7961 7994] [8048 8244] [8634 8686] [9134 9178] [12581 13487] [14285 14862] [14898 15071] [22374 22527] [26853 26944] [27379 27920]")
undim = fvf.rfs(undim, dim2, mappings="[2731 2802] [2851 3108] [4444 4614] [4781 5156] [20144 20404]")
undim = fvf.rfs(undim, dim3, mappings="[3109 3147] [8771 8860] [13902 14284] [14863 14897] [25518 26047] [26437 26557] [26945 27053] [28077 29071]")
undim = fvf.rfs(undim, dim4, mappings="[13828 13901]")

sq_mask = kgf.squaremask(scaled, 1049, 594, 0, 238)
ed_undim = fvf.rfs(undim, dim3, mappings="[32254 32305]")
undim = core.std.MaskedMerge(undim, ed_undim, sq_mask)

denoisechroma = core.knlm.KNLMeansCL(undim, d=1, a=2, h=0.4, channels="UV", device_type='gpu', device_id=0)
denoiseluma = core.knlm.KNLMeansCL(undim, d=3, a=2, h=0.35, channels="Y", device_type='gpu', device_id=0)
denoise = core.std.ShufflePlanes([denoiseluma, denoisechroma], planes=[0, 1, 2], colorfamily=vs.YUV)
taa = vstaa.TAAmbk(denoise,aatype='Nnedi3')
db = taa.f3kdb.Deband(range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(denoise)
merged = core.std.MaskedMerge(db, taa, mask)

final = adaptivegrain.adaptive_grain(merged)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()

#vspipe -y "x264.vpy" - | ffmpeg -i pipe: -c:v libx264 -tune animation -crf 16 -preset slower -aq-mode 3 -pix_fmt yuv420p10le -x264-params no-dct-decimate:no-fast-pskip -y "x264.mp4"