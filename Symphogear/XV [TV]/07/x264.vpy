import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import adjust
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 32768

opstart = 2568
op_112_mappings = f'''
[{opstart+1663} {opstart+1691}]
[{opstart+1935} {opstart+1962}]
'''
op_135_mappings = f'''
[{opstart+1614} {opstart+1657}]
'''

kiri_hsff = 8110
kiri_henshin120_mappings = f'''
[{kiri_hsff} {kiri_hsff+15}]
[{kiri_hsff+42} {kiri_hsff+45}]
[{kiri_hsff+159} {kiri_hsff+161}]
[{kiri_hsff+205} {kiri_hsff+215}]
[{kiri_hsff+289} {kiri_hsff+291}]
[{kiri_hsff+301} {kiri_hsff+318}]
[{kiri_hsff+389} {kiri_hsff+393}]
[{kiri_hsff+456} {kiri_hsff+461}]
[{kiri_hsff+489} {kiri_hsff+498}]
{kiri_hsff+535}
[{kiri_hsff+542} {kiri_hsff+563}]
[{kiri_hsff+639} {kiri_hsff+731}]
'''


src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 07 [1080p].mkv")
src = core.fmtc.bitdepth(src, bits=16)
logo_mask = core.imwri.Read('mask_2.png')
logo_mask = core.resize.Bilinear(logo_mask, format=src.format.id, matrix_s="709")
deblock = core.deblock.Deblock(src, quant=16)
Y, U, V = kgf.split(deblock)
Y = kgf.inverse_scale(Y, height=872, kernel="bicubic", b=1/3, c=1/3, mask_detail=True,
	 descale_mask_zones=f"[{opstart} {opstart+3000}]")
Y = nnedi3_rpow2(Y).resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.ShufflePlanes([Y, U, V], planes=[0], colorfamily=vs.YUV)
scaled = fvf.rfs(scaled, src, mappings="[31877 34045]") # ED is just text on black so 1080p overlay

logo_merge = core.std.MaskedMerge(scaled, src, logo_mask)
scaled = fvf.rfs(scaled, logo_merge, mappings="[17059 17236]")

dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.20, cont=1.20)
dim4 = adjust.Tweak(scaled, sat=1.50, cont=1.50)

undim = fvf.rfs(scaled, dim1, mappings=op_135_mappings)
undim = fvf.rfs(undim, dim2, mappings=op_112_mappings+" [30445 30461] [30462 30484]")
undim = fvf.rfs(undim, dim3, mappings=kiri_henshin120_mappings)
undim = fvf.rfs(undim, dim4, mappings="[7319 7338]")

denoisechroma = core.knlm.KNLMeansCL(undim, d=1, a=2, h=0.4, channels="UV", device_type='gpu', device_id=0)
denoiseluma = core.knlm.KNLMeansCL(undim, d=3, a=2, h=0.35, channels="Y", device_type='gpu', device_id=0)
denoise = core.std.ShufflePlanes([denoiseluma, denoisechroma], planes=[0, 1, 2], colorfamily=vs.YUV)
taa = vstaa.TAAmbk(denoise,aatype='Nnedi3')
db = taa.f3kdb.Deband(range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(denoise)
final = core.std.MaskedMerge(db, taa, mask)

final = kgf.adaptive_grain(final)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()

#vspipe -y "x264.vpy" - | ffmpeg -i pipe: -c:v libx264 -tune animation -crf 16 -preset slower -aq-mode 3 -pix_fmt yuv420p10le -x264-params no-dct-decimate:no-fast-pskip -y "x264.mp4"