import vapoursynth as vs

from lvsfunc.kernels import Bicubic
from lvsfunc.mask import detail_mask
from lvsfunc.scale import descale

from vardefunc.deband import dumb3kdb

from vsutil import depth

core = vs.core


def cr_prefilter(clip: vs.VideoNode) -> vs.VideoNode:
    rescaled = depth(descale(clip, height=810, kernel=Bicubic(b=0, c=1/2)), 16)
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
