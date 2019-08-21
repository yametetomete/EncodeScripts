import vapoursynth as vs
import adjust
core = vs.core

#adaptive grain modified to use kage's rust version of the masking.
#https://git.kageru.moe/kageru/adaptivegrain/src/branch/master
#cheap_mask approximates the result of the polynomial mask by inverting the luma and adjusting brightness/contrast.
#this is about 2-3x faster but is probably not worth it unless your script is for some reason bottlenecked by this.
#cheap_mask is based of using the default luma_scaling of 12
def adaptive_grain(clip: vs.VideoNode, strength=0.25, static=True, luma_scaling=12, show_mask=False, cheap_mask=False):
	y = core.std.ShufflePlanes(clip, 0, vs.GRAY)
	grained = core.grain.Add(clip, var=strength, constant=static)
	mask = y
	if cheap_mask:
		mask = core.std.Invert(y)
		if clip.format.bits_per_sample == 32:
			#adjust with float expects 3 planes
			mask = core.std.ShufflePlanes(mask, [0], vs.YUV)
			mask = adjust.Tweak(mask, cont=1.7, bright=-0.351)
			mask = core.std.ShufflePlanes(mask, 0, vs.GRAY)
		elif clip.format.bits_per_sample == 16:
			mask = adjust.Tweak(mask, cont=1.7, bright=-23000)
		else:
			mask = adjust.Tweak(mask, cont=1.7, bright=-98)
	else:
		luma = y.std.PlaneStats()
		mask = core.adg.Mask(luma, luma_scaling)
		
	if show_mask:
		return mask
		
	return core.std.MaskedMerge(clip, grained, mask)