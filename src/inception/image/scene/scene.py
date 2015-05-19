"""
Base scene module
"""
from .vanishingpoint import ZhangVanishingPointEstimator, JLinkageVanishingPointEstimator

def estimate_scene_description(image):
    """
    Given an image, estimates the scene descriptor for that image
    
    :Parameters:
        image : `numpy.array` or `Image`
            The image whose scene description to estimate
            
    :Returns:
        The scene description for that image
    """
    return SceneDescription(image)

class SceneDescription(object):
    """
    A general purpose scene description which contains all the (usually 3D) information we've able to infer
    about the scene captured by the image
    """
    
    def __init__(self, image):
        # estimate vanishing point/camera properties
        self.vpestimator = JLinkageVanishingPointEstimator(image)
        self.vpestimator.estimate()
        
        self._camera_matrix = None
        print("Detected vanishing points (x,y,z): %s" % self.get_vanishing_points())
        print("Focal length: %s" % self.focal_length)
    
    @property
    def focal_length(self):
        """
        The estimated focal length of the camera used to render the scne
        
        :Rtype:
            `float`
        """
        return self.vpestimator.focal_length
    
    @property
    def camera_matrix(self):
        """
        The 3x3 intrinsic camera matrix to transform from camera space to image (pixel) space
        
        :Rtype:
            `numpy.array`
        """
        if self._camera_matrix is None:
            self._camera_matrix = self.vpestimator.get_intrinsic_camera_transformation()
        return self._camera_matrix
            
    def get_world_to_camera_transformation(self, origin=(0,0)):
        """
        Gets the transformation from world space to camera space given the target point
        in image space of the origin
        
        :Parameters:
            origin : `tuple`
                Where the origin lies in image space
                
        :Returns:
            A tuple of (R,t) where R is the rotation matrix and t is the translation vector to get
            into world space
        """
        return self.vpestimator.solve_world_to_cam(origin=origin)
    
    def get_vanishing_points(self):
        """
        Get the image space coordinates of the 3 vanishing points in the scene
        
        :Returns:
            A 3x2 array of the 3 vanishing point coordinates in image space
        """
        return self.vpestimator.get_projective_vanishing_points()