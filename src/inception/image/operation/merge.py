"""
Merge related operations
"""

import numpy
from .base import Operation
from ..image import Image
from ..place import normalize_shape

_default_image_size = (200,200,4)

class MergeOperation(Operation):
    """
    An operation for merging any number of differently sized images via an over operation
    """
    def __init__(self, images, offsets=None):
        """
        Initializes the merge operation
        
        :Parameters:
            images : `list`
                An iterable of `Image` object, which will be merged from first to last
                (So first image will be on the bottom layer)
            offsets : `list`
                An iterable of offset tuples of (row,colum) where the offset gives the offset
                from the upper-left corner of the canvas for the corresponding image in `images`.  
                The canvas size is determined by the first 
                image and its offset and subsequent offsets are relative to it.  
                Negative offsets equate to cropping off that many pixels from that image.
        """
        self.images = images
        self.opimage = None
        
        if offsets is None:
            offsets = [(0,0)] * len(images) # row, then col
        if len(offsets) < len(images):
            offsets = offsets + ([(0,0)] * (len(images) - len(offsets)))
        self.offsets = offsets
        
    def run(self):
        if not self.images:
            self.opimage = Image(numpy.zeros(_default_image_size))
            return self.opimage
        
        # width and height determined entirely by the size of the first image and its offest
        canvas = self.images[0]
    
        height = canvas.height + self.offsets[0][0]
        width = canvas.width + self.offsets[0][1]
        # normalize canvas dims (copies canvas to new image so not in-place as well)
        canvas = Image(normalize_shape(canvas, self.offsets[0], width, height))
        canvas.to_rgba()
        
        # perform the merge operation on the rest of the images...
        for i, image in enumerate(self.images[1:]):
            image.to_rgba()
            image = normalize_shape(image.data, self.offsets[i+1], width, height)
            canvas = self.merge(image, canvas)
        
        self.opimage = Image(canvas)
        return self.opimage
    
    def merge(self, image1, image2):
        """
        Merges image 1 over image 2
        
        :Parameters:
            image1 : `Image`
                The image to merge in
            image2 : `image`
                The image to merge on top of
        
        :Returns:
            The newly merged image
            
        :Rtype:
            `Image`
        """
        return self.over(image1, image2) # image 1 over image 2
        
    def over(self, image1, image2):
        """
        Performs an over operation of image 1 over image 2
        
        :Parameters:
            image1 : `Image`
                The image to place over image 2
            image2 : `Image`
                The image to place under image 1
                
        :Returns:
            The newly merged image
            
        :Rtype:
            `Image`
        """
        # alpha_a + alpha_b*(1-alpha_a)        
        new_alpha = image1[...,3] + numpy.multiply(image2[...,3], (1 - image1[...,3]))

        new_alpha_safe = new_alpha.copy()
        new_alpha_safe[new_alpha_safe == 0] = 1.0
        
        # (1/alpha_0) *  (alpha_a * col_a + alpha_b * col_b * (1- alpha_a)
        new_red = self.over_channel(image1[...,0], image2[...,0], image1[...,3], image2[...,3]) / new_alpha_safe
        new_green = self.over_channel(image1[...,1], image2[...,1], image1[...,3], image2[...,3]) / new_alpha_safe
        new_blue = self.over_channel(image1[...,2], image2[...,2], image1[...,3], image2[...,3]) / new_alpha_safe
    
        return numpy.dstack((new_red, new_green, new_blue, new_alpha))
        
    def over_channel(self, image1_channel, image2_channel, alpha1, alpha2):
        """
        Performs an over for a given channel
        
        :Parameters:
            image1_channel : `numpy.array`
                A specific channel for image 1 to composite over the image 2 channel
            image2_channel : `numpy.array`
                A specific channel for image 2
            alpha1 : `numpy.array`
                The alpha channel of image 1
            alpha2 : `numpy.arra`
                The alpha channel of image 2
                
        :Returns:
            The image1 channel composited over the image2 channel
        
        :Rtype:
            `numpy.array`
        """
        return numpy.multiply(image1_channel, alpha1) + numpy.multiply(numpy.multiply(image2_channel, alpha2), 1 - alpha1)
        
