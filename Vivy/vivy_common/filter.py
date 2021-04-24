import vapoursynth as vs
import kagefunc as kgf
import lvsfunc as lvf
import vardefunc as vdf

from awsmfunc import bbmod
from lvsfunc.types import Range
from mvsfunc import BM3D
from typing import List, Optional

from yt_common import antialiasing

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


def denoise(clip: vs.VideoNode, sigma: float = 0.75) -> vs.VideoNode:
    bm3d: vs.VideoNode = BM3D(clip, sigma=sigma, depth=16)
    return bm3d


def deband(clip: vs.VideoNode) -> vs.VideoNode:
    deb: vs.VideoNode = vdf.dumb3kdb(clip, radius=18, threshold=36, grain=[24, 0])
    return deb


def antialias(clip: vs.VideoNode, noaa: Optional[List[Range]] = None) -> vs.VideoNode:
    clamp = antialiasing.sraa_clamp(clip, mask=antialiasing.mask_strong(clip))
    return lvf.misc.replace_ranges(clamp, clip, noaa) if noaa else clamp


def finalize(clip: vs.VideoNode) -> vs.VideoNode:
    grain = kgf.adaptive_grain(clip, 0.1)
    return vsutil.depth(grain, 10)
