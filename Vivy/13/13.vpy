import vapoursynth as vs

from vivy_common import (VivyConfig, VivySource, antialias, deband, denoise,
                         finalize, fsrcnnx_rescale, letterbox_edgefix, letterbox_refix, regrain)

from yt_common.automation import SelfRunner
from yt_common.deband import gray_mask
from yt_common.chapters import Chapter
from yt_common.source import waka_replace

from lvsfunc.mask import BoundingBox
from lvsfunc.types import Range
from lvsfunc.util import replace_ranges
from lvsfunc.dehardsub import HardsubLine, HardsubSignFade, HardsubMask, bounded_dehardsub

from awsmfunc import bbmod
from vsutil import scale_value
from vsutil import Range as CRange

import lvsfunc as lvf
from debandshit import f3kbilateral
from vsutil import iterate

from typing import List, Optional

import os

core = vs.core


EPNUM: int = int(os.path.basename(os.path.splitext(__file__)[0]))
CONFIG: VivyConfig = VivyConfig(EPNUM)
SOURCE: VivySource = VivySource(CONFIG)

CHAPTERS: List[Chapter] = [
    Chapter("Intro", 0),
    Chapter("OP", 1990),
    Chapter("Part A", 4149),
    Chapter("Part B", 16378),
    Chapter("Credits", 30657),
    Chapter("Outro", 32390),
]

WAKA_REPLACE: List[List[Range]] = [
    [(30657, 31496)],
    [],
]
SIGNS_RU: List[HardsubMask] = [
    HardsubLine([
        (1996, 4110),
        (21898, 24539),
        (24975, 28802),
    ], ((283, 844), (1349, 204))),
    HardsubLine([
        (1529, 1570),
    ]),
    HardsubSignFade([
        (1906, 1989),
        (22928, 22951),
    ]),
]

CREDITS: List[Range] = [
    (30657, 32377),
]

NOSCALE: List[Range] = [
]
NOSCALE += CREDITS
AA_NONE: List[Range] = [
]
AA_NONE += CREDITS
AA_STRONGER: List[Range] = [
]
LETTERBOX: List[Range] = [
    (33393, 33545),
]
LETTERBOX_FADES: List[Range] = [
]
DUMBSHIT_DEBAND: List[Range] = [
    (29745, 29870),
]


def credits_ef(clip: vs.VideoNode, ranges: Optional[List[Range]] = None) -> vs.VideoNode:
    assert clip.format is not None
    black = scale_value(0, 8, clip.format.bits_per_sample, scale_offsets=True,
                        range_in=CRange.FULL, range=CRange.LIMITED)
    y = clip.std.ShufflePlanes(0, vs.GRAY)
    y_crop = y.std.Crop(left=1050, top=55, right=98, bottom=55)
    y_bb = bbmod(y_crop, top=2, bottom=2, left=3, right=2)
    y_aa = antialias(y_bb)
    y_border = y_aa.std.AddBorders(left=1050, top=55, right=98, bottom=55, color=black)
    y_mask = BoundingBox((1049, 54), (774, 972)).get_mask(y_border)
    y_fix = core.std.MaskedMerge(y, y_border, y_mask)
    fixed = core.std.ShufflePlanes([y_fix, clip], [0, 1, 2], vs.YUV)
    return replace_ranges(clip, fixed, ranges)


def colored_deband(clip: vs.VideoNode, deb_ref: vs.VideoNode, ranges: Optional[List[Range]] = None
                   ) -> vs.VideoNode:
    deband_strong = iterate(clip.std.ShufflePlanes(0, vs.GRAY),
                            lambda c: f3kbilateral(c, range=12, y=80), 2)  # type: ignore
    deband_strong_u = iterate(clip.std.ShufflePlanes(1, vs.GRAY),
                              lambda c: f3kbilateral(c, range=12, y=40), 2)  # type: ignore
    deband_strong_v = iterate(clip.std.ShufflePlanes(2, vs.GRAY),
                              lambda c: f3kbilateral(c, range=12, y=40), 2)  # type: ignore
    db_yeet = core.std.ShufflePlanes([deband_strong, deband_strong_u, deband_strong_v], [0, 0, 0], vs.YUV)
    db_yeet = core.std.MaskedMerge(db_yeet, clip, lvf.mask.detail_mask(clip))
    cmask = gray_mask(db_yeet, y=(0.165, 0.3))
    db_cmask = core.std.MaskedMerge(deb_ref, db_yeet, cmask)
    return replace_ranges(deb_ref, db_cmask, ranges)


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
    deb = colored_deband(edgefix, deb, DUMBSHIT_DEBAND)
    aa = antialias(deb, stronger=AA_STRONGER, noaa=AA_NONE)
    refix = letterbox_refix(aa, deb, LETTERBOX)
    cfix = credits_ef(refix, CREDITS)
    grain = regrain(cfix)
    final = finalize(grain)
    final.set_output(0)
    return final


if __name__ == "__main__":
    SelfRunner(CONFIG, SOURCE, filter, filter_basic, chapters=CHAPTERS)
else:
    filter()
