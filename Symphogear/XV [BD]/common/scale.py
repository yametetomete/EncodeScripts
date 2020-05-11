import vapoursynth as vs
import vsutil

from functools import partial
from kagefunc import retinex_edgemask
from lvsfunc.aa import upscaled_sraa
from lvsfunc.kernels import Bicubic
from lvsfunc.misc import replace_ranges
from lvsfunc.scale import descale as ldescale
from typing import List, NamedTuple, Tuple, Union

core = vs.core


class FadeRange(NamedTuple):
    ref: int
    range_: Tuple[int, int]


def _sraa_frameeval(n: int, clip: vs.VideoNode, w: int, h: int):
    frame = clip.get_frame(n)
    if frame.height < 1080:
        rfactor = 2.5
    else:
        rfactor = 1.5
    return upscaled_sraa(clip.resize.Bicubic(frame.width, frame.height),
                         rfactor=rfactor, h=h, ar=w/h)


def _sraa_reupscale(clip: vs.VideoNode, width: int, height: int):
    sraa = clip.std.FrameEval(partial(_sraa_frameeval, clip=clip, w=width,
                                      h=height))
    scale = sraa.resize.Spline36(width, height, format=vs.GRAY16)
    return scale


def _fade_ranges_with_refs(clip, reupscaled, ranges):
    mask = core.std.BlankClip(clip)
    for r in ranges:
        rmask = core.std.Expr([clip[r.ref], reupscaled[r.ref]], "x y - abs")
        rmask = vsutil.iterate(rmask, core.std.Maximum, 4)
        rmask = rmask.std.Binarize(4000)
        rmask = core.std.Expr([mask, rmask], "x y +")
        mask = replace_ranges(mask, rmask, [r.range_])

    return mask


def _really_dumb_inverse_mask(clip, reupscaled: vs.VideoNode,
                              ranges: List[FadeRange]) -> vs.VideoNode:
    reupscaled = reupscaled.resize.Bicubic(format=clip.format.id)
    line_mask = retinex_edgemask(clip, 0.0001).std.Binarize(10000)
    fade_mask = _fade_ranges_with_refs(clip, reupscaled, ranges)
    mask = core.std.Expr([fade_mask, line_mask.std.Invert()], "x y +")
    return mask.resize.Bicubic(format=clip.format.id)


def descale(clip: vs.VideoNode, force_scale: List[Union[int, Tuple[int, int]]],
            no_scale: List[Union[int, Tuple[int, int]]],
            fade_ranges: List[FadeRange], show_mask=False) -> vs.VideoNode:
    dmask = partial(_really_dumb_inverse_mask, ranges=fade_ranges)
    kernel = Bicubic(b=1/3, c=1/3)
    heights = [871, 872, 873]
    y = vsutil.get_y(clip)
    ys = ldescale(y, upscaler=_sraa_reupscale, height=heights,
                  kernel=kernel, threshold=0.003, mask=dmask,
                  show_mask=show_mask)
    if show_mask:
        return ys

    yf = ldescale(y, upscaler=_sraa_reupscale, height=heights,
                  kernel=kernel, threshold=0, mask=dmask)
    yd = replace_ranges(ys, yf, force_scale)
    scaled = core.std.ShufflePlanes([yd, clip], planes=[0, 1, 2],
                                    colorfamily=vs.YUV)
    scaled = replace_ranges(scaled, clip, no_scale)
    return scaled
