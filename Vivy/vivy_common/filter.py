import vapoursynth as vs
import kagefunc as kgf
import lvsfunc as lvf
import vardefunc as vdf

from awsmfunc import bbmod
from debandshit import f3kbilateral
from lvsfunc.aa import upscaled_sraa
from lvsfunc.denoise import bm3d
from lvsfunc.kernels import Bicubic
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range
from typing import List, Optional

from yt_common import antialiasing
from yt_common.data import FSRCNNX
from yt_common.deband import morpho_mask

import vsutil

core = vs.core


def fsrcnnx_rescale(src: vs.VideoNode, noscale: Optional[List[Range]] = None,
                    kernel: Optional[lvf.kernels.Kernel] = None) -> vs.VideoNode:
    def _vdf_fsrcnnx(clip: vs.VideoNode, width: int, height: int) -> vs.VideoNode:
        clip = core.std.ShufflePlanes([vsutil.depth(clip.resize.Point(vsutil.get_w(864), 864), 16),
                                       src.resize.Bicubic(vsutil.get_w(864), 864)],
                                      planes=[0, 1, 2], colorfamily=vs.YUV)

        return vsutil.get_y(vsutil.depth(vdf.fsrcnnx_upscale(clip, width, height, FSRCNNX), 32))

    kernel = kernel if kernel else lvf.kernels.Bicubic()
    descale = lvf.scale.descale(src, height=864, upscaler=_vdf_fsrcnnx, kernel=kernel) \
        .resize.Bicubic(format=vs.YUV420P16)
    return lvf.misc.replace_ranges(descale, src, noscale) if noscale else descale


def _fixplane(clip: vs.VideoNode, top: int, bottom: int,
              bbt: int, bbb: int, chroma: bool = False, blur: int = 20) -> vs.VideoNode:
    return core.std.StackVertical([bbmod(clip.std.Crop(bottom=clip.height-top), bottom=1 if not chroma else 0),
                                   bbmod(clip.std.Crop(top=top, bottom=bottom), top=bbt, bottom=bbb, blur=blur),
                                   bbmod(clip.std.Crop(top=clip.height-bottom), top=1 if not chroma else 0)])


def letterbox_edgefix(clip: vs.VideoNode, ranges: List[Range]) -> vs.VideoNode:
    fy = _fixplane(clip.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY), top=132, bottom=131, bbt=3, bbb=3)
    fu = _fixplane(clip.std.ShufflePlanes(planes=1, colorfamily=vs.GRAY), top=66, bottom=65, bbt=2, bbb=2, chroma=True)
    fv = _fixplane(clip.std.ShufflePlanes(planes=2, colorfamily=vs.GRAY), top=66, bottom=65, bbt=2, bbb=2, chroma=True)
    return replace_ranges(clip, core.std.ShufflePlanes([fy, fu, fv], planes=[0, 0, 0], colorfamily=vs.YUV), ranges)


def letterbox_refix(aa: vs.VideoNode, noaa: vs.VideoNode, ranges: List[Range]) -> vs.VideoNode:
    return replace_ranges(aa, core.std.StackVertical([
        aa.std.Crop(bottom=aa.height-130),
        noaa.std.Crop(top=130, bottom=aa.height-134),
        aa.std.Crop(top=134, bottom=132),
        noaa.std.Crop(top=aa.height-132, bottom=130),
        aa.std.Crop(top=aa.height-130)
    ]), ranges)


def denoise(clip: vs.VideoNode, sigma: float = 1.5, h: float = 0.7) -> vs.VideoNode:
    return core.std.ShufflePlanes([
        bm3d(clip.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY), sigma=sigma, radius=1),
        clip.knlm.KNLMeansCL(d=3, a=1, h=h, channels="UV"),
    ], planes=[0, 1, 2], colorfamily=vs.YUV)


def deband(clip: vs.VideoNode) -> vs.VideoNode:
    grad_mask, yrangebig = morpho_mask(clip.dfttest.DFTTest(sigma=14, sigma2=10, sbsize=1, sosize=0)
                                       .rgvs.RemoveGrain(3))
    y = vsutil.get_y(clip)
    mask = lvf.mask.detail_mask(clip, brz_b=0.03)
    deband_dumb: vs.VideoNode = vdf.dumb3kdb(clip, radius=16, threshold=24)
    deband_weak: vs.VideoNode = core.std.MaskedMerge(vsutil.get_y(deband_dumb), y, mask)
    deband_norm: vs.VideoNode = vsutil.get_y(vdf.dumb3kdb(clip, radius=16, threshold=30))
    deband_strong: vs.VideoNode = f3kbilateral(y, range=12, y=50)
    deband = core.std.MaskedMerge(deband_strong, deband_norm, grad_mask)
    deband = core.std.MaskedMerge(deband, deband_weak, yrangebig)
    deband = core.std.ShufflePlanes([deband, deband_dumb], planes=[0, 1, 2], colorfamily=vs.YUV)
    return deband


def antialias(clip: vs.VideoNode, weak: Optional[List[Range]] = None, strong: Optional[List[Range]] = None,
              stronger: Optional[List[Range]] = None, noaa: Optional[List[Range]] = None) -> vs.VideoNode:
    mask = antialiasing.combine_mask(clip, weak or [])
    clamp = antialiasing.sraa_clamp(clip, mask=mask)
    sraa = core.std.MaskedMerge(clip, upscaled_sraa(clip, rfactor=2, downscaler=Bicubic(b=0, c=1/2).scale), mask)
    sraa_13 = core.std.MaskedMerge(clip, upscaled_sraa(clip, rfactor=1.3, downscaler=Bicubic(b=0, c=1/2).scale), mask)
    return replace_ranges(replace_ranges(replace_ranges(clamp, clip, noaa or []), sraa, strong or []), sraa_13,
                          stronger or [])


def regrain(clip: vs.VideoNode) -> vs.VideoNode:
    sgrain: vs.VideoNode = kgf.adaptive_grain(clip, 0.15, luma_scaling=10)
    dgrain: vs.VideoNode = kgf.adaptive_grain(clip, 0.1, luma_scaling=25, static=False)
    grain = dgrain.std.MergeDiff(clip.std.MakeDiff(sgrain))
    return grain


def finalize(clip: vs.VideoNode) -> vs.VideoNode:
    return vsutil.depth(clip, 10)
