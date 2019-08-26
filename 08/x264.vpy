import vapoursynth as vs
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as vstaa
import adjust
import adaptivegrain as grain
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 32768

opstart = 2230
op_112_mappings = f'''
[{opstart+1665} {opstart+1693}]
[{opstart+1937} {opstart+1964}]
'''
op_135_mappings = f'''
[{opstart+1616} {opstart+1659}]
'''

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 08 [1080p].mkv")
src = core.fmtc.bitdepth(src, bits=16)
logo_mask = core.imwri.Read('mask_2.png')
logo_mask = core.resize.Bilinear(logo_mask, format=src.format.id, matrix_s="709")
deblock = core.deblock.Deblock(src, quant=16)
Y, U, V = kgf.split(deblock)
Y = kgf.inverse_scale(Y, height=872, kernel="bicubic", b=1/3, c=1/3, mask_detail=True,
	 descale_mask_zones=f"[{opstart} {opstart+3000}]")
Y = nnedi3_rpow2(Y).resize.Spline36(1920, 1080, format=vs.GRAY16)
scaled = core.std.ShufflePlanes([Y, U, V], planes=[0], colorfamily=vs.YUV)
scaled = fvf.rfs(scaled, src, mappings="[31822 34045]") # ED is just text on black so 1080p overlay

#fixing the box video in credits
yuv444 = core.fmtc.resample(scaled, css="444", kernel="lanczos")
box_crop = core.std.Crop(yuv444, 144, 1104, 305, 397)
box_crop = core.edgefixer.Continuity(box_crop, left=4, right=4, top=1, bottom=1)
box_full = core.std.AddBorders(box_crop, 144, 1104, 305, 397, color=[0, 0, 0])
box_full = core.fmtc.resample(scaled, css="420", kernel="lanczos")
box_mask = kgf.squaremask(scaled, 683, 381, 136, 304) # a little bit bigger to get some of the garbage around it
box_merged = core.std.MaskedMerge(scaled, box_full, box_mask)
scaled = fvf.rfs(scaled, box_merged, mappings="[32003 34045]")

logo_merge = core.std.MaskedMerge(scaled, src, logo_mask)
scaled = fvf.rfs(scaled, logo_merge, mappings="[14350 14515]")

dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.15, cont=1.15)

undim = fvf.rfs(scaled, dim1, mappings=op_135_mappings+" [5424 5549] [26107 26204]")
undim = fvf.rfs(undim, dim2, mappings=op_112_mappings)
undim = fvf.rfs(undim, dim3, mappings="[19011 19099] [19294 19780] [20971 21037] [21832 21971] [25539 25580] [30154 30377] [5925 5955]")

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