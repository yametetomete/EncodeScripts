import vapoursynth as vs
import os

from typing import Any, Dict, List, Optional

from yt_common.antialiasing import sraa_clamp, mask_strong
from yt_common.data import FSRCNNX

from G41Fun import MaskedDHA
from awsmfunc import bbmod
from kagefunc import retinex_edgemask
from lvsfunc.denoise import bm3d
from lvsfunc.kernels import Bicubic, Kernel
from lvsfunc.mask import detail_mask
from lvsfunc.misc import replace_ranges, scale_thresh
from lvsfunc.scale import descale as ldescale
from lvsfunc.types import Range
from vardefunc import fsrcnnx_upscale, diff_creditless_mask, dumb3kdb
from vsutil import depth
from vsutil import Range as CRange

NCED = os.path.join(os.path.dirname(__file__),
                    "../bdmv/[180223][BDMV] プリンセス・プリンシパル VI/PRINCESS_PRINCIPAL_6/BDMV/STREAM/00013.m2ts")

core = vs.core


def edgefix(clip: vs.VideoNode) -> vs.VideoNode:
    bb: vs.VideoNode = bbmod(clip, top=3, bottom=3, left=3, right=3, blur=500)
    return bb


def denoise(clip: vs.VideoNode, sigma: float = 0.75, h: float = 0.4) -> vs.VideoNode:
    return core.std.ShufflePlanes([
        bm3d(core.std.ShufflePlanes(clip, planes=0, colorfamily=vs.GRAY), sigma=sigma, radius=1),
        clip.knlm.KNLMeansCL(d=3, a=1, h=h)
    ], planes=[0, 1, 2], colorfamily=vs.YUV)


def _nnedi3_double(clip: vs.VideoNode) -> vs.VideoNode:
    nnargs: Dict[str, Any] = dict(field=0, dh=True, nsize=4, nns=4, qual=2, pscrn=2)
    nn = clip.std.Transpose() \
        .nnedi3.nnedi3(**nnargs) \
        .std.Transpose() \
        .nnedi3.nnedi3(**nnargs)
    return nn.resize.Bicubic(src_top=0.5, src_left=0.5)


def descale(clip: vs.VideoNode, kernel: Kernel = Bicubic(b=0, c=1/2), mask: bool = False) -> vs.VideoNode:
    def _fsrlineart(clip: vs.VideoNode, width: int, height: int) -> vs.VideoNode:
        clip = clip.resize.Point(1280, 720)
        assert clip.format is not None
        nn = depth(_nnedi3_double(depth(clip, 16)), clip.format.bits_per_sample)
        fsr = fsrcnnx_upscale(clip, width, height, upscaled_smooth=nn, shader_file=FSRCNNX)
        mask = retinex_edgemask(depth(fsr.std.ShufflePlanes(0, vs.GRAY), 16))
        mask = mask.std.Binarize(scale_thresh(0.65, mask)).std.Maximum()
        mask = depth(mask, clip.format.bits_per_sample, range_in=CRange.FULL, range=CRange.FULL)
        return core.std.MaskedMerge(nn.resize.Bicubic(width, height, filter_param_a=0, filter_param_b=1/2), fsr, mask)
    return depth(ldescale(clip, height=720, kernel=kernel, upscaler=_fsrlineart), 16) if mask \
        else depth(ldescale(clip, height=720, kernel=kernel, upscaler=_fsrlineart, mask=None), 16)


def deband(clip: vs.VideoNode, strong: Optional[List[Range]] = None) -> vs.VideoNode:
    mask = detail_mask(clip)
    deband = core.std.MaskedMerge(dumb3kdb(clip, radius=16, threshold=40), clip, mask)
    deband_strong = core.std.MaskedMerge(dumb3kdb(clip, radius=16, threshold=50), clip, mask)
    return replace_ranges(deband, deband_strong, strong or [])


def antialias(clip: vs.VideoNode) -> vs.VideoNode:
    def _sraa_pp_dehalo(sraa: vs.VideoNode) -> vs.VideoNode:
        sraa = MaskedDHA(sraa, rx=2.4, darkstr=0.1, brightstr=0.75)
        return sraa
    return sraa_clamp(clip, postprocess=_sraa_pp_dehalo, mask=mask_strong(clip))


def regrain(clip: vs.VideoNode) -> vs.VideoNode:
    mask_bright = clip.std.PlaneStats().adg.Mask(5)
    mask_dark = clip.std.PlaneStats().adg.Mask(15)
    sgrain_l = core.std.MaskedMerge(clip, clip.grain.Add(var=0.15, constant=True, seed=393), mask_bright.std.Invert())
    sgrain_h = core.std.MaskedMerge(clip, clip.grain.Add(var=0.25, uvar=0.1, constant=True, seed=393), mask_bright)
    sgrain_h = core.std.MaskedMerge(clip, sgrain_h, mask_dark.std.Invert())
    sgrain = sgrain_h.std.MergeDiff(clip.std.MakeDiff(sgrain_l))
    dgrain = core.std.MaskedMerge(clip, clip.grain.Add(var=0.35, uvar=0.1, constant=False, seed=393), mask_dark)
    grain = dgrain.std.MergeDiff(clip.std.MakeDiff(sgrain))
    return grain


def scenefilter_ed(clip: vs.VideoNode, src: vs.VideoNode, ed: Optional[int], mask: bool = True) -> vs.VideoNode:
    if ed is None:
        return clip
    den = denoise(src)
    dehalo = MaskedDHA(den, rx=2, darkstr=0.1, brightstr=0.75)
    edc = replace_ranges(den, dehalo, [(ed+2121, ed+2159)])
    edc = antialias(edc)
    edc = regrain(edc)
    if mask:
        nc = depth(core.lsmas.LWLibavSource(NCED)[24:-24], 16)
        dcm = diff_creditless_mask(src, src[ed:], nc, ed, 6425, prefilter=True)
        edc = core.std.MaskedMerge(edc, den, dcm)
    return replace_ranges(clip, edc, [(ed, ed+2159)])


def finalize(clip: vs.VideoNode) -> vs.VideoNode:
    return depth(clip, 10)
