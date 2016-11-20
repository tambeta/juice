
import pyglet

from juice.tileset import TileSet
from juice.terrainlayer import \
    TerrainLayer, RiverLayer, SeaLayer, BiomeLayer, CityLayer

class GameView:
    
    """ A class representing a rendering of the game state onto the main
    viewport.
    """
    
    def __init__(self, terrain):
        self.terrain = terrain

    def blit(self, x_offset, y_offset, w, h, tile_dim):
        
        """ Blit a portion of the rendered map onto the active buffer. Offsets
        and dimensions given in game coordinates.
        """
        
        tileset = TileSet("assets/img/tileset.png", tile_dim)
        land_tile = tileset.get_tile(19, 9)
        water_tile = tileset.get_tile(28, 3)
        
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
                water_tile.blit(blitx, blity)
            else:
                land_tile.blit(blitx, blity)        
