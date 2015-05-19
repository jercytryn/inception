from inception.image.statadjust.statadjust import *

if __name__ == '__main__':
    """
    x = numpy.array([.25])
    y = numpy.array([.3])
    Y = numpy.array([.5])
    print xyY_to_cct(numpy.dstack((x,y,Y)))
    mired = numpy.array([155])
    tint = numpy.array([82661])
    print cct_to_xy(numpy.dstack((mired,tint)))
    print xyY_to_cct(cct_to_xy(numpy.dstack((mired,tint))))
    print cct_to_xy(xyY_to_cct(numpy.dstack((x,y,Y))))
    print temp_gettemp(.25,.3)
    print temp_getxy(155,82661)
    print temp_gettemp(*temp_getxy(155,82661))
    print temp_getxy(*temp_gettemp(.25,.3))
    """

    """
    # test 1:
    # create an input image with some baseline luminance and all the color temps
    x = numpy.arange(0,1,.001)
    y = numpy.vstack([x]*1000)
    res = numpy.dstack((y,y.transpose(),numpy.zeros_like(y)+.5))
    i = Image(xyY_to_rgb(res))

    # output the image
    i.save("colortest.png")
    
    # output the image when transformed and then back again
    # next convert to a color temperature
    temp = xyY_to_cct(res)
    temp[..., 0] += 0
        
    # convert the color temperature back into xy chromaticity
    xynew = cct_to_xy(temp)
    res[...,0] = xynew[...,0]
    res[...,1] = xynew[...,1]
    
    # finally, back into rgb
    i2 = Image(xyY_to_rgb(res.clip(0,1))) 
    i2.save("colortest2.png")
    
    print("DONE")
    """
    from inception.image.image import Image
    from inception.image.operation import merge
    import os, glob
    testdir = os.path.abspath(os.path.dirname(__file__) + '/../../../../test/images/statadjust')
    #mattes = glob.glob(testdir + "/brigh*_small_matte.jpg")
    mattes = glob.glob(testdir + "/ice_stand_small_matte.jpg")
    #mattes.extend(glob.glob(testdir + "/col*_small_matte.jpg"))
    mattes.extend(glob.glob(testdir + "/dance_small_matte.jpg"))
    backgrounds = [a.rsplit("_matte.jpg",1)[0] + ".jpg" for a in mattes]
    
    foregroundImages = []
    backgroundImages = []
    for i, matte in enumerate(mattes):
        backgroundImages.append(Image.from_filepath(backgrounds[i]))
        matteImage = Image.from_filepath(matte)
        foregroundImage = backgroundImages[-1].clone()
        foregroundImage.to_rgba()
        foregroundImage[..., 3] = linear_to_srgb(getluminance(srgb_to_linear(matteImage.data)))
        foregroundImages.append(foregroundImage)
        foregroundImage.filename = matteImage.filename
    
    # test the images
    for i in range(len(backgroundImages)):
        bg = backgroundImages[i]
        fg = i + 1 if (i < len(backgroundImages) - 1) else 0
        fg = foregroundImages[fg]
        
        print("-------- Running on %s over %s ----------" % (os.path.basename(fg.filename), os.path.basename(bg.filename)))
        results = statadjust(fg.data, bg.data, intermediary_results=True)
        suffix = ['before_0','contrast_1','lum_2', 'cct_3','sat_4']
        if not os.path.exists(testdir+'/results'):
            os.makedirs(testdir+'/results')
        for i, result in enumerate([fg.data] + results):
            print("Merging to form %s" % suffix[i])
            merger = merge.MergeOperation([bg, Image.from_any(result)], offsets=[(0,0),(0,0)]).run()
            #merger = Image.from_any(result[..., 3])
            merger.save(testdir + '/results/%s_%s.jpg' % (os.path.basename(bg.filename).rsplit('.',1)[0],suffix[i]))
    
    """
    x = backgroundImages[0]
    Image.from_any(x.data).save(testdir+'/orig.png')
    newspace = srgb_to_linear(x.data)
    Image.from_any(linear_to_srgb(setlog2luminance(newspace, -2.5).clip(0,1))).save(testdir+'/foo.png')
    """
    #x = Image.from_filepath("./a0711-WP_IMG_1592.jpg")
    #Image.from_any(x.data).save("orig.png")
    #Image.from_any(getluminance(x.data)).save("lum.png")
    #Image.from_any(srgb_to_linear(x.data)).save("linear.png")
    #Image.from_any(linear_to_srgb(srgb_to_linear(x.data))).save("roundtrip.png")
    #Image.from_any(hsv_to_rgb(rgb_to_hsv(x.data))).save("hsvround.png")
    #Image.from_any(getcontrast(x.data)).save("contrast.png")
    #Image.from_any(getcolortemp(x.data)).save("cct.png")
    
    #foo = gethue(x.data)
    """
    i = rgb_to_hsv(x.data)
    i[..., 0] += (180-78.0)/360.0
    i[..., 0] = i[..., 0] % 1.0
    i = hsv_to_rgb(i)
    Image.from_any(i).save("blah.png")
    """
    #Image.from_any(gethue(x.data)).save("hue.png")
    #green = Image.from_filepath("./green.png")
    #red = Image.from_filepath("./red.png")
    #purple = Image.from_filepath("./purple.png")
    
    #Image.from_any(hue_match(green.data, purple.data)).save("match.png")
    
    
    
    