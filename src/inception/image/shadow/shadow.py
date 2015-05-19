"""
Main module for shadow-based image manipulations
"""

import cv2
import scipy.ndimage
import numpy, math
from ..scene.scene import estimate_scene_description
from ..place import normalize_shape

def create_shadow(foreground, background, blur=15, opacity=.45, segments=10, offset=(0,0), scene_description=None,
                  skip_soften=False):
    """
    Generates a feasible shadow for the foreground image to cast on the background image
    
    :Parameters:
        foreground : `Image`
            The foreground image which should cast a shadow
        background : `Image`
            The background image which should receive the shadow
        blur : `float`
            The amount of gaussian blur to apply to soften the shadow, on average. 
        opacity : `float`
            The average baseline opacity for the softened shadow [0,1]
        segments : `int`
            The number of unique slices to use when applying spatially varying gaussian blur
        offset : `tuple`
            A tuple of (row, column) denoting the offset into the destination image where the upper-left
            corner of the source image will begin (once merged). Default=(0,0)
        scene_description : `SceneDescription`
            A scene description object for the background scene, containing various descriptors needed
            to create shadows.  If not given, the scene description is computed on the fly.
        skip_soften : `bool`
            If True, do not perform any shadow softening. Default=False
            
    :Returns:
        The generated shadow image, of same dimensions as the dest_image
        
    :Rtype:
        `Image`
    """
    if scene_description is None: 
        if hasattr(background, 'scene_description') and background.scene_description is not None:
            scene_description = background.scene_description
        else:
            scene_description = estimate_scene_description(background)
    
    # normalize foreground size onto background (expanding background if necessary)
    foreground = normalize_foreground(foreground, background, offset)
    
    # create a black version of the foreground
    shadow = blacken_image(foreground)
    
    # find the bottom left-most part of the foreground, assumed to be touching the ground
    ys_top = shadow[...,3].nonzero()[0].min()
    xs_left = shadow[...,3].nonzero()[1].min()
    ys_bottom = shadow[...,3].nonzero()[0].max()
    xs_right = shadow[...,3].nonzero()[1].max()
    
    if not skip_soften:
        shadow = temper_shadow(shadow, blur, opacity, segments, (xs_left, xs_right, ys_bottom, ys_top))      
    
    H = compute_homography(background, scene_description, xs_left, xs_right, ys_bottom, ys_top)
    shadow = cv2.warpPerspective(shadow,H,(shadow.shape[1],shadow.shape[0]))
    
    # finally, crop shadow to fit into background
    shadow = normalize_foreground(shadow, background, (min(offset[0], 0), min(offset[1], 0)), expand=False)
    
    return shadow

def temper_shadow(shadow, blur, opacity, segments, bounds):
    """
    Softens the given shadow image
    
    :Parameters:
        blur : `float`
            The amount of gaussian blur to apply to soften the shadow, on average. 
        opacity : `float`
            The average baseline opacity for the softened shadow [0,1]
        segments : `int`
            The number of unique slices to use when applying spatially varying gaussian blur
        bounds : `tuple`
            The tight axis-aligned bounding box around the unwarped shadow given as
            (xleft, xright, ybottom, ytop)
            
    :Returns:
        The tempered shadow image
    """
    (xs_left, xs_right, ys_bottom, ys_top) = bounds
    # qualitative blur amount should be independent of the size
    # use ~400px as the baseline and compare to image width
    blur = blur * float(xs_right - xs_left) / 400
    
    # blur and darken the shadow based on distance from bottom
    # apply varying opacity
    minopacity = max(0, opacity / 3.0)
    maxopacity = min(opacity * 1.5, 1.0)
    minopacity2 = max(0, opacity / 2.0)
    def smoothstep(minval, maxval,t):
        t = t*t*(3-2*t)
        return minval + (maxval - minval)*t
    opacity_mult = numpy.zeros_like(shadow[ys_top:ys_bottom+1, xs_left:xs_right+1, 3])
    height = ys_bottom - ys_top + 1
    hinge = int(height / 6.0)
    step1 = numpy.linspace(0.0, 1.0, num=height-hinge)
    step2 = numpy.linspace(1.0, 0.0, num=hinge)
    opacity_mult[:height-hinge, :] = numpy.tile(numpy.reshape(step1, (height-hinge,1)), (1, xs_right-xs_left+1))
    opacity_mult[height-hinge:, :] = numpy.tile(numpy.reshape(step2, (hinge,1)), (1, xs_right-xs_left+1)) 
    opacity_mult[:height-hinge, :] = smoothstep(minopacity, maxopacity, opacity_mult[:height-hinge, :])
    opacity_mult[height-hinge:, :] = smoothstep(minopacity2, maxopacity, opacity_mult[height-hinge:, :])
    shadow[ys_top:ys_bottom+1, xs_left:xs_right+1, 3] = shadow[ys_top:ys_bottom+1, xs_left:xs_right+1, 3] * opacity_mult
    
    # apply numerous overlapping slices of blurring
    slice_size = math.ceil((ys_bottom - ys_top)/segments)
    minblur = blur / 2.0
    maxblur = blur * 4.0
    blur_step = (maxblur / minblur)**(1.0/(segments-2))
    
    for i in range(segments-1):
        blur_amount = minblur * (blur_step**i)
        c0 = max(xs_left - int(math.ceil(blur_amount)), 0)
        c1 = xs_right+1 + int(math.ceil(blur_amount))
        r0 = max(ys_top+(segments-i-1)*slice_size - slice_size - int(math.ceil(blur_amount)), 0)
        r1 = ys_top+(segments-i)*slice_size+ 1 + int(math.ceil(blur_amount))
        shadow[r0:r1, c0:c1, 3] = scipy.ndimage.gaussian_filter(shadow[r0:r1, c0:c1, 3], sigma=blur_amount)
    # apply a final blur to help hide the seams
    shadow[..., 3] = scipy.ndimage.gaussian_filter(shadow[..., 3], sigma=blur)
    return shadow
    
def compute_homography(image, scene_description, x0, x1, y0, y1):
    """
    Computes the perspective transformation in image space to warp the image to the shadow
    
    :Parameters:
        image : `numpy.array`
            The background image
        scene_description : `SceneDescription`
            An estimated scene descripton for the background image
        x0 : `int`
            The leftmost tightest bounding coordinate for the foreground object
        x1 : `int`
            The rightmost tightest bounding coordinate for the foreground object
        y0 : `int`
            The bottommost tightest bounding coordinate for the foreground object
        y1 : `int`
            The topmost tightest bounding coorindate for the foreground object
            
    :Returns:
        The 3x3 perspective transformation matrix needed to warp the foreground to its shadow
    """
    # create the correct transformation and apply it    
    # first, use the scene description to get image space to world space transformation
    # origin is set to the bottom-left corner of the foreground object
    cam_to_im = scene_description.camera_matrix
    world_to_cam, T = scene_description.get_world_to_camera_transformation(origin=(x0, y0))
    cam_to_world = numpy.linalg.inv(world_to_cam)
    world_to_im = cam_to_im.dot(world_to_cam)
    im_to_world = cam_to_world.dot(numpy.linalg.inv(cam_to_im))
     
    ## usually in world space, x points left, y toward cam, z points up (z=0 is ground plane) rel to image space 
    # but don't assume anything about how the world-space coords are aligned, just figure it out based on
    # biggest diff between top and bottom, left and right of image about the principal point
    
    world_top = im_to_world.dot(numpy.array((image.width / 2.0, 0, 1)))
    world_bottom = im_to_world.dot(numpy.array((image.width / 2.0, image.height - 1, 1)))
    up_index = abs(world_top - world_bottom)[:3].argmax()
    up_flipped = False
    if (world_top - world_bottom)[up_index] < 0:
        up_flipped = True
    
    world_left = im_to_world.dot(numpy.array((0, image.height / 2.0, 1)))
    world_right = im_to_world.dot(numpy.array((image.width - 1, image.height / 2.0, 1)))
    right_index = abs(world_right - world_left)[:3].argmax()
    right_flipped = False
    if (world_right - world_left)[right_index] < 0:
        right_flipped = True
    cam_index = 0 if ((up_index == 1 and right_index == 2) or (up_index == 2 and right_index == 1)) else \
                (1 if ((up_index == 0 and right_index == 2) or (up_index == 2 and right_index == 0)) else 2)
    
    # get height of object in world space
    object_top = im_to_world.dot(numpy.array([x0,y1,1]))
    height = abs(object_top[up_index] - T[up_index])

    # TODO: would be nice to parametrize the desired light position in the absence of automatic light estimation
    # for now, just pick an arbitrary position
    # set the light object 1 height above the camera, partway between the object and the camera
    cam_to_obj = T
    w = .2 # how far along the line from camera to object plane [0,1]
    h = 1.6 # how many units in foreground hight space the light is above the camera
    # make the light a bit to the side to show off the shadow a bit more
    light_pos = numpy.zeros((4,), dtype='float64')
    if right_flipped:
        light_pos[right_index] = cam_to_obj[right_index] * w + height/4
    else:
        light_pos[right_index] = cam_to_obj[right_index] * w - height/4
    light_pos[cam_index] = cam_to_obj[cam_index] * w
    light_pos[up_index] = h*height if not up_flipped else - h*height 
    light_pos[3] = 1

    # create a matrix to project the planar polygon onto the ground plane (y=foreground_pos[1])
    # from the light 
    # e.g. see http://math.stackexchange.com/questions/320527/projecting-a-point-on-a-plane-through-a-matrix
    plane = numpy.zeros((4,))
    plane[up_index] = 1
    plane[3] = -T[up_index] # assumes bottom left point of foreground plane touches ground
    lambd = numpy.dot(plane, light_pos)
    l = light_pos
    f = plane
    world_to_ground = numpy.array([[lambd - f[0]*l[0], -f[1]*l[0], -f[2]*l[0], -f[3]*l[0]],
                                   [-f[0]*l[1], lambd - f[1]*l[1], -f[2]*l[1], -f[3]*l[1]],
                                   [-f[0]*l[2], -f[1]*l[2], lambd - f[2]*l[2], -f[3]*l[2]],
                                   [-f[0]*l[3], -f[1]*l[3], -f[2]*l[3], lambd - f[3]*l[3]]])
    
    # finally, just project the 4 corners of the object in world space onto the ground plane and then
    # convert those 4 points back into image space
    # this gives us the correspondences needed to get the perspective transformation in image space
    im_pts = numpy.array([(x0,y0),(x0,y1),(x1,y0),(x1,y1)],dtype='float64')
    im_pts_hom = cv2.convertPointsToHomogeneous(im_pts).squeeze()
    im_pts_ground = []
    
    for im_pt in im_pts_hom:
        pt_world = im_to_world.dot(im_pt)
        pt_world = numpy.array([pt_world[0], pt_world[1], pt_world[2], 1])
        ground_world = world_to_ground.dot(pt_world)
        ground_im = world_to_im.dot(ground_world[:3])
        im_pts_ground.append(ground_im)

    # perspective divide
    im_pts_ground = cv2.convertPointsFromHomogeneous(numpy.array(im_pts_ground)).squeeze()
    return cv2.getPerspectiveTransform(im_pts.astype('float32'), im_pts_ground.astype('float32'))    

def blacken_image(image):
    """
    Creates an all black copy of the given image, preserving the alpha channel
    
    :Parameters:
        image : `numpy.array`
            The image to black
    
    :Returns:
        A blackened copy of the image
    """
    image = image.copy()
    image[...,:3] = 0
    return image

def normalize_foreground(foreground, background, offset, expand=True):
    """
    Normalizes the shape of the given foreground image to match the shape of the background image
    
    :Paramters:
        foreground : `numpy.array`
            The foreground image to normalize
        background : `numpy.array`
            The background image whose size we want to match to
        offset : `tuple`
            A tuple of (row, column) denoting the offset into the destination image where the upper-left
            corner of the source image will begin (once merged). Default=(0,0)
        expand : `bool`
            If True, expands the normalized foreground so as not to crop it at all, e.g. if negative offsets
            or the like. Otherwise, perform a crop based on offset and going over the background size as in
            a normal merge
            
    :Returns:
        A copy of the foreground, normalized relative to the background
    """
    return normalize_shape(foreground, offset, background.shape[1], background.shape[0], 
                           dtype=background.dtype, expand=expand)

