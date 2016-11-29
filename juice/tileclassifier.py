
import numpy as np

from logging import debug, info, warning, error
from juice.gamefieldlayer import GameFieldLayer

class TileClassifier:

    """ A class for converting a GameFieldLayer into the space of possible
    tiles of the standard tileset and removing illegal tiles, thereby
    normalizing the field.
    """

    TS_CONCAVE  = np.array([
        [True, True, True],
        [True, True, True],
        [False, True, True]])
    TS_CONVEX   = np.array([
        [None, False, None],
        [True, True, False],
        [True, True, None]])
    TS_STRAIGHT   = np.array([
        [None, False, None],
        [True, True, True],
        [True, True, True]])

    # Note: Rotated variations of the same types are expected to be
    # successive integers.

    TT_EMPTY        = 0
    TT_NA           = 1
    TT_SOLID        = 2

    TT_CONCAVE_NE   = 11
    TT_CONCAVE_SE   = 12
    TT_CONCAVE_SW   = 13
    TT_CONCAVE_NW   = 14

    TT_CONVEX_NE    = 15
    TT_CONVEX_SE    = 16
    TT_CONVEX_SW    = 17
    TT_CONVEX_NW    = 18

    TT_STRAIGHT_N   = 19
    TT_STRAIGHT_E   = 20
    TT_STRAIGHT_S   = 21
    TT_STRAIGHT_W   = 22

    def __init__(self, flayer, rev=False):

        """ Constructor. cls_matrix is a matrix representing "interesting" (the
        terrain) and "uninteresting" tiles at first (a boolean matrix), later
        filled with tile type IDs. By default, all nonzero values are considered
        interesting. Passing true for rev reverses this condition.
        """

        assert(self.TT_EMPTY == 0)

        cm = np.full(flayer.matrix.shape, self.TT_EMPTY, dtype=np.uint8)
        cm[flayer.matrix == 0 if rev else flayer.matrix != 0] = self.TT_NA

        self._cls_matrix = cm
        self._flayer = flayer
        self._dim = flayer.matrix.shape[0]
        self._rev = rev

    def classify(self):

        """ Classify the input GameFieldLayer, i.e. remove all illegal tiles and
        label the rest as a tiletype. Remove slivers first, then mark any tiles
        representable with the standard tile set. Repeat until convergence.
        """

        m = self._cls_matrix
        dim = self._dim

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
            n += self._apply_tilespecs(m, self.TS_CONCAVE, self.TS_CONVEX, self.TS_STRAIGHT)

            if (n <= 0):
                break
            debug("Classification pass: %d tiles removed", n)
        
        return GameFieldLayer(m)
        
    def _apply_tilespecs(self, m, *tilespecs):

        """ Apply a list of tilespecs, i.e. remove illegal tiles. """

        dim = self._dim
        ext_m = self._extend_matrix(m)
        mask = np.full((dim, dim), True, dtype=bool)

        for tilespec in (tilespecs):
            initial_tt = None

            if (np.equal(tilespec, self.TS_STRAIGHT).all()):
                initial_tt = self.TT_STRAIGHT_N
            elif (np.equal(tilespec, self.TS_CONCAVE).all()):
                initial_tt = self.TT_CONCAVE_NE
            elif (np.equal(tilespec, self.TS_CONVEX).all()):
                initial_tt = self.TT_CONVEX_NE

            for x in range(1, dim+1):
                for y in range(1, dim+1):
                    cls = self._classify_tile(ext_m, mask, x, y, tilespec, initial_tt)
                    if (type(cls) is bool):
                        mask[y-1, x-1] = cls
                    elif (type(cls) is int):
                        mask[y-1, x-1] = False
                        m[y-1, x-1] = cls
                    elif (cls is not None):
                        raise ValueError(cls)

        m[mask] = False
        self._flayer.matrix[mask] = (0xFF if self._rev else 0)

        return np.count_nonzero(mask)

    def _classify_tile(self, m, mask, x, y, tilespec, initial_tt):

        """ Classify a single tile. tilespec may be a valid ternary matrix which
        is rotated into all possible positions and compared with the tile's
        immediate neighborhood _or_ a callable. Returns a TT _or_ a boolean
        affecting only the mask _or_ None for no effect at all.
        """

        nhood = m[y-1:y+2, x-1:x+2]
        i = 0

        if (not mask[y-1, x-1]):            # already classed as OK, return
            return False
        elif (m[y, x] == self.TT_EMPTY):    # non-interesting tile is OK, return
            return False
        elif (nhood.all() > self.TT_EMPTY): # interior terrain tile is OK, return
            return self.TT_SOLID

        if (callable(tilespec)):
            return tilespec(m, x, y, nhood)

        # Test tilespec at 4 rotations at most

        nhood_bool = nhood > self.TT_EMPTY

        while (i < 4):
            if (self._is_ternary_matrix_equal(tilespec, nhood_bool)):
                return initial_tt + i
            tilespec = self._rotate_matrix(tilespec)
            i += 1

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

