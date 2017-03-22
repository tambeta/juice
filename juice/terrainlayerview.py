
import functools
import re

from juice.terrainlayer     import \
    TerrainLayer, SeaLayer, BiomeLayer
from juice.tileclassifier   import TileClassifierSolid, TileClassifierLine, TileClassifierDelta
from juice.tileset          import PlaceholderTile

class TerrainLayerView:

    """ A factory class returning a suitable subclass upon instantiation
    parametrized by a TerrainLayer subclass. This is a parallel structure to
    the TerrainLayer hierarchy for loose coupling.
    """

    def __new__(cls, tlayer, *args):
        tltype = type(tlayer)
        tlname = tltype.__name__

        if (cls is not TerrainLayerView):
            raise TypeError("Cannot instantiate TerrainLayerView subclasses directly")
        if (not issubclass(tltype, TerrainLayer)):
            raise TypeError("Subclass of TerrainLayer expected")

        for subclass in cls.__subclasses__():
            m = re.match(r"_(\w+)View", subclass.__name__)

            if (m and m.group(1) == tlname):
                class dummyclass: pass
                r = dummyclass()
                r.__class__ = subclass
                return r

        raise TypeError("No matching TerrainLayerView subclass for " + str(type(tlayer).__name__))

    def __init__(self, tlayer, tileset):
        self.terrainlayer = tlayer
        self._tileset = tileset

    def get_tiles(self):
        raise NotImplementedError("No get_tiles() for ", type(self).__name__)

class _SeaLayerView(TerrainLayerView):
    @functools.lru_cache()
    def get_tiles(self):
        tileset = self._tileset

        return {
            TileClassifierSolid.TT_STRAIGHT_N    : tileset.get_tile(22, 8),
            TileClassifierSolid.TT_STRAIGHT_E    : tileset.get_tile(23, 9),
            TileClassifierSolid.TT_STRAIGHT_S    : tileset.get_tile(22, 10),
            TileClassifierSolid.TT_STRAIGHT_W    : tileset.get_tile(21, 9),

            TileClassifierSolid.TT_CONVEX_NE     : tileset.get_tile(23, 8),
            TileClassifierSolid.TT_CONVEX_SE     : tileset.get_tile(23, 10),
            TileClassifierSolid.TT_CONVEX_SW     : tileset.get_tile(21, 10),
            TileClassifierSolid.TT_CONVEX_NW     : tileset.get_tile(21, 8),

            TileClassifierSolid.TT_CONCAVE_NE    : tileset.get_tile(23, 6),
            TileClassifierSolid.TT_CONCAVE_SE    : tileset.get_tile(23, 7),
            TileClassifierSolid.TT_CONCAVE_SW    : tileset.get_tile(22, 7),
            TileClassifierSolid.TT_CONCAVE_NW    : tileset.get_tile(22, 6),

            TileClassifierSolid.TT_SOLID         : tileset.get_tile(22, 9),
            TileClassifierSolid.TT_EMPTY         : tileset.get_tile(28, 3),
            TileClassifierSolid.TT_NA            : tileset.get_tile(16, 3)
        }

class _RiverLayerView(TerrainLayerView):
    @functools.lru_cache()
    def get_tiles(self):
        tileset = self._tileset

        return {
            TileClassifierSolid.TT_EMPTY        : None,
            TileClassifierLine.TT_STRAIGHT_NS   : PlaceholderTile(color="#03e", layout=(
                (0, 1, 0),
                (0, 1, 0),
                (0, 1, 0)
            )),
            TileClassifierLine.TT_STRAIGHT_WE   : PlaceholderTile(color="#03e", layout=(
                (0, 0, 0),
                (1, 1, 1),
                (0, 0, 0)
            )),
            TileClassifierLine.TT_CORNER_NE     : PlaceholderTile(color="#88f", layout=(
                (0, 1, 0),
                (0, 1, 1),
                (0, 0, 0)
            )),
            TileClassifierLine.TT_CORNER_SE     : PlaceholderTile(color="#88f", layout=(
                (0, 0, 0),
                (0, 1, 1),
                (0, 1, 0)
            )),
            TileClassifierLine.TT_CORNER_SW     : PlaceholderTile(color="#88f", layout=(
                (0, 0, 0),
                (1, 1, 0),
                (0, 1, 0)
            )),
            TileClassifierLine.TT_CORNER_NW     : PlaceholderTile(color="#88f", layout=(
                (0, 1, 0),
                (1, 1, 0),
                (0, 0, 0)
            )),
            TileClassifierLine.TT_SOURCE_N      : PlaceholderTile(color="#800", layout=(
                (0, 1, 0),
                (0, 1, 0),
                (0, 0, 0)
            )),
            TileClassifierLine.TT_SOURCE_E      : PlaceholderTile(color="#800", layout=(
                (0, 0, 0),
                (0, 1, 1),
                (0, 0, 0)
            )),
            TileClassifierLine.TT_SOURCE_S      : PlaceholderTile(color="#800", layout=(
                (0, 0, 0),
                (0, 1, 0),
                (0, 1, 0)
            )),
            TileClassifierLine.TT_SOURCE_W      : PlaceholderTile(color="#800", layout=(
                (0, 0, 0),
                (1, 1, 0),
                (0, 0, 0)
            )),
            TileClassifierLine.TT_TBONE_N       : PlaceholderTile(color="#03e", layout=(
                (0, 1, 0),
                (1, 1, 1),
                (0, 0, 0)
            )),
            TileClassifierLine.TT_TBONE_E       : PlaceholderTile(color="#03e", layout=(
                (0, 1, 0),
                (0, 1, 1),
                (0, 1, 0)
            )),
            TileClassifierLine.TT_TBONE_S       : PlaceholderTile(color="#03e", layout=(
                (0, 0, 0),
                (1, 1, 1),
                (0, 1, 0)
            )),
            TileClassifierLine.TT_TBONE_W       : PlaceholderTile(color="#03e", layout=(
                (0, 1, 0),
                (1, 1, 0),
                (0, 1, 0)
            )),
            TileClassifierLine.TT_FOURWAY       : PlaceholderTile(color="#03e", layout=(
                (0, 1, 0),
                (1, 1, 1),
                (0, 1, 0)
            )),
        }

class _DeltaLayerView(TerrainLayerView):
    @functools.lru_cache()
    def get_tiles(self):
        return {
            TileClassifierDelta.TT_EMPTY    : None,
            TileClassifierDelta.TT_DELTA_N  : PlaceholderTile(color="#9f8", layout=(
                (1, 1, 1),
                (0, 0, 0),
                (0, 0, 0)
            )),   
            TileClassifierDelta.TT_DELTA_E  : PlaceholderTile(color="#9f8", layout=(
                (0, 0, 1),
                (0, 0, 1),
                (0, 0, 1)
            )),   
            TileClassifierDelta.TT_DELTA_S  : PlaceholderTile(color="#9f8", layout=(
                (0, 0, 0),
                (0, 0, 0),
                (1, 1, 1)
            )),   
            TileClassifierDelta.TT_DELTA_W  : PlaceholderTile(color="#9f8", layout=(
                (1, 0, 0),
                (1, 0, 0),
                (1, 0, 0)
            )),   
        }

class _BiomeLayerView(TerrainLayerView):
    @functools.lru_cache()
    def get_tiles(self):
        tileset = self._tileset

        return {
            TileClassifierSolid.TT_STRAIGHT_N    : tileset.get_tile(13, 8),
            TileClassifierSolid.TT_STRAIGHT_E    : tileset.get_tile(14, 9),
            TileClassifierSolid.TT_STRAIGHT_S    : tileset.get_tile(13, 10),
            TileClassifierSolid.TT_STRAIGHT_W    : tileset.get_tile(12, 9),

            TileClassifierSolid.TT_CONVEX_NE     : tileset.get_tile(14, 8),
            TileClassifierSolid.TT_CONVEX_SE     : tileset.get_tile(14, 10),
            TileClassifierSolid.TT_CONVEX_SW     : tileset.get_tile(12, 10),
            TileClassifierSolid.TT_CONVEX_NW     : tileset.get_tile(12, 8),

            TileClassifierSolid.TT_CONCAVE_NE    : tileset.get_tile(14, 6),
            TileClassifierSolid.TT_CONCAVE_SE    : tileset.get_tile(14, 7),
            TileClassifierSolid.TT_CONCAVE_SW    : tileset.get_tile(13, 7),
            TileClassifierSolid.TT_CONCAVE_NW    : tileset.get_tile(13, 6),

            TileClassifierSolid.TT_SOLID         : tileset.get_tile(13, 9),
            TileClassifierSolid.TT_EMPTY         : None,
            TileClassifierSolid.TT_NA            : tileset.get_tile(16, 3)
        }

class _CityLayerView(TerrainLayerView):
    @functools.lru_cache()
    def get_tiles(self):
        tileset = self._tileset

        return {
            0 : None,
            1 : PlaceholderTile(color="#BA0000", layout=(
                (1, 1, 1),
                (1, 0, 1),
                (1, 1, 1)
            )),  
        }

class _RoadLayerView(TerrainLayerView):
    def get_tiles(self):
        raise NotImplementedError()
