import vapoursynth as vs
import vsutil

from kagefunc import adaptive_grain, retinex_edgemask
from lvsfunc.misc import replace_ranges
from mvsfunc import BM3D
from toolz.functoolz import curry
from typing import List, Optional, Tuple, Union
from vardefunc import dcm

core = vs.core

Range = Union[int, Tuple[int, int]]


def denoise(clip: vs.VideoNode) -> vs.VideoNode:
    denoisechroma = core.knlm.KNLMeansCL(clip, d=1, a=2, h=0.45, channels="UV",
                                         device_type='gpu', device_id=0)
    denoiseluma = core.knlm.KNLMeansCL(clip, d=3, a=2, h=0.4, channels="Y",
                                       device_type='gpu', device_id=0)
    return core.std.ShufflePlanes([denoiseluma, denoisechroma],
                                  planes=[0, 1, 2], colorfamily=vs.YUV)


@curry
def w2x(clip: vs.VideoNode, w2x_range: List[Range]) -> vs.VideoNode:
    rgb = clip.resize.Bicubic(format=vs.RGBS, matrix_in_s="709")
    w2x = rgb.w2xnvk.Waifu2x(noise=1, scale=1, model=2) \
        .resize.Bicubic(format=clip.format.id, matrix_s="709")

    bm3d = BM3D(clip, sigma=[0, 5], ref=w2x)
    bm3d = core.std.ShufflePlanes([w2x, bm3d], planes=[0, 1, 2],
                                  colorfamily=vs.YUV)
    denoise = replace_ranges(clip, bm3d, w2x_range)
    return denoise


@curry
def deband(clip: vs.VideoNode, hard: List[Range],
           harder: List[Range]) -> vs.VideoNode:
    line = retinex_edgemask(clip).std.Binarize(9500).rgvs.RemoveGrain(3) \
        .std.Inflate()
    nf3kdb = clip.neo_f3kdb.Deband(range=18, y=32, cb=24, cr=24, grainy=24,
                                   grainc=0, output_depth=16, sample_mode=4)
    nf3kdb = core.std.MaskedMerge(nf3kdb, clip, line)
    placebo = clip.placebo.Deband(iterations=3, threshold=3, radius=24,
                                  grain=4)
    placebo2 = clip.placebo.Deband(iterations=3, threshold=5, radius=32,
                                   grain=4)
    debanded = replace_ranges(nf3kdb, placebo, hard)
    debanded = replace_ranges(debanded, placebo2, harder)
    return debanded


@curry
def mask_oped(clip: vs.VideoNode, src: vs.VideoNode,
              op: Optional[Tuple[int, int]], ed: Optional[Tuple[int, int]],
              src_op: vs.VideoNode, src_ed: vs.VideoNode) -> vs.VideoNode:
    merge = clip
    if op is not None:
        credit_op_m = dcm(clip, src[op[0]:op[1]+1],
                          src_op[:op[1]-op[0]+1], op[0], op[1], 2, 2)
        merge = core.std.MaskedMerge(merge, src, credit_op_m)
    if ed is not None:
        credit_ed_m = dcm(clip, src[ed[0]:ed[1]+1],
                          src_ed[:ed[1]-ed[0]+1], ed[0], ed[1], 2, 2)
        merge = core.std.MaskedMerge(merge, src, credit_ed_m)
    return merge


@curry
def mask_logo(clip: vs.VideoNode, src: vs.VideoNode, src_logo: vs.VideoNode,
              range: Range) -> vs.VideoNode:
    mask = vsutil.get_y(src_logo).std.Binarize(19).fmtc.bitdepth(bits=16)
    mask = vsutil.iterate(mask, core.std.Inflate, 5)
    merge = core.std.MaskedMerge(clip, src, mask)
    merge = replace_ranges(clip, merge, [range])
    return merge


def finalize(clip: vs.VideoNode) -> vs.VideoNode:
    final = adaptive_grain(clip, 0.3)
    final = final.fmtc.bitdepth(bits=10, dmode=3)
    return final
