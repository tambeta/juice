
import abc
import collections
import itertools
import re

import numpy as np

from logging import debug, info, warning, error
from juice.gamefieldlayer import GameFieldLayer

_TileSpec = collections.namedtuple("TileSpec", ["array", "initial_tt", "rotations"])

class LayerClassification(GameFieldLayer):
    
    """ A small adapter class for storing the classification [into
    tiletypes]. Stores the classifier class.
    """
    
    def __init__(self, matrix, cfier):        
        if (not issubclass(cfier, TileClassifier)):
            raise TypeError("LayerClassification constructor expects a TileClassifier subclass")
        
        self.classifier = cfier
        super().__init__(matrix)

class TileClassifier(metaclass=abc.ABCMeta):
    
    """ Subclasses of TileClassifier convert a GameFieldLayer into the space
    of possible tiles of the standard tileset and removing illegal tiles,
    thereby normalizing the field. The first variation is
    TileClassifierSolid for layers of expansive segments represented by
    solid or straight, convex and concave edge tiles. The second is
    TileClassifierLine for layers of line objects, e.g. rivers.
    """

    TT_EMPTY        = 0
    TT_NA           = 1

    def __init__(self, flayer, rev=False, extend=True):

        """ Constructor. cls_matrix is a matrix representing "interesting" (the
        terrain) and "uninteresting" tiles at first (a boolean matrix), later
        filled with tile type IDs. By default, all nonzero values are considered
        interesting. Passing true for rev reverses this condition. If extend is
        true, the layer will seemingly extend beyond the edge, otherwise the
        tile just beyond the edge will be considered empty (whatever its
        semantics for the given layer).
        """

        assert(self.TT_EMPTY == 0)

        self._cls_matrix = self._init_matrix(flayer, rev=rev)
        self._flayer = flayer
        self._dim = flayer.matrix.shape[0]
        self._rev = rev
        self._extend = extend

    @abc.abstractmethod
    def classify(self, tilespec_lists):
        
        """ Classify the input GameFieldLayer, i.e. remove all illegal tiles and
        label the rest as a tiletype. Repeat until convergence.
        """
        
        m = self._cls_matrix
        
        while (True):
            n = 0
            
            for tsl in tilespec_lists:
                n += self._apply_tilespecs(m, *tsl)
            debug("Classification pass: %d tiles removed", n)
            
            if (n <= 0):
                break
        
        return LayerClassification(m, self.__class__)

    @classmethod
    def get_tt_str(cls, tt):
        
        """ Transform a tile type ID (an integer) into the corresponding
        string.
        """
        
        for (k, v) in vars(cls).items():
            if (not re.match(r"TT", k)):
                continue
            elif (v == tt):
                return k
        
        raise ValueError("No such tile type ID for {}: {}".format(cls.__name__, tt))

    def _init_matrix(self, flayer, rev=False, empty=False):
        cm = np.full(flayer.matrix.shape, self.TT_EMPTY, dtype=np.uint8)
        
        if (not empty):
            cm[flayer.matrix == 0 if rev else flayer.matrix != 0] = self.TT_NA
        return cm
        
    def _apply_tilespecs(self, m, *tilespecs):

        """ Apply a list of tilespecs, i.e. remove illegal tiles. """

        dim = self._dim
        ext_m = self._extend_matrix(m, self._extend)
        mask = np.full((dim, dim), True, dtype=bool)
        extrange = range(1, dim+1)
        
        for (tilespec, x, y) in itertools.product(tilespecs, extrange, extrange):
            cls = self._classify_tile(ext_m, mask, x, y, tilespec)
            if (type(cls) is bool):
                mask[y-1, x-1] = cls
            elif (type(cls) is int):
                mask[y-1, x-1] = False
                m[y-1, x-1] = cls
            elif (cls is not None):
                raise ValueError(cls)
        
        m[mask] = False
        self._flayer.matrix[mask] = (0xFE if self._rev else 0)

        return np.count_nonzero(mask)

    def _classify_tile(self, m, mask, x, y, tilespec):

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
        elif (type(self) is TileClassifierSolid and nhood.all() > self.TT_EMPTY):
            return self.TT_SOLID            # interior terrain tile is OK, return

        if (callable(tilespec)):
            return tilespec(m, x, y, nhood)

        # Test tilespec at 4 rotations at most

        nhood_bool  = nhood > self.TT_EMPTY
        initial_tt  = tilespec.initial_tt
        rotations   = tilespec.rotations or 4
        ts_matrix   = tilespec.array
        
        while (i < rotations):
            if (self._is_ternary_matrix_equal(ts_matrix, nhood_bool)):
                return initial_tt + i
            ts_matrix = self._rotate_matrix(ts_matrix)
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

    def _extend_matrix(self, m, with_same):

        """ Expand a tile matrix over the borders by one: all values are
        continued further, i.e. terrain continues to terrain and non-terrain
        continues to non-terrain. The result is a matrix with 2 added to both
        dimensions. If with_same is false, values aren't continued and padding
        is all zeroes.
        """
        
        dim = self._dim
        
        def stack_row(i):
            if (not with_same):
                return np.zeros(dim)
            return m[i]
            
        def stack_col(i):
            if (not with_same):
                return np.zeros((dim+2, 1))
            return np.expand_dims(m[:,i], axis=1)
        
        m = np.vstack((stack_row(0), m))
        m = np.vstack((m, stack_row(-1)))        
        m = np.hstack((stack_col(0), m))
        m = np.hstack((m, stack_col(-1)))

        return m
    
class TileClassifierSolid(TileClassifier):
    
    # Note: Rotated variations of the same types are expected to be
    # successive integers.

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

    TS_CONCAVE  = _TileSpec._make((np.array([
        [True, True, True],
        [True, True, True],
        [False, True, True]]), TT_CONCAVE_NE, None))
    TS_CONVEX   = _TileSpec._make((np.array([
        [None, False, None],
        [True, True, False],
        [True, True, None]]), TT_CONVEX_NE, None))
    TS_STRAIGHT   = _TileSpec._make((np.array([
        [None, False, None],
        [True, True, True],
        [True, True, True]]), TT_STRAIGHT_N, None))

    def classify(self):

        """ The solid layer type classifier removes "slivers" first for
        efficiency, then classifies to the standard tileset.
        """

        def sliver_spec(m, x, y, nhood):

            """ Callable tilespec defining "slivers" i.e. terrain portions of
            width 1.
            """

            if ((not nhood[0, 1] and not nhood[2, 1]) or (not nhood[1, 0] and not nhood[1, 2])):
                return True
            return False

        return super().classify(
            ((sliver_spec,), (self.TS_CONCAVE, self.TS_CONVEX, self.TS_STRAIGHT)))

class TileClassifierLine(TileClassifier):
    
    TT_STRAIGHT_NS   = 21
    TT_STRAIGHT_WE   = 22
    
    TT_SOURCE_N      = 31
    TT_SOURCE_E      = 32
    TT_SOURCE_S      = 33
    TT_SOURCE_W      = 34
    
    TT_CORNER_NE     = 41
    TT_CORNER_SE     = 42
    TT_CORNER_SW     = 43
    TT_CORNER_NW     = 44
    
    TT_TBONE_N       = 51
    TT_TBONE_E       = 52
    TT_TBONE_S       = 53
    TT_TBONE_W       = 54
    
    TT_FOURWAY       = 61
    
    TS_STRAIGHT  = _TileSpec._make((np.array([
        [None,  True,  None],
        [False, True,  False],
        [None,  True,  None]]), TT_STRAIGHT_NS, 2))
    TS_SOURCE   = _TileSpec._make((np.array([
        [None,  True,  None],
        [False, True,  False],
        [None,  None,  None]]), TT_SOURCE_N, 4))
    TS_CORNER   = _TileSpec._make((np.array([
        [None,  True,  None],
        [False, True,  True],
        [None,  False, None]]), TT_CORNER_NE, 4))
    TS_TBONE    = _TileSpec._make((np.array([
        [None,  True,  None],
        [True,  True,  True],
        [None,  False, None]]), TT_TBONE_N, 4))
    TS_FOURWAY  = _TileSpec._make((np.array([
        [None,  True,  None],
        [True,  True,  True],
        [None,  True,  None]]), TT_FOURWAY, 1))
    
    def classify(self):
        return super().classify(
            ((self.TS_STRAIGHT, self.TS_SOURCE, self.TS_CORNER, self.TS_TBONE, self.TS_FOURWAY),))        

class TileClassifierDelta(TileClassifier):
    
    TT_DELTA_N  = 71
    TT_DELTA_E  = 72
    TT_DELTA_S  = 73
    TT_DELTA_W  = 74

    def __init__(self, flayer, terrain=None):
        self._cls_matrix = self._init_matrix(flayer, empty=True)
        self._flayer = flayer
        self._terrain = terrain

    def classify(self):
        
        """ Classify deltas by determining the orientation of river -> sea
        junctions.
        """
        
        m = self._cls_matrix
        t = self._terrain
        flayer = self._flayer
        
        def set_delta_dir(cx, cy, x, y):
            if (flayer[cx, cy] != t.DELTA_SEA):
                return
                
            if (cx - x == -1):
                m[y, x] = self.TT_DELTA_W
            elif (cx - x == 1):
                m[y, x] = self.TT_DELTA_E
            elif (cy - y == -1):
                m[y, x] = self.TT_DELTA_N
            elif (cy - y == 1):
                m[y, x] = self.TT_DELTA_S
            else:
                raise RuntimeError("GameFieldLayer.foreach_edge_neighbor broken")            
        
        for c in np.argwhere(flayer.matrix == t.DELTA_RIVER):
            x = c[1]; y = c[0]
            flayer.foreach_edge_neighbor(set_delta_dir, x, y, x, y)
        
        return LayerClassification(m, self.__class__)
