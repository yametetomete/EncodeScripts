import vapoursynth as vs

import math

from havsfunc import SMDegrain
from lvsfunc.aa import nnedi3, clamp_aa, upscaled_sraa
from lvsfunc.kernels import Bicubic
from lvsfunc.misc import replace_ranges, scale_thresh
from lvsfunc.types import Range
from lvsfunc.util import pick_repair

from typing import Any, Callable, Dict, List, Optional, Union

from .scale import nnedi3_double

from vsutil import get_w, get_y


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


def supersample_aa(clip: vs.VideoNode,
                   rfactor: float = 1.5,
                   rep: Optional[int] = None,
                   width: Optional[int] = None, height: Optional[int] = None,
                   downscaler: Optional[Callable[[vs.VideoNode, int, int], vs.VideoNode]]
                   = Bicubic(b=0, c=1/2).scale,
                   aafun: Optional[Callable[[vs.VideoNode, vs.VideoNode], vs.VideoNode]] = None,
                   nnedi3cl: Optional[bool] = None,
                   **eedi3_args: Any) -> vs.VideoNode:
    """
    A function that performs a supersampled single-rate AA to deal with heavy aliasing and broken-up lineart.
    Useful for Web rips, where the source quality is not good enough to descale,
    but you still want to deal with some bad aliasing and lineart.
    It works by supersampling the clip, performing AA, and then downscaling again.
    Downscaling can be disabled by setting `downscaler` to `None`, returning the supersampled luma clip.
    The dimensions of the downscaled clip can also be adjusted by setting `height` or `width`.
    Setting either `height` or `width` will also scale the chroma accordingly.
    Original function written by Zastin, heavily modified by LightArrowsEXE.
    Alias for this function is `lvsfunc.sraa`.
    Dependencies:
    * RGSF (optional: 32 bit clip)
    * vapoursynth-eedi3
    * vapoursynth-nnedi3
    * vapoursynth-nnedi3cl (optional: opencl)
    :param clip:            Input clip
    :param rfactor:         Image enlargement factor. 1.3..2 makes it comparable in strength to vsTAAmbk
                            It is not recommended to go below 1.3 (Default: 1.5)
    :param rep:             Repair mode (Default: None)
    :param width:           Target resolution width. If None, determined from `height`
    :param height:          Target resolution height (Default: ``clip.height``)
    :param downscaler:      Resizer used to downscale the AA'd clip
    :param aafun:           Single-rate antialiaser to apply after supersampling.
                            Takes an input clip and an sclip. (Default: eedi3)
    :param nnedi3cl:        OpenCL acceleration for nnedi3 upscaler (Default: False)
    :return:                Antialiased and optionally rescaled clip
    """
    if clip.format is None:
        raise ValueError("upscaled_sraa: 'Variable-format clips not supported'")

    luma = get_y(clip)

    nnargs: Dict[str, Any] = dict(field=0, nsize=0, nns=4, qual=2)
    # TAAmbk defaults are 0.5, 0.2, 20, 3, 30
    eeargs: Dict[str, Any] = dict(field=0, dh=False, alpha=0.2, beta=0.6, gamma=40, nrad=2, mdis=20)
    eeargs.update(eedi3_args)

    if rfactor < 1:
        raise ValueError("upscaled_sraa: '\"rfactor\" must be above 1'")

    ssw = round(clip.width * rfactor)
    ssw = (ssw + 1) & ~1
    ssh = round(clip.height * rfactor)
    ssh = (ssh + 1) & ~1

    height = height or clip.height

    if width is None:
        width = clip.width if height == clip.height else get_w(height, aspect_ratio=clip.width / clip.height)

    def _nnedi3(clip: vs.VideoNode, dh: bool = False) -> vs.VideoNode:
        return clip.nnedi3cl.NNEDI3CL(dh=dh, **nnargs) if nnedi3cl \
            else clip.nnedi3.nnedi3(dh=dh, **nnargs)

    def _eedi3(clip: vs.VideoNode, sclip: vs.VideoNode) -> vs.VideoNode:
        return clip.eedi3m.EEDI3(sclip=sclip, **eeargs)

    aafun = aafun or _eedi3

    # Nnedi3 upscale from source height to source height * rounding (Default 1.5)
    up_y = _nnedi3(luma, dh=True)
    up_y = up_y.resize.Spline36(height=ssh, src_top=0.5).std.Transpose()
    up_y = _nnedi3(up_y, dh=True)
    up_y = up_y.resize.Spline36(height=ssw, src_top=0.5)

    # Single-rate AA
    aa_y = aafun(up_y, _nnedi3(up_y))
    aa_y = core.std.Transpose(aa_y)
    aa_y = aafun(aa_y, _nnedi3(aa_y))

    scaled = aa_y if downscaler is None else downscaler(aa_y, width, height)
    scaled = pick_repair(scaled)(scaled, luma.resize.Bicubic(width, height), mode=rep) if rep else scaled

    if clip.format.num_planes == 1 or downscaler is None:
        return scaled
    if height is not clip.height or width is not clip.width:
        if height % 2:
            raise ValueError("upscaled_sraa: '\"height\" must be an even number when not passing a GRAY clip'")
        if width % 2:
            raise ValueError("upscaled_sraa: '\"width\" must be an even number when not passing a GRAY clip'")

        chroma = Bicubic().scale(clip, width, height)
        return core.std.ShufflePlanes([scaled, chroma], planes=[0, 1, 2], colorfamily=vs.YUV)
    return core.std.ShufflePlanes([scaled, clip], planes=[0, 1, 2], colorfamily=vs.YUV)
