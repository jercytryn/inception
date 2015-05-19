"""
Module for Poisson Blending operations
"""

import numpy
import cv2
from .base import Operation
from ..image import Image

class PoissonOperation(Operation):
    """
    Implements a poisson image blending operation, a la
    Perez, Patrick, Michel Gangnet, and Andrew Blake. "Poisson image editing." ACM Transactions on Graphics (TOG). Vol. 22. No. 3. ACM, 2003.
    APA
    """
    def __init__(self, source_image, dest_image, offset=(0, 0), clone_type=cv2.NORMAL_CLONE):
        """
        Initializes a poisson blending operation
        
        :Parameters:
            source_image : `Image`
                The image to composite
            dest_image : `Image`
                The image to blend source into
            offset : `tuple`
                A tuple of (row, column) denoting the offset into the destination image where the upper-left
                corner of the source image should begin. Default=(0,0)
            clone_type : `int`
                A flag determining the type of blending to do.  Support normal clone (cv2.NORMAL_CLONE), mixed 
                clone for mixing gradients (cv2.MIXED_CLONE) and feature exchange (cv2.FEATURE_EXCHANGE).
                See http://docs.opencv.org/3.0-beta/modules/photo/doc/cloning.html for more details.
        """
        self.source_image = self.image = source_image
        self.dest_image = dest_image
        self.offset = offset
        self.clone_type = clone_type
        self.opimage = None
        
    def run(self):
        """
        Runs the operation
        
        :Returns:
            A single image with foreground and background blended together seamlessly
            
        :Rtype:
            `Image`
        """
        # TODO: add support for merging off the edge of the image
        rows, cols = self.image.shape[:2]
        self.image.to_rgba()

        # float->int and swaps channels
        opencv_source = self.source_image.opencvimage 
        opencv_dest = self.dest_image.opencvimage
        # construct a mask with 0 corresponding to alpha of 0 in the source
        self.mask_image = (self.source_image[...,3] * 255).astype('uint8')

        offset = (self.offset[1] + cols / 2, self.offset[0] + rows / 2)
        opencv_result = cv2.seamlessClone(opencv_source, opencv_dest, 
                                          self.mask_image, offset, self.clone_type)
        self.opimage = Image(opencv_result[:, :, ::-1]) # swap channels back to rgb
        return self.opimage
    
    