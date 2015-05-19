"""
Image implementation
This provides a layer of encapsulation for the convenience of the internal inception framework
"""
import os, urlparse, ssl, cStringIO, urllib
import numpy
from PIL import Image as PILImage
from PIL.ImageFile import ImageFile

class Image(object):
    """
    An image object representing an image stored in RGB[A] or L floating point representation
    """
    
    def __init__(self, data, pilimage=None, filename=None, scene_description=None):
        """
        Initializes an image
        
        :Parameter:
            data : `numpy.array`
                The underlying numpy array representing the actual pixels of the image.
                dtype can be 'uint8' if numbers range 0-255 otherwise should be 'float64'
            pilimage : `PIL.Image`
                Internal usage: The python image library image representation
            filename : `basestring`
                Internal usage: The filename this object came from
            scene_description : `SceneDescription`
                Internal usage: The cached scene description for this image
        """
        if data.dtype == 'uint8':
            self._data = data.astype('float64') / 255
        else:
            self._data = data
            
        self._pilimage = pilimage
        
        # promote filename attr from PIL Image
        self.filename = filename
        
        # cached scene description
        self._scene_description = scene_description
    
    @classmethod
    def from_any(cls, thing):
        """
        Tries to construct an image from whatever the user hands it
        """
        if isinstance(thing, basestring):
            return cls.from_url(thing)
        
        if hasattr(thing, 'read'):
            return cls.from_stream(thing)
        
        if isinstance(thing, cls):
            return cls(thing._data, pilimage=thing._pilimage, filename=thing.filename, 
                       scene_description=thing._scene_description)
        
        if isinstance(thing, ImageFile) or hasattr(thing, 'putpixel'):
            return cls.from_image(thing)
        
        if isinstance(thing, numpy.ndarray):
            return cls(thing)
        
        if hasattr(thing, 'paintEngine'):
            return cls.from_qimage(thing)
        
        return cls.from_list(thing)
    
    @classmethod
    def from_qimage(cls, image):
        """
        Constructs an image from a `QImage` object
        
        :Parameters:
            image : `QtGui.QImage`
                The qt image object
        
        :Returns:
            A new instance of `Image`
            
        :Rtype:
            `Image`
        """
        from PySide import QtGui
        image = image.convertToFormat(QtGui.QImage.Format.Format_RGB32)

        width = image.width()
        height = image.height()

        ptr = image.constBits()    
        
        orig = numpy.array(ptr).reshape(height, width, 4)
        new_array = numpy.empty((height, width, 4), orig.dtype)
        new_array[...,0] = orig[...,2]
        new_array[...,1] = orig[...,1]
        new_array[...,2] = orig[...,0]
        new_array[...,3] = orig[...,3]
        return cls(new_array)
    
    @classmethod
    def from_list(cls, l):
        """
        Constructs an image from a list of lists
        
        :Parameters:
            l : `list`
                A list of list of lists of floats [0.0-1.0] or ints [0-255] representing the channels of image
                in row, col, channel order 
        
        :Returns:
            A new instance of `Image`
            
        :Rtype:
            `Image`
        """
        return cls(numpy.array(l))
    
    @classmethod
    def from_url(cls, url):
        """
        Constructs an image from the given url or filepath
        Supports protocols such as 'file' and 'http'
        
        :Parameters:
            url : `basestring`
                The url or filepath denoting the location of the image
                
        :Returns:
            A new instance of `Image`
            
        :Rtype:
            `Image`
        """
        handler = ImageResourceHandler.get(url)
        if handler.rawsupport:
            return cls.from_filepath(handler.filename)
        else:
            return cls.from_stream(handler.getstream(), resource=handler.filename)
    
    @classmethod
    def from_filepath(cls, filepath):
        """
        Constructs an image from the given filepath
        
        :Parameters:
            filepath : `basestring`
                The path to an image on disk. May be a relative or absolute path
                and may include environment variables
        
        :Returns:
            A new instance of `Image`
            
        :Rtype:
            `Image`
        """
        filepath = os.path.expandvars(os.path.expanduser(filepath))
        image = PILImage.open(filepath)
        c = cls(numpy.asarray(image))
        # we already have the pil image, so lets cache it
        c._pilimage = image
        c.filename = image.filename
        return c
    
    @classmethod
    def from_stream(cls, stream, resource=None):
        """
        Constructs an image from the given stream, e.g. a file object or the like
        
        :Parameters:
            stream : `object`
                Any object that behaves like a file and can be read from
        
        :Returns:
            A new instance of `Image`
            
        :Rtype:
            `Image`
        """
        image = PILImage.open(stream)
        c = cls(numpy.asarray(image))
        # we already have the pil image, so lets cache it
        c._pilimage = image
        if resource:
            c.filename = resource
        return c
    
    @classmethod
    def from_image(cls, image):
        """
        Constructs an image from a `PIL.Image` object
        
        :Parameters:
            image : `PIL.Image`
                The image stored as a PIL Image object
        
        :Returns:
            A new instance of `Image`
            
        :Rtype:
            `Image`
        """
        c = cls(numpy.asarray(image))
        # we already have the pil image, so lets cache it
        c._pilimage = image
        if hasattr(image, 'filename'):
            c.filename = image.filename
        return c
    
    @property
    def pilimage(self):
        """
        The `PIL.Image` object for this image
        
        :Rtype:
            `PIL.Image`
        """
        # lazy-load
        if self._pilimage is None:
            self._pilimage = PILImage.fromarray(numpy.uint8(self.data*255))
        return self._pilimage
    
    @property
    def opencvimage(self):
        """
        The opencv representation for this image.
        Generally opencv algorithms operate on three channel 8-bit BGR
        
        :Rtype:
            `numpy.array`
        """
        rgb = numpy.uint8(self.data[...,:3]*255)
        return rgb[:, :, ::-1].copy() 
    
    @property
    def qimage(self):
        """
        The QImage for this image
        
        :Rtype:
            `PySide.QtGui.QImage`
        """
        # adapted from http://kogs-www.informatik.uni-hamburg.de/~meine/software/vigraqt/qimage2ndarray.py
        from PySide import QtGui
        rows, cols, chans = self.data.shape
        bgra = numpy.empty((rows, cols, 4), numpy.uint8, 'C')
        bgra[...,2] = self.data[...,0] * 255
        bgra[...,1] = self.data[...,1] * 255
        bgra[...,0] = self.data[...,2] * 255
        if self.data.shape[2] < 4:
            bgra[...,3].fill(255)
        else:
            bgra[...,3] = self.data[...,3] * 255
        format = QtGui.QImage.Format_ARGB32
        image = QtGui.QImage(bgra.data, cols, rows, format)
        image.ndarray = bgra
        return image
    
    @property
    def scene_description(self):
        """
        The cached scene description, if any
        
        :Rtype:
            `SceneDescription`
        """
        return self._scene_description
    
    @scene_description.setter
    def scene_description(self, value):
        self._scene_description = value
    
    @property
    def data(self):
        """
        The underlying (numpy) data representation for this image
        
        :Rtype:
            `numpy.ndarray`
        """
        return self._data
    
    @data.setter
    def data(self, val):
        self._data = val
        self._clear_cache()
        
    @property
    def height(self):
        """
        The image height, in pixels
        
        :Rtype:
            `int`
        """
        return self.data.shape[0]
    
    @property
    def width(self):
        """
        The image width, in pixels
        
        :Rtype:
            `int`
        """
        return self.data.shape[1]
    
    def to_grayscale(self):
        """
        Converts this image to 1 channel grayscale, in place. 
        Warning: This is a lossy operation
        """
        rows, cols = self.data.shape[:2]
        if len(self.data.shape) == 2:
            # already grayscale
            return
        
        chans = self.data.shape[2]
        if chans == 1:
            self.data = self.data[..., 0]
        elif chans >= 3:
            # luminance conversion
            # see http://stackoverflow.com/questions/12201577/convert-rgb-image-to-grayscale-in-python
            self.data = numpy.dot(self.data[...,:3], [0.299, 0.587, 0.114])
        else:
            raise ValueError("Unsupported number of channels for grayscale conversion: %s" % chans)
    
    def to_rgb(self):
        """
        Convenience function to convert this image from grayscale or rgba
        to RGB in place.  Simply copies the single channel into each color channel for grayscale
        """
        rows, cols = self.data.shape[:2]
        chans = self.data.shape[2] if len(self.data.shape) > 2 else 1
        
        if chans == 3:
            # no-op
            return
        elif chans == 4:
            self.data = self.data[..., :3]
            return
        elif chans == 2:
            raise ValueError("Unsupported number of channels for rgb conversion: %s" % chans)
            
        # according to 
        # http://www.socouldanyone.com/2013/03/converting-grayscale-to-rgb-with-numpy.html
        # this pattern is fastest for general use    
        tmp = numpy.empty((rows, cols, 3), dtype=numpy.float64)
        if len(self.data.shape) > 2:
            tmp[:,:,0] = self.data[...,0]
        else:
            tmp[:,:,0] = self.data
        tmp[:,:,1] = tmp[:,:,2] = tmp[:,:,0]
        self.data = tmp
    
    def to_rgba(self):
        """
        Convenience function to convert this image from grayscale or RGB to RGBA in place.
        For grayscale, fills each color channel with the grayscale channel. The alpha channel
        is assumed to be all opaque.  
        If the image is already RGBA, this is a no-op
        """
        rows, cols = self.data.shape[:2]
        if len(self.data.shape) > 2:
            chans = self.data.shape[2]
        else:
            self.data = self.data.reshape(rows,cols,1)
            chans = 1
            
        if chans >= 4:
            # short circuit, we're already in RGBA
            return 
        
        if chans == 1:
            self.to_rgb()

        # add a 4th channel, with all 1.0 alpha values
        alpha = numpy.ones((rows, cols, 1))
        tmp = numpy.dstack((self.data[:,:,0], self.data[:,:,1], self.data[:,:,2], alpha))
        self.data = tmp
        
    def save(self, outpath, *args, **kwargs):
        """
        Serializes the data to the given outpath. This is currently just a paper-thin 
        wrapper around `PIL.Image.save()`
        
        :Parameters:
            outpath : `basestring`
                The path to which the image should be output
                
            *args :
                Extra arguments to pass through to `PIL.Image.save`
                
            **kwargs : 
                Extra keyword arguments to pass through to `PIL.Image.save`
        """        
        return self.pilimage.save(outpath, *args, **kwargs)
    
    def shallow_clone(self):
        """
        Performs a shallow copy of this image object
        
        :Returns:
            The shallow clone
        
        :Rtype:
            `Image`
        """
        return self.__class__(self._data, self._pilimage, self.filename, self._scene_description)
    
    def clone(self):
        """
        Performs a deep copy of this image object
        
        :Returns:
            The deep clone
        
        :Rtype:
            `Image`
        """
        copy = self.shallow_clone()
        copy._data = copy._data.copy()
        return copy
    
    def _clear_cache(self):
        """
        Private method to clear the internal cache for this image. This is so that lazy-loaded but
        cached properties can be properly recalculated when the underlying image changed
        """
        self._pilimage = None
    
    def __getattr__(self, attr):
        # passthrough all unknown attributes to the wrapped numpy object, so that this can in many ways
        # be treated identically to a numpy array for convenience and ease of support in either type
        # in the framework
        try:
            return getattr(self.data, attr)
        except AttributeError:            
            raise AttributeError("Neither '%s' object nor its wrapped '%s' object has attribute '%s'" %
                                 (self.__class__.__name__, self.data.__class__.__name__, attr))
    
    def __getitem__(self, key):
        # passthrough all dictionary lookups to the underlying numpy array
        return self.data[key]
    
    def __setitem__(self, key, val):
        # the underlying image is changing, so clear the cache
        # MAINT: in practice this may slow things down too much so may want to have
        # calling classes take on the responsibility of clearing the cache
        # of course, if speed is desired, the calling class could simple do
        # self.data[...] = ... to do without caching, then clear the cache only at the end
        self._clear_cache() 
        # passthrough all dictionary setter to the underlying numpy array
        self.data[key] = val

class ImageResourceHandler(object):
    """
    An abstract handler of image resources of a particular scheme/protocol
    This also serves as the registry point for custom handlers via:
    
    >>> ImageResourceHandler.registerHandler('xkcd', XKCDResourceHandler)
    
    The handler passed in has no need to sublcass from `ImageResourceHandler`
    but must at the very least implement the `rawsupport` property and the
    `getscheme` method
    """
    
    _scheme = None
    _handlers = None
    
    @classmethod
    def get(cls, url):
        """
        Gets the appropriate handler to deal with the resource pointed to by the given url
        
        :Parameters:
            url : `basestring`
                A uniform resource locator of any supported scheme
                
        :Returns:
            A image resource handler capable of reading the given resource
        """
        if cls._handlers is None:
            cls._load_default_handlers()
        parsed = urlparse.urlparse(url)
        if not parsed.scheme:
            scheme = 'file'
        else:
            scheme = parsed.scheme
        if scheme not in cls._handlers:
            raise KeyError("Unregistered handler for scheme '%s' required to parse URI '%s'" % (scheme, url))
        return cls._handlers[scheme](parsed)
        
    @classmethod
    def _load_default_handlers(cls):
        """
        Private - Loads all default handlers (e.g. all subclasses) accessible to the image resource handler
        at this point
        """
        if cls._handlers is None:
            cls._handlers = {}
            for handler in cls.__subclasses__():
                schemes = [handler._scheme] if isinstance(handler._scheme, basestring) else handler._scheme
                for scheme in schemes:
                    cls._handlers[scheme] = handler
        
    @classmethod
    def register_handler(cls, scheme, handler):
        """
        Registers a new handler for a given scheme
        
        :Parameters:
            scheme : `basestring`
                The protocol this handler supports
            handler : `object`
                A handler with a `rawsupport` property and `getstream` method
        """
        if cls._handlers is None:
            cls._load_default_handlers()
        cls._handlers[scheme] = handler
        
    def __init__(self, urlparse):
        self.urlparse = urlparse
    
    @property
    def rawsupport(self):
        """
        If True, the system can handle the url path of this scheme directly as a filepath 
        without needing to use a stream. Subclasses should still implement `getstream` 
        as well to be good conforming citizens and allow flexibility.
        """
        return False
    
    @property
    def filename(self):
        """
        The path part of the url (does not include query args, fragments or the like)
        """
        return self.urlparse.path
    
    def getstream(self):
        """
        Get a readable stream object which can be used to read bits from the resource with a
        read() method.
        Must be implemented by subclasses
        
        :Returns:
            A readable stream which can be used to read the resource this is handling
        """
        raise NotImplementedError()

class FileResourceHandler(ImageResourceHandler):
    """
    A file resource handler
    """
    _scheme = 'file'
    
    @property
    def rawsupport(self):
        return True
    
    def getstream(self):
        # this is not strictly speaking necessary, but just in case we want it
        return open(self.urlparse.path)
    
class HttpResourceHandler(ImageResourceHandler):
    """
    An http resource handler. Can also handle https urls
    """
    _scheme = ['http','https']
    
    def getstream(self):
        # HACK: bypass verification (see PEP 476)
        # also see http://stackoverflow.com/questions/27835619/ssl-certificate-verify-failed-error
        context = ssl._create_unverified_context()
        return cStringIO.StringIO(urllib.urlopen(self.urlparse.geturl(), context=context).read())
        
    
        
        
        
        