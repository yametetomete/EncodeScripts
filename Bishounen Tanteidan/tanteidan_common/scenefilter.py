import vapoursynth as vs

import vsutil

from typing import Any, List, Optional, Tuple

from lvsfunc.mask import DeferredMask
from lvsfunc.misc import replace_ranges, scale_thresh
from lvsfunc.types import Range


core = vs.core


class SelfDehardsub(DeferredMask):
    """
    oh god why
    basically use a reference frame to mask OP credits when they're on a static bg
    """
    thresh: float
    expand: int
    inflate: int
    prebrz: Optional[float]

    def __init__(self, *args: Any, thresh: float = 0.01, expand: int = 2,
                 inflate: int = 3, prebrz: Optional[float] = None, **kwargs: Any) -> None:
        self.thresh = thresh
        self.expand = expand
        self.inflate = inflate
        self.prebrz = prebrz
        super().__init__(*args, **kwargs)

    def get_mask(self, clip: vs.VideoNode, ref: vs.VideoNode) -> vs.VideoNode:
        """
        Get the bounded mask.
        :param clip:  Source
        :param ref:   Reference clip
        :return:      Bounded mask
        """
        if self.bound:
            bm = self.bound.get_mask(ref)
            bm = bm if not self.blur else bm.std.BoxBlur(hradius=5, vradius=5, hpasses=5, vpasses=5)

        if self.prebrz:
            clip = vsutil.get_y(clip).std.Binarize(scale_thresh(self.prebrz, clip)).std.Invert()
            ref = vsutil.get_y(ref).std.Binarize(scale_thresh(self.prebrz, ref)).std.Invert()

        if ref.format is None or clip.format is None:
            raise ValueError("SelfDehardsub: 'Variable-format clips not supported'")

        if len(self.refframes) == 0:
            hm = vsutil.depth(self._mask(clip, ref), clip.format.bits_per_sample,
                              range=vsutil.Range.FULL, range_in=vsutil.Range.FULL)
        else:
            hm = core.std.BlankClip(ref, format=ref.format.replace(color_family=vs.GRAY,
                                                                   subsampling_h=0, subsampling_w=0).id)
            for range, rf in zip(self.ranges, self.refframes):
                mask = vsutil.depth(self._mask(clip, ref[rf]), clip.format.bits_per_sample,
                                    range=vsutil.Range.FULL, range_in=vsutil.Range.FULL)
                hm = replace_ranges(hm, core.std.Expr([hm, mask*len(hm)], expr="x y max"), range)

        return hm if self.bound is None else core.std.MaskedMerge(core.std.BlankClip(hm), hm, bm)

    def _mask(self, clip: vs.VideoNode, ref: vs.VideoNode) -> vs.VideoNode:
        assert clip.format is not None
        hsmf = core.std.Expr([clip, ref], 'x y - abs') \
            .resize.Point(format=clip.format.replace(subsampling_w=0, subsampling_h=0).id)
        if clip.format.num_planes > 1:
            hsmf = core.std.Expr(vsutil.split(hsmf), "x y z max max")
        hsmf = vsutil.iterate(vsutil.iterate(hsmf.std.Binarize(scale_thresh(self.thresh, clip))
                                             .std.Minimum(),
                                             core.std.Maximum, self.expand),
                              core.std.Inflate, self.inflate)
        return hsmf


def get_op_scenefilters(start: Optional[int]) -> Tuple[List[Range], List[DeferredMask]]:
    if start is None:
        return [], []
    return [
        (start+319, start+320),
        (start+327, start+328),
        (start+334, start+335),
        (start+1019, start+1021),
        (start+1029, start+1031),
        (start+1039, start+1041),
        (start+1067, start+1372),
        (start+1481, start+1689),
    ], [
        SelfDehardsub((start+1170, start+1274), ((217, 441), (597, 198)), refframes=1274),
        SelfDehardsub((start+1275, start+1369), ((1069, 337), (593, 361)), refframes=1371),
        SelfDehardsub((start+1481, start+1581), ((247, 294), (647, 467)), refframes=1582),
        SelfDehardsub((start+1584, start+1688), ((352, 443), (277, 190)), refframes=1689),
    ]
