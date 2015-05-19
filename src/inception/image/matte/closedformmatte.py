"""
Closed form matting implementation, ported from the original matlab code.  
Based on 
A. Levin D. Lischinski and Y. Weiss. A Closed Form Solution to Natural Image Matting.
Conference on Computer Vision and Pattern Recognition (CVPR), June 2007.
"""
import scipy.sparse
import scipy.sparse.linalg
import scipy.ndimage
import numpy.linalg
from ..analyze import detect_bg

def alphamatte(image, **kwargs):
    """
    Mattes the given image using closed form matting
    
    :Parameters:
        image : `numpy.array`
            The input image to matte
            
        scribble : `numpy.array`
            An image that provides constraints on definite foreground and definite background,
            background is given value of 0 and foreground a value of 1.  Everything gray is unknown.
            If not given, constraints are determined procedurally based on difference from background color
            Default=None
            
        epsilon : `float`
            Regularizing term, default=.0000001
            
        win_size : `int`
            Window size, default=1
            
    :Returns:
        The resulting alpha channel
    
    :Rtype:
        `numpy.array`
    """
    return runMatting(image, **kwargs)

def generate_scribbles(image, bg_color, bg_threshold=.000000000001, fg_threshold=.05):
    """
    Auto-generate conservative scribbles from an image with a given solid background color 
    """
    # use a very conservative estimation of scribbles
    # everything that is exactly the bg_color becomes background
    # everything that is very far from the bg_color becomes foreground
    image_diff = abs(image[...,:3] - bg_color[:3])
    bg_mask = numpy.all(image_diff < bg_threshold, axis=2)
    fg_mask = numpy.all(image_diff > fg_threshold, axis=2)
    consts_map = bg_mask | fg_mask # all constraints
    consts_vals = fg_mask # just foreground
    return (consts_map, consts_vals)

def runMatting(image, scribble=None, epsilon=None, win_size=None):
    """
    Runs the closed form matting algorithm
    
    :Parameters:
        image : `numpy.array`
            The input image to matte
            
        scribble : `numpy.array`
            An image that provides constraints on definite foreground and definite background,
            background is given value of 0 and foreground a value of 1.  Everything gray is unknown.
            If not given, constraints are determined procedurally based on difference from background color
            Default=None
            
        epsilon : `float`
            Regularizing term, default=.0000001
            
        win_size : `int`
            Window size, default=1
            
    :Returns:
        The resulting alpha channel
    
    :Rtype:
        `numpy.array`
    """
    if scribble is None:
        consts_map, consts_vals = generate_scribbles(image, detect_bg(image))
    else:
        bg_mask = numpy.all(scribble[...,:3] < .05, axis=2)
        fg_mask = numpy.all(scribble[...,:3] > .95, axis=2)
        consts_map = bg_mask | fg_mask # all constraints
        consts_vals = fg_mask # just foreground
        
    return solveAlpha(image, consts_map, consts_vals, epsilon=epsilon, win_size=win_size)

def solveAlpha(image, consts_map, consts_vals, epsilon=None, win_size=None, lambda_val=100):
    h, w, _ = image.shape[:3]
    img_size = w * h
    kwargs = {}
    if epsilon is not None:
        kwargs['epsilon'] = epsilon
    if win_size is not None:
        kwargs['win_size'] = win_size
        
    A = getLaplacian1(image, consts_map, **kwargs)
    D = scipy.sparse.spdiags(consts_map.flatten(1),0,img_size,img_size).tocsc();

    x = scipy.sparse.linalg.spsolve((A + lambda_val*D), lambda_val * numpy.multiply(consts_map.flatten(1), consts_vals.flatten(1)))
    return x.reshape(h,w,order='F').clip(0,1)

def getLaplacian1(image, consts, epsilon=.0000001, win_size=1):
    neb_size = (win_size * 2 + 1)**2
    h, w, c = image.shape[:3]
    if (c > 3):
        c = 3
    img_size = w*h
    #consts = scipy.ndimage.binary_erosion(consts, numpy.ones((win_size*2+1, win_size*2+1)), border_value=1)
    
    indsM = numpy.array(range(img_size)).reshape(h,w,order='F')
    tlen = sum(sum(1 - consts[win_size:-win_size, win_size:-win_size]) * (neb_size**2))
    
    row_inds = numpy.zeros((tlen,1))
    col_inds = numpy.zeros((tlen,1))
    vals = numpy.zeros((tlen,1))
    
    len_val = 0
    for j in range(win_size, w-win_size):
        for i in range(win_size, h-win_size):
            if (consts[i,j]):
                continue
            win_inds = indsM[i-win_size:i+win_size+1, j-win_size:j+win_size+1].flatten(1)
            winI = image[i-win_size:i+win_size+1,j-win_size:j+win_size+1,:3].reshape(neb_size, c, order='F')
            win_mu = winI.mean(axis=0).transpose()
            win_var = numpy.linalg.inv((winI.transpose().dot(winI)/neb_size) - win_mu.dot(win_mu.transpose()) + numpy.identity(c)*epsilon/neb_size)
            winI = winI - numpy.tile(win_mu.transpose(), (neb_size, 1))
            tvals = (1 + winI.dot(win_var).dot(winI.transpose())) / neb_size
            
            row_inds[len_val:neb_size**2 + len_val] = numpy.tile(win_inds, (1,neb_size)).reshape(neb_size**2, 1, order='F')
            col_inds[len_val:neb_size**2 + len_val] = numpy.tile(win_inds.transpose(), (neb_size,1)).reshape(neb_size**2, 1, order='F')
            
            vals[len_val:neb_size**2 + len_val, 0] = tvals.flatten(1)
            len_val += neb_size**2
    
    vals = vals[:len_val].squeeze()
    row_inds = row_inds[:len_val].squeeze()
    col_inds = col_inds[:len_val].squeeze()
    
    A = scipy.sparse.coo_matrix((vals, (row_inds, col_inds)), shape=(img_size, img_size)).tocsc()
            
    sumA = A.sum(axis=1)
    return (scipy.sparse.spdiags(sumA.flatten(1), 0, img_size, img_size) - A)
    

    
    
    