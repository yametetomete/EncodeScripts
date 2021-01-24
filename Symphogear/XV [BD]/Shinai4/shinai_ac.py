#!/usr/bin/env python3

import acsuite
import os
import vapoursynth as vs

core = vs.core

ac = acsuite.AC()
path = "../bdmv/KIXA_90893/BDMV/Stream/00007.m2ts"
src = core.lsmas.LWLibavSource(path)
ac.eztrim(src, [(24, -24)], os.path.splitext(path)[0] + ".wav", "shinai.wav")
