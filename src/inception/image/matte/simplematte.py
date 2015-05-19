"""
A dead simple baseline matting algorithm
"""
import numpy
import scipy.ndimage
from ..analyze import detect_bg

def alphamatte(image, tol=.2):
    """
    Performs simple matting on the given image
    
    :Parameters:
        image : `numpy.array`
            The image to matte
        tol : `float`
            Tolerance such that any pixels whose difference from the background color exceeds
            this in any channel is considered definite foreground
    """
    
    bg_color = detect_bg(image)
    color_diff = abs(image - bg_color)
    matte = color_diff.sum(axis=2) / 3
    matte[numpy.any(color_diff > tol, axis=2)] = 1
    return matte

