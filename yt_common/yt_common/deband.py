import vapoursynth as vs

from enum import Enum
from functools import partial
from typing import Any, Callable, List, Optional, Tuple, Union

from lvsfunc.util import scale_thresh

import vsutil


core = vs.core


class XxpandModes(Enum):
    SQUARE = 1
    ELLIPSE = 2
    LOSANGE = 3


def mt_xxpand_multi(clip: vs.VideoNode, sw: int = 1, sh: Optional[int] = None,
                    mode: XxpandModes = XxpandModes.SQUARE,
                    planes: Union[int, List[int], None] = None, start: int = 0,
                    m__imum: Callable[..., vs.VideoNode] = core.std.Maximum, **params: Any) -> List[vs.VideoNode]:
    """
    blame zastin for this
    """
    sh = vsutil.fallback(sh, sw)
    assert clip.format is not None
    planes = list(range(clip.format.num_planes)) if planes is None else [planes] if isinstance(planes, int) else planes

    if mode == XxpandModes.ELLIPSE:
        coordinates = [[1]*8, [0, 1, 0, 1, 1, 0, 1, 0], [0, 1, 0, 1, 1, 0, 1, 0]]
    elif mode == XxpandModes.LOSANGE:
        coordinates = [[0, 1, 0, 1, 1, 0, 1, 0]] * 3
    else:
        coordinates = [[1]*8] * 3

    clips = [clip]

    end = min(sw, sh) + start

    for x in range(start, end):
        clips += [m__imum(clips[-1], coordinates=coordinates[x % 3], planes=planes, **params)]

    for x in range(end, end + sw - sh):
        clips += [m__imum(clips[-1], coordinates=[0, 0, 0, 1, 1, 0, 0, 0], planes=planes, **params)]

    for x in range(end, end + sh - sw):
        clips += [m__imum(clips[-1], coordinates=[0, 1, 0, 0, 0, 0, 1, 0], planes=planes, **params)]

    return clips


def morpho_mask(clip: vs.VideoNode) -> Tuple[vs.VideoNode, vs.VideoNode]:
    """
    blame zastin for this
    """
    y = vsutil.get_y(clip)
    assert y.format is not None

    maxm = partial(mt_xxpand_multi, m__imum=core.std.Maximum)
    minm = partial(mt_xxpand_multi, m__imum=core.std.Minimum)

    ymax = maxm(y, sw=40, mode='ellipse')
    ymin = minm(y, sw=40, mode='ellipse')

    thr = round(0.0125 * ((1 << y.format.bits_per_sample) - 1))
    ypw0 = y.std.Prewitt()
    ypw = ypw0.std.Binarize(thr).rgvs.RemoveGrain(11)

    rad = 3
    thr = round(0.0098 * ((1 << y.format.bits_per_sample) - 1))
    yrangesml = core.std.Expr([ymax[3], ymin[3]], 'x y - abs')
    yrangesml = yrangesml.std.Binarize(thr).std.BoxBlur(0, 2, 1, 2, 1)

    rad = 16
    thr = round(0.0156 * ((1 << y.format.bits_per_sample) - 1))
    yrangebig0 = core.std.Expr([ymax[rad], ymin[rad]], 'x y - abs')
    yrangebig = yrangebig0.std.Binarize(thr)
    yrangebig = minm(yrangebig,
                     sw=rad * 3 // 4,
                     threshold=(1 << y.format.bits_per_sample)//((rad * 3 // 4) + 1),
                     mode='ellipse')[-1]
    yrangebig = yrangebig.std.BoxBlur(0, rad//4, 1, rad//4, 1)

    rad = 30
    thr = round(0.0039 * ((1 << y.format.bits_per_sample) - 1))
    ymph = core.std.Expr([y, maxm(ymin[rad], sw=rad, mode='ellipse')[rad],
                          minm(ymax[rad], sw=rad, mode='ellipse')[rad]], 'x y - z x - max')
    ymph = ymph.std.Binarize(round(0.00586 * ((1 << y.format.bits_per_sample) - 1)))
    ymph = ymph.std.Minimum().std.Maximum()
    ymph = ymph.std.BoxBlur(0, 4, 1, 4, 1)

    grad_mask = core.std.Expr([ymph, yrangesml, ypw], expr="x y z max max")

    return grad_mask, yrangebig


def color_mask(clip: vs.VideoNode, y: Tuple[float, float], u: Tuple[float, float], v: Tuple[float, float]
               ) -> vs.VideoNode:
    expr = f"x {scale_thresh(y[0], clip)} >= x {scale_thresh(y[1], clip)} <= and "  # Y bounds check
    expr += f"y {scale_thresh(u[0], clip)} >= y {scale_thresh(u[1], clip)} <= and and "  # U bounds check
    expr += f"z {scale_thresh(v[0], clip)} >= z {scale_thresh(v[1], clip)} <= and and "  # V bounds check
    expr += f"{scale_thresh(1.0, clip)} 0 ?"  # brz
    wmask = core.std.Expr(vsutil.split(clip.resize.Bicubic(format=vs.YUV444P16)), expr)
    wmask = wmask.std.Inflate().std.Binarize()
    wmask_edge = wmask.std.Prewitt().std.Binarize()
    wmask = core.std.Expr([wmask, wmask_edge], "x y -")  # preserve edges for sharpness
    return wmask


def gray_mask(clip: vs.VideoNode, y: Tuple[float, float], cthr: float = 0.02) -> vs.VideoNode:
    expr = f"x {scale_thresh(y[0], clip)} >= x {scale_thresh(y[1], clip)} <= and "  # Y bounds check
    expr += "y z >= and "  # U >= V for blue-ish grays
    expr += f"y z - abs {scale_thresh(cthr, clip)} <= and "  # UV proximity check
    expr += f"{scale_thresh(1.0, clip)} 0 ?"  # brz
    wmask = core.std.Expr(vsutil.split(clip.resize.Bicubic(format=vs.YUV444P16)), expr)
    wmask = wmask.std.Inflate().std.Binarize()
    wmask_edge = wmask.std.Prewitt().std.Binarize()
    wmask = core.std.Expr([wmask, wmask_edge], "x y -")  # preserve edges for sharpness
    return wmask
