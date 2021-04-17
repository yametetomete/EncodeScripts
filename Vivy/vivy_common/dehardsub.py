import vapoursynth as vs
import kagefunc as kgf
import lvsfunc as lvf

from typing import List, NamedTuple, Optional, Tuple, Union

from .util import Range

core = vs.core


class Position(NamedTuple):
    x: int
    y: int


class Size(NamedTuple):
    x: int
    y: int


class BoundingBox():
    pos: Position
    size: Size

    def __init__(self, pos: Position, size: Size):
        self.pos = pos
        self.size = size


class HardsubSign():
    range: Range
    bound: Optional[BoundingBox]
    refframe: Optional[int]
    highpass: int
    expand: int

    def __init__(self,
                 range: Range,
                 bound: Union[BoundingBox, Tuple[Tuple[int, int], Tuple[int, int]], None],
                 refframe: Optional[int] = None, highpass: int = 5000, expand: int = 8):
        self.range = range
        self.refframe = refframe
        self.highpass = highpass
        self.expand = expand
        if bound is None:
            self.bound = None
        elif isinstance(bound, BoundingBox):
            self.bound = bound
        else:
            self.bound = BoundingBox(Position(bound[0][0], bound[0][1]), Size(bound[1][0], bound[1][1]))

    def _hardsub_mask(self, hrdsb: vs.VideoNode, ref: vs.VideoNode) -> vs.VideoNode:
        if self.refframe is not None:
            mask = kgf.hardsubmask_fades(hrdsb[self.refframe], ref[self.refframe],
                                         highpass=self.highpass, expand_n=self.expand)
        else:
            mask = kgf.hardsubmask_fades(hrdsb, ref, highpass=self.highpass, expand_n=self.expand)

        assert isinstance(mask, vs.VideoNode)
        return mask

    def _bound_mask(self, ref: vs.VideoNode) -> vs.VideoNode:
        if self.bound is not None:
            mask = kgf.squaremask(ref, self.bound.size.x, self.bound.size.y,
                                  self.bound.pos.x, self.bound.pos.y)
        else:
            mask = kgf.squaremask(ref, ref.width, ref.height, 0, 0)

        assert isinstance(mask, vs.VideoNode)
        return mask

    def get_mask(self, hrdsb: vs.VideoNode, ref: vs.VideoNode) -> vs.VideoNode:
        bm = self._bound_mask(ref)
        hm = self._hardsub_mask(hrdsb, ref)
        return core.std.MaskedMerge(core.std.BlankClip(hm), hm, bm)


def get_all_masks(hrdsb: vs.VideoNode, ref: vs.VideoNode, signs: List[HardsubSign]) -> vs.VideoNode:
    """
    Scenefiltering helper, not used in encode
    """
    assert ref.format is not None
    mask = core.std.BlankClip(ref, format=ref.format.replace(color_family=vs.GRAY, subsampling_w=0, subsampling_h=0).id)
    for sign in signs:
        mask = lvf.misc.replace_ranges(mask, core.std.Expr([mask, sign.get_mask(hrdsb, ref)], 'x y +'), [sign.range])
    return mask


def bounded_dehardsub(hrdsb: vs.VideoNode, ref: vs.VideoNode, signs: List[HardsubSign]) -> vs.VideoNode:
    bound = hrdsb
    for sign in signs:
        bound = lvf.misc.replace_ranges(bound,
                                        core.std.MaskedMerge(bound, ref, sign.get_mask(hrdsb, ref)),
                                        [sign.range])

    return bound
