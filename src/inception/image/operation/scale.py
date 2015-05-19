"""
Scale operation module
"""

import scipy.misc
from .base import Operation
from ..image import Image

class ScaleOperation(Operation):
    """
    A simple operation for scaling the given image
    """
    def __init__(self, image, target_width, target_height=None, maintain_ratio=False, interp='bilinear'):
        """
        Initializes the scale operation
        
        :Parameters:
            image : `Image`
                The image to scale
            target_width : `int`
                The desired width in pixels after scaling
            target_height : `int`
                If given, the desired height in pixels after scaling
                Ignored if maintain_ratio=True. Default=None
            maintain_ratio : `bool`
                If True, maintains the aspect ratio of the original image.
                Otherwise, respects target width and target height. Default=False
            interp : `basestring`
                The type of sampling to perform when scaling. Default='bilinear'
                See http://docs.scipy.org/doc/scipy-0.15.1/reference/generated/scipy.misc.imresize.html
                for more details
        """
        self.image = image
        self.target_width = target_width
        self.target_height = target_height
        self.maintain_ratio = maintain_ratio
        self.interp = interp
        self.opimage = None
        
    def run(self):
        """
        Runs the operation
        
        :Returns:
            A scaled copy of the input image
            
        :Rtype:
            `Image`
        """
        rows, cols = self.image.shape[:2]
        if not self.target_height or self.maintain_ratio:
            size = self.target_width / float(cols)
        else:
            size = (self.target_height, self.target_width)
        self.opimage = Image(scipy.misc.imresize(self.image.data, size, self.interp))
        return self.opimage