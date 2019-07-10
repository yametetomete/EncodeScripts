import vapoursynth as vs
import fag3kdb
import kagefunc as kgf
import fvsfunc as fvf
import vsTAAmbk as taa

core = vs.get_core()
core.max_cache_size = 16384

src = core.ffms2.Source("[HorribleSubs] Symphogear XV - 01 [1080p].mkv",track=0)

#resmapling to 444 and 16bit for filters
resam = src.std.AssumeFPS(fpsnum=24000, fpsden=1001)
resam = core.fmtc.bitdepth(resam, bits=16)
resam = core.fmtc.resample(resam, css="444", kernel="lanczos")

#gpu accelerated noise reduction
#i use a h paramater quite a bit under the default 1.2 to prevent killing more details but mostly for personal taste
fil = core.knlm.KNLMeansCL(resam, d=1, a=2, h=0.4, channels="YUV", device_type='gpu', device_id=0)

#episode doesnt really have any aliasing but it doesnt hurt and doesnt eat cpu time at all relatively
taa = taa.TAAmbk(fil,aatype='Nnedi3')

#flash3kyuu_deband
#retinex_edgemask merge is used to help preserve details on edges
band = taa.f3kdb.Deband(range=12, y=60, cb=40, cr=40, grainy=15, grainc=0, output_depth=16)
mask = kgf.retinex_edgemask(fil)
merge = core.std.MaskedMerge(band, fil, mask)
#adaptive grain helps preserve details from the encoder. this is less important for x265 but it doesnt hurt to do
merge = kgf.adaptive_grain(merge)

#debugging edgemask merge
#stack1 = core.std.StackHorizontal([resam, fil])
#blank = core.std.BlankClip(merge)
#stack2 = core.std.StackHorizontal([core.std.ShufflePlanes(clips=[mask,blank], planes=[0, 1, 2], colorfamily=vs.YUV), merge])
#merge = core.std.StackVertical([stack1, stack2])

#debugging taa
#stack1 = core.std.StackHorizontal([fil, taa])
#stack2 = core.std.StackHorizontal([core.std.BlankClip(taa), core.std.MakeDiff(fil, taa, planes=[0])])
#merge = core.std.StackVertical([stack1, stack2])
 
#actual final output
final = core.fmtc.resample(merge, css="420", kernel="lanczos")
final = core.fmtc.bitdepth(final, bits=10, dmode=3)
final.set_output()

#ffmpeg
#vspipe -y "x265_Icebingo.vpy" - | ffmpeg -i pipe: -c:v libx264 -tune animation -crf 16 -pix_fmt yuv420p10 -preset slow -y "test1.mp4"
#vspipe -y "x265_Icebingo.vpy" - | ffmpeg -i pipe: -c:v libx265 -tune animation -crf 17 -pix_fmt yuv420p10 -preset slow -y "xv01.mp4"