
import pyglet

from juice.tileset import TileSet
from juice.gamefieldlayer import GameFieldLayer
from juice.terrainlayer import \
    TerrainLayer, RiverLayer, SeaLayer, BiomeLayer, CityLayer

class GameView:

    """ A class representing a rendering of the game state onto the main
    viewport.
    """

    TILE_WATER      = 0
    TILE_N          = 1
    TILE_E          = 2
    TILE_S          = 3
    TILE_W          = 4
    TILE_CONVEX_NE  = 5
    TILE_CONVEX_SE  = 6
    TILE_CONVEX_SW  = 7
    TILE_CONVEX_NW  = 8
    TILE_CONCAVE_NE = 9
    TILE_CONCAVE_SE = 10
    TILE_CONCAVE_SW = 11
    TILE_CONCAVE_NW = 12
    TILE_LAND       = 13
    TILE_ISLAND     = 14
    TILE_NA         = 255

    def __init__(self, terrain, tiledim):
        self.terrain = terrain
        self.tiledim = tiledim
        self.tileset = TileSet("assets/img/tileset.png", tiledim)
        self.tilemap = self._construct_tilemap()
        self.tiles = self._gather_tiles()

    def blit(self, x_offset, y_offset, w, h):

        """ Blit a portion of the rendered map onto the active buffer. Offsets
        and dimensions given in game coordinates.
        """
        
        tiles = self.tiles
        tile_dim = self.tiledim
        tilemap = self.tilemap

        screenbuf = pyglet.image.get_buffer_manager().get_color_buffer()
        screen_w = screenbuf.width
        screen_h = screenbuf.height

        layer = self.terrain.get_layer_by_type(SeaLayer)

        for (x, y, v) in layer.get_points(x_offset, y_offset, w, h, skip_zero=False):
            xdelta = x - x_offset
            ydelta = y - y_offset
            blitx = xdelta * tile_dim
            blity = screen_h - (tile_dim * (ydelta + 1))
            tile_id = tilemap.matrix[y, x]

            tiles[tile_id].blit(blitx, blity)

    def _construct_tilemap(self):

        """ Construct a tile map, i.e. a GameFieldLayer of tile IDs for
        rendering the view.
        """

        dim = self.terrain.dim
        tilemap = GameFieldLayer(dim, self.TILE_WATER)
        layer = self.terrain.get_layer_by_type(SeaLayer)
        matrix = layer.matrix

        tile_conds = (
            ((False, False, False, False, False, False, False, False), self.TILE_LAND),
            ((True, True, True, True), self.TILE_ISLAND),

            ((True, True, False, False), self.TILE_CONVEX_NE),
            ((False, True, True, False), self.TILE_CONVEX_SE),
            ((False, False, True, True), self.TILE_CONVEX_SW),
            ((True, False, False, True), self.TILE_CONVEX_NW),

            ((False, False, False, False, False, True, False, False), self.TILE_CONCAVE_NE),
            ((False, False, False, False, False, False, False, True), self.TILE_CONCAVE_SE),
            ((False, True, False, False, False, False, False, False), self.TILE_CONCAVE_SW),
            ((False, False, False, True, False, False, False, False), self.TILE_CONCAVE_NW),

            ((True, False, False, False), self.TILE_N),
            ((False, True, False, False), self.TILE_E),
            ((False, False, True, False), self.TILE_S),
            ((False, False, False, True), self.TILE_W),
        )

        for (x, y, v) in layer.get_points(skip_zero=False):
            if (v > 0):
                continue
            tilemap.matrix[y, x] = self.TILE_NA

            for cond in tile_conds:
                if (self._check_tile_neighbors(matrix, x, y, cond[0])):
                    tilemap.matrix[y, x] = cond[1]
                    break

        return tilemap

    def _check_tile_neighbors(self, matrix, x, y, conds):

        """ Check if a (x, y) coordinate in matrix satisfies conds: a 4-tuple
        of N, E, S, W _or_ an 8-tuple of N, NE, E, SE, S, SW, W, NW neighbors
        and their expected values. The matrix is reduced to a binary matrix
        first: all values are mapped to True, unless zero (False). Note that in
        case of edge coordinates, the value at (x, y) is considered to extend
        over the edge.
        """

        dim = matrix.shape[0]
        v = (matrix[y, x] != 0)
        (n_v, e_v, s_v, w_v) = (None, None, None, None)
        (ne_v, se_v, sw_v, nw_v) = (None, None, None, None)

        n_v = (v if (y == 0)         else (matrix[y-1, x] != 0))
        e_v = (v if (x == dim - 1)   else (matrix[y, x+1] != 0))
        s_v = (v if (y == dim - 1)   else (matrix[y+1, x] != 0))
        w_v = (v if (x == 0)         else (matrix[y, x-1] != 0))

        if (len(conds) == 8):
            ne_v = (e_v if (y == 0)       else (n_v if (x == dim - 1) else (matrix[y-1, x+1] != 0)))
            se_v = (e_v if (y == dim - 1) else (s_v if (x == dim - 1) else (matrix[y+1, x+1] != 0)))
            sw_v = (w_v if (y == dim - 1) else (s_v if (x == 0)       else (matrix[y+1, x-1] != 0)))
            nw_v = (w_v if (y == 0)       else (n_v if (x == 0)       else (matrix[y-1, x-1] != 0)))

            if (conds == (n_v, ne_v, e_v, se_v, s_v, sw_v, w_v, nw_v)):
                return True
            return False
        elif (len(conds) == 4):
            if (conds == (n_v, e_v, s_v, w_v)):
                return True
            return False

        raise ValueError(
            "Expected `conds` to be a 4- or 8-tuple, received a {}-tuple".format(len(conds)))

    def _gather_tiles(self):

        """ Gather tiles into a labeled structure. """

        tileset = self.tileset

        return {
            self.TILE_N         : tileset.get_tile(22, 8),
            self.TILE_E         : tileset.get_tile(23, 9),
            self.TILE_S         : tileset.get_tile(22, 10),
            self.TILE_W         : tileset.get_tile(21, 9),

            self.TILE_CONVEX_NE : tileset.get_tile(23, 8),
            self.TILE_CONVEX_SE : tileset.get_tile(23, 10),
            self.TILE_CONVEX_SW : tileset.get_tile(21, 10),
            self.TILE_CONVEX_NW : tileset.get_tile(21, 8),

            self.TILE_CONCAVE_NE: tileset.get_tile(23, 6),
            self.TILE_CONCAVE_SE: tileset.get_tile(23, 7),
            self.TILE_CONCAVE_SW: tileset.get_tile(22, 7),
            self.TILE_CONCAVE_NW: tileset.get_tile(22, 6),

            self.TILE_LAND      : tileset.get_tile(22, 9),
            self.TILE_ISLAND    : tileset.get_tile(21, 7),
            self.TILE_WATER     : tileset.get_tile(28, 3),
            self.TILE_NA        : tileset.get_tile(16, 3)
        }
