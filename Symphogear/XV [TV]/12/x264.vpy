import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import adjust
import vsutil
from nnedi3_rpow2 import nnedi3_rpow2
from ytttfunc import descale_eval
from ytttfunc import adaptivegrain

core = vs.core
core.max_cache_size = 32768

ed = [31646, 34043]
logo = [11640, 11805]
chris = 13412 # youtube henshin for chris doesn't have the intro so i picked an arbitrary ref frame

chris_mappings_115 = f'''
[{chris+344} {chris+791}]
'''

chris_mappings_135_115 = f'''
[{chris+1031} {chris+1060}]
'''

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 12 [1080p].mkv")
src = core.fmtc.bitdepth(src, bits=16)

# todo: examine potential for actually descaling this episode
# flashback to ep10 at ~5:00 (bad non-descalable episode)
logo_mask = core.imwri.Read('mask_2.png')
logo_mask = core.resize.Bilinear(logo_mask, format=src.format.id, matrix_s="709")
deblock = core.deblock.Deblock(src, quant=16)
Y = vsutil.get_y(deblock)

HEIGHT = 873
Yconst = kgf.inverse_scale(Y, height=HEIGHT, kernel="bicubic", b=1/3, c=1/3, mask_detail=False)
Ynn = nnedi3_rpow2(Yconst).resize.Spline36(1920, 1080, format=vs.GRAY16)

# threshold scaling works basically not at all
# so instead we're just going to use it for range functionality
Yde = descale_eval.descale_range(Y, heights=list(range(870, 875)), threshold=1, debug=False, mask_detail=True)
Yde = Yde.resize.Point(Yde.width, Yde.height, format=vs.GRAY16)

scaled_all = core.std.ShufflePlanes([Yde, deblock], planes=[0, 1, 2], colorfamily=vs.YUV)

scaled = scaled_all
logo_merge = core.std.MaskedMerge(scaled, deblock, logo_mask)
scaled = fvf.rfs(scaled, logo_merge, mappings=f"[{logo[0]} {logo[1]}]")
scaled = fvf.rfs(scaled, src, mappings=f"[{ed[0]} {ed[1]}]")

dim1 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim2 = adjust.Tweak(scaled, sat=1.35, cont=1.15)

undim = fvf.rfs(scaled, dim1, mappings=chris_mappings_115+" [3776 6034] [7898 8022] [14687 14740] [15948 16019] [16074 16103] [16826 16840] [17259 17444] [17811 17861] [17976 18020] [18084 18137]")
undim = fvf.rfs(undim, dim2, mappings=chris_mappings_135_115)

denoisechroma = core.knlm.KNLMeansCL(undim, d=1, a=2, h=0.4, channels="UV", device_type='gpu', device_id=0)
denoiseluma = core.knlm.KNLMeansCL(undim, d=3, a=2, h=0.35, channels="Y", device_type='gpu', device_id=0)
denoise = core.std.ShufflePlanes([denoiseluma, denoisechroma], planes=[0, 1, 2], colorfamily=vs.YUV)
taa = vstaa.TAAmbk(denoise,aatype='Nnedi3')
db = taa.f3kdb.Deband(range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(denoise)
merged = core.std.MaskedMerge(db, taa, mask)

Y, U, V = kgf.split(merged)
Y = Y.edgefixer.Continuity(top=3, left=4)
U = U.edgefixer.Continuity(top=2, left=3)
V = V.edgefixer.Continuity(top=2, left=3)
endcardfix = core.std.ShufflePlanes([Y, U, V], planes=[0], colorfamily=vs.YUV)
fixed = fvf.rfs(merged, endcardfix, mappings="[31601 31645]")

final = adaptivegrain.adaptive_grain(fixed)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()

#vspipe -y "x264.vpy" - | ffmpeg -i pipe: -c:v libx264 -tune animation -crf 16 -preset slower -aq-mode 3 -pix_fmt yuv420p10le -x264-params no-dct-decimate:no-fast-pskip -y "x264.mp4"