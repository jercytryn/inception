from inception.image.scene.vanishingpoint import *

if __name__ == '__main__':
    x=ZhangVanishingPointEstimator("../../../../test/images/vanishing.jpg")
    x.estimate()
    print x.get_projective_vanishing_points()
