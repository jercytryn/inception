"""
Shadowing operations
"""
from ..shadow import shadow
from .base import Operation
from ..image import Image

class GenerateShadowOperation(Operation):
    """
    A shadow generation operation which acts on a foreground and background and generates a
    feasible foreground shadow onto the background scene
    """
    def __init__(self, foreground, background, offset=(0,0), scene_description=None, **kwargs):
        """
        Initializes the shadow generation operation.
        
        :Parameters:
            foreground : `Image`
                The foreground image which should cast a shadow
            background : `Image`
                The background image which should receive the shadow
            offset : `tuple`
                A tuple of (row, column) denoting the offset into the destination image where the upper-left
                corner of the source image will begin (once merged). Default=(0,0)
            scene_description : `SceneDescription`
                A scene description object for the background scene, containing various descriptors needed
                to create shadows.  If not given, the scene description is computed on the fly.
            **kwargs :
                Any additional keyword arguments to pass through to `inception.image.shadow.create_shadow`
        """
        self.image = foreground
        self.background = background
        self.offset = offset
        self.scene_description = scene_description or self.background.scene_description 
        self.opimage = None
        
        self.kwargs = kwargs
        
    def run(self):
        """
        Runs the operation
        
        :Returns:
            The generated shadow image (RGBA)
            
        :Rtype:
            `Image`
        """
        self.opimage = Image(shadow.create_shadow(self.image, self.background, 
                                                  offset=self.offset, scene_description=self.scene_description,
                                                  **self.kwargs))
        return self.opimage