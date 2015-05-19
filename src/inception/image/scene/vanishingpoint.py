"""
Module for vanishing point computation
"""

import numpy, scipy, tempfile, logging, os, subprocess, shlex, shutil, re, math
import cv2
from ..image import Image

def _get_topdir():
    """
    Private: Get the top directory of the repository
    """
    try:
        # tmp hack: assumes git dependency
        orig_dir = os.getcwd()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        gittop = subprocess.check_output(shlex.split('git rev-parse --show-toplevel')).strip()
        return gittop
    except subprocess.CalledProcessError:
        # less hacky, more fickle if reorg though
        d = os.path.dirname
        return d(d(d(d(d(os.path.abspath(__file__))))))
    finally:
        os.chdir(orig_dir)

class AbstractVanishingPointEstimator(object):
    """
    An abstract estimator used to generate vanishing point guesses
    """
    def __init__(self, image):
        self.image = Image.from_any(image)
        # the unit (x,y,z) coords of the vanishing points in 
        self._vanishing_points = []
        self.principal_point = None
        self.focal_length = None    
    
    def __getstate__(self):
        d = dict(self.__dict__)
        d.pop('image')
        return d
    
    def __setstate__(self, state):
        state['image'] = None
        self.__dict__ = state
    
    def estimate(self):
        """
        Perform the vanishing point estimation
        Subclasses wishing to be concrete must override this method
        """
        raise NotImplementedError()
    
    def get_intrinsic_camera_transformation(self):
        """
        Gets the 3x3 intrinsic camera matrix to transform from camera space to image (pixel) space
        
        :Rtype:
            `numpy.array`
        """
        # form the appropriate transformation matrix from unit space
        xform = numpy.zeros((3,3))
        xform[2,2] = 1
        xform[0,0] = xform[1,1] = self.focal_length
        xform[0,2] = self.principal_point[0]
        xform[1,2] = self.principal_point[1]
        return xform
    
    def get_projective_vanishing_points(self):
        """
        Get the image space coordinates of the 3 vanishing points in the scene
        
        :Returns:
            A 3x2 array of the 3 vanishing point coordinates in image space
        """
        xform = self.get_intrinsic_camera_transformation()
        output = numpy.zeros((3,2))
        for i in range(3):
            inter = xform.dot(self._vanishing_points[i])
            output[i,...] = inter[0:2] / inter[2]
        return output
    
    def solve_world_to_cam(self, origin=(0,0)):
        """
        Solve for the rotation and translation to get from world space to camera space
        
        :Parameters:
            origin : `tuple`
                Where the origin lies in image space
                
        :Returns:
            A tuple of (R,t) where R is the rotation matrix and t is the translation vector to get
            into world space
        """
        # based on "Camera calibration using 2 or 3 vanishing points" (Orghidan et al. 2012)
        
        # first, need to solve for the scaling factor so can get rotation matrix R
        vs = self.get_projective_vanishing_points()
        A = numpy.array([[vs[0][0], vs[1][0], vs[2][0]],
                         [vs[0][1], vs[1][1], vs[2][1]],
                         [vs[0][0]**2, vs[1][0]**2, vs[2][0]**2],
                         [vs[0][1]**2, vs[1][1]**2, vs[2][1]**2],
                         [vs[0][0]*vs[0][1], vs[1][0]*vs[1][1], vs[2][0]*vs[2][1]]])
        b = numpy.array([self.principal_point[0], self.principal_point[1],
                         self.focal_length**2 + self.principal_point[0]**2,
                         self.focal_length**2 + self.principal_point[1]**2,
                         self.principal_point[0]*self.principal_point[1]])
        x = scipy.linalg.pinv2(A).dot(b)
        l1 = math.sqrt(abs(x[0]))
        l2 = math.sqrt(abs(x[1]))
        l3 = math.sqrt(abs(x[2]))
        
        # now, plug this in to get the rotation matrix
        u1 = vs[0][0]
        v1 = vs[0][1]
        u2 = vs[1][0]
        v2 = vs[1][1]
        u3 = vs[2][0]
        v3 = vs[2][1]
        u0 = self.principal_point[0]
        v0 = self.principal_point[1]
        
        R = numpy.array([[l1 * (u1 - u0)/self.focal_length, l2 * (u2 - u0)/self.focal_length, l3 * (u3 - u0)/self.focal_length],
                         [l1 * (v1 - v0)/self.focal_length, l2 * (v2 - v0)/self.focal_length, l3 * (v3 - v0)/self.focal_length],
                         [l1, l2, l3]])
        
        # finally solve for the translation in image space 
        # to do this, we assume the matrix KR maps to a space whose origin is at the camera
        # once we figure out where our given origin maps to in world space, that tells us 
        # how much we want to translate in world space to get there
        K = self.get_intrinsic_camera_transformation()
        t = numpy.linalg.inv(K.dot(R)).dot(numpy.array([origin[0], origin[1], 1]))
        return (R, t)   

class GenericLineExtractorMixin(object):
    """
    A generic line extractor mixin which extracts lines using a simple canny edge filter followed by 
    a probabilistic Hough transform.
    """
    
    def extract_lines(self, image):
        """
        Extracts the line segments found for the given image
        
        :Returns:
            A [y x 4] or [y x 5] array of y lines found given as
            (x1, y1, x2, y2) or (x1, y1, x2, y2, width)
        """
        opencvimg = image.opencvimage
        gray = cv2.cvtColor(opencvimg, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (0,0), 1)
        edges = cv2.Canny(blur, 20, 70)
        maxLineGap = 10
        minLineLength = numpy.array([])
        return cv2.HoughLinesP(edges,1,numpy.pi/180,20,minLineLength,maxLineGap).squeeze()    

class LSDLineExtractorMixin(object):
    """
    Ported from https://github.com/seanbell/opensurfaces/blob/master/server/photos/tasks.py#L136
    Sean Bell, Paul Upchurch, Noah Snavely, Kavita Bala
    OpenSurfaces: A Richly Annotated Catalog of Surface Appearance
    ACM Transactions on Graphics (SIGGRAPH 2013)
    """
    def _get_lsd_dir(self):
        """
        Private - the directory where the LSD matlab code lives
        """
        return os.path.join(_get_topdir(), 'thirdParty', 'vpdetection', 'lsd-1.5')
    
    def extract_lines(self, image):
        """
        Extracts the line segments found for the given image
        
        :Returns:
            A [y x 4] or [y x 5] array of y lines found given as
            (x1, y1, x2, y2) or (x1, y1, x2, y2, width)
        """
        vpdetection_dir = self._get_lsd_dir()
        tempdir = tempfile.mkdtemp(prefix='lsd-line-extract-')
        results = None
        try:
            # save image to local tmpdir
            localname = os.path.join(tempdir, 'image.jpg')
            image.save(localname)
    
            # detect line segments using LSD (Grompone, G., Jakubowicz, J., Morel,
            # J. and Randall, G. (2010). LSD: A Fast Line Segment Detector with a
            # False Detection Control. IEEE Transactions on Pattern Analysis and
            # Machine Intelligence, 32, 722.)
            linesname = os.path.join(tempdir, 'lines.txt')
            matlab_command = ";".join([
                "try",
                "lines = lsd(double(rgb2gray(imread('%s'))))" % localname,
                "save('%s', 'lines', '-ascii', '-tabs')" % linesname,
                "catch",
                "end",
                "quit",
            ])
            cmd = "matlab -nodisplay -nosplash -nodesktop -r \"%s\"" % matlab_command
            print("[Running] %s" % cmd)
            subprocess.check_call(args=shlex.split(cmd), cwd=vpdetection_dir)
            
            # finally, collect results as a numpy array
            # so it can be passed to arbitrary subsequent vp estimators
            rows = None
            with open(linesname) as fobj:
                rows = fobj.readlines()
            results = numpy.array([[float(entry) for entry in row.split()] for row in rows])
            
        finally:
            shutil.rmtree(tempdir)
        return results

class JLinkageVanishingPointEstimator(AbstractVanishingPointEstimator, LSDLineExtractorMixin):
    """
    Ported from https://github.com/seanbell/opensurfaces/blob/master/server/photos/tasks.py#L136
    Sean Bell, Paul Upchurch, Noah Snavely, Kavita Bala
    OpenSurfaces: A Richly Annotated Catalog of Surface Appearance
    ACM Transactions on Graphics (SIGGRAPH 2013)
    """    
    def __init__(self, image):
        super(JLinkageVanishingPointEstimator, self).__init__(image)
        
        self._projective_vanishing_points = []
    
    def get_projective_vanishing_points(self):
        return self._projective_vanishing_points
    
    def _get_matlab_code(self):
        """
        The path of the vpdetection matlab package
        """
        return os.path.join(_get_topdir(), 'thirdParty', 'vpdetection', 'matlab')
    
    @property
    def fov(self):
        return 60 # TODO... how can we get this, esp if no image tag with this info?
    
    @property
    def aspect_ratio(self):
        return (float(self.image.width) /
                float(self.image.height))
    
    def line_cluster_length(self, lines):
        return sum(
            math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            for x1, y1, x2, y2 in lines
        )
        
    def normalized(self, v):
        """ Normalize an nd vector """
        norm = numpy.linalg.norm(v)
        if norm:
            return numpy.array(v) / norm
        else:
            return v
    
    def normalized_cross(self, a, b):
        """ 3D cross product """
        return self.normalized(numpy.cross(a, b))
        
    def vanishing_point_to_vector(self, v):
        """ Return the 3D unit vector corresponding to a vanishing point
        (specified in normalized coordinates) """
        dim = max(self.image.width, self.image.height)
        focal_y = 0.5 * dim / (self.image.height *
                                        math.tan(math.radians(self.fov / 2)))
        return self.normalized((
            (v[0] - 0.5) * self.aspect_ratio,
            0.5 - v[1],  # flip y coordinate
            -focal_y
        ))
        
    def vector_to_vanishing_point(self, v):
        """ Return the 2D vanishing point (in normalized coordinates)
        corresponding to 3D vector """
        dim = max(self.image.width, self.image.height)
        focal_y = 0.5 * dim / (self.image.height *
                                        math.tan(math.radians(self.fov / 2)))
        if abs(v[2]) < 1e-10:
            return (
                0.5 + v[0] * (focal_y / self.aspect_ratio) * 1e10,
                0.5 - v[1] * focal_y * 1e10,  # flip y coordinate
            )
        else:
            return (
                0.5 + v[0] * (focal_y / self.aspect_ratio) / (-v[2]),
                0.5 - v[1] * focal_y / (-v[2]),  # flip y coordinate
            )
        
    def vectors_to_points(self, image, vectors):
        width, height = image.width, image.height
        points = [self.vector_to_vanishing_point(v) for v in vectors]
        return [(p[0] * width, p[1] * height) for p in points]        
    
    def homo_line(self, a, b):
        """
        Return the homogenous equation of a line passing through a and b,
        i.e. [ax, ay, 1] cross [bx, by, 1]
        """
        return (a[1] - b[1], b[0] - a[0], a[0] * b[1] - a[1] * b[0])
    
    def line_residual(self, l, p):
        """ Returns the distance between an endpoint of l and the line from p to
        the midpoint of l.  Based on Equation (2) of [Tardif, ICCV 2009
        http://www-etud.iro.umontreal.ca/~tardifj/fichiers/Tardif_ICCV2009.pdf] """
        x1, y1, x2, y2 = l
        midpoint = (0.5 * (x1 + x2), 0.5 * (y1 + y2))
        e = self.homo_line(p, midpoint)
        d = max(1e-4, e[0] ** 2 + e[1] ** 2)
        return (e[0] * x1 + e[1] * y1 + e[2]) / math.sqrt(d)
    
    def sphere_to_unit(self, v):
        """ Convert (theta, phi) to (x, y, z) """
        sin_theta = math.sin(v[0])
        cos_theta = math.cos(v[0])
        return (sin_theta * math.cos(v[1]),
                sin_theta * math.sin(v[1]),
                cos_theta)
    
    def unit_to_sphere(self, v):
        """ Convert (x, y, z) to (theta, phi) """
        return (math.acos(v[2]), math.atan2(v[1], v[0]))
    
    # unpack vectors from current solution (x)
    def unpack_x(self, x):
        return [
            numpy.array(self.sphere_to_unit(x[i:i + 2]))
            for i in xrange(0, len(x), 2)
        ]
    
    # pack vectors into solution vector (x)
    def pack_x(self, vecs):
        x = []
        for v in vecs:
            x += list(self.unit_to_sphere(v))
        return x
    
    def abs_dot(self, a, b):
        """ Return :math:`|a \dot b|` """
        return abs(numpy.dot(a, b))
    
    def estimate(self):
        
        # algorithm parameters
        max_em_iter = 0  # if 0, don't do EM
        min_cluster_size = 10
        min_line_len2 = 4.0
        residual_stdev = 0.75
        max_clusters = 8
        outlier_weight = 0.2
        weight_clamp = 0.1
        lambda_perp = 1.0
        verbose = False
        
        width, height = self.image.width, self.image.height
        
        # estimate line segments in image
        lines = self.extract_lines(self.image)
        
        vpdetection_dir = self._get_matlab_code()       
         
        tempdir = tempfile.mkdtemp()
        try:
            linesname = os.path.join(tempdir, 'lines.txt')
            with open(linesname, 'w') as fobj:
                fobj.write(os.linesep.join('\t'.join(str(entry) for entry in row) for row in lines))

            # cluster lines using J-linkage (Toldo, R. and Fusiello, A. (2008).
            # Robust multiple structures estimation with J-Linkage. European
            # Conference on Computer Vision(ECCV), 2008.)
            # and (Tardif J.-P., Non-iterative Approach for Fast and Accurate
            # Vanishing Point Detection, 12th IEEE International Conference on
            # Computer Vision, Kyoto, Japan, September 27 - October 4, 2009.)
            clustername = os.path.join(tempdir, 'clusters.txt')
            cmd = './vpdetection %s %s' % (linesname, clustername)
            subprocess.check_call(
                args=shlex.split(cmd),
                cwd=vpdetection_dir)
    
            # collect line clusters
            clusters_dict = {}
            all_lines = []
            for row in open(clustername, 'r').readlines():
                cols = row.split()
                idx = int(cols[4])
                line = [float(f) for f in cols[0:4]]
    
                # discard small lines
                x1, y1, x2, y2 = line
                len2 = (x1 - x2) ** 2 + (y2 - y1) ** 2
                if len2 < min_line_len2:
                    continue
    
                if idx in clusters_dict:
                    clusters_dict[idx].append(line)
                    all_lines.append(line)
                else:
                    clusters_dict[idx] = [line]
    
        finally:
            shutil.rmtree(tempdir)
        
        # discard invalid clusters and sort by cluster length
        thresh = 3 if max_em_iter else min_cluster_size
        clusters = filter(lambda x: len(x) >= thresh, clusters_dict.values())
        clusters.sort(key=self.line_cluster_length, reverse=True)
        if max_em_iter and len(clusters) > max_clusters:
            clusters = clusters[:max_clusters]
        print("Using %s clusters and %s lines" % (len(clusters), len(all_lines)))
        if not clusters:
            print("Not enough clusters")
            return
        
        # Solve for optimal vanishing point using V_GS in 5.2 section of
        # (http://www-etud.iro.umontreal.ca/~tardif/fichiers/Tardif_ICCV2009.pdf).
        # where "optimal" minimizes algebraic error.
        vectors = []
        for lines in clusters:
            # Minimize 'algebraic' error to get an initial solution
            A = numpy.zeros((len(lines), 3))
            for i in xrange(0, len(lines)):
                x1, y1, x2, y2 = lines[i]
                A[i, :] = [y1 - y2, x2 - x1, x1 * y2 - y1 * x2]
            __, __, VT = numpy.linalg.svd(A, full_matrices=False, compute_uv=True)
            if VT.shape != (3, 3):
                raise ValueError("Invalid SVD shape (%s)" % VT.size)
            x, y, w = VT[2, :]
            p = [x / w, y / w]
            v = self.vanishing_point_to_vector(
                (p[0] / width, p[1] / height)
            )
            vectors.append(v)
        
        # EM
        if max_em_iter:
    
            # complete orthonormal system
            if len(vectors) >= 2:
                vectors.append(self.normalized_cross(vectors[0], vectors[1]))
    
            ### EM refinement ###
    
            x0 = None
            x_opt = None
            exp_coeff = 0.5 / (residual_stdev ** 2)
    
            num_weights_nnz = 0
            num_weights = 0
    
            for em_iter in xrange(max_em_iter):
    
                ### E STEP ###
    
                # convert back to vanishing points
                points = self.vectors_to_points(self.image, vectors)
    
                # last column is the outlier cluster
                weights = numpy.zeros((len(all_lines), len(vectors) + 1))
    
                # estimate weights (assume uniform prior)
                for i_p, p in enumerate(points):
                    weights[:, i_p] = [self.line_residual(l, p) for l in all_lines]
                weights = numpy.exp(-exp_coeff * numpy.square(weights))
    
                # outlier weight
                weights[:, len(points)] = outlier_weight
    
                # normalize each row (each line segment) to have unit sum
                weights_row_sum = weights.sum(axis=1)
                weights /= weights_row_sum[:, numpy.newaxis]
    
                # add sparsity
                weights[weights < weight_clamp] = 0
                num_weights += weights.size
                num_weights_nnz += numpy.count_nonzero(weights)
    
                # check convergence
                if (em_iter >= 10 and len(x0) == len(x_opt) and
                        numpy.linalg.norm(numpy.array(x0) - numpy.array(x_opt)) <= 1e-5):
                    break
    
                # sort by weight
                if len(vectors) > 1:
                    vectors_weights = [
                        (v, weights[:, i_v].sum()) for i_v, v in enumerate(vectors)
                    ]
                    vectors_weights.sort(key=lambda x: x[1], reverse=True)
                    vectors = [x[0] for x in vectors_weights]
    
                ### M STEP ###
    
                # objective function to minimize
                def objective_function(x, *args):
                    cur_vectors = self.unpack_x(x)
                    cur_points = self.vectors_to_points(self.image, cur_vectors)
    
                    # line-segment errors
                    residuals = [
                        weights[i_l, i_p] * self.line_residual(all_lines[i_l], p)
                        for i_p, p in enumerate(cur_points)
                        for i_l in numpy.flatnonzero(weights[:, i_p])
                    ]
    
                    # penalize deviations from 45 or 90 degree angles
                    if lambda_perp:
                        residuals += [
                            lambda_perp * math.sin(4 * math.acos(self.abs_dot(v, w)))
                            for i_v, v in enumerate(cur_vectors)
                            for w in cur_vectors[:i_v]
                        ]
    
                    return residuals
    
                # slowly vary parameters
                t = min(1.0, em_iter / 20.0)
    
                # vary tol from 1e-2 to 1e-6
                tol = math.exp(math.log(1e-2) * (1 - t) + math.log(1e-6) * t)
    
                from scipy.optimize import leastsq
                x0 = self.pack_x(vectors)
                x_opt, __ = leastsq(objective_function, x0, ftol=tol, xtol=tol)
                vectors = self.unpack_x(x_opt)
    
                ### BETWEEN ITERATIONS ###
    
                if verbose:
                    print 'EM: %s iters, %s clusters, weight sparsity: %s%%' % (
                        em_iter, len(vectors), 100.0 * num_weights_nnz / num_weights)
                    print 'residual: %s' % sum(y ** 2 for y in objective_function(x_opt))
    
                # complete orthonormal system if missing
                if len(vectors) == 2:
                    vectors.append(self.normalized_cross(vectors[0], vectors[1]))
    
                # merge similar clusters
                cluster_merge_dot = math.cos(math.radians(t * 20.0))
                vectors_merged = []
                for v in vectors:
                    if (not vectors_merged or
                            all(self.abs_dot(v, w) < cluster_merge_dot for w in vectors_merged)):
                        vectors_merged.append(v)
                if verbose and len(vectors) != len(vectors_merged):
                    print 'Merging %s --> %s vectors' % (len(vectors), len(vectors_merged))
                vectors = vectors_merged
    
            residual = sum(r ** 2 for r in objective_function(x_opt))
            print 'EM: %s iters, residual: %s, %s clusters, weight sparsity: %s%%' % (
                em_iter, residual, len(vectors), 100.0 * num_weights_nnz / num_weights)
    
            # final points
            points = self.vectors_to_points(self.image, vectors)
    
            # sanity checks
            assert len(vectors) == len(points)
    
            # re-assign clusters
            clusters_points = [([], p) for p in points]
            line_map_cluster = numpy.argmax(weights, axis=1)
            for i_l, l in enumerate(all_lines):
                i_c = line_map_cluster[i_l]
                if i_c < len(points):
                    clusters_points[i_c][0].append(l)
    
            # throw away small clusters
            clusters_points = filter(
                lambda x: len(x[0]) >= min_cluster_size, clusters_points)
    
            # reverse sort by cluster length
            clusters_points.sort(
                key=lambda x: self.line_cluster_length(x[0]), reverse=True)
    
            # split into two parallel arrays
            clusters = [cp[0] for cp in clusters_points]
            points = [cp[1] for cp in clusters_points]
    
        else:  # no EM
    
            for i_v, lines in enumerate(clusters):
                def objective_function(x, *args):
                    p = self.vectors_to_points(self.image, self.unpack_x(x))[0]
                    return [self.line_residual(l, p) for l in lines]
                from scipy.optimize import leastsq
                x0 = self.pack_x([vectors[i_v]])
                x_opt, __ = leastsq(objective_function, x0)
                vectors[i_v] = self.unpack_x(x_opt)[0]
    
            # delete similar vectors
            cluster_merge_dot = math.cos(math.radians(20.0))
            vectors_merged = []
            clusters_merged = []
            for i_v, v in enumerate(vectors):
                if (not vectors_merged or
                        all(self.abs_dot(v, w) < cluster_merge_dot for w in vectors_merged)):
                    vectors_merged.append(v)
                    clusters_merged.append(clusters[i_v])
            vectors = vectors_merged
            clusters = clusters_merged
    
            # clamp number of vectors
            if len(clusters) > max_clusters:
                vectors = vectors[:max_clusters]
                clusters = clusters[:max_clusters]
    
            points = self.vectors_to_points(self.image, vectors)
    
        # normalize to [0, 0], [1, 1]
        clusters_normalized = [[
            [l[0] / width, l[1] / height, l[2] / width, l[3] / height]
            for l in lines
        ] for lines in clusters]
    
        points_normalized = [
            (x / width, y / height) for (x, y) in points
        ]
       
        # get things back into the common format
        # e.g. vanishing points in image pixels, which we conveniently already have
        # for now, just take the first 3...
        self._projective_vanishing_points = numpy.array(points[:3], dtype='float64')
    
        # compute focal length as in "Camera calibration using 2 or 3 vanishing points" (Orghidan et al. 2012)
        self.principal_point = (width / 2.0, height / 2.0)
        vps = self._projective_vanishing_points
        vpmin = numpy.linalg.norm(vps, axis=1).argmin()
        vpsecond = 0 if vpmin == 1 else 1
        
        self.focal_length = math.sqrt(numpy.linalg.norm((self.principal_point-vps[vpmin])*(vps[vpsecond]-self.principal_point)))

class ZhangVanishingPointEstimator(AbstractVanishingPointEstimator, LSDLineExtractorMixin):
    """
    Based on 
    Lilian Zhang, Huimin Lu, Reinhard Koch, 
    Vanishing Point Estimation and Line Classification in a Manhattan World with a Unifying Camera Model,  
    submitted to IJCV.
    Using Matlab code from http://www.mip.informatik.uni-kiel.de/tiki-download_file.php?fileId=2105
    """
    
    def _get_patch_file(self):
        """
        Private - the path to the patch file to apply
        """
        return os.path.join(_get_topdir(), 'thirdParty', 'VanishingPointMatlabCode_patch.diff')
    
    def _get_matlab_code(self):
        """
        Private - the path to the matlab code directory
        """
        return os.path.join(_get_topdir(), 'thirdParty', 'VanishingPointMatlabCode')
    
    def estimate(self):
        # extract lines and get in format readable by matlab lines may or may not have width at the end
        lines = self.extract_lines(self.image)
        result_lines = []
        try:
            for i, (x1, y1, x2, y2, width) in enumerate(lines):
                result_lines.append("{0}    {1}    {2}    {3}    {4}".format(i+1, x1, y1, x2, y2))
        except ValueError:
            for i, (x1, y1, x2, y2) in enumerate(lines):
                result_lines.append("{0}    {1}    {2}    {3}    {4}".format(i+1, x1, y1, x2, y2))
        
        orig_dir = os.getcwd()
        # create a temporary working directory
        tempdir = tempfile.mkdtemp(prefix="zhang-vanishing-")
        logging.debug("Created temporary directory at '{0}'".format(tempdir))
        
        try:
            # copy the matlab vanishing point estimation source and apply patch
            matlab_code_dir = self._get_matlab_code()
            matlab_code_base = os.path.basename(matlab_code_dir) 
            matlab_tmp_dir = os.path.join(tempdir, matlab_code_base)
    
            shutil.copytree(matlab_code_dir, matlab_tmp_dir)
            os.chdir(os.path.join(tempdir, matlab_tmp_dir))
            with open(os.devnull, "w") as f:
                subprocess.check_call(shlex.split('patch -p1 -i {0}'.format(self._get_patch_file())), stdout=f)
            
            # put the text/image files in the right places so that the matlab script knows where to find the data it needs
            matlab_run_dir = os.path.join(matlab_tmp_dir, 'PerspectiveCamera')
            matlab_example_dir = os.path.join(matlab_run_dir,'ExampleData','ECD')
            matlab_image_dir = os.path.join(matlab_example_dir,'Images')
            if not os.path.exists(matlab_image_dir):
                os.makedirs(matlab_image_dir)
            matlab_extract_dir = os.path.join(matlab_example_dir,'ExtractedLines')
            if not os.path.exists(matlab_extract_dir):
                os.makedirs(matlab_extract_dir)
            
            self.image.save(os.path.join(matlab_image_dir, 'New001.jpg'))
            with open(os.path.join(matlab_extract_dir, 'lines001.txt'),'w') as f:
                f.write(os.linesep.join(result_lines))
            with open(os.path.join(matlab_example_dir, 'imageName.list'), 'w') as f:
                f.write('./ExampleData/ECD/Images/New001.jpg')
            with open(os.path.join(matlab_example_dir, 'lineFile.list'), 'w') as f:
                f.write('./ExampleData/ECD/ExtractedLines/lines001.txt')
            
            # run the matlab script and collect the output
            cmd = "matlab -nodisplay -nosplash -nodesktop -r \"try;run('{0}');catch;end;quit\""
            cmd = cmd.format(os.path.join(matlab_run_dir, 'mainVPandFocalEstimation.m'))
            print("[Running] %s" % cmd)

            # TODO: may want to handle for certain invalid output, e.g. nans or infs should matlab error
            output = subprocess.check_output(shlex.split(cmd))
            
            # finally, parse the output
            if '<START OUTPUT>' in output and '<END OUTPUT>' in output:
                output = output.split('<START OUTPUT>', 1)[-1].split('<END OUTPUT>', 1)[0]
                pat = 'ID =\s?(?P<id>\d+),.*focal =\s?(?P<focal>[0-9e\-\.]+),'
                match = re.search(pat, output)
                self.focal_length = float(match.group('focal'))
                
                pp_output = output.split('principalPoint =')[-1].strip()
                pp_output = tuple(float(i) for i in pp_output.split())
                self.principal_point = pp_output
                
                vp_output = output.split('unitVanishing =')[-1].strip().split(os.linesep)
                self._vanishing_points = numpy.zeros((3,3))
                for i in range(3):
                    # store a new x,y,z vanishing point on each row (not column)
                    self._vanishing_points[:,i] = [float(x) for x in vp_output[i].split()]
                
            else:
                logging.warn("Matlab errored with the following output:")
                print(output)
                raise ValueError("Error running matlab!")
    
        finally:
            shutil.rmtree(tempdir)
            os.chdir(orig_dir)
        
    
    