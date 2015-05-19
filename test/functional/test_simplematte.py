from inception.image.matte.simplematte import *

if __name__ == '__main__':
    from inception.image.image import Image
    image = Image.from_filepath("../../../../test/images/buff_small.png")#traditional-buffets-and-sideboards.jpg")
    image = Image.from_filepath("../../../../test/images/traditional-buffets-and-sideboards.jpg")
    
    import time
    t1 = time.time()
    print("Starting")
    result = alphamatte(image.data)

    t2 = time.time()
    print("Done (in %2.2f seconds)!" % (t2-t1))
    image.to_rgba()
    image[..., 3] = result
    from PIL import Image as PILImage
    green = Image.from_any(PILImage.new('RGBA', (image.shape[1], image.shape[0]), color=(0,255,0,255)))
    from inception.image.operation.merge import MergeOperation
    mop = MergeOperation([green, image]).run()
    mop.save(image.filename.rsplit('.',1)[0] + '_greencomp.png')
    Image.from_any(result).save(image.filename.rsplit('.',1)[0] + '_matte.png')