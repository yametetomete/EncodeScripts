#!/usr/bin/env python3

import acsuite
import os
import vapoursynth as vs

core = vs.core

ac = acsuite.AC()
path = r"../bdmv/KIXA_90891/BDMV/STREAM/00006.m2ts"
src = core.lsmas.LWLibavSource(path)
ac.eztrim(src, [(0, -24)], os.path.splitext(path)[0] + ".wav", "ep8pv.wav")
