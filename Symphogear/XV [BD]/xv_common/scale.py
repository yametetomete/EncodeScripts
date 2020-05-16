import vapoursynth as vs
import vsutil

from kagefunc import retinex_edgemask
from lvsfunc.aa import upscaled_sraa
from lvsfunc.kernels import Bicubic
from lvsfunc.misc import replace_ranges
from lvsfunc.scale import descale as ldescale
from toolz.functoolz import curry
from typing import List, NamedTuple, Tuple

from .filter import Range

core = vs.core


class FadeRange(NamedTuple):
    ref: int
    range_: Tuple[int, int]


@curry
def _sraa_frameeval(n: int, clip: vs.VideoNode, w: int, h: int
                    ) -> vs.VideoNode:
    frame = clip.get_frame(n)
    if frame.height < 1080:
        rfactor = 2.5
    else:
        rfactor = 1.5
    return upscaled_sraa(clip.resize.Bicubic(frame.width, frame.height),
                         rfactor=rfactor, h=h, ar=w/h)


def _sraa_reupscale(clip: vs.VideoNode, width: int, height: int
                    ) -> vs.VideoNode:
    sraa = clip.std.FrameEval(_sraa_frameeval(clip=clip, w=width,
                                              h=height))
    scale = sraa.resize.Spline36(width, height, format=vs.GRAY16)
    return scale


def _fade_ranges_with_refs(clip: vs.VideoNode, reupscaled: vs.VideoNode,
                           ranges: List[FadeRange]) -> vs.VideoNode:
    mask = core.std.BlankClip(clip)
    for r in ranges:
        rmask = core.std.Expr([clip[r.ref], reupscaled[r.ref]], "x y - abs")
        rmask = rmask.std.Binarize(1500)
        rmask = vsutil.iterate(rmask, core.std.Maximum, 4)
        rmask = vsutil.iterate(rmask, core.std.Inflate, 2)
        rmask = core.std.Expr([mask, rmask], "x y +")
        mask = replace_ranges(mask, rmask, [r.range_])

    return mask


@curry
def _inverse_mask(clip: vs.VideoNode, reupscaled: vs.VideoNode,
                  ranges: List[FadeRange] = []) -> vs.VideoNode:
    reupscaled = reupscaled.resize.Bicubic(format=clip.format.id)
    line_mask = retinex_edgemask(clip, 0.0001).std.Binarize(10000)
    fade_mask = _fade_ranges_with_refs(clip, reupscaled, ranges)
    mask = core.std.Expr([fade_mask, line_mask.std.Invert()], "x y +")
    return mask.resize.Bicubic(format=clip.format.id)


@curry
def descale(clip: vs.VideoNode, force_scale: List[Range],
            no_scale: List[Range], fade_ranges: List[FadeRange],
            show_mask: bool = False) -> vs.VideoNode:
    kernel = Bicubic(b=1/3, c=1/3)
    heights = [871, 872, 873]
    y = vsutil.get_y(clip)
    ys = ldescale(y, upscaler=_sraa_reupscale, height=heights,
                  kernel=kernel, threshold=0.003,
                  mask=_inverse_mask(ranges=fade_ranges), show_mask=show_mask)
    if show_mask:
        return ys

    yf = ldescale(y, upscaler=_sraa_reupscale, height=heights,
                  kernel=kernel, threshold=0,
                  mask=_inverse_mask(ranges=fade_ranges))
    yd = replace_ranges(ys, yf, force_scale)
    scaled = core.std.ShufflePlanes([yd, clip], planes=[0, 1, 2],
                                    colorfamily=vs.YUV)
    scaled = replace_ranges(scaled, clip, no_scale)
    return scaled


@curry
def descale720(clip: vs.VideoNode, src: vs.VideoNode, ranges: List[Range]
               ) -> vs.VideoNode:
    y = ldescale(vsutil.get_y(src), upscaler=_sraa_reupscale, height=720,
                 kernel=Bicubic(b=1/3, c=1/3), threshold=0, mask=_inverse_mask)
    scaled = core.std.ShufflePlanes([y, src], planes=[0, 1, 2],
                                    colorfamily=vs.YUV)
    scaled = replace_ranges(clip, scaled, ranges)
    return scaled
