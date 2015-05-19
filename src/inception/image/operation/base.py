"""
Useful base functionality for use internally by the operations modules
"""
class Operation(object):
    """
    An abstract operation that represents some modification/action on 
    this operations's image. Implementation of a particular operation can be created by 
    subclassing this and then overidding the `run()` method (and possibly the constructor).
    
    This abstraction allows bookkeeping/higher-level parts of the api to treat
    each operation as a discrete command, for the purposes of undos, tracking, etc.
    """
    def __init__(self, image, *args, **kwargs):
        """
        Initializes the operation
        
        :Parameters:
            image : `Image`
                An image to operate on
        """
        self.image = image
        self.opimage = None
    
    def run(self):
        """
        Runs the operation and returns the resulting image after applying the operation
        
        :Rtype:
            `Image`
        """
        self.opimage = self.image.clone()
        return self.opimage
