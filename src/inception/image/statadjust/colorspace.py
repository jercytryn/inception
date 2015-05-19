import numpy, math

###############################################################
# color space transformations
def srgb_to_linear(image):
    """
    Converts the given image from sRGB color space to linear color space
    
    :Parameters:
        image : `numpy.array`
            The sRGB image
            
    :Returns:
        THe image in linear color space
    """
    a = 0.055
    return numpy.select([image <= 0.04045],[image/12.92],default=pow((image + a)/(1+a), 2.4))

def linear_to_srgb(image):
    """
    Converts the given image from linear color space to sRGB color space
    
    :Parameters:
        image : `numpy.array`
            The linear image
            
    :Returns:
        THe image in sRGB color space
    """
    a = 0.055
    return numpy.select([image <= 0.0031308],[12.92 * image],default=(1+a)*pow(image,1/2.4) - a)

# hsv color space
# adapted from standard python colorsys lib
# see also http://stackoverflow.com/questions/7274221/changing-image-hue-with-python-pil
def rgb_to_hsv(image):
    """
    Converts the given linear color space RGB image to HSV
    
    :Parameters:
        image : `numpy.array`
            The linear color image
            
    :Returns:
        The image in HSV color space
    """
    hsv = numpy.zeros_like(image)
    hsv[..., 3:] = image[..., 3:]
    
    r, g, b = image[..., 0], image[..., 1], image[..., 2]
    maxc = numpy.max(image[..., :3], axis=-1)
    minc = numpy.min(image[..., :3], axis=-1)
    v = maxc
    diffvals = (maxc != minc)
    hsv[diffvals, 1] = (maxc-minc)[diffvals] / maxc[diffvals]
    rc, gc, bc = numpy.zeros_like(r), numpy.zeros_like(r), numpy.zeros_like(r)
    rc[diffvals] = (maxc-r)[diffvals] / (maxc-minc)[diffvals]
    gc[diffvals] = (maxc-g)[diffvals] / (maxc-minc)[diffvals]
    bc[diffvals] = (maxc-b)[diffvals] / (maxc-minc)[diffvals]
    
    hsv[..., 0] = numpy.select([r == maxc, g == maxc], [bc-gc, 2.0+rc-bc], default=4.0+gc-rc)
    hsv[..., 0] = (hsv[..., 0]/6.0) % 1.0
    hsv[..., 2] = v
    return hsv

def hsv_to_rgb(image):
    """
    Converts the given linear color space HSV image to RGB
    
    :Parameters:
        image : `numpy.array`
            The linear color image
            
    :Returns:
        The image in RGB color space
    """
    rgb = numpy.zeros_like(image)
    rgb[..., 3:] = image[..., 3:]
    
    h, s, v = image[..., 0], image[..., 1], image[..., 2]
    i = (h*6.0).astype('uint8') # XXX assume truncates!
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i%6
    
    r = numpy.select([s == 0.0, i == 0, i == 1, i == 2, i == 3, i == 4], [v, v, q, p, p, t], default=v)
    g = numpy.select([s == 0.0, i == 0, i == 1, i == 2, i == 3, i == 4], [v, t, v, v, q, p], default=p)
    b = numpy.select([s == 0.0, i == 0, i == 1, i == 2, i == 3, i == 4], [v, p, p, t, v, v], default=q)
    rgb[..., 0] = r
    rgb[..., 1] = g
    rgb[..., 2] = b
    return rgb

def rgb_to_xyY(image):
    """
    Converts the given linear color space RGB image to xyY color space
    
    :Parameters:
        image : `numpy.array`
            The linear color image
            
    :Returns:
        The image in xyY color space
    """
    # see http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
    # srgb
    r, g, b = image[..., 0], image[..., 1], image[..., 2]
    
    # to XYZ first
    XYZ = numpy.zeros_like(image)
    XYZ[..., 3:] = image[..., 3:]
    
    X = .4125 * r + .3576 * g + .1805 * b
    Y = .2126 * r + .7152 * g + .0722 * b
    Z = .0193 * r + .1192 * g + .9505 * b
    XYZ[..., 0] = X
    XYZ[..., 1] = Y
    XYZ[..., 2] = Z
    
    # srgb reference white:
    # x=0.3127, y=0.3290; z=0.3583
    
    # now to xyY
    xyY = numpy.zeros_like(image)
    # when X=Y=Z=0, set x and y to reference white
    xyY[..., 0] = .3127
    xyY[..., 1] = .3290
    
    mask = numpy.ma.mask_or(numpy.ma.mask_or((X != Y),(Y != Z)),(Z != 0))
    
    xyY[..., 3:] = image[..., 3:]
    
    xyY[..., 0][mask] = X[mask] / (X+Y+Z)[mask]
    xyY[..., 1][mask] = Y[mask] / (X+Y+Z)[mask] 
    xyY[..., 2] = Y
    
    return xyY

def xyY_to_rgb(image):
    """
    Converts the given linear color space xyY image to RGB color space
    
    :Parameters:
        image : `numpy.array`
            The linear color image
            
    :Returns:
        The image in RGB color space
    """
    # http://www.brucelindbloom.com/index.html?Eqn_xyY_to_XYZ.html
    # convert to XYZ first
    x, y, Y = image[..., 0], image[..., 1], image[..., 2]
    XYZ = numpy.zeros_like(image)
    mask = (y != 0)
    XYZ[...,0][mask] = (x * Y)[mask] / y[mask]
    XYZ[...,1][mask] = Y[mask]
    XYZ[...,2][mask] = ((1-x-y) * Y)[mask] / y[mask]
    
    X, Y, Z = XYZ[...,0], XYZ[...,1], XYZ[...,2]
    rgb = numpy.zeros_like(image)
    rgb[..., 3:] = image[..., 3:]
    
    r = 3.2406 * X + -1.5372 * Y + -.4986 * Z
    g = -.9689 * X + 1.8758 * Y + .0415 * Z
    b = .0557 * X + -.2040 * Y + 1.0570 * Z
    rgb[..., 0] = r
    rgb[..., 1] = g
    rgb[..., 2] = b
    return rgb
  
# based off of (Wyszecki & Stiles, p.224-9) 
# Note: 0.24792 is a corrected value for the error found in W&S as 0.24702
k_temp_table=numpy.array([(0,    0.18006,  0.26352,   -0.24341),
                          (10,    0.18066,  0.26589,   -0.25479),
                          (20,    0.18133,  0.26846,   -0.26876),
                          (30,    0.18208,  0.27119,   -0.28539),
                          (40,    0.18293,  0.27407,   -0.30470),
                          (50,    0.18388,  0.27709,   -0.32675),
                          (60,    0.18494,  0.28021,   -0.35156),
                          (70,    0.18611,  0.28342,   -0.37915),
                          (80,    0.18740,  0.28668,   -0.40955),
                          (90,    0.18880,  0.28997,   -0.44278),
                          (100,   0.19032,  0.29326,   -0.47888),
                          (125,   0.19462,  0.30141,   -0.58204),
                          (150,   0.19962,  0.30921,   -0.70471),
                          (175,   0.20525,  0.31647,   -0.84901),
                          (200,   0.21142,  0.32312,   -1.0182),
                          (225,   0.21807,  0.32909,   -1.2168),
                          (250,   0.22511,  0.33439,   -1.4512),
                          (275,   0.23247,  0.33904,   -1.7298), 
                          (300,   0.24010,  0.34308,   -2.0637),
                          (325,   0.24792,  0.34655,   -2.4681), 
                          (350,   0.25591,  0.34951,   -2.9641), 
                          (375,   0.26400,  0.35200,   -3.5814), 
                          (400,   0.27218,  0.35407,   -4.3633), 
                          (425,   0.28039,  0.35577,   -5.3762), 
                          (450,   0.28863,  0.35714,   -6.7262), 
                          (475,   0.29685,  0.35823,   -8.5955), 
                          (500,   0.30505,  0.35907,  -11.324), 
                          (525,   0.31320,  0.35968,  -15.628), 
                          (550,   0.32129,  0.36011,  -23.325), 
                          (575,   0.32931,  0.36038,  -40.770), 
                          (600,   0.33724,  0.36051, -116.45)])

def cct_to_xy(temperature):
    """
    Convert the two-channel mired, tint temperature image to xy chromaticity
    
    :Parameters:
        temperature : `numpy.array`
            An array of depth 2 containing mired, tint
            
    :Returns:
        The image in xy chromaticity space
    """
    # adapted from original "Understanding and Improving the Realism of Image Composites" code
    
    # http://www.brucelindbloom.com/index.html?Eqn_XYZ_to_T.html
    # also see opt-prop matlab toolbox 

    mired = temperature[..., 0]
    tint = temperature[..., 1]

    k_tint_scale = -3000.0;
    ## Begin
    # Find inverse temperature to use as index.
    r = mired;
    
    # Convert tint to offset in uv space.
    offset = tint * (1.0 / k_tint_scale);
    
    indexarray = numpy.zeros(temperature.shape[:-1], dtype='uint64')
    # initialize mask to all false
    mask = (indexarray != indexarray)
    
    # Search for line pair containing coordinate.
    for index in range(30):   
        
        newmask = (r < k_temp_table[index + 1][0])
        newmask = (newmask | (index==29))
        indexarray[newmask & (~mask)] = index
        
        mask = mask | newmask
        
    # Find relative weight of first line.
    f = (k_temp_table[indexarray + 1,0] - r) / (k_temp_table[indexarray + 1,0] - k_temp_table[indexarray,0])
    
    # Interpolate the black body coordinates.
    u = k_temp_table[indexarray,1] * f +  k_temp_table[indexarray + 1,1] * (1.0 - f)
    v = k_temp_table[indexarray,2] * f +  k_temp_table[indexarray + 1,2] * (1.0 - f)
    
    # Find vectors along slope for each line.
    uu1 = 1.0
    vv1 = k_temp_table[indexarray,3]
    uu2 = 1.0
    vv2 = k_temp_table[indexarray + 1,3]
    
    len1 = (1.0 + vv1 * vv1) ** (1/2.0)
    len2 = (1.0 + vv2 * vv2) ** (1/2.0)
    uu1 = uu1 / len1
    vv1 = vv1 / len1
    uu2 = uu2 / len2
    vv2 = vv2 / len2
    
    # Find vector from black body point.
    uu3 = uu1 * f + uu2 * (1.0 - f)
    vv3 = vv1 * f + vv2 * (1.0 - f)
    len3 = (uu3 * uu3 + vv3 * vv3) ** (1/2.0)
    uu3 = uu3 / len3
    vv3 = vv3 / len3
    
    # Adjust coordinate along this vector.
    u = u + uu3 * offset
    v = v + vv3 * offset
    
    # Convert to xy coordinates.    
    denom = (u - 4.0 * v + 2.0);
    x = 1.5 * u / denom
    y = v / denom
    
    result = numpy.zeros_like(temperature)
    result[..., 0] = x
    result[..., 1] = y
    return result

def xyY_to_cct(image):
    """
    Convert the xyY linear image to a 2-channel image containing mired, tint
    
    :Parameters:
        image : `numpy.array`
            The image in xyY space
            
    :Returns:
        The color temperature image
    """
    # adapted from original "Understanding and Improving the Realism of Image Composites" code
    
    # also http://www.brucelindbloom.com/index.html?Eqn_XYZ_to_T.html
    # also i_xy2cct.m in opt-prop matlab toolbox source code    

    k_tint_scale = -3000.0
    
    x = image[..., 0]
    y = image[..., 1]
    
    ## 
    # Convert to uv space.
    denom = -x + 6*y + 1.5
    mask = (numpy.ma.mask_or((x != y),(y != 0)))
    # assuming rgb (3 channel)
    uv = numpy.zeros(image.shape[:-1] + (2,),dtype='float64')
    uv[...,0][mask] = (2.0 * x)[mask] / denom[mask]
    uv[...,1][mask] = (3.0 * y)[mask] / denom[mask]
    u = uv[..., 0]
    v = uv[..., 1]
    
    # Search for line pair coordinate is between.
    last_dt = numpy.zeros(image.shape[:-1], dtype='float64')
    last_dv = numpy.zeros_like(last_dt) 
    last_du = numpy.zeros_like(last_dt) 
    
    indexarray = numpy.zeros(image.shape[:-1], dtype='uint64')
    best_dt = numpy.zeros(image.shape[:-1], dtype='float64')
    best_dv = numpy.zeros_like(best_dt)
    best_du = numpy.zeros_like(best_dt)
    
    # initialize mask to all false
    mask = (indexarray != indexarray)
    
    for index in range(1, 31):
        # Convert slope (of mired line) to delta-u and delta-v, with length 1.
        du = 1.0
        dv = k_temp_table[index][3]
        length = math.sqrt (1.0 + dv * dv)
        du = du / length
        dv = dv / length
        
        # Find delta from black body point to test coordinate.
        uu = u - k_temp_table[index][1]
        vv = v - k_temp_table[index][2]
        
        # Find distance above or below the mired line.
        dt = - uu * dv + vv * du    #    (du,dv) X (uu, vv).  s.t., norm(du, -dv) = 1.0f
        
        # If below line, we have found line pair.
        newmask = (dt <= 0.0)
        newmask = (newmask | (index == 30))
        indexarray[newmask & (~mask)] = index
        best_dt[newmask & (~mask)] = dt[newmask & (~mask)]
        best_du[newmask & (~mask)] = du
        best_dv[newmask & (~mask)] = dv
        
        mask = mask | newmask
        
        last_dt[~mask] = dt[~mask]
        last_du[~mask] = du
        last_dv[~mask] = dv
                
    # Find fractional weight of two lines
    best_dt[(best_dt > 0.0) & mask] = 0.0
    best_dt[mask] = -best_dt[mask]        # the distant to k_temp_table[idx] along slope

    #f:  weight to k_temp_table[index]    
    f = numpy.zeros(image.shape[:-1], dtype='float64')
    m = (~(indexarray == 2))
    f[m] = best_dt[m] / (last_dt + best_dt)[m]
    
    # Interpolate the temperature.
    mired = k_temp_table[indexarray-1,0] * f +   k_temp_table[indexarray,0] * (1.0 - f)
    #temperature = 1.0e6 / mired;
    
    # Find delta from black body point to test coordinate.
    uu = u - (k_temp_table[indexarray-1,1] * f + k_temp_table[indexarray,1] * (1.0 - f))
    vv = v - (k_temp_table[indexarray-1,2] * f + k_temp_table[indexarray,2] * (1.0 - f))
    
    # Interpolate vectors along slope (of mired lines).
    du = best_du * (1.0 - f) + last_du * f
    dv = best_dv * (1.0 - f) + last_dv * f
    length = (du * du + dv * dv) ** (1/2.0)
    m = (length != 0)
    du[m] = du[m] / length[m]
    dv[m] = dv[m] / length[m]
    du[~m] = 0.0
    dv[~m] = 0.0
    # Find distance along slope (of mired lines).
    tint = (uu * du + vv * dv) * k_tint_scale

    result = numpy.zeros(image.shape[:-1] + (2,), dtype=image.dtype)
    result[..., 0] = mired
    result[..., 1] = tint
    return result
