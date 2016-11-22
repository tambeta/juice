
import sys

import numpy as np

class TileClassifier:
    TT_CONCAVE  = np.array([
        [False, True, True],
        [True, True, True],
        [True, True, True]])   
    TT_CONVEX   = np.array([
        [None, False, None],
        [False, True, True],
        [None, True, True]])
    TT_STRAIGHT   = np.array([
        [None, False, None],
        [True, True, True],
        [True, True, True]])
    
    def __init__(self):
        pass
        
        #print(tt_concave, "\n", tt_concave.dtype)

    def _remove_slivers(self, flayer, m):
        
        """ First normalization pass: remove "slivers", i.e. width 1 terrain
        portions.
        """
        
        it = np.nditer(m, flags=["multi_index"])
        
        while (not it.finished):
            v = int(it[0])
            p = it.multi_index
            x = p[1]
            y = p[0]
            #yield (x + p[1], y + p[0], v)

            x_axis_empty = 0
            y_axis_empty = 0

            def tally_slivers(cx, cy):
                nonlocal x_axis_empty, y_axis_empty
                
                if (abs(cx - x) == 1 and not m[cy, cx]):
                    x_axis_empty += 1
                elif (abs(cy - y) == 1 and not m[cy, cx]):
                    y_axis_empty += 1
            
            self._foreach_edge_neighbor(tally_slivers, x, y)
            
            if (x_axis_empty >= 2 or y_axis_empty >=2):
                n_removed += 1
                m[y, x] = False

            it.iternext()        
        
        print("Sliver removal: {}".format(n_removed))
        
        #for (x, y, v) in self.get_points(skip_zero=False):
        #    if (v > 0):
        #        continue
        #    
        #    x_axis_water = 0
        #    y_axis_water = 0
        #    
        #    def tally_slivers(cx, cy):
        #        nonlocal x_axis_water, y_axis_water
        #        
        #        if (abs(cx - x) == 1 and m[cy, cx] != 0):
        #            x_axis_water += 1
        #        elif (abs(cy - y) == 1 and m[cy, cx] != 0):
        #            y_axis_water += 1
        #    
        #    self._foreach_edge_neighbor(tally_slivers, x, y)
        #    
        #    if (x_axis_water >= 2 or y_axis_water >=2):
        #        n_removed += 1
        #        m[y, x] = 0xFE
        #
        #print("Normalize pass: {} tiles removed".format(n_removed))
        #
        #if (n_removed > 0):
        #    self._normalize()        
    
    def normalize(self, flayer):
        
        """ Normalize a GameFieldLayer. """

        orig_m = flayer.matrix
        m = flayer.matrix == 0
        dim = m.shape[0]        
        
        #self._remove_slivers(flayer, m)
        
        def rotate_matrix(m):
            return np.fliplr(np.transpose(m))        
            
        def compare_ternary_matrices(a, b):
            ai = a.flat
            bi = b.flat
            equal = True
            
            try:
                while(True):
                    av = next(ai)
                    bv = next(bi)
                    
                    if (av == None or bv == None):
                        continue
                    elif (av != bv):
                        equal = False
                        break
            except StopIteration:
                pass
            
            return equal

        def classify_tile(x, y, tilespec):
            nhood = m[y-1:y+2, x-1:x+2]
            i = 4 # rotate 4 times
            
            while (i > 0):
                if (compare_ternary_matrices(tilespec, nhood)):
                    orig_m[y-1, x-1] = 0xFF
                    break
                tilespec = rotate_matrix(tilespec)
                i -= 1
        
        # Expand matrix over the borders
        
        m = np.vstack((m[0], m))
        m = np.vstack((m, m[-1]))
        m = np.hstack((np.expand_dims(m[:,0], axis=1), m))
        m = np.hstack((m, np.expand_dims(m[:,-1], axis=1)))
        
        # Classify tiles of matrix
       
        for tilespec in (self.TT_CONCAVE, self.TT_CONVEX, self.TT_STRAIGHT):
        #for tilespec in (self.TT_CONCAVE):
            for x in range(1, dim):
                for y in range(1, dim):
                    classify_tile(x, y, tilespec)
        
