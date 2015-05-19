"""
Contains low-level convenience functions for analyzing images without actually changing any
data in the image
"""

import numpy
from .scene import estimate_scene_description

def validate_as_foreground(image):
    """
    Automatically detects whether the image is a valid foreground element, ready to insert
    
    :Parameters:
        image : `Image` or `numpy.array`
            The image to validate
    
    :Returns:
        True if the image is a valid foreground, False otherwise
    """
    # currently, just hack this by doing a floodfill inward and then check if the entire border
    # is transparent
    threshold = .01
    if image.shape < 2 or image.shape[0] < 2 or image.shape[1] < 2:
        return False
    
    # get the background color
    background_color = detect_bg(image)
    chans = len(background_color)
    # TODO: support other colors than white
    # for now, just short-circuit if the detected color is not white
    if tuple([1.0])*chans != background_color:
        return False
    
    # next, perform a floodfill
    ## Edit: for now, just check whether all border rows/columns are within a small threshold of the 
    # background color
    for slice in (image[0,...], image[-1,...], image[:,0,...], image[:,-1,...]):
        if len(slice.shape) > 1:
            slice = slice.sum(axis=1) / 3
            bg = numpy.array(background_color).sum() / 3
        else:
            bg = background_color
            
        if not numpy.all(abs(slice - bg) < threshold):
            return False
        
    return True

def detect_bg(image):
    """
    Helper function to automatically "detect" e.g. guess at the background color of a (usually opaque) image
    
    :Parameters:
        image : `Image` or `numpy.ndarray`
            The image whose background color we wish to detect
            
    :Returns:
        The background color of the image
        
    :Rtype:
        `tuple`
    """
    # HACK:
    # for now, simply scan the border of the image and use the most common pixel value
    rows, cols = image.shape[:2]
    if len(image.shape) > 2:
        chans = image.shape[2]
    else:
        image = image.reshape(rows,cols,1)
        chans = 1
    
    # top and left:
    border_pixels = numpy.concatenate((image[:1,:,:].reshape(cols, chans), image[:,:1,:].reshape(rows,chans)))
    if rows > 1:
        border_pixels = numpy.concatenate((border_pixels, image[-1:,:,:].reshape(cols,chans)))
    if cols > 1:
        border_pixels = numpy.concatenate((border_pixels, image[:,-1:,:].reshape(rows,chans)))
    
    # grab the most common pixel value
    counter = {}
    indices = {}
    for pixel in border_pixels:
        # ignore mostly transparent pixels
        if len(pixel) < 4 or pixel[3] > .1: 
            val = tuple((255 * pixel).astype('uint8'))
            counter[val] = counter.get(val, 0) + 1
    
    if counter:
        mode = tuple(float(a)/255 for a in max(counter.keys(), key=lambda x: counter[x]))
        return mode
    
    return tuple([1.0])*chans # default to whites




        
    
        
        
    
