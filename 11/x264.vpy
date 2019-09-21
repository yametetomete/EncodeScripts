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

op = [3381, 5777]
ed = [31888, 34045]
title = [5779, 5860]
logo = [16437, 16602]
bikki = [10353, 11490]
maria = [23535, 24735]

op_112_mappings = f'''
[{op[0]+1665} {op[0]+1693}]
[{op[0]+1937} {op[0]+1964}]
'''
op_135_mappings = f'''
[{op[0]+1616} {op[0]+1659}]
'''

bikki_140_mappings = f'''
[{bikki[0]+555} {bikki[0]+623}]
[{bikki[0]+675} {bikki[0]+689}]
[{bikki[0]+692} {bikki[0]+733}]
[{bikki[0]+751} {bikki[0]+872}]
{bikki[0]+987}
'''
bikki_130_mappings = f'''
[{bikki[0]+938} {bikki[0]+955}]
'''
bikki_115_mappings = f'''
[{bikki[0]+624} {bikki[0]+656}]
[{bikki[0]+974} {bikki[0]+986}]
[{bikki[0]+988} {bikki[0]+1010}]
'''
bikki_105_mappings = f'''
[{bikki[0]+972} {bikki[0]+973}]
[{bikki[0]+1011} {bikki[0]+1012}]
'''

# this fucker is totally different from the youtube version
maria_130_mappings = f'''
[{maria[0]+844} {maria[0]+857}]
'''
maria_115_mappings = f'''
[{maria[0]+858} {maria[0]+863}]
[{maria[0]+1029} {maria[0]+1032}]
[{maria[0]+1068} {maria[0]+1069}]
[{maria[0]+1081} {maria[0]+1092}]
[{maria[0]+1121} {maria[0]+1122}]
[{maria[0]+1149} {maria[0]+1151}]
[{maria[0]+1160} {maria[0]+1161}]
'''

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 11 [1080p].mkv")
src = core.fmtc.bitdepth(src, bits=16)

# todo: examine potential for actually descaling this episode
# flashback to ep10 at ~5:00 (bad non-descalable episode)
logo_mask = core.imwri.Read('mask_2.png')
logo_mask = core.resize.Bilinear(logo_mask, format=src.format.id, matrix_s="709")
deblock = core.deblock.Deblock(src, quant=16)
Y = vsutil.get_y(deblock)

Ycond = descale_eval.descale_range(Y, heights=list(range(871, 875)), threshold=7e-6, debug=False, mask_detail=True)
Ycond = Ycond.resize.Point(Ycond.width, Ycond.height, format=vs.GRAY16)

# high-action regions I value the increased sharpness from the descale more than the ringing you have to zoom in 10x to notice
Yforce = descale_eval.descale_range(Y, heights=list(range(871, 875)), threshold=1, debug=False, mask_detail=True)
Yforce = Yforce.resize.Point(Yforce.width, Yforce.height, format=vs.GRAY16)

scaled_force = core.std.ShufflePlanes([Yforce, deblock], planes=[0, 1, 2], colorfamily=vs.YUV)
scaled_cond = core.std.ShufflePlanes([Ycond, deblock], planes=[0, 1, 2], colorfamily=vs.YUV)

scaled = scaled_cond
logo_merge = core.std.MaskedMerge(scaled_force, deblock, logo_mask)
scaled = fvf.rfs(scaled, logo_merge, mappings=f"[{logo[0]} {logo[1]}]")
scaled = fvf.rfs(scaled, scaled_force, mappings=f"[{op[0]} {op[1]}]")
scaled = fvf.rfs(scaled, scaled_force, mappings=f"[{title[0]} {title[1]}]")
scaled = fvf.rfs(scaled, scaled_force, mappings=f"[{bikki[0]} {bikki[1]}]")
scaled = fvf.rfs(scaled, scaled_force, mappings=f"[{maria[0]} {maria[1]}]")
scaled = fvf.rfs(scaled, scaled_force, mappings=f"[{ed[0]} {ed[1]}]")

dim1 = adjust.Tweak(scaled, sat=1.35, cont=1.35)
dim2 = adjust.Tweak(scaled, sat=1.12, cont=1.12)
dim3 = adjust.Tweak(scaled, sat=1.15, cont=1.15)
dim4 = adjust.Tweak(scaled, sat=1.40, cont=1.40)
dim5 = adjust.Tweak(scaled, sat=1.30, cont=1.30)
dim6 = adjust.Tweak(scaled, sat=1.05, cont=1.05)

undim = fvf.rfs(scaled, dim1, mappings=op_135_mappings)
undim = fvf.rfs(undim, dim2, mappings=op_112_mappings)
undim = fvf.rfs(undim, dim3, mappings=bikki_115_mappings+maria_115_mappings+"[1204 1361] [29425 29525] [29905 29993] [13161 13168]")
undim = fvf.rfs(undim, dim4, mappings=bikki_140_mappings+"[29133 29210]")
undim = fvf.rfs(undim, dim5, mappings=bikki_130_mappings+maria_130_mappings)
undim = fvf.rfs(undim, dim6, mappings=bikki_105_mappings)

denoisechroma = core.knlm.KNLMeansCL(undim, d=1, a=2, h=0.4, channels="UV", device_type='gpu', device_id=0)
denoiseluma = core.knlm.KNLMeansCL(undim, d=3, a=2, h=0.35, channels="Y", device_type='gpu', device_id=0)
denoise = core.std.ShufflePlanes([denoiseluma, denoisechroma], planes=[0, 1, 2], colorfamily=vs.YUV)
taa = vstaa.TAAmbk(denoise,aatype='Nnedi3')
db = taa.f3kdb.Deband(range=16, y=40, cb=32, cr=32, grainy=24, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(denoise)
final = core.std.MaskedMerge(db, taa, mask)

final = adaptivegrain.adaptive_grain(final)
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()

#vspipe -y "x264.vpy" - | ffmpeg -i pipe: -c:v libx264 -tune animation -crf 16 -preset slower -aq-mode 3 -pix_fmt yuv420p10le -x264-params no-dct-decimate:no-fast-pskip -y "x264.mp4"