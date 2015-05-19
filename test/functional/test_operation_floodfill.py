from inception.image.operation.floodfill import *

if __name__ == '__main__':
    # unittests
    # TODO: remove all this add to more official unittests
        
    print("Running floodfill tests")
    
    def test_detect_bg():
        print("Testing detect_bg")
        image1 = Image.from_filepath("../../../../test/images/circ.png")
        image2 = Image.from_filepath("../../../../test/images/buff_small.png")
        
        print detect_bg(image1) == (1.0, 0.2627450980392157, 0.26666666666666666, 1.0)
        print detect_bg(image2) == (1.0, 1.0, 1.0)
    
    test_detect_bg()    
    
    def test_spiral():
        print("Testing spiral")
        
        def testfunc(foo):
            print("Exploring %s" % foo)
            return False
        
        m1 = [[1,2,3,4],[12,13,14,5],[11,16,15,6],[10,9,8,7]] # 4x4
        m2 = [[1,2,3,4,5],[16,17,18,19,6],[15,24,25,20,7],[14,23,22,21,8],[13,12,11,10,9]] # 5x5
        m3 = [[1,2,3,4,5],[14,15,16,17,6],[13,20,19,18,7],[12,11,10,9,8]] # 4x5
        m4 = [[1,2,3,4],[14,15,16,5],[13,20,17,6],[12,19,18,7],[11,10,9,8]] # 5x4
        m5 = [range(1,9),[18,19,20,21,22,23,24,9],range(17,9,-1)] # 3x8
        m6 = [[1],[2]] # 2x1
        m7 = [[1,2]] # 1x2
        m8 = [[1]] # 1x1
        m9 = [[]] # 1x0
        
        for m in [m1,m2,m3,m4,m5,m6,m7,m8,m9]:
            print("-------------------")
            print("Running on %s-sized matrix" % str(tuple([len(m),len(m[0])])))
            try:
                FloodfillOperation(Image.from_list([[1]]))._spiral(numpy.array(m), testfunc)
            except TargetNotFoundError:
                print("Not found")
    
    test_spiral()
    
    def test_floodfill():
        
        def timeit(func, *args, **kwargs):
            import time
            s = time.time()
            ret = func(*args, **kwargs)
            e = time.time()
            print("Ran in %2.3f sec" % (e-s))
            return ret
        
        image1 = Image.from_filepath("../../../../test/images/circ.png")
        image2 = Image.from_filepath("../../../../test/images/buff_small.png")
        image3 = Image.from_filepath("../../../../test/images/traditional-buffets-and-sideboards.jpg")
        image4 = Image.from_filepath("../../../../test/images/circ_opaque.png")
                
        import os
        
        for i in [image1,image2,image3,image4]:
            op = FloodfillOperation(i)        
            print("Running on %s" % os.path.basename(i.filename))
            timeit(op.run)
            i.save(i.filename.rsplit('.',1)[0] + '_floodfill.png')
        
    test_floodfill()
    """
    # TODO: inline floodfill
    # e.g.
    # see http://docs.scipy.org/doc/scipy/reference/tutorial/weave.html#catalog-search-paths-and-the-pythoncompiled-variable
    
    def foo():
        print("here!!")
        a = 'string'
        weave.inline(r'printf("%s\n",std::string(a).c_str());',['a'])
    import scipy.weave as weave
    foo() 
    """