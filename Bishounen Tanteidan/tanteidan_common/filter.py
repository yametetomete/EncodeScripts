import vapoursynth as vs

import vsutil

from G41Fun import MaskedDHA
from debandshit import f3kbilateral
from havsfunc import LSFmod
from lvsfunc.mask import detail_mask
from lvsfunc.misc import replace_ranges
from lvsfunc.types import Range
from mvsfunc import BM3D
from vardefunc import dumb3kdb

from typing import List, Optional, Sequence, Union

from yt_common.antialiasing import combine_mask, sraa_clamp
from yt_common.deband import morpho_mask


core = vs.core


def denoise(clip: vs.VideoNode, sigma: Union[float, Sequence[float]] = 0.75) -> vs.VideoNode:
    den: vs.VideoNode = BM3D(clip, sigma=sigma)
    return den


def deband(clip: vs.VideoNode) -> vs.VideoNode:
    """
    mostly stole this from varde
    """
    grad_mask, yrangebig = morpho_mask(clip.dfttest.DFTTest(sigma=14, sigma2=10, sbsize=1, sosize=0)
                                       .rgvs.RemoveGrain(3))
    y = vsutil.get_y(clip)
    mask = detail_mask(y, brz_a=0.05, brz_b=0.03)
    dumb: vs.VideoNode = dumb3kdb(clip)
    deband_weak = core.std.MaskedMerge(vsutil.get_y(dumb), y, mask)
    deband_norm = f3kbilateral(y, y=36)
    deband_strong = f3kbilateral(y, y=65)
    deband = core.std.MaskedMerge(deband_strong, deband_norm, grad_mask)
    deband = core.std.MaskedMerge(deband, deband_weak, yrangebig)
    deband = core.std.ShufflePlanes([deband, dumb], planes=[0, 1, 2], colorfamily=vs.YUV)
    return deband


def antialias(clip: vs.VideoNode, weak: Optional[List[Range]] = None, noaa: Optional[List[Range]] = None,
              dehalo: bool = True, sharpen: bool = False) -> vs.VideoNode:
    def _sraa_pp_sharpdehalo(sraa: vs.VideoNode) -> vs.VideoNode:
        if sharpen:  # all this really seems to do is make the haloing worse, will not be using!
            y = LSFmod(vsutil.get_y(sraa), strength=70, Smode=3, edgemode=0, source=vsutil.get_y(clip))
            sraa = core.std.ShufflePlanes([y, sraa], planes=[0, 1, 2], colorfamily=vs.YUV)
        sraa = MaskedDHA(sraa, rx=1.7, ry=1.7, darkstr=0, brightstr=0.75) if dehalo else sraa
        return sraa
    clamp = sraa_clamp(clip, mask=combine_mask(clip, weak or []), postprocess=_sraa_pp_sharpdehalo)
    return replace_ranges(clamp, clip, noaa or [])


def regrain(clip: vs.VideoNode) -> vs.VideoNode:
    mask_bright = clip.std.PlaneStats().adg.Mask(10)
    mask_dark = clip.std.PlaneStats().adg.Mask(25)
    sgrain_l = core.std.MaskedMerge(clip, clip.grain.Add(var=0.1, constant=True, seed=393), mask_bright.std.Invert())
    sgrain_h = core.std.MaskedMerge(clip, core.std.MaskedMerge(clip, clip.grain.Add(var=0.2, constant=True, seed=393),
                                                               mask_bright),
                                    mask_dark.std.Invert())
    sgrain = sgrain_h.std.MergeDiff(clip.std.MakeDiff(sgrain_l))
    dgrain = core.std.MaskedMerge(clip, clip.grain.Add(var=0.3, constant=False, seed=393), mask_dark)
    grain = dgrain.std.MergeDiff(clip.std.MakeDiff(sgrain))
    return grain


def finalize(clip: vs.VideoNode) -> vs.VideoNode:
    return vsutil.depth(clip, 10)
