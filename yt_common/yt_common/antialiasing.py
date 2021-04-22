import vapoursynth as vs

import vsutil

from kagefunc import kirsch
from lvsfunc.aa import clamp_aa, upscaled_sraa
from lvsfunc.misc import replace_ranges, scale_thresh
from lvsfunc.types import Range

from typing import Any, Dict, List, Optional, Union


core = vs.core


def nnedi3(clip: vs.VideoNode, opencl: bool = False) -> vs.VideoNode:
    nnedi3_args: Dict[str, Any] = dict(field=0, dh=True, nsize=3, nns=3, qual=1)

    y = vsutil.get_y(clip)

    def _nnedi3(clip: vs.VideoNode) -> vs.VideoNode:
        return clip.nnedi3cl.NNEDI3CL(**nnedi3_args) if opencl \
            else clip.nnedi3.nnedi3(**nnedi3_args)

    aa = _nnedi3(y.std.Transpose())
    aa = aa.resize.Spline36(height=clip.width, src_top=0.5).std.Transpose()
    aa = _nnedi3(aa)
    aa = aa.resize.Spline36(height=clip.height, src_top=0.5)
    return aa


def aa_mask_weak(clip: vs.VideoNode) -> vs.VideoNode:
    # use bilateral to smear the noise as much as possible without destroying lines
    pre = vsutil.get_y(clip).bilateral.Bilateral(sigmaS=5, sigmaR=0.75)
    # frei-chen edge detection
    gx = core.std.Convolution(pre, [-7, 0, 7, -10, 0, 10, -7, 0, 7], divisor=7, saturate=False)
    gy = core.std.Convolution(pre, [-7, -10, -7, 0, 0, 0, 7, 10, 7], divisor=7, saturate=False)
    return core.std.Expr([gx, gy], 'x dup * y dup * + sqrt').std.Binarize(scale_thresh(0.25, clip)) \
        .std.Maximum().std.Convolution([1]*9)


def aa_mask_strong(clip: vs.VideoNode) -> vs.VideoNode:
    mask: vs.VideoNode = kirsch(vsutil.get_y(clip)).std.Binarize(scale_thresh(0.25, clip)) \
        .std.Maximum().std.Convolution([1]*9)
    return mask


def aa_mask(clip: vs.VideoNode, weak: Union[Range, List[Range], None] = None) -> vs.VideoNode:
    weak = weak or []
    return replace_ranges(aa_mask_strong(clip), aa_mask_weak(clip), weak)


def sraa_clamp(clip: vs.VideoNode, mask: Optional[vs.VideoNode] = None,
               strength: float = 3, opencl: bool = False) -> vs.VideoNode:
    sraa = upscaled_sraa(clip, rfactor=1.3, opencl=opencl,
                         downscaler=lambda c, w, h: c.resize.Bicubic(w, h, filter_param_a=0, filter_param_b=1/2))
    clamp = clamp_aa(clip, nnedi3(clip, opencl=opencl), sraa, strength=strength)
    return core.std.MaskedMerge(clip, clamp, mask, planes=0) if mask else clamp
