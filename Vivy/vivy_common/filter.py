import vapoursynth as vs
import kagefunc as kgf
import lvsfunc as lvf
import vardefunc as vdf

from awsmfunc import bbmod
from debandshit import f3kbilateral
from lvsfunc.types import Range
from mvsfunc import BM3D
from typing import List, Optional

from yt_common import antialiasing
from yt_common.deband import morpho_mask

import os
import vsutil

core = vs.core

FSRCNNX = os.path.join(os.path.dirname(__file__), "shaders/FSRCNNX_x2_56-16-4-1.glsl")


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


def letterbox_edgefix(clip: vs.VideoNode, ranges: List[Range]) -> vs.VideoNode:
    edgefix = bbmod(clip.std.Crop(top=132, bottom=132), top=2, bottom=2, blur=500).std.AddBorders(top=132, bottom=132)
    return lvf.misc.replace_ranges(clip, edgefix, ranges)


def denoise(clip: vs.VideoNode, sigma: float = 1.5) -> vs.VideoNode:
    bm3d: vs.VideoNode = BM3D(clip, sigma=sigma, depth=16)
    return bm3d


def deband(clip: vs.VideoNode) -> vs.VideoNode:
    grad_mask, yrangebig = morpho_mask(clip.dfttest.DFTTest(sigma=14, sigma2=10, sbsize=1, sosize=0)
                                       .rgvs.RemoveGrain(3))
    y = vsutil.get_y(clip)
    mask = lvf.mask.detail_mask(clip)
    deband_dumb: vs.VideoNode = vdf.dumb3kdb(clip)
    deband_weak: vs.VideoNode = core.std.MaskedMerge(vsutil.get_y(deband_dumb), y, mask)
    deband_norm: vs.VideoNode = f3kbilateral(y, y=36)
    deband_strong: vs.VideoNode = f3kbilateral(y, y=65)
    deband = core.std.MaskedMerge(deband_strong, deband_norm, grad_mask)
    deband = core.std.MaskedMerge(deband, deband_weak, yrangebig)
    deband = core.std.ShufflePlanes([deband, deband_dumb], planes=[0, 1, 2], colorfamily=vs.YUV)
    return deband


def antialias(clip: vs.VideoNode, noaa: Optional[List[Range]] = None) -> vs.VideoNode:
    clamp = antialiasing.sraa_clamp(clip, mask=antialiasing.mask_strong(clip))
    return lvf.misc.replace_ranges(clamp, clip, noaa) if noaa else clamp


def regrain(clip: vs.VideoNode) -> vs.VideoNode:
    sgrain: vs.VideoNode = kgf.adaptive_grain(clip, 0.15, luma_scaling=10)
    dgrain: vs.VideoNode = kgf.adaptive_grain(clip, 0.1, luma_scaling=25, static=False)
    grain = dgrain.std.MergeDiff(clip.std.MakeDiff(sgrain))
    return grain


def finalize(clip: vs.VideoNode) -> vs.VideoNode:
    return vsutil.depth(clip, 10)
