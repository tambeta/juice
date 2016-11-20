
import pyglet

from juice.tileset import TileSet
from juice.gamefieldlayer import GameFieldLayer
from juice.terrainlayer import \
    TerrainLayer, RiverLayer, SeaLayer, BiomeLayer, CityLayer

class GameView:
    
    """ A class representing a rendering of the game state onto the main
    viewport.
    """
    
    TILE_WATER  = 0
    TILE_N      = 1
    TILE_E      = 2
    TILE_S      = 3
    TILE_W      = 4
    TILE_NE     = 5
    TILE_SE     = 6
    TILE_SW     = 7
    TILE_NW     = 8
    TILE_LAND   = 9
    
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
        
        """ Construct a tile map. """
        
        tilemap = GameFieldLayer(self.terrain.dim, self.TILE_LAND)
        layer = self.terrain.get_layer_by_type(SeaLayer)
        
        for (x, y, v) in layer.get_points():
            tilemap.matrix[y, x] = self.TILE_WATER
        return tilemap

    def _gather_tiles(self):
        
        """ Gather tiles into a labeled structure. """
        
        tileset = self.tileset

        return {
            self.TILE_N     : tileset.get_tile(22, 8),
            self.TILE_E     : tileset.get_tile(23, 9),
            self.TILE_S     : tileset.get_tile(22, 10),
            self.TILE_W     : tileset.get_tile(21, 9),
            self.TILE_NE    : tileset.get_tile(23, 8),
            self.TILE_SE    : tileset.get_tile(23, 10),
            self.TILE_SW    : tileset.get_tile(21, 10),
            self.TILE_NW    : tileset.get_tile(21, 8),
            self.TILE_LAND  : tileset.get_tile(22, 9),
            self.TILE_WATER : tileset.get_tile(28, 3)
        }
