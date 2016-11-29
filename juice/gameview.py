
import pyglet

from juice.tileset import TileSet
from juice.gamefieldlayer import GameFieldLayer
from juice.tileclassifier import TileClassifier
from juice.terrainlayer import \
    TerrainLayer, RiverLayer, SeaLayer, BiomeLayer, CityLayer

class GameView:

    """ A class representing a rendering of the game state onto the main
    viewport.
    """

    def __init__(self, terrain, tiledim):
        self._terrain = terrain
        self._tiledim = tiledim
        self._tileset = TileSet("assets/img/tileset.png", tiledim)
        self._tiles = self._gather_tiles()

    def blit(self, x_offset, y_offset, w, h):

        """ Blit a portion of the rendered map onto the active buffer. Offsets
        and dimensions given in game coordinates.
        """
        
        tiles = self._tiles
        tile_dim = self._tiledim
        slayer = self._terrain.get_layer_by_type(SeaLayer)
        tilemap = slayer.classification        

        screenbuf = pyglet.image.get_buffer_manager().get_color_buffer()
        screen_w = screenbuf.width
        screen_h = screenbuf.height

        for (x, y, v) in tilemap.get_points(x_offset, y_offset, w, h, skip_zero=False):
            xdelta = x - x_offset
            ydelta = y - y_offset
            blitx = xdelta * tile_dim
            blity = screen_h - (tile_dim * (ydelta + 1))
            tiletype = tilemap.matrix[y, x]

            tiles[tiletype].blit(blitx, blity)

    def _gather_tiles(self):

        """ Gather tiles into a labeled structure. """

        tileset = self._tileset

        return {
            TileClassifier.TT_STRAIGHT_N    : tileset.get_tile(22, 8),
            TileClassifier.TT_STRAIGHT_E    : tileset.get_tile(23, 9),
            TileClassifier.TT_STRAIGHT_S    : tileset.get_tile(22, 10),
            TileClassifier.TT_STRAIGHT_W    : tileset.get_tile(21, 9),

            TileClassifier.TT_CONVEX_NE     : tileset.get_tile(23, 8),
            TileClassifier.TT_CONVEX_SE     : tileset.get_tile(23, 10),
            TileClassifier.TT_CONVEX_SW     : tileset.get_tile(21, 10),
            TileClassifier.TT_CONVEX_NW     : tileset.get_tile(21, 8),

            TileClassifier.TT_CONCAVE_NE    : tileset.get_tile(23, 6),
            TileClassifier.TT_CONCAVE_SE    : tileset.get_tile(23, 7),
            TileClassifier.TT_CONCAVE_SW    : tileset.get_tile(22, 7),
            TileClassifier.TT_CONCAVE_NW    : tileset.get_tile(22, 6),

            TileClassifier.TT_SOLID         : tileset.get_tile(22, 9),
            TileClassifier.TT_EMPTY         : tileset.get_tile(28, 3),
            TileClassifier.TT_NA            : tileset.get_tile(16, 3)
        }
