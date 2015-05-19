"""
Base placement module
"""

import numpy

def normalize_shape(image, offset, width, height, dtype=None, expand=False):
    """
    Normalizes the shape of the given image to the given dimensions, placing its upper right corner
    at the upper right corner of a black image but offset by the given offset.
    
    :Parameters:
        image : `numpy.array`
            The image to normalize
        offset : `tuple`
            A tuple of (row, column) denoting the offset into the black image where the upper-left
            corner of the source image should begin. Default=(0,0)
        width : `int`
            The width to normalize to in pixels
        height : `int`
            The height to normalize to in pixels
        dtype : `basestring`
            The datatype of the resulting image
        expand : `bool`
            If True, rather than conform the image inside the (height, width) array, the array is expanded
            such that the image is not cropped, even when it exceeds the boundary of the given width/height.
            Otherwise, the image is cropped outside the width/height. Default=False
    """
    if dtype is None:
        dtype = image.dtype
    # blow up op image to match max width and height
    before_rows = max(offset[0], 0)
    before_cols = max(offset[1], 0)
    chans = image.shape[2]
    
    # insert the image into a new normalized (black) image
    r0, c0 = abs(min(offset[0], 0)), abs(min(offset[1], 0)) # how much to offset into the image itself
    r1, c1 = min(image.shape[0], height-before_rows), min(image.shape[1], width-before_cols) 
    
    if expand:
        # covers all cases regardless of the offset and size of image relative to the situated width/height
        height = max(image.shape[0] + before_rows, height + r0)
        width = max(image.shape[1] + before_cols, width + c0)
        
        r0, c0 = 0, 0
        r1, c1 = image.shape[0], image.shape[1]
    
    new_image = numpy.zeros((height, width, chans), dtype=dtype)
    
    new_image[before_rows:before_rows+(r1-r0), before_cols:before_cols+(c1-c0), :] = image[r0:r1, c0:c1, :]
    return new_image    