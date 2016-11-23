
import numpy as np

class TileClassifier:

    """ A class for converting a GameFieldLayer into the space of possible
    tiles of the standard tileset and removing illegal tiles, thereby
    normalizing the field.
    """

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

    def __init__(self, flayer, rev=False):

        """ Constructor. bool_matrix is a boolean matrix representing
        "interesting" (the terrain) and "uninteresting" tiles. By default, all
        nonzero values are considered interesting. Passing true for rev reverses
        this condition.
        """

        self.flayer = flayer
        self.bool_matrix = (flayer.matrix == 0 if rev
            else flayer.matrix != 0)
        self.dim = flayer.matrix.shape[0]

    def normalize(self):

        """ Normalize the GameFieldLayer, i.e. remove all illegal tiles. Remove
        slivers first, then mark any tiles representable with the standard tile
        set. Repeat until convergence.
        """

        m = self.bool_matrix
        dim = self.dim

        def sliver_spec(m, x, y, nhood):

            """ Callable tilespec defining "slivers" i.e. terrain portions of
            width 1.
            """

            if ((not nhood[0, 1] and not nhood[2, 1]) or (not nhood[1, 0] and not nhood[1, 2])):
                return True
            return False

        while (True):
            n = 0
            n += self._apply_tilespecs(m, sliver_spec)
            n += self._apply_tilespecs(m, self.TT_CONCAVE, self.TT_CONVEX, self.TT_STRAIGHT)

            if (n <= 0):
                break

    def _apply_tilespecs(self, m, *tilespecs):

        """ Apply a list of tilespecs, i.e. remove illegal tiles. """
        
        dim = self.dim
        ext_m = self._extend_matrix(m)
        mask = np.full((dim, dim), True, dtype=bool)

        for tilespec in (tilespecs):
            for x in range(1, dim+1):
                for y in range(1, dim+1):
                    cls = self._classify_tile(ext_m, mask, x, y, tilespec)
                    if (cls is not None): mask[y-1, x-1] = cls

        m[mask] = False
        self.flayer.matrix[mask] = 0xFF
        #self.flayer.matrix[np.invert(mask)] = 0xFF
        #self.flayer.matrix[mask] = 1 # TODO: dependent on rev

        return np.count_nonzero(mask)

    def _classify_tile(self, m, mask, x, y, tilespec):

        """ Classify a single tile. tilespec may be a valid ternary matrix which
        is rotated into all possible positions and compared with the tile's
        immediate neighborhood _or_ a callable.
        """

        nhood = m[y-1:y+2, x-1:x+2]
        i = 4                       # rotate 4 times

        if (not mask[y-1, x-1]):    # already classed as OK, return
            return False
        elif (not m[y, x]):         # non-interesting tile is OK, return
            return False
        elif (nhood.all() == True): # interior terrain tile is OK, return
            return False

        if (callable(tilespec)):
            return tilespec(m, x, y, nhood)

        while (i > 0):
            if (self._is_ternary_matrix_equal(tilespec, nhood)):
                return False
            tilespec = self._rotate_matrix(tilespec)
            i -= 1

    def _rotate_matrix(self, m):
        return np.fliplr(np.transpose(m))

    def _is_ternary_matrix_equal(self, a, b):

        """ Compare two ternary matrices for equality. None values are
        considered equal to any value.
        """

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

    def _extend_matrix(self, m):

        """ Expand a tile matrix over the borders by one: all values are
        continued further, i.e. terrain continues to terrain and non-terrain
        continues to non-terrain. The result is a matrix with 2 added to both
        dimensions.
        """

        m = np.vstack((m[0], m))
        m = np.vstack((m, m[-1]))
        m = np.hstack((np.expand_dims(m[:,0], axis=1), m))
        m = np.hstack((m, np.expand_dims(m[:,-1], axis=1)))

        return m

