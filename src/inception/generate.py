"""
Public api for generating completely automated arbitrary composites
"""

import sys
from .image import Image
from .image.place import randomplace
from .image.analyze import validate_as_foreground
from .base import magic_insert

def generate_magic_composite(foreground_resource, background_resource):
    """
    Attempts to insert the given foreground image represented by a url or path into the given background resource

    :Parameters:
        foreground_resource : `object`
            The image resource of the object to insert into the scene.  Accepts valid fileobj or path
        background_resource : `object`
            The image resource of the scene to insert into. Accepts valid fileobj or path

    :Returns:
        The composited final image in an RGB multidim array if the foreground_resource was feasible (e.g. it is a valid image) or None otherwise

    :Rtype:
        `numpy.ndarray` or `Nonetype`

    :Raises `ValueError`:
        If either of the given resources could not be loaded.
    """
    try:
        foreground = Image.from_any(foreground_resource)
    except Exception:
        exc_class, exc, tb = sys.exc_info()
        new_exc = ValueError("Failed to load foreground resource %s" % foreground_resource)
        raise new_exc.__class__, new_exc, tb
    try:
        background = Image.from_any(background_resource)
    except Exception:
        exc_class, exc, tb = sys.exc_info()
        new_exc = ValueError("Failed to load foreground resource %s" % background_resource)
        raise new_exc.__class__, new_exc, tb
    
    if not validate_as_foreground(foreground):
        return None
    
    boundingbox = randomplace(foreground, background)
    return magic_insert(foreground, background, boundingbox)
    

    
    
    