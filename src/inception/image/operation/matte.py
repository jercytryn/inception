"""
Module for basic matting operations
"""

from ..image import Image
from .base import Operation
#from ..matte.simplematte import alphamatte as alphamatte_simple
from ..matte.bordermatte import alphamatte as alphamatte_simple
from ..matte.closedformmatte import alphamatte as alphamatte_closed

class SimpleMatteOperation(Operation):
    """
    A simple "border matting" operation
    """
    def __init__(self, image, **kwargs):
        """
        Initializes a border matte operation
        
        :Parameters:
            image : `Image`
                The image to matte
            tol_low : `float`
                A lower tolerance of image difference with background below which pixel is 
                assumed to be part of the background.
            tol_high : `float`
                An upper tolerance on the image difference above which pixels are assumed to be part
                of the foreground
        """
        self.image = image
        self.kwargs = kwargs
        self.opimage = None
        
    def run(self):
        """
        Runs the operation
        
        :Returns:
            A copy of the input image, whose alpha channel is populated based on the matting
            
        :Rtype:
            `Image`
        """
        self.image.to_rgba()
        result = Image.from_any(alphamatte_simple(self.image.data, **self.kwargs))
        self.opimage = self.image.clone()
        self.opimage.to_rgba()
        self.opimage[..., 3] = result
        return self.opimage 
    
class ClosedFormMatteOperation(Operation):
    """
    Performs a closed-form matting on the given image, based on 
    A. Levin D. Lischinski and Y. Weiss. A Closed Form Solution to Natural Image Matting.
    Conference on Computer Vision and Pattern Recognition (CVPR), June 2007.
    """
    def __init__(self, image, **kwargs):
        self.image = image
        self.kwargs = kwargs
        self.opimage = None
        
    def run(self):
        """
        Runs the operation
        
        :Returns:
            A copy of the input image, whose alpha channel is populated based on the matting
            
        :Rtype:
            `Image`
        """
        result = Image.from_any(alphamatte_closed(self.image.data, **self.kwargs))
        self.opimage = self.image.clone()
        self.opimage.to_rgba()
        self.opimage[..., 3] = result
        return self.opimage 