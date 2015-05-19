"""
Top level inception api
"""
__all__ = ['floodfill','poissonblend','scale', 'magic_insert', 'inception']

from .image import Image
from .image.operation.floodfill import FloodfillOperation
from .image.operation.scale import ScaleOperation
from .image.operation.poisson import PoissonOperation
from .image.operation.merge import MergeOperation
from .image.operation.matte import SimpleMatteOperation
from .image.operation.statadjust import StatAdjustOperation
from .image.operation.shadow import GenerateShadowOperation

def floodfill(image, *args, **kwargs):
    """
    Performs a floodfill on the given image
    
    :Parameters:
        image : `Image` or `numpy.array` or `basestring`
            The image object we would like to operate on as a numpy array, url, filepath, or image object
        keycolor : `tuple`
            The color to key out in the floodfill. If `None` specified, this is detected
            automatically. Default=None
        channel : `basestring`
            The channel we wish to be replaced with `replacevalue` for all pixels contiguous
            with the seeded pixel. Valid values are 'r','g','b', and 'a'. Default='a'
        replacevalue : `float`
            The value to replace the given channel with for the pixels that match the keycolor
            and are contiguous with the seeded pixel. Default=0.0
        tol : `float`
            The threshold tolerance to allow in the difference of squares between pixels contiguous with the 
            seed pixel and the key color. The the difference of squared norms exceeds tol, the pixel is not 
            treated as equal for the purpose of floodfilling. Default=.04
        seedpixel : `tuple`
            Any iterable of (row, col) indices for where to begin the floodfill. Note that this is assumed
            to be the same as keycolor.  If not, the floodfill may end up being a no-op.
            If seedpixel is None, the seed is determined procedurally by spiraling inward clockwise from the
            upper righthand pixel of the image. Default=None
    
    :Returns:
        A copy of the image after floodfill has been performed
        
    :Rtype:
        `Image`
    """
    image = Image.from_any(image)
    return FloodfillOperation(image, *args, **kwargs).run()

def simplematte(image, *args, **kwargs):
    """
    Performs a simple but effective "border matte" algorithm on the given image
    
    :Parameters:
        image : `Image` or `numpy.array` or `basestring`
                The image object we would like to operate on as a numpy array, url, filepath, or image object
        tol_low : `float`
            A lower tolerance of image difference with background below which pixel is 
            assumed to be part of the background.
        tol_high : `float`
            An upper tolerance on the image difference above which pixels are assumed to be part
            of the foreground
            
    :Returns:
        A copy of the image, with its alpha channel set based on the matting
        
    :Rtype:
        `Image`
    """
    image = Image.from_any(image)
    return SimpleMatteOperation(image, *args, **kwargs).run()

def poissonblend(source_image, dest_image, boundingbox, mask=None, **kwargs):
    """
    Performs a  poisson blending operation of the given source image into the given destination
    image
    
    :Parameters:
        source_image : `Image` or `numpy.array` or `basestring`
            The image to composite
        dest_image : `Image` or `numpy.array` or `basestring`
            The image to blend source into
        boundingbox : `tuple`
            The bounding box for where to insert the source image in the dest image, given as four
            coordinates corresponding to (upperleft.x, upperleft.y, lowerright.x, lowerright.y)
        mask : `numpy.array`
            A one-channel mask image to use instead of the source image alpha channel
            Not yet implemented
        clone_type : `int`
            A flag determining the type of blending to do.  Support normal clone (cv2.NORMAL_CLONE), mixed 
            clone for mixing gradients (cv2.MIXED_CLONE) and feature exchange (cv2.FEATURE_EXCHANGE).
            See http://docs.opencv.org/3.0-beta/modules/photo/doc/cloning.html for more details.
    
    :Returns:
        The blended composite
        
    :Rtype:
        `Image`
    """
    # TODO: mask support
    if mask is not None:
        raise NotImplementedError()
    source_image = Image.from_any(source_image)
    dest_image = Image.from_any(dest_image)
    return PoissonOperation(source_image, dest_image, offset=(boundingbox[1], boundingbox[0]), **kwargs).run()

def statadjust(source_image, dest_image, boundingbox, **kwargs):
    """
    Performs a statistical adjustment operation on the source image to match the destination image
    
    :Parameters:
        source_image : `Image` or `numpy.array` or `basestring`
            The foreground image to adjust to match the lighting quality of the background image
        dest_image : `Image` or `numpy.array` or `basestring`
            The background image to match to
        boundingbox : `tuple`
            The bounding box for where the source image will be inserted into the dest image once merged, 
            given as four coordinates corresponding to (upperleft.x, upperleft.y, lowerright.x, lowerright.y)
            
    :Returns:
        A statistically adjusted copy of the source image
        
    :Rtype:
        `Image`
    """
    source_image = Image.from_any(source_image)
    dest_image = Image.from_any(dest_image)
    return StatAdjustOperation(source_image, dest_image, offset=(boundingbox[1], boundingbox[0]), **kwargs).run()

def scale(image, *args, **kwargs):
    """
    Scales the given image
    
    :Parameters:
        image : `Image` or `numpy.array` or `basestring`
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
    
    :Returns:
        The scaled image
        
    :Rtype:
        `Image`
    """
    image = Image.from_any(image)
    return ScaleOperation(image, *args, **kwargs).run()

def merge(*args, **kwargs):
    """
    Merges the given images from first to last so that the first image will be on the bottom layer
    
    :Parameters:
        *args :
            `Image` objects to merge, which will be merged from first to last.
            Can also be given as resource paths, urls, or numpy arrays 
        offsets : `list`
            An iterable of offset tuples of (row,colum) where the offset gives the offset
            from the upper-left corner of the canvas for the corresponding image in `images`.  
            The canvas size is determined by the first 
            image and its offset and subsequent offsets are relative to it.  
            Negative offsets equate to cropping off that many pixels from that image.
    
    :Returns:
        The resulting merged image
    
    :Rtype:
        `Image`
    """
    images = [Image.from_any(image) for image in args]
    return MergeOperation(images, **kwargs).run()

def shadow(source_image, dest_image, boundingbox, scene_description=None, **kwargs):
    """
    Generates a feasible shadow for the source image to cast on the destination image
    
    :Parameters:
        source_image : `Image` or `numpy.array` or `basestring`
            The foreground image which should cast a shadow
        dest_image : `Image` or `numpy.array` or `basestring`
            The background image which should receive the shadow
        boundingbox : `tuple`
            The bounding box for where the source image will be inserted into the dest image once merged, 
            given as four coordinates corresponding to (upperleft.x, upperleft.y, lowerright.x, lowerright.y)
        scene_description : `SceneDescription`
            A scene description object for the background scene, containing various descriptors needed
            to create shadows.  If not given, the scene description is computed on the fly.
        blur : `float`
            The amount of gaussian blur to apply to soften the shadow, on average. 
        opacity : `float`
            The average baseline opacity for the softened shadow [0,1]
        segments : `int`
            The number of unique slices to use when applying spatially varying gaussian blur
        skip_soften : `bool`
            If True, do not perform any shadow softening. Default=False
            
    :Returns:
        The generated shadow image, of same dimensions as the dest_image
        
    :Rtype:
        `Image`
    """
    source_image = Image.from_any(source_image)
    dest_image = Image.from_any(dest_image)
    return GenerateShadowOperation(source_image, dest_image, offset=(boundingbox[1], boundingbox[0]), 
                                   scene_description=scene_description, **kwargs).run()
    
def magic_insert(source_image, dest_image, boundingbox=None, constrain_scale=None, 
                 generate_shadow=True, perform_statadjust=True,
                 scene_description=None, **kwargs):        
    """
    Performs a "magic" automatic insertion of the source image into the destination 
    image at the specified bounding box location.
    
    :Parameters:
        source_image : `Image`
            The foreground image to insert
        dest_image : `Image`
            The background image into which to insert the foreground
        boundingbox : `tuple`
            The bounding box for where the source image will be inserted into the dest image once merged, 
            given as four coordinates corresponding to (upperleft.x, upperleft.y, lowerright.x, lowerright.y)
        generate_shadow : `bool`
            If True, generates a shadow. Otherwise, skips shadow generation. Default=True
        perform_statadjust : `bool`
            If True, performs statistical image adjustment on the source_image to better match 
            global lighting of dest_image. Default=True
        scene_description : `SceneDescription`
            A scene description object for the background scene, containing various descriptors needed
            to create shadows.  If not given, the scene description is computed on the fly.
        **kwargs : 
            Keyword arguments specific to the various parts of the pipeline.  Supports nested dictionaries
            with keys 'matteargs', 'scaleargs', 'shadowargs', 'statadjustargs', and 'mergeargs' whose key-value
            pairs are passed through as parameters to the corresponding operations
            
    :Returns:
        The resulting magic composite
        
    :Rtype:
        `Image`
    """
    # simple boundary-based matting
    source_image = simplematte(source_image, **kwargs.get('matteargs',{}))
    
    # compute bounding box, if needed
    if not boundingbox:
        boundingbox = [0, 0, source_image.width, source_image.height]
    elif constrain_scale:
        constrain_scale = constrain_scale.lower() 
        if len(boundingbox) < 4:
            boundingbox = boundingbox + ([0] * 4 - len(boundingbox))
        if constrain_scale == 'x':
            boundingbox[3] = boundingbox[1] + (boundingbox[2] - boundingbox[0]) * (source_image.height / float(source_image.width))
        elif constrain_scale == 'y' and boundingbox[3] != 0:
            boundingbox[2] = boundingbox[0] + (boundingbox[3] - boundingbox[1]) * (source_image.width / float(source_image.height))
        elif constrain_scale == 'xy' or constrain_scale == 'both' or (boundingbox[2] == 0 or boundingbox[3] == 0):
            boundingbox[2] = boundingbox[0] + source_image.width
            boundingbox[3] = boundingbox[1] + source_image.height
        else:
            raise ValueError("Unrecognized value for constrain_scale: '%s'" % constrain_scale)
    
    # scale
    width = boundingbox[2] - boundingbox[0]
    height = boundingbox[3] - boundingbox[1]
    source_image = scale(source_image, width, height, **kwargs.get('scaleargs',{}))
    
    # generate shadow
    if generate_shadow:
        genshadow = shadow(source_image, dest_image, boundingbox, scene_description=scene_description,
                           **kwargs.get('shadowargs',{}))
    
    # light
    if perform_statadjust:
        source_image = statadjust(source_image, dest_image, boundingbox, **kwargs.get('statadjustargs',{}))
    
    # blend
    if generate_shadow:
        return merge(dest_image, genshadow, source_image, offsets=[(0,0), (0,0), (boundingbox[1], boundingbox[0])], 
                     **kwargs.get('mergeargs',{}))
    return merge(dest_image, source_image, offsets=[(0,0), (boundingbox[1], boundingbox[0])], **kwargs.get('mergeargs',{}))

# alias
inception = magic_insert
