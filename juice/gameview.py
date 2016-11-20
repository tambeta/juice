
import pyglet

from juice.tileset import TileSet
from juice.terrainlayer import \
    TerrainLayer, RiverLayer, SeaLayer, BiomeLayer, CityLayer

class GameView:
    
    """ A class representing a rendering of the game state onto the main
    viewport.
    """
    
    TILE_N = "TILE_N"
    TILE_E = "TILE_E"
    TILE_S = "TILE_S"
    TILE_W = "TILE_W"
    TILE_NE = "TILE_NE"
    TILE_SE = "TILE_SE"
    TILE_SW = "TILE_SW"
    TILE_NW = "TILE_NW"
    TILE_LAND = "TILE_LAND"
    TILE_WATER = "TILE_WATER"
    
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
        
        screenbuf = pyglet.image.get_buffer_manager().get_color_buffer()
        screen_w = screenbuf.width
        screen_h = screenbuf.height
        
        layer = self.terrain.get_layer_by_type(SeaLayer)
        
        for (x, y, v) in layer.get_points(x_offset, y_offset, w, h, skip_zero=False):
            xdelta = x - x_offset
            ydelta = y - y_offset
            blitx = xdelta * tile_dim
            blity = screen_h - (tile_dim * (ydelta + 1))            
            
            if (v > 0):
                tiles[self.TILE_WATER].blit(blitx, blity)
            else:
                tiles[self.TILE_LAND].blit(blitx, blity)        

    def _construct_tilemap(self):
        
        """ Construct a tile map. """
        
        # TODO: 

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
