
from warnings import warn

import pyglet

from juice.tileset import TileSet
from juice.terrainlayer import TerrainLayer
from juice.terrainlayerview import TerrainLayerView

class GameView:

    """ A class representing a rendering of the game state onto the main
    viewport.
    """

    def __init__(self, terrain, tiledim):
        self._tiledim = tiledim
        self._layerviews = []
        self._screenbuf = pyglet.image.get_buffer_manager().get_color_buffer()

        tileset = TileSet("assets/img/tileset.png", tiledim)

        for tl in terrain.get_layers():
            self._layerviews.append(TerrainLayerView(tl, tileset))

    def blit(self, x_offset, y_offset, w, h):

        """ Blit a portion of the rendered map onto the active buffer, looping
        over TerrainLayerViews in order. Offsets and dimensions given in game
        coordinates.
        """

        screenbuf = self._screenbuf
        tile_dim = self._tiledim
        screen_w = screenbuf.width
        screen_h = screenbuf.height

        for lview in self._layerviews:
            tlayer = lview.terrainlayer
            tilemap = tlayer.classification

            try:
                tiles = lview.get_tiles()
            except NotImplementedError:
                warn("No tile gfx specification found for {}, skipping"
                    .format(type(lview).__name__))
                continue

            if (not tilemap):
                warn("No tile classification found for {}, skipping"
                    .format(type(tlayer).__name__))
                continue

            for (x, y, v) in tilemap.get_points(x_offset, y_offset, w, h, skip_zero=False):
                xdelta = x - x_offset
                ydelta = y - y_offset
                blitx = xdelta * tile_dim
                blity = screen_h - (tile_dim * (ydelta + 1))
                tiletype = tilemap.matrix[y, x]
                tile = tiles[tiletype]

                if (tile):
                    tile.blit(blitx, blity)
