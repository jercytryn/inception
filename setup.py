#!/usr/bin/env python

from distutils.core import setup

# TODO: in order for this work as a valid installation, need a way of
# copying the thirdParty directory alongside as well as this contains
# all the matlab scripts
# until then, can manually copy thirdParty to site-packages or wherever
# this gets installed. Ugly, but will work for now
setup(name='Inception',
      version='0.1',
      description='Automated 2d object insertion framework',
      author='Jeremy Cytryn',
      url='https://github.com/jercytryn/inception',
      license='MIT',
      packages=['inception', 'inception.ui', 'inception.ui.tool',
                'inception.image',
                'inception.image.matte','inception.image.operation',
                'inception.image.place','inception.image.scene',
                'inception.image.shadow','inception.image.statadjust'],
      package_dir = {'': 'src'},
      package_data = {'inception.ui': ['*.ui'],
                      },
      scripts=['scripts/inception-gui', 'scripts/inception']
      )
      