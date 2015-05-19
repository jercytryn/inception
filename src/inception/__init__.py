"""
Inception api for semi-automaed 2D object insertion into indoor scenery

>>> import inception
>>> inception.magic_insert('http://my/awesome/foreground.jpg', '/Users/mrayder/background.png', (30, 40, 300, 500))
"""

# expose the top level api methods up the very top level of the package
# e.g. so that can just do 
# >>> import inception
# >>> inception.magic_insert()
# for instance
from .base import inception, magic_insert, floodfill, scale, poissonblend, shadow, statadjust
from .generate import generate_magic_composite
from .image import Image

