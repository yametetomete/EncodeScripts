import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix, letterbox_refix, regrain)

from yt_common.automation import SelfRunner
from yt_common.chapters import Chapter
from yt_common.source import waka_replace

from lvsfunc.types import Range
from lvsfunc.dehardsub import HardsubLine, HardsubSignFade, HardsubMask, bounded_dehardsub
from lvsfunc.mask import BoundingBox
from lvsfunc.misc import replace_ranges, scale_thresh

from awsmfunc import bbmod

from vsutil import Range as CRange
from vsutil import scale_value, split

from typing import List, Tuple

import os

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 624),
    Chapter("Part A", 2782),
    Chapter("Part B", 10790),
    Chapter("ED", 31530),
    Chapter("PV", 33688),
]

WAKA_REPLACE: List[List[Range]] = [
    [(31530, 32333)],
    [],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubLine([
        (630, 2744),
    ], ((283, 844), (1349, 204))),
    HardsubSignFade([
        (4202, 4322),
        (6794, 6812),
        (33951, 34047),
    ]),
]

NOSCALE: List[Range] = [
]
AA_NONE: List[Range] = [
]
AA_STRONGER: List[Range] = [
]
LETTERBOX: List[Range] = [
    (33688, 33720),
    (33764, 33820),
]
LETTERBOX_FADES: List[Range] = [
]
LETTERBOX_HOR_SHIFT: List[Range] = [
    (2789, 3011),
    (3242, 3703),
]
LETTERBOX_BW_VER_SHIFT: List[Range] = [
    (2818, 2829),
]
WMASK_BLUR: List[Range] = [
    (2789, 2799),
    (2808, 2816),
    (2857, 3915),
]


def black(clip: vs.VideoNode) -> Tuple[float, float, float]:
    assert clip.format is not None
    return (
        scale_value(0, 8, clip.format.bits_per_sample, scale_offsets=True, range_in=CRange.FULL, range=CRange.LIMITED),
        scale_thresh(0.5, clip),
        scale_thresh(0.5, clip),
    )


def letterbox_shift_hor(clip: vs.VideoNode, ranges: List[Range]) -> vs.VideoNode:
    shift = clip.resize.Bicubic(src_left=241)
    crop_y = shift.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY).std.Crop(right=585)
    bb_y = bbmod(crop_y, left=4)
    borders = core.std.ShufflePlanes([
        bb_y.std.AddBorders(left=292, right=293, color=black(clip)[0]),
        shift.std.Crop(right=584).std.AddBorders(left=292, right=292, color=black(clip))
    ], planes=[0, 1, 2], colorfamily=vs.YUV)
    return replace_ranges(clip, borders, ranges)


def letterbox_shift_vert_gray(clip: vs.VideoNode, ranges: List[Range]) -> vs.VideoNode:
    assert clip.format is not None
    shift = clip.resize.Bicubic(src_top=55)
    crop_y = shift.std.ShufflePlanes(planes=0, colorfamily=vs.GRAY).std.Crop(bottom=190)
    bb_y: vs.VideoNode = bbmod(crop_y, top=2, bottom=1)
    # this is used for a range thats in black and white so fuck dealing with
    # chroma subsampling bullshit
    borders = bb_y.std.AddBorders(top=95, bottom=95, color=black(clip)[0]).resize.Bicubic(format=clip.format.id)
    return replace_ranges(clip, borders, ranges)


def stupid_bullshit(clip: vs.VideoNode, ranges: List[Range]) -> vs.VideoNode:
    expr = f"y {scale_thresh(0.47, clip)} >= y {scale_thresh(0.53, clip)} <= and "  # U bounds check
    expr += f"z {scale_thresh(0.47, clip)} >= z {scale_thresh(0.53, clip)} <= and and "  # V bounds check
    expr += f"x {scale_thresh(0.7, clip)} >= x {scale_thresh(0.82, clip)} <= and and "  # Y bounds check
    expr += f"{scale_thresh(1.0, clip)} 0 ?"  # brz
    wmask = core.std.Expr(split(clip.resize.Bicubic(format=vs.YUV444P16)), expr)
    wmask = wmask.std.Inflate().std.Binarize()
    wmask_edge = wmask.std.Prewitt().std.Binarize()
    wmask = core.std.Expr([wmask, wmask_edge], "x y -")  # preserve edges for sharpness
    wmask = core.std.MaskedMerge(wmask.std.BlankClip(), wmask, BoundingBox((345, 52), (1228, 309)).get_mask(wmask))
    merge = core.std.MaskedMerge(clip, clip.std.BoxBlur(), wmask)
    return replace_ranges(clip, merge, ranges)


def filter_basic() -> vs.VideoNode:
    wakas, ref = SOURCE.dhs_source()
    waka = wakas[0]
    waka, wakas = waka_replace(waka, wakas[1:], WAKA_REPLACE)
    src = bounded_dehardsub(waka, ref, SIGNS_RU, wakas)
    src.set_output(1)
    return src


def filter() -> vs.VideoNode:
    src = filter_basic()
    den = denoise(src)
    rescale = fsrcnnx_rescale(den, NOSCALE)
    edgefix = letterbox_edgefix(rescale, crops=LETTERBOX, fades=LETTERBOX_FADES)
    deb = deband(edgefix)
    aa = antialias(deb, stronger=AA_STRONGER, noaa=AA_NONE)
    refix = letterbox_refix(aa, deb, LETTERBOX)
    fuck = stupid_bullshit(refix, WMASK_BLUR)
    rfixh = letterbox_shift_hor(fuck, LETTERBOX_HOR_SHIFT)
    rfixv = letterbox_shift_vert_gray(rfixh, LETTERBOX_BW_VER_SHIFT)
    grain = regrain(rfixv)
    final = finalize(grain)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, filter_basic, chapters=CHAPTERS)
else:
    filter()
