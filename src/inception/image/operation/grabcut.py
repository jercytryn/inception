"""
GrabCut operation implementation
"""

import cv2, numpy
from ..image import Image
from .base import Operation
from ..matte.bordermatte import alphamatte

class GrabcutMatteOperation(Operation):
    """
    Performs a GrabCut image segmentation on the given image a la
    C. Rother, V. Kolmogorov, and A. Blake, GrabCut: Interactive foreground extraction using
    iterated graph cuts, ACM Trans. Graph., vol. 23, pp. 309-314 2004
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
        self.image.to_rgba()
        bordermatte = Image.from_any(alphamatte(self.image.data, tol_low=.001))
        
        # apply opencv's grabcut: http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_grabcut/py_grabcut.html
        
        # use the bordermatte result as our seeding constraint mask
        mask = numpy.ones((self.image.shape[0],self.image.shape[1]),dtype='uint8') * 2
        mask[bordermatte <= 0.0000001] = 0
        mask[bordermatte >= .9999999] = 1
        
        bgdModel = numpy.zeros((1,65),numpy.float64)
        fgdModel = numpy.zeros((1,65),numpy.float64)
        
        img = self.image.opencvimage

        mask, bgdModel, fgdModel = cv2.grabCut(img,mask,None,bgdModel,fgdModel,5,cv2.GC_INIT_WITH_MASK)
        mask = Image(255 * numpy.where((mask==2)|(mask==0),1,0).astype('uint8'))
        
        self.opimage = self.image.clone()
        self.opimage.to_rgba()
        self.opimage[..., 3] = mask
        return self.opimage 