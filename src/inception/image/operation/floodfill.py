"""
Floodfill operation implementation
"""
import math, functools
import numpy
from .base import Operation
from ..image import Image
from ..analyze import detect_bg

class TargetNotFoundError(Exception):
    """
    An internal use exception that indicates the lack of a valid pixel from a selection operation
    e.g. see `FloofillOperation._spiral()`
    """
    pass

class FloodfillOperation(Operation):
    """
    A floodfill operation implementing a more or less generic floodfill operation
    """
    def __init__(self, image, keycolor=None, channel='a', replacevalue=0.0, tol=.04, seedpixel=None):
        """
        Initializes a floodfill operation with all the needed parameters
        
        :Parameters:
            image : `Image`
                The image object we would like to operate on
            keycolor : `tuple`
                The color to key out in the floodfill. If `None` specified, this is detected
                automatically. Default=None
                [TODO: should also support lists and `numpy.ndarray` but currently untested]
            channel : `basestring`
                The channel we wish to be replaced with `replacevalue` for all pixels contiguous
                with the seeded pixel. Valid values are 'r','g','b', and 'a'. Default='a'
            replacevalue : `float`
                The value to replace the given channel with for the pixels that match the keycolor
                and are contiguous with the seeded pixel. Default=0.0
            tol : `float`
                The threshold tolerance to allow in the difference of squares between pixels contiguous with the 
                seed pixel and the key color. The the difference of squared norms exceeds tol, the pixel is not 
                treated as equal for the purpose of floodfilling. Default=.04
            seedpixel : `tuple`
                Any iterable of (row, col) indices for where to begin the floodfill. Note that this is assumed
                to be the same as keycolor.  If not, the floodfill may end up being a no-op.
                If seedpixel is None, the seed is determined procedurally by spiraling inward clockwise from the
                upper righthand pixel of the image. Default=None
                
        """
        self.image = image
        self.channel = 'rgba'.index(channel.lower())
        self.keycolor = keycolor
        self.replacevalue = replacevalue
        self.tol = tol
        self.seedpixel = None
        
        self.opimage = None
            
    def run(self):            
        """
        Runs the floodfill on this operation's image

        :Returns:
            A copy of the input image after floodfill has been applied
            
        :Rtype:
            `Image`
        """
        image = self.image.clone()
        # get dims
        rows, cols = image.shape[:2]
        if len(image.shape) > 2:
            chans = image.shape[2]
        else:
            image = image.reshape(rows,cols,1)
            chans = 1
        
        if 0 < self.channel < 3 and chans < 3:
            # need to convert to RGB
            image.to_rgb()   
        elif self.channel == 3 and chans < 4:
            # need to convert to RGBA
            image.to_rgba()
         
        # convenient to put here though because this happens
        # after we've reshaped the image as necessary
        # so the keycolor num channels should match
        if self.keycolor is None:
            self.keycolor = detect_bg(image)
        
        # find a pixel with the keycolor on the edge to start
        if self.seedpixel is None:
            try:
                first_index = self._spiral(image, functools.partial(self._floatIterEquals, self.keycolor))
            except TargetNotFoundError:
                # there are no pixels of the given color in the whole image, so we're done
                return
        else:
            first_index = self.seedpixel
                
        # so we don't run up against python's recursion limits, lets do the floodfill with a set (order doesn't matter anyways)
        pixels = set([first_index])
        
        # TODO: inline floodfill as the all python implementation is rather slow
        # e.g.
        # see http://docs.scipy.org/doc/scipy/reference/tutorial/weave.html#catalog-search-paths-and-the-pythoncompiled-variable
        while pixels:
            row, col = pixels.pop()
            
            if not self._floatIterEquals(image[row, col, ...], self.keycolor) or \
                    self._floatEquals(image[row, col, self.channel], self.replacevalue, tol=1e-9):
                # base case: on an already changed pixel or a border pixel
                continue 
                        
            # if we get here, this pixel needs to be changed (it is the keycolor) and hasn't been
            # changed already
            image.data[row, col, self.channel] = self.replacevalue
                        
            # "recurse" to all surrounding pixels
            if row < rows - 1:
                pixels.add((row+1, col))
            if row > 0:
                pixels.add((row-1, col))
            if col < cols - 1:
                pixels.add((row, col+1))
            if col > 0:
                pixels.add((row, col-1))
        self.opimage = image
        return image
        
    def _floatIterEquals(self, first, second, tol=None):
        """
        Private method to determine whether two iterables of floats are equal
        within some tolerance.  
        
        :Parameters:
            first : `numpy.ndarray`
                Any iterable to compare against second
            second : `numpy.ndarray`
                Any iterable to compare against first
            tol : `float`
                The threshold at which each float is considered equal
                Defaults to the tolerance passed into the operation.
                
        :Returns:
            True if the two iterables are considered equal with the given tolerance, False
            otherwise.
            
        :Rtype:
            `bool`
        """
        if tol is None:
            tol = self.tol
        return all([self._floatEquals(first[i], second[i], tol=tol) for i in range(len(first))]) 

    def _floatEquals(self, first, second, tol=None):
        """
        Private method to determine whether 2 floats are equal within some tolerance
        
        :Parameters:
            first : `float`
                The first float to compare
            second : `float`
                The second float ot compare
            tol : `float`
                The threshold at which first and second are considered equal. Defaults to the tolerance
                passed into the operation
                
        :Returns:
            True if the floats are considered equal within the given tolerance, False otherwise
            
        :Rtype:
            `bool`
        """
        if tol is None:
            tol = self.tol
        return abs(first - second) <= tol
                 
    def _spiral(self, matrix, func):
        """
        Private helper method to iterate through all cells of an image starting at the upper-left 
        pixel and apply the given function to each cell, passing in the value at that cell.
        Returns the first index of the matrix whose value evaluates to True
        
        :Parameters:
            matrix : `numpy.ndarray`
                A matrix of at least 2 dimensions
            function : `function` or `instancemethod`
                A function to run on each cell. It should take one parameter, the value at the cell.
                Should return True for a pixel whose indices we wish to capture
                
        :Returns:
            The indices of the first cell in the matrix for which the function evaluated to True.
            The indices are returned as a tuple of (row, col)
        
        :Rtype:
            `tuple`
        """
        rows, cols = matrix.shape[:2]
        row_jumps, col_jumps = rows-1, cols
        
        row = 0
        col = -1
        row_diff = 0
        col_diff = 1
        
        row_counter = 0
        col_counter = 0
        
        for _ in range(rows * cols):
            
            # update row, col
            row += row_diff
            col += col_diff
            
            # test
            if func(matrix[row, col, ...]):
                # short-circuit
                return (row, col)
            
            # update counters and traversal direction
            row_counter += abs(row_diff)
            col_counter += abs(col_diff)
            
            if row_diff and row_counter >= row_jumps:
                row_jumps -= 1
                row_counter = 0
                col_diff = -1 if row_diff > 0 else 1
                row_diff = 0
            elif col_diff and col_counter >= col_jumps:
                col_jumps -= 1
                col_counter = 0
                row_diff = 1 if col_diff > 0 else -1
                col_diff = 0
            
        raise TargetNotFoundError("No pixels match target function")
        

