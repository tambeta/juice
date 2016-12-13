
import functools
import re

from juice.terrainlayer     import \
    TerrainLayer, SeaLayer, BiomeLayer
from juice.tileclassifier   import TileClassifierSolid, TileClassifierLine
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
    pass


