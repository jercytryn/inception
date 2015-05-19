from inception.generate import *

if __name__ == '__main__':
    import random
    import os
    from inception.image.image import Image
    
    urlfilepath = "../urls.txt"
    urls = []
    if os.path.exists(urlfilepath):
        with open(urlfilepath) as fileobj:
            urls = [l.strip() for l in fileobj.readlines() if l.strip()]
    
    random.seed(0)
    bg = os.path.abspath("../../test/images/traditional-living-room.jpg")
    
    for url in urls[9:]:
        print("Compositing %s" % url)        
        name = url.rsplit('/',1)[-1]
        result = generate_magic_composite(url, bg)
        
        if result:
            result.save(name)
        else:
            print("Invalid foreground url '%s'" % url)
    