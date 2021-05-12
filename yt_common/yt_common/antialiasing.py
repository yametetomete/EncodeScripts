import vapoursynth as vs

import vsutil

from havsfunc import SMDegrain
from lvsfunc.aa import nnedi3, clamp_aa, upscaled_sraa
from lvsfunc.kernels import Bicubic
from lvsfunc.misc import replace_ranges, scale_thresh
from lvsfunc.types import Range

from typing import Callable, List, Optional, Union


core = vs.core


def mask_weak(clip: vs.VideoNode) -> vs.VideoNode:
    # use bilateral to smear the noise as much as possible without destroying lines
    pre = vsutil.get_y(clip).bilateral.Bilateral(sigmaS=5, sigmaR=0.75)
    # frei-chen edge detection
    gx = core.std.Convolution(pre, [-7, 0, 7, -10, 0, 10, -7, 0, 7], divisor=7, saturate=False)
    gy = core.std.Convolution(pre, [-7, -10, -7, 0, 0, 0, 7, 10, 7], divisor=7, saturate=False)
    return core.std.Expr([gx, gy], 'x dup * y dup * + sqrt').std.Binarize(scale_thresh(0.25, clip)) \
        .std.Maximum().std.Convolution([1]*9)


def mask_strong(clip: vs.VideoNode) -> vs.VideoNode:
    mask: vs.VideoNode = SMDegrain(vsutil.get_y(clip), tr=3, thSAD=500, RefineMotion=True, prefilter=4) \
        .std.Prewitt().std.Binarize(scale_thresh(0.25, clip)).std.Maximum().std.Convolution([1]*9)
    return mask


def combine_mask(clip: vs.VideoNode, weak: Union[Range, List[Range], None] = None) -> vs.VideoNode:
    return replace_ranges(mask_strong(clip), mask_weak(clip), weak or [])


def sraa_clamp(clip: vs.VideoNode, mask: Optional[vs.VideoNode] = None,
               strength: float = 2, opencl: bool = True,
               postprocess: Optional[Callable[[vs.VideoNode], vs.VideoNode]] = None) -> vs.VideoNode:
    sraa = upscaled_sraa(clip, rfactor=1.3, nnedi3cl=opencl, downscaler=Bicubic(b=0, c=1/2).scale)
    sraa = postprocess(sraa) if postprocess else sraa
    clamp = clamp_aa(clip, nnedi3(clip, opencl=opencl), sraa, strength=strength)
    return core.std.MaskedMerge(clip, clamp, mask, planes=0) if mask else clamp
