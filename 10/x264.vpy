import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import adjust
import adaptivegrain as grain
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 32768

opstart = 5563
op_112_mappings = f'''
[{opstart+1665} {opstart+1693}]
[{opstart+1937} {opstart+1964}]
'''
op_135_mappings = f'''
[{opstart+1616} {opstart+1659}]
'''

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 10 [1080p].mkv")
src = core.fmtc.bitdepth(src, bits=16)
#logo_mask = core.imwri.Read('mask_2.png')
#logo_mask = core.resize.Bilinear(logo_mask, format=src.format.id, matrix_s="709")
deblock = core.deblock.Deblock(src, quant=16)
#this episode is bad
#Y, U, V = kgf.split(deblock)
#Y = kgf.inverse_scale(Y, height=872, kernel="bicubic", b=1/3, c=1/3, mask_detail=True,
#	 descale_mask_zones=f"[{opstart} {opstart+3000}] [31338 33494]")
#Y = nnedi3_rpow2(Y).resize.Spline36(1920, 1080, format=vs.GRAY16)
#scaled = core.std.ShufflePlanes([Y, U, V], planes=[0], colorfamily=vs.YUV)
scaled = deblock

#logo_merge = core.std.MaskedMerge(scaled, src, logo_mask)
#scaled = fvf.rfs(scaled, logo_merge, mappings="[17924 18089]")

dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.05, cont=1.05)
dim4 = adjust.Tweak(scaled, sat=1.07, cont=1.07)
dim5 = adjust.Tweak(scaled, sat=1.30, cont=1.30)
dim6 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim7 = adjust.Tweak(scaled, sat=1.10, cont=1.15)

undim = fvf.rfs(scaled, dim1, mappings=op_135_mappings)
undim = fvf.rfs(undim, dim2, mappings=op_112_mappings)
undim = fvf.rfs(undim, dim3, mappings="19745")
undim = fvf.rfs(undim, dim4, mappings="19746")
undim = fvf.rfs(undim, dim2, mappings="[19747 19748]")
undim = fvf.rfs(undim, dim5, mappings="[19995 20010]")
undim = fvf.rfs(undim, dim6, mappings="[19749 19810] [19834 19870] [20016 20025] [20042 20044] [20063 20082]")
# reality can be whatever i want
undim = fvf.rfs(undim, dim7, mappings="[20576 20720] [20841 20900] [21577 21725] [22555 22672] [22736 22848] [23153 23154] [23188 23219] [23346 23362] [25181 25249] [26416 26546] [26583 26628] [26770 26817] [27517 27740] [28272 28443] [28516 28586] [28947 29030]")
undim = fvf.rfs(undim, dim1, mappings="[26866 26919]") # this one is fucked

denoisechroma = core.knlm.KNLMeansCL(undim, d=1, a=2, h=0.4, channels="UV", device_type='gpu', device_id=0)
denoiseluma = core.knlm.KNLMeansCL(undim, d=3, a=2, h=0.35, channels="Y", device_type='gpu', device_id=0)
denoise = core.std.ShufflePlanes([denoiseluma, denoisechroma], planes=[0, 1, 2], colorfamily=vs.YUV)
taa = vstaa.TAAmbk(denoise,aatype='Nnedi3')
db = taa.f3kdb.Deband(range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(denoise)
final = core.std.MaskedMerge(db, taa, mask)

final = grain.adaptive_grain(final)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()

#vspipe -y "x264.vpy" - | ffmpeg -i pipe: -c:v libx264 -tune animation -crf 16 -preset slower -aq-mode 3 -pix_fmt yuv420p10le -x264-params no-dct-decimate:no-fast-pskip -y "x264.mp4"