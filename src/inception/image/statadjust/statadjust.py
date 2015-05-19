import math
import numpy
import scipy.ndimage
from .colorspace import linear_to_srgb, srgb_to_linear
from .colorspace import cct_to_xy, xyY_to_cct
from .colorspace import xyY_to_rgb, rgb_to_xyY
from .colorspace import rgb_to_hsv, hsv_to_rgb

## PARAMETERS
# hack to prevent very few sample points mucking things up
_hist_threshold = 5
_near_zero = .0000000001
_bg_scale = 2.0 # the scale of background to consider relative to foreground
# see also bottom for statistic-specific configuration

## CONSTANTS
top_ratio = 1/1024.0
bottom_ratio = 1-top_ratio
highlight_ratio = 1/128.0
undershadow_thres = .013
overhighlight_thres = .8714

# TODO: can optimize this a lot by caching the various color spaces of a single image
def statadjust(foreground, background, offset=(0,0), intermediary_results=False):
    """
    Performs a statistics-based image adjustment to better match 
    color/lighting in foreground to background
    
    :Parameters:
        foreground : `numpy.array`
            The foreground image to match to the background
        background : `numpy.array`
            The background image to match to
        offset : `tuple`
            A tuple of (row, column) denoting the offset into the destination image where the upper-left
            corner of the source image will begin (once merged). Default=(0,0)
        intermediary_results : `bool`
            If True, return the image at each stage of adjustment (contrast, luminance, cct, saturation)
            Otherwise, just returns the final result after each adjustment applied in turn.
            Default=False
            
    :Returns:
        The resulting foreground copy adjusted to match background, if intermediary_results=False
        Otherwise, returns a list of foreground image copies, represented the result of each intermediary
        adjustment in the pipeline
        
    :Rtype:
        `numpy.array` or `list`
    """
    
    results = []
    
    foreground = foreground.copy()
    
    # only select background within area equal to bb of fg * 3
    # offset given as row, column
    # ignore the alpha matte, which may be much larger than the actual foreground
    if len(foreground.shape) > 2 and foreground.shape[2] > 3:
        foreground_nonzero = numpy.nonzero(foreground[...,3])
        row_min, col_min = foreground_nonzero[0].min(), foreground_nonzero[1].min()
        foreground_rows = foreground_nonzero[0].max() - row_min + 1
        foreground_cols = foreground_nonzero[1].max() - col_min + 1
        offset = (offset[0] + row_min, offset[1] + col_min)
    else:
        foreground_rows = foreground.shape[0]
        foreground_cols = foreground.shape[1]
    
    bgstart = [max(offset[0] - ((_bg_scale - 1)/2.0) * foreground_rows, 0),
               max(offset[1] - ((_bg_scale - 1)/2.0) * foreground_cols, 0)]
    bgend = [bgstart[0] + _bg_scale * foreground_rows,
             bgstart[1] + _bg_scale * foreground_cols]
    if bgend[0] > background.shape[0]:
        bgend[0] = background.shape[0]
        bgstart[0] = max(bgend[0] - _bg_scale * foreground_rows, 0)
    if bgend[1] > background.shape[1]:
        bgend[1] = background.shape[1]
        bgstart[1] = max(bgend[1] - _bg_scale * foreground_cols, 0)
        
    if len(background.shape) > 2:
        background = background[bgstart[0]:bgend[0], bgstart[1]:bgend[1], :3]
    else:
        background = background[bgstart[0]:bgend[0], bgstart[1]:bgend[1], :3]
    
    # morphologically erode alpha matte of foreground
    foregroundmonly = foreground
    foregroundalpha = None
    if len(foregroundmonly.shape) > 2 and foregroundmonly.shape[2] > 3:
        foregroundalpha = foreground[..., 3].copy()
        foregroundmonly[..., 3] = scipy.ndimage.grey_erosion(foregroundmonly[..., 3], size=(3,3))
    else:
        foregroundmonly = foreground.copy()
    
    # discard areas where alpha < .5
    if len(foregroundmonly.shape) > 2 and foreground.shape[2] > 3:
        foregroundmonly = foregroundmonly[foregroundmonly[...,3] > .5]
    
    foreground = foreground[...,:3]
    foregroundmonly = foregroundmonly[...,:3]
    
    # convert everything to linear space
    foregroundmonly = srgb_to_linear(foregroundmonly)
    foreground = srgb_to_linear(foreground)
    background = srgb_to_linear(background)
    
    # adjust local constrast
    foregroundmonly, foreground = match_contrast(foregroundmonly, foreground, background)
    if intermediary_results:
        results.append(linear_to_srgb(foreground))
        if foregroundalpha is not None:
            results[-1] = numpy.dstack((results[-1][:,:,0], results[-1][:,:,1], results[-1][:,:,2], foregroundalpha))
    
    # adjust luminance, CCT, and finally saturation to match
    for stat in ('luminance', 'cct', 'saturation'):
        foregroundmonly, foreground = match(stat, foregroundmonly, foreground, background, 
                                            filter_exposure=statfuncs[stat]['filter_exposure'])
        
        if intermediary_results:
            results.append(linear_to_srgb(foreground))
            if foregroundalpha is not None:
                results[-1] = numpy.dstack((results[-1][:,:,0], results[-1][:,:,1], results[-1][:,:,2], foregroundalpha))
        
    # convert back to sRGB
    if intermediary_results:
        return results
    
    foreground = linear_to_srgb(foreground)
    if foregroundalpha is not None:
        foreground = numpy.dstack((foreground[:,:,0], foreground[:,:,1], foreground[:,:,2], foregroundalpha))
    return foreground

def compute_stats(statname, image, filter_exposure=True):   
    """ 
    Computes low, medium, and high mean values for the given statistic.
    For statistics configured to allow an overhighlight metric, also computes 
    a fourth image statistic
    
    :Parameters:
        statname : `basestring`
            The name of the image statistic, (e.g. luminance, cct, saturation)
        image : `numpy.array`
            The image to compute statistics for
        filter_exposure : `bool`
            If True, only includes pixels that are not over or underexposed
            in computing the various metrics
            
    :Returns:
        A tuple of (low, medium, high) metric values for the image, or (low, medium, high, extra),
        if the statistic is configured to allow 'different_brightness'
    """
    measure = statfuncs[statname]['get'](image).flatten()
    
    # filter out over and underexposed for certain stats
    lum = None
    if filter_exposure:
        lum = getluminance(image).flatten()            
        measure = measure[(lum >= undershadow_thres) & (lum < overhighlight_thres)]
    if statfuncs[statname].get('low_threshold'):
        measure = measure[(measure > statfuncs[statname].get('low_threshold'))]
    if statfuncs[statname].get('high_threshold'):
        measure = measure[(measure < statfuncs[statname].get('high_threshold'))]

    if statfuncs[statname].get('lower_fill_threshold') and measure.size < statfuncs[statname]['lower_fill_threshold']:
        m = statfuncs[statname]['low_threshold'] * numpy.ones(statfuncs[statname].get('lower_fill_threshold'), dtype=measure.dtype)
        m[:measure.size] = measure
        measure = m

    # sort from high to low
    measure.sort()
    measure = measure[::-1]
    
    measure_high = measure[:math.floor(top_ratio*measure.size)]
    measure_low = measure[math.floor(bottom_ratio*measure.size):]
    
    # compute image statistics (low, medium, and high)
    measure_mean_high = measure_high.mean()
    measure_mean_low = measure_low.mean()
    measure_mean_medium = measure.mean()
    
    # if we don't have enough pixels above/below threshold, ignore the statistic
    if (measure_high.size <= _hist_threshold):
        measure_mean_high = None
    if (measure_low.size <= _hist_threshold):
        measure_mean_low = None    
    
    if statfuncs[statname]['different_brightness']:
        # in this case, we have a fourth order statistic to compare against
        if lum is None:
            lum = getluminance(image).flatten()
        # remove overexposed from lum
        lum = lum[(lum < overhighlight_thres)]
        lum.sort()
        lum[::-1]
        
        # bright threshold
        b = lum[math.floor(highlight_ratio*lum.size)]

        measure_extra = measure[(measure >= b) & (measure < overhighlight_thres)]
        if (measure_extra.size <= _hist_threshold):
            measure_mean_extra = None
        else:
            measure_mean_extra = measure_extra.mean()

        return (measure_mean_low, measure_mean_medium, measure_mean_high, measure_mean_extra)
    
    return (measure_mean_low, measure_mean_medium, measure_mean_high)

def _bezt(t, p0, p1, p2):
    """
    For reference, a quadratic bezier curve as a function of t.
    Works with a single scalar or an array of t values
    """
    t = numpy.repeat([t],2,axis=0).transpose()
    return (1 - t)**2 * p0 + 2*(1-t)*t*p1 + t**2 * p2  

def _bezx(x, p0, p1, p2):
    """
    A quadratic bezier giving y as a function of x.
    Special case of inside the unit square scaled appropriately.
    """
    # derived from http://www.flong.com/texts/code/shapers_bez/
    x = (x - p0[0])/(p2[0] - p0[0])
    a = (p1[0] - p0[0])/(p2[0] - p0[0])
    b = (p1[1] - p0[1])/(p2[1] - p0[1])

    # NOTE This singularity case only valid when control point always 
    # on the line from (0,1)->(1,0) on the unit square
    # this is always the case with the contrast bezier
    if abs(a-.5) < _near_zero:
        # account for the singularity when near straight line
        y = x
        
    else:
        t = numpy.sqrt(a**2 + (1-2*a)*x) - a
        t /= (1 - 2*a)
        y = (1 - 2*b) * t**2 + 2 * b * t
    return p0[1] + (p2[1] - p0[1])*y

def match_contrast(foregroundmonly, foreground, background):
    """
    Matches contrast between the measure-only foreground and background images
    and applies it to the foreground
    
    :Parameters:
        foregroundmonly : `numpy.array`
            The measure-only foreground image
        foreground : `numpy.array`
            The write-only foreground image
        background : `numpy.array`
            The background image to match local contrast to
            
    :Returns:
        A tuple of (newforegroundmonly, newforeground) representing the shifted
        measure-only foreground and foreground respectively
    """
    print("Matching contrast...")
    
    # compute the baseline contrast in the correct space
    resultfg = compute_stats('contrast', foregroundmonly, filter_exposure=False)
    resultbg = compute_stats('contrast', background, filter_exposure=False)
    
    lomeanbg, medmeanbg, himeanbg = resultbg
    lomeanfg, medmeanfg, himeanfg = resultfg
    
    origmean = himeanfg
    
    # get luminance for zone retrieval
    Yfg = getluminance(foregroundmonly).flatten()
    
    # convert to xyY to do luminance transformation
    foregroundmonly_xyY = rgb_to_xyY(foregroundmonly)
    meanlum = Yfg.mean()

    # curve points
    pm = numpy.array((meanlum, meanlum))
    p0 = numpy.array((0,0))
    p1 = numpy.array((1,1))
    p11 = numpy.array((meanlum, 1))
    p01 = numpy.array((meanlum, 0))
    p02 = numpy.array((0, meanlum))
    p12 = numpy.array((1, meanlum))
    
    # search space of curves between .4 >= alpha >= .6 for beset match
    bestmatch = float('inf')
    bestmean = float('inf')
    bestalpha = None
    
    maskLower = (foregroundmonly_xyY[...,2] <= meanlum)
    maskUpper = ~maskLower
    
    for alpha in numpy.arange(.4,.6,.02):
        # get control points
        pU = p11 + alpha * (p12 - p11)
        pL = p01 + alpha * (p02 - p01)
         
        transformedfg = numpy.zeros_like(foregroundmonly_xyY[...,2])
        transformedfg[maskLower] = _bezx(foregroundmonly_xyY[...,2][maskLower], p0, pL, pm)
        transformedfg[maskUpper] = _bezx(foregroundmonly_xyY[...,2][maskUpper], pm, pU, p1)
        
        # compute the contrast in the correct space
        contrastfg = getcontrast_from_lum(transformedfg).flatten()
        contrastfg = contrastfg[(contrastfg > statfuncs['contrast']['low_threshold'])]
        if contrastfg.size < statfuncs['contrast']['lower_fill_threshold']:
            m = statfuncs['contrast']['low_threshold'] * numpy.ones(statfuncs['contrast']['lower_fill_threshold'], dtype=contrastfg.dtype)
            m[:contrastfg.size] = contrastfg
            contrastfg = m
        
        contrastfg.sort()
        contrastfg = contrastfg[::-1]
        himeanfg = contrastfg[:math.floor(top_ratio*contrastfg.size)].mean()

        if himeanbg is None or himeanfg is None or numpy.isnan(himeanbg) or numpy.isnan(himeanfg):
            continue
        if abs(himeanbg - himeanfg) < abs(bestmatch):
            bestmatch = himeanbg - himeanfg
            bestalpha = alpha        
            bestmean = himeanfg
        
        # to visualize curve, can do:
        #import matplotlib.pyplot as plt     
        #x = numpy.arange(0, meanlum, .01)
        #plt.plot(x, _bezx(x, p0, pL, pm));
        #x = numpy.arange(meanlum, 1, .01)
        #plt.plot(x, _bezx(x, pm, pU, p1));
        #plt.show()   
        
        # OR
        #x = numpy.arange(0, 1, .01)
        #y1 = _bezt(x, p0, pL, pm)
        #y2 = _bezt(x, pm, pU, p1)
        #plt.plot(y1[...,0],y1[...,1])
        #plt.plot(y2[...,0],y2[...,1])
        #plt.show()
    if bestalpha is None:
        bestalpha = .5
        bestmean = 0
        bestmatch = 0
    
    # do the actual shift of the foreground
    if origmean is not None:
        print("Shifting high zone mean contrast by %s using alpha=%2.2f (best match of %s)" % (bestmean - origmean, bestalpha, bestmatch))
    else:
        print("Shifting high zone mean contrast with alpha=%2.2f" % (bestalpha))
    pU = p11 + bestalpha * (p12 - p11)
    pL = p01 + bestalpha * (p02 - p01)
    
    newforegroundmonly = foregroundmonly_xyY
    newforeground = rgb_to_xyY(foreground)
    
    maskLowerFgmonly = maskLower
    maskUpperFgmonly = maskUpper
    
    maskLowerFg = (newforeground[...,2] <= meanlum)
    maskUpperFg = ~maskLowerFg
    
    newforegroundmonly[...,2][maskLowerFgmonly] = _bezx(newforegroundmonly[...,2][maskLowerFgmonly], p0, pL, pm)
    newforegroundmonly[...,2][maskUpperFgmonly] = _bezx(newforegroundmonly[...,2][maskUpperFgmonly], pm, pU, p1)
    
    newforeground[...,2][maskLowerFg] = _bezx(newforeground[...,2][maskLowerFg], p0, pL, pm)
    newforeground[...,2][maskUpperFg] = _bezx(newforeground[...,2][maskUpperFg], pm, pU, p1)
    
    return (xyY_to_rgb(newforegroundmonly).clip(0,1), xyY_to_rgb(newforeground).clip(0,1))

def match(statname, foregroundmonly, foreground, background, filter_exposure=True): 
    """
    Match the given image statistic between the measure-only foreground and background images, and apply
    the result to the given foreground image.
    
    :Parameters:
        foregroundmonly : `numpy.array`
            The measure-only foreground image
        foreground : `numpy.array`
            The write-only foreground image
        background : `numpy.array`
            The background image to match local contrast to
        filter_exposure : `bool`
            If True, only includes pixels that are not over or underexposed
            in computing the various metrics
            
    :Returns:
        A tuple of (newforegroundmonly, newforeground) representing the shifted
        measure-only foreground and foreground respectively
    """
    print("Matching %s..." % statname)
    
    resultfg = compute_stats(statname, foregroundmonly, filter_exposure=filter_exposure)
    resultbg = compute_stats(statname, background, filter_exposure=filter_exposure)
    
    try:
        lomeanbg, medmeanbg, himeanbg = resultbg
        lomeanfg, medmeanfg, himeanfg = resultfg
        extrameanbg = None
        extrameanfg = None
    except ValueError:
        lomeanbg, medmeanbg, himeanbg, extrameanbg = resultbg
        lomeanfg, medmeanfg, himeanfg, extrameanfg = resultfg
    
    # conveservative: choose the zone such that the shift amount to match is minimized
    shiftlow = float('inf')
    shifthi = float('inf')
    shiftextra = float('inf')
    
    if lomeanbg is not None and lomeanfg is not None:
        shiftlow = lomeanbg - lomeanfg
    if himeanbg is not None and himeanfg is not None:
        shifthi = himeanbg - himeanfg
    if extrameanbg is not None and extrameanfg is not None:
        shiftextra = extrameanbg - extrameanfg

    shift = medmeanbg - medmeanfg

    print("L,M,H: %2.2f,%2.2f,%2.2f" % (shiftlow, shift, shifthi))
    
    # conservative-ish hack: sign of zone shift must match whole histogram shift direction
    if shiftlow * shift < 0:
        shiftlow = float('inf')
    if shifthi * shift < 0:
        shifthi = float('inf')
    if shiftextra * shift < 0:
        shifthi = float('inf')
    
    if abs(shiftlow) <= abs(shifthi) and abs(shiftlow) <= abs(shift) and abs(shiftlow) <= abs(shiftextra):
        # select low zone
        print("Selecting low zone")
        shift = shiftlow
    elif abs(shifthi) <= abs(shift) and abs(shifthi) <= abs(shiftlow) and abs(shifthi) <= abs(shiftextra):
        # select high zone
        print("Selecting high zone")
        shift = shifthi
    elif abs(shiftextra) <= abs(shift) and abs(shiftextra) <= abs(shiftlow) and abs(shiftextra) <= abs(shifthi):
        print("Selecting extra bright zone")
        shift = shiftextra
    else:
        # select medium zone
        print("Selecting medium zone")
    
    # dampen the shift amount by a fixed scale
    if statfuncs[statname]['scale'] < 1.0:
        print("Dampening shift by factor of %s" % statfuncs[statname]['scale'])
    shift *= statfuncs[statname]['scale']
    
    # last failsafe: clamp the shift
    if 'clamp_shift' in statfuncs[statname]:
        clamp = statfuncs[statname]['clamp_shift']
        shift = clamp[0] if shift < clamp[0] else (clamp[1] if shift > clamp[1] else shift)
    if 'clamp_abs' in statfuncs[statname]:
        clamp = statfuncs[statname]['clamp_abs']
        if medmeanfg + shift > clamp[1]:
            shift = clamp[1] - medmeanfg
        elif medmeanfg + shift < clamp[0]:
            shift = clamp[0] - medmeanfg
            
    # now that we have the zone set, perform the shift by the shift amount
    print("Shifting foreground %s by %s" % (statname, shift))
    foregroundmonly = statfuncs[statname]['set'](foregroundmonly, shift).clip(0,1)
    foreground = statfuncs[statname]['set'](foreground, shift).clip(0,1)
    return (foregroundmonly, foreground)

def hue_match(foreground, background):
    """
    Matches mean hue of the given foreground to the given background image
    
    :Parameters:
        foreground : `numpy.array`
            The foreground image
        background : `numpy.array`
            The background image
            
    :Returns:
        The foreground image with hue matched to background
    """
    foreground = srgb_to_linear(foreground)
    background = srgb_to_linear(background)
    
    fghue = gethue(foreground)
    bghue = gethue(background)
    fgmean = fghue.mean()
    bgmean = bghue.mean()
    
    foreground = rgb_to_hsv(foreground)
    foreground[..., 0] += (bgmean - fgmean)
    foreground[..., 0] = foreground[..., 0] % 1.0
    return linear_to_srgb(hsv_to_rgb(foreground))


# measurement getters
eps = 3.03e-4

def getluminance(image):
    #0.2989 * R + 0.5870 * G + 0.1140 * B 
    #return .2989 * image[...,0] + .5870 * image[...,1] + .1140 * image[...,2]
    return .2126 * image[...,0] + .7152 * image[...,1] + .0722 * image[...,2] # conversion to Y

def getlog2luminance(image):
    image = getluminance(image)
    image = eps + (image*(1-eps)) # renormalize to [eps, 1.0]
    return numpy.log2(image)

def setlog2luminance(image, shift):
    image = numpy.log2(eps + rgb_to_xyY(image)*(1-eps))
    image[..., 2] += shift
    return xyY_to_rgb(((2 ** image) - eps)/(1-eps)) 

def getsaturation(image):
    hsv = rgb_to_hsv(image)
    return hsv[..., 1]

def setsaturation(image, shift):
    image = rgb_to_hsv(image)
    image[..., 1] += shift
    return hsv_to_rgb(image.clip(0,1))

def getlog2saturation(image):
    image = getsaturation(image)
    image = eps + (image*(1-eps)) # renormalize to [eps, 1.0]
    return numpy.log2(image)

def setlog2saturation(image, shift):
    image = numpy.log2(eps + rgb_to_hsv(image)*(1-eps))
    image[..., 1] += shift
    return hsv_to_rgb(((2 ** image) - eps)/(1-eps))

def getcolortemp(image):
    return xyY_to_cct(rgb_to_xyY(image))[...,0]
    
def setcolortemp(image, shift):
    # convert into xyY space
    xyY = rgb_to_xyY(image)
    # next convert to a color temperature
    temp = xyY_to_cct(xyY)
    
    # shift the color temperature mired by the specified amount
    temp[..., 0] += shift
    
    # convert the color temperature back into xy chromaticity
    xynew = cct_to_xy(temp)
    xyY[...,0] = xynew[...,0]
    xyY[...,1] = xynew[...,1]
    
    # finally, back into rgb
    return xyY_to_rgb(xyY.clip(0,1))

def gethue(image):
    return rgb_to_hsv(image)[..., 0]

def sethue(image, shift):
    image = rgb_to_hsv(image)
    image[..., 0] += shift
    image[..., 0] = image[..., 0] % 1.0
    return hsv_to_rgb(image)

def getcontrast(image):
    luminance = getluminance(image)
    return getcontrast_from_lum(luminance)

def getcontrast_from_xyY(image):
    luminance = image[...,2]
    return getcontrast_from_lum(luminance)

def getcontrast_from_lum(luminance):
    sigma = 1.5
    avgluminance = scipy.ndimage.filters.gaussian_filter(luminance, sigma, truncate=3.0) 
    mask = (avgluminance != 0)
    contrast = numpy.zeros_like(luminance)
    contrast[mask] = luminance[mask] / avgluminance[mask]
    return contrast

##### Statistis-specific configuration ########
statfuncs = {'luminance': {'get':getlog2luminance,
                           'set':setlog2luminance,
                           'filter_exposure':False,
                           'different_brightness':False,
                           'clamp_abs':[-11.686,0],
                           'scale':.8},
             'saturation':{'get':getlog2saturation,
                           'set':setlog2saturation,
                           'filter_exposure':True,
                           'different_brightness':False,
                           'clamp_abs':[-11.686,0],
                           'scale':.75},
             'cct':{'get':getcolortemp,
                    'set':setcolortemp,
                    'filter_exposure':True,
                    'different_brightness':True,
                    'clamp_abs':[1.0e6/20000, 1.0e6/1500],
                    'scale':.8},
             'contrast':{'get':getcontrast,
                         'set':None, # contrast is curve adjusted
                         'filter_exposure':False,
                         'different_brightness':False,
                         'low_threshold':.1,
                         'lower_fill_threshold':100,
                         'scale':1.0}}



    