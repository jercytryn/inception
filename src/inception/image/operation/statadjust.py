"""
Statistics-based image adjustment operations
"""

from ..image import Image
from ..statadjust import adjust 
from .base import Operation

class StatAdjustOperation(Operation):
    """
    Performs a statistical image match of the foreground to the background,
    using an adapted version of "Understanding and Improving the Realism of 
    Image Composites" (Xue et al. 2012)
    """
    def __init__(self, foreground, background, offset=(0,0)):
        """
        Initializes the statistical adjustment operation.  
        
        :Parameters:
            foreground : `Image`
                The foreground image to adjust to match the lighting quality of the background image
            background : `Image`
                The background image to match to
            offset : `tuple`
                A tuple of (row, column) denoting the offset into the destination image where the upper-left
                corner of the source image will begin (once merged). Default=(0,0)
        """
        self.image = foreground
        self.background = background
        self.offset = offset
        self.opimage = None
        
    def run(self):
        """
        Runs the operation
        
        :Returns:
            A copy of the foreground image after statistical image adjustments have been applied
            
        :Rtype:
            `Image`
        """
        self.opimage = Image(adjust(self.image, self.background, self.offset))
        return self.opimage