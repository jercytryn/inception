
from inception.base import magic_insert, shadow, simplematte, statadjust, scale
from inception.image import Image
from inception.image.scene.scene import estimate_scene_description

def magic_insert_shadow_only(source_image, dest_image, boundingbox=None, 
                 scene_description=None, **kwargs):
    if not boundingbox:
        raise NotImplementedError("Need a value for `boundingbox` -- automatic bounding box calculation not yet implemented!")

    # simple boundary-based matting
    source_image = simplematte(source_image)
    
    # scale
    width = boundingbox[2] - boundingbox[0] + 1
    height = boundingbox[3] - boundingbox[1] + 1
    source_image = scale(source_image, width, height)
    
    # generate shadow
    genshadow = shadow(source_image, dest_image, boundingbox, scene_description=scene_description,
                       **kwargs.get('shadowargs',{}))
    return genshadow

if __name__ == '__main__':
    
    backgrounds = ['P1020826','P1040863','P1080032', 'P1080078', 'antique-furniture-living-room',
                   '1823724', 'Furniture-Wallpaper-hd-for-desktop']
    # given from gimp as (offset of bottom corner (x,y), then rect size)
    valid_obj_bboxes = [((217, 410, 150, 150), (500, 450, 200, 200)),
                        ((207, 300, 40, 43), (250,410,111,104), (434, 402, 150, 150)),
                        ((318, 403, 167, 160),),
                        ((334, 414, 49, 43), (230, 370, 72, 85)),
                        ((520, 1200, 450, 585),(1191,840,402,375),(798,843,99,100)),
                        ((474, 489, 280, 243),(848,598,350,350)),
                        ((1790,1058,450,570),)]
    
    foregrounds = ['bookcase','couch1','chair1','counter1','couch2']
    
    bbs = zip(backgrounds, valid_obj_bboxes)
    
    for background, bboxes in bbs:
        print("Loading background %s" % background)
        # load background and scene description
        bgpath = "../bg/%s.jpg" % background
        bg = Image.from_any(bgpath)
        sd = estimate_scene_description(bg)
        bg.scene_description = sd
        
        for foreground in foregrounds:
            print("Processing %s" % foreground)
            for i, (endX, endY, sizeX, sizeY) in enumerate(bboxes):
                fgpath = "../fg/%s.jpg" % foreground
                fg = Image.from_any(fgpath)
                
                aspect = fg.shape[0] / float(fg.shape[1])
                bbox = (endX - sizeX, int(endY - (aspect * sizeX)), endX, endY)
                print endX, endY, sizeX, sizeY, bbox
                
                magic_insert(fg, bg, bbox, generate_shadow=True).save('demo/%s_%s_%s_0comp.png' % (background, foreground, i))
                magic_insert_shadow_only(fg, bg, bbox).save('demo/%s_%s_%s_1shadowsoft.png' % (background, foreground, i))
                magic_insert_shadow_only(fg, bg, bbox, shadowargs=dict(skip_soften=True)).save('demo/%s_%s_%s_2shadow.png' % (background, foreground, i))
                
        
    
    