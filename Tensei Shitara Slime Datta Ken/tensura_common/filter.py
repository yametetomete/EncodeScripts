import vapoursynth as vs

from yt_common.antialiasing import mask_strong, sraa_clamp
from yt_common.data import FSRCNNX
from yt_common.scale import nnedi3_double

from lvsfunc.aa import upscaled_sraa
from lvsfunc.kernels import Bicubic
from lvsfunc.mask import BoundingBox, detail_mask
from lvsfunc.misc import replace_ranges, scale_thresh
from lvsfunc.scale import descale as ldescale
from lvsfunc.types import Range

from awsmfunc import bbmod
from debandshit import f3kbilateral
from kagefunc import retinex_edgemask
from vardefunc import dumb3kdb, fsrcnnx_upscale
from vsutil import depth
from vsutil import Range as CRange

from typing import List, Optional, Tuple

core = vs.core


def _fsrlineart(clip: vs.VideoNode, width: int, height: int) -> vs.VideoNode:
    clip = clip.resize.Point(1440, 810)
    assert clip.format is not None
    nn = depth(nnedi3_double(depth(clip, 16)), clip.format.bits_per_sample)
    fsr = fsrcnnx_upscale(clip, width, height, upscaled_smooth=nn, shader_file=FSRCNNX)
    mask = retinex_edgemask(depth(fsr.std.ShufflePlanes(0, vs.GRAY), 16))
    mask = mask.std.Binarize(scale_thresh(0.65, mask)).std.Maximum()
    mask = depth(mask, clip.format.bits_per_sample, range_in=CRange.FULL, range=CRange.FULL)
    return core.std.MaskedMerge(nn.resize.Bicubic(width, height, filter_param_a=0, filter_param_b=1/2), fsr, mask)


def edgefix(clip: vs.VideoNode) -> vs.VideoNode:
    bb: vs.VideoNode = bbmod(clip, top=1, bottom=1, left=1, right=1, blur=500)
    return bb


def descale(clip: vs.VideoNode) -> vs.VideoNode:
    return depth(ldescale(clip, height=810, kernel=Bicubic(b=0, c=1/2), upscaler=_fsrlineart), 16)


def denoise(clip: vs.VideoNode, h: float = 0.7) -> vs.VideoNode:
    den = core.std.ShufflePlanes([
        clip.knlm.KNLMeansCL(d=3, a=2, h=h, channels="Y"),
        clip.knlm.KNLMeansCL(d=3, a=2, h=0.2, channels="UV"),
    ], planes=[0, 1, 2], colorfamily=vs.YUV)
    return core.std.MaskedMerge(den, clip, detail_mask(den))


def deband(clip: vs.VideoNode, strong: Optional[List[Range]] = None,
           nuclear: Optional[List[Range]] = None) -> vs.VideoNode:
    dmask = detail_mask(clip)
    deb = dumb3kdb(clip, radius=16, threshold=30)
    if strong:
        debs = dumb3kdb(clip, radius=24, threshold=60)
        deb = replace_ranges(deb, debs, strong or [])
    if nuclear:
        debn = core.std.ShufflePlanes([
            f3kbilateral(clip.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY), y=60),
            deb
        ], planes=[0, 1, 2], colorfamily=vs.YUV)
        deb = replace_ranges(deb, debn, nuclear or [])
    return core.std.MaskedMerge(deb, clip, dmask)


def antialias(clip: vs.VideoNode, strong: Optional[List[Range]] = None,
              sangnom: Optional[List[Tuple[Range, List[BoundingBox]]]] = None) -> vs.VideoNode:
    clamp = sraa_clamp(clip, mask=mask_strong)
    if strong or sangnom:
        sraa_13 = upscaled_sraa(clip, rfactor=1.3)
        sraa_13 = core.std.MaskedMerge(clip, sraa_13, mask_strong(sraa_13))
        clamp = replace_ranges(clamp, sraa_13, strong or [])
    if sangnom:
        sn = upscaled_sraa(sraa_13, aafun=lambda c: c.sangnom.SangNom())
        sn = core.std.MaskedMerge(sraa_13, sn, mask_strong(sn))
        for r, ms in sangnom:
            mask = core.std.BlankClip(clip.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY))
            for m in ms:
                mask = core.std.Expr([mask, m.get_mask(clip)], "x y max")
            clamp = replace_ranges(clamp, core.std.MaskedMerge(clamp, sn, mask), r)
    return clamp


def regrain(clip: vs.VideoNode) -> vs.VideoNode:
    # doing a fairly heavy regrain since the source was so insanely grainy
    # but still nowhere near to the extent the source was
    mask_bright = clip.std.PlaneStats().adg.Mask(5)
    mask_dark = clip.std.PlaneStats().adg.Mask(15)
    sgrain_l = core.std.MaskedMerge(clip, clip.grain.Add(var=0.15, constant=True, seed=393), mask_bright.std.Invert())
    sgrain_h = core.std.MaskedMerge(clip, clip.grain.Add(var=0.25, uvar=0.1, constant=True, seed=393), mask_bright)
    sgrain_h = core.std.MaskedMerge(clip, sgrain_h, mask_dark.std.Invert())
    sgrain = sgrain_h.std.MergeDiff(clip.std.MakeDiff(sgrain_l))
    dgrain = core.std.MaskedMerge(clip, clip.grain.Add(var=0.35, uvar=0.1, constant=False, seed=393), mask_dark)
    grain = dgrain.std.MergeDiff(clip.std.MakeDiff(sgrain))
    return grain


def finalize(clip: vs.VideoNode) -> vs.VideoNode:
    return depth(clip, 10)


def megurumono_scenefilter(clip: vs.VideoNode, start: Optional[int] = None) -> vs.VideoNode:
    if start is None:
        return clip
    DEBAND_STRONG: List[Range] = [
        (start+12, start+256),
        (start+778, start+1007),
        (start+1025, start+1059),
        (start+1217, start+1322),
        (start+1368, start+1437),
    ]
    ef = edgefix(clip)
    den = denoise(ef)
    descaled = descale(den)
    deb = deband(descaled, strong=DEBAND_STRONG)
    aa = antialias(deb)
    grain = regrain(aa)
    return grain
