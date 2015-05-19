from inception.image.shadow.shadow import *

if __name__ == '__main__':
    import os
    from inception.image.image import Image
    from inception.image.matte.bordermatte import alphamatte
    from inception.image.operation.merge import MergeOperation
    from inception.image.operation.scale import ScaleOperation
    from PIL import Image as PILImage

    image = Image.from_filepath("../../../../test/images/traditional-buffets-and-sideboards.jpg")
    bg = Image.from_filepath("../../../../test/images/vanishing.jpg")
    
    result = alphamatte(image.data)
    
    filename = image.filename
    image.to_rgba()
    image[..., 3] = result
    image = ScaleOperation(image, image.width/3.0).run()

    offset = 20, 200
    
    pickle_path = bg.filename.rsplit('.', 1)[0] + '.scene.pkl'
    #pickle_path = bg.filename.rsplit('/',1)[0] + '/definitive.vanishing.pkl'
    import cPickle
    if (os.path.exists(pickle_path)):
        with open(pickle_path, 'r') as f:
            sd = cPickle.load(f)
        print("Detected vanishing points (x,y,z): %s" % sd.get_vanishing_points())
        print("Focal length: %s" % sd.focal_length)
        print(sd.vpestimator.vanishing_points)
    else:
        sd = estimate_scene_description(bg)
        with open(pickle_path, 'w') as f:
            cPickle.dump(sd, f)
    bg.scene_description = sd
    
    shadow = Image.from_any(create_shadow(image, bg, offset=offset, scene_description=None, skip_soften=True))
    image[...,3] *= .5
    mop = MergeOperation([bg, shadow, image], offsets=[(0,0),(0,0),offset]).run()
    mop.save(filename.rsplit('.',1)[0] + '_shadowcomp.png')
    
    """
    green = Image.from_any(PILImage.new('RGBA', (image.shape[1], image.shape[0]), color=(0,255,0,255)))
    mop = MergeOperation([green, shadow]).run()
    mop.save(filename.rsplit('.',1)[0] + '_greencomp.png')
    """
    Image.from_any(shadow).save(filename.rsplit('.',1)[0] + '_matte.png')
    