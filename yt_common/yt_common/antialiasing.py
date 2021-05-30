import vapoursynth as vs

import math

from havsfunc import SMDegrain
from lvsfunc.aa import nnedi3, clamp_aa, upscaled_sraa
from lvsfunc.kernels import Bicubic
from lvsfunc.misc import replace_ranges, scale_thresh
from lvsfunc.types import Range

from typing import Any, Callable, Dict, List, Optional, Union

from .scale import nnedi3_double


core = vs.core


def mask_weak(clip: vs.VideoNode) -> vs.VideoNode:
    # use bilateral to smear the noise as much as possible without destroying lines
    pre = clip.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY) \
        .bilateral.Bilateral(sigmaS=5, sigmaR=0.75)
    # g41f's broken frei-chen edge detection
    gx = core.std.Convolution(pre, [-7, 0, 7, -10, 0, 10, -7, 0, 7], divisor=7, saturate=False)
    gy = core.std.Convolution(pre, [-7, -10, -7, 0, 0, 0, 7, 10, 7], divisor=7, saturate=False)
    return core.std.Expr([gx, gy], 'x dup * y dup * + sqrt').std.Binarize(scale_thresh(0.25, clip)) \
        .std.Maximum().std.Convolution([1]*9)


def mask_strong(clip: vs.VideoNode) -> vs.VideoNode:
    pre: vs.VideoNode = SMDegrain(clip.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY),
                                  tr=3, thSAD=500, RefineMotion=True, prefilter=4)
    mask = pre.std.Prewitt().std.Binarize(scale_thresh(0.25, clip)).std.Maximum().std.Convolution([1]*9)
    return mask


def combine_mask(clip: vs.VideoNode, weak: Union[Range, List[Range], None] = None) -> vs.VideoNode:
    return replace_ranges(mask_strong(clip), mask_weak(clip), weak or [])


def sraa_clamp(clip: vs.VideoNode, mask: Optional[Callable[[vs.VideoNode], vs.VideoNode]] = None,
               strength: float = 2, opencl: bool = False,
               postprocess: Optional[Callable[[vs.VideoNode], vs.VideoNode]] = None) -> vs.VideoNode:
    sraa = upscaled_sraa(clip, rfactor=1.3, nnedi3cl=opencl, downscaler=Bicubic(b=0, c=1/2).scale)
    sraa = postprocess(sraa) if postprocess else sraa
    clamp = clamp_aa(clip, nnedi3(clip, opencl=opencl), sraa, strength=strength)
    return core.std.MaskedMerge(clip, clamp, mask(sraa), planes=0) if mask else clamp


def _zastin_default_mask(clip: vs.VideoNode) -> vs.VideoNode:
    return clip.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY) \
        .std.Prewitt() \
        .std.Binarize(scale_thresh(0.25, clip)) \
        .std.Maximum() \
        .std.BoxBlur(0, 1, 1, 1, 1)


def zastinAA(clip: vs.VideoNode, rfactor: float = 2.0,
             maskfun: Callable[[vs.VideoNode], vs.VideoNode] = _zastin_default_mask,
             **eedi3override: Any) -> vs.VideoNode:
    eedi3args: Dict[str, Any] = {'field': 0, 'alpha': 0.125, 'beta': 0.25, 'gamma': 40,
                                 'nrad': 2, 'mdis': 20, 'vcheck': 2, 'vthresh0': 12,
                                 'vthresh1': 24, 'vthresh2': 4}
    eedi3args.update(eedi3override)
    y = clip.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY)

    def eedi3s(clip: vs.VideoNode, mclip: Optional[vs.VideoNode] = None) -> vs.VideoNode:
        out = clip.eedi3m.EEDI3(mclip=mclip, sclip=clip, **eedi3args)
        if mclip is not None:
            return core.std.Expr([clip, out, mclip], 'z y x ?')
        return out

    def resize_mclip(mclip: vs.VideoNode, w: Optional[int] = None, h: Optional[int] = None) -> vs.VideoNode:
        iw = mclip.width
        ih = mclip.height
        ow = w if w is not None else iw
        oh = h if h is not None else ih
        if (ow > iw and ow/iw != ow//iw) or (oh > ih and oh/ih != oh//ih):
            mclip = mclip.resize.Point(iw * math.ceil(ow / iw), ih * math.ceil(oh / ih))
        return mclip.fmtc.resample(ow, oh, kernel='box', fulls=1, fulld=1)

    aaw = round(y.width * rfactor) & ~1
    aah = round(y.height * rfactor) & ~1
    mask = maskfun(y)
    mclip = resize_mclip(mask, aaw, aah)

    aa = y.std.Transpose()
    aa = nnedi3_double(aa)
    aa = aa.resize.Spline16(aah, aaw)
    aa = eedi3s(aa, mclip=mclip.std.Transpose()).std.Transpose()
    aa = eedi3s(aa, mclip=mclip).resize.Spline16(y.width, y.height)

    return core.std.ShufflePlanes([core.std.MaskedMerge(y, aa, mask), clip], planes=[0, 1, 2], colorfamily=vs.YUV)
