from inception.image.matte.closedformmatte import *

if __name__ == '__main__':
    from inception.image.image import Image
    image = Image.from_filepath("../../../../test/images/traditional-buffets-and-sideboards.jpg")
    import time
    t1 = time.time()
    print("Starting")
    result = alphamatte(image.data)#, scribble=Image.from_filepath("../../../../test/images/buff_small_scribble2.png").data)
    t2 = time.time()
    print("Done (in %2.2f seconds)!" % (t2-t1))

    consts_map, consts_vals = generate_scribbles(image.data, detect_bg(image.data))
    Image.from_any(consts_map).save(image.filename.rsplit('.',1)[0] + '_cm.png')
    Image.from_any(consts_vals).save(image.filename.rsplit('.',1)[0] + '_cv.png')

    #result = scipy.ndimage.grey_erosion(result, footprint=scipy.ndimage.generate_binary_structure(2, 1))

    image.to_rgba()
    image[..., 3] = result
    
    from PIL import Image as PILImage
    green = Image.from_any(PILImage.new('RGBA', (image.shape[1], image.shape[0]), color=(0,255,0,255)))
    from inception.image.operation.merge import MergeOperation
    mop = MergeOperation([green, image]).run()
    mop.save(image.filename.rsplit('.',1)[0] + '_greencomp.png')
    Image.from_any(result).save(image.filename.rsplit('.',1)[0] + '_matte.png')