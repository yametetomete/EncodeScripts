import vapoursynth as vs

from typing import Any, Dict


def nnedi3_double(clip: vs.VideoNode) -> vs.VideoNode:
    nnargs: Dict[str, Any] = dict(field=0, dh=True, nsize=4, nns=4, qual=2, pscrn=2)
    nn = clip.std.Transpose() \
        .nnedi3.nnedi3(**nnargs) \
        .std.Transpose() \
        .nnedi3.nnedi3(**nnargs)
    return nn.resize.Bicubic(src_top=0.5, src_left=0.5)
