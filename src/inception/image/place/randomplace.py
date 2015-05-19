"""
Random placement
"""

import math, random

def randomplace(foreground, background, randmin=2, randmax=5):
    """
    Generates a random but "somewhat feasible" position and scale for the foreground object
    Returns a valid bounding box for placement.
    
    :Returns:
        `A bounding box of the form (upperleft.x, upperleft.y, lowerright.x, lowerright.y)`
    
    :Rtype:
        `tuple`
    """
    if randmin <= 0 or randmax < randmin:
        raise ValueError("Bad input random range")
    
    # first pick a random scale
    # somewhere between 1/randmin and 1/randmax the size of the background
    bgwidth = background.shape[1]
    scale = randmin + random.random() * (randmax - randmin)
    
    fgwidth = int(bgwidth / scale) + 1
    fgheight = int(fgwidth * foreground.shape[0]/foreground.shape[1])
    
    # pick an arbitrary x position so that the whole width is in the image when possible 
    if bgwidth > fgwidth:
        xoffset = random.randint(0, bgwidth - fgwidth)
    else:
        # otherwise, allow it to offset anywhere from right side of the two aligned to left side aligned
        xoffset = random.randint(bgwidth - fgwidth, 0)
    
    # pick a y position somewhere in the lower 2/3 for now as that will tend to be correct more of the time
    yoffset = random.randint(background.shape[0] / 3, max(background.shape[0] / 3 + 1, background.shape[0] - fgheight))
    
    return xoffset, yoffset, xoffset + fgwidth, yoffset + fgheight
    
    
    