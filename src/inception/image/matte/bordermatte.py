"""
"Border" matting implementation
"""

import numpy
import scipy.ndimage
from ..analyze import detect_bg

def alphamatte(image, tol_low=.03, tol_high=.25):
    """
    Mattes the given image by isolating a border of unsure pixels based on difference from
    background color and applying operacity based on coverage along the border.  An erosion
    is performed to further improve quality of the alpha channel
    
    :Parameters:
        image : `numpy.array`
            The image to matte
        tol_low : `float`
            A lower tolerance of image difference with background below which pixel is 
            assumed to be part of the background.
        tol_high : `float`
            An upper tolerance on the image difference above which pixels are assumed to be part
            of the foreground
            
    :Returns:
        The resulting alpha channel
    
    :Rtype:
        `numpy.array`
    """
    erode_size = min(image.shape[:2]) / 100
    bg_color = detect_bg(image)
    matte = numpy.zeros(image.shape[:-1], dtype=image.dtype)
    color_diff = abs(image - bg_color)
    
    # isolate the border
    inmask = (numpy.any(color_diff > tol_low, axis=2))
    matte[inmask] = 1
    inside = scipy.ndimage.grey_erosion(matte, size=(erode_size,erode_size))
    border = matte - inside
    bordermask = ((1 - border) < 0.0001)

    matte[bordermask] = (1.5*(color_diff.sum(axis=2) / 3)).clip(0,1)[bordermask]
    matte[bordermask & (numpy.any(color_diff > tol_high, axis=2))] = 1

    matte = scipy.ndimage.grey_erosion(matte, size=(erode_size/2,erode_size/2))    
    return matte
