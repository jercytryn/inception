from inception.image.analyze import *

if __name__ == '__main__':
    import os
    import urllib, cStringIO
    from inception.image.image import Image
    urlfilepath = "../../../test/urls.txt"
    urls = []
    if os.path.exists(urlfilepath):
        with open(urlfilepath) as fileobj:
            urls = [l.strip() for l in fileobj.readlines() if l.strip()]
    
    for url in urls:
        fileobj = cStringIO.StringIO(urllib.urlopen(url).read())
        img = Image.from_any(fileobj)
        print validate_as_foreground(img), url
        
        