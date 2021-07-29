import vapoursynth as vs

from lvsfunc.kernels import Bicubic
from lvsfunc.mask import detail_mask
from lvsfunc.scale import descale

from vardefunc.deband import dumb3kdb

from vsutil import depth

from typing import Any, Dict

core = vs.core


def _nnedi3_rescale(clip: vs.VideoNode, width: int, height: int) -> vs.VideoNode:
    nnargs: Dict[str, Any] = dict(field=0, dh=True, nsize=4, nns=4, qual=2, pscrn=2)
    nn = clip.resize.Point(1440, 810, format=vs.GRAY16).std.Transpose() \
        .nnedi3.nnedi3(**nnargs) \
        .std.Transpose() \
        .nnedi3.nnedi3(**nnargs)
    return nn.resize.Bicubic(width, height, filter_param_a=0, filter_param_b=1/2,
                             src_top=0.5, src_left=0.5, format=vs.GRAYS)


def cr_prefilter(clip: vs.VideoNode) -> vs.VideoNode:
    rescaled = depth(descale(clip, height=810, kernel=Bicubic(b=0, c=1/2), upscaler=_nnedi3_rescale), 16)
    return rescaled


def deband_tv(clip: vs.VideoNode) -> vs.VideoNode:
    dmask = detail_mask(clip)
    deb = dumb3kdb(clip, radius=16, threshold=40)
    return core.std.MaskedMerge(deb, clip, dmask)


def regrain_tv(clip: vs.VideoNode) -> vs.VideoNode:
    mask_bright = clip.std.PlaneStats().adg.Mask(10)
    mask_dark = clip.std.PlaneStats().adg.Mask(25)
    sgrain_l = core.std.MaskedMerge(clip, clip.grain.Add(var=0.1, constant=True, seed=393), mask_bright.std.Invert())
    sgrain_h = core.std.MaskedMerge(clip, clip.grain.Add(var=0.15, uvar=0.1, constant=True, seed=393), mask_bright)
    sgrain_h = core.std.MaskedMerge(clip, sgrain_h, mask_dark.std.Invert())
    sgrain = sgrain_h.std.MergeDiff(clip.std.MakeDiff(sgrain_l))
    dgrain = core.std.MaskedMerge(clip, clip.grain.Add(var=0.25, uvar=0.1, constant=False, seed=393), mask_dark)
    grain = dgrain.std.MergeDiff(clip.std.MakeDiff(sgrain))
    return grain
