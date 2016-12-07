
import functools
import itertools
from warnings import warn

import numpy as np
import pyglet
import pyglet.sprite
import pyglet.graphics
import pyglet.image

from juice.terrainlayer     import TerrainLayer
from juice.terrainlayerview import TerrainLayerView
from juice.gamefieldlayer   import GameFieldLayer

class GameView:

    """ A class representing a rendering of the game state onto the main
    viewport.
    """

    def __init__(self, terrain, tileset):
        self._screenbuf = pyglet.image.get_buffer_manager().get_color_buffer()
        self._tiledim = tileset.tiledim
        self._terrain = terrain
        self._layerviews = []
        self._sprites = None
        self._x = None
        self._y = None

        for tl in terrain.get_layers():
            self._layerviews.append(TerrainLayerView(tl, tileset))

        (self._tileidx, self._tilemap) = self._construct_tilemap()

    def blit(self, x, y, w, h):

        """ Blit a portion of the rendered map onto the active buffer. Offsets
        and dimensions given in game coordinates.
        """
        
        if (not self._sprites):
            self._sprites = self._generate_sprites(x, y, w, h)
            self._x = x
            self._y = y
        
        tiledim = self._tiledim
        sprites = self._sprites
        old_x = self._x
        old_y = self._y
        
        if (old_x != x or old_y != y):
            x_delta_px = (x - old_x) * tiledim
            y_delta_px = (y - old_y) * tiledim
            
            for s in sprites:
                s.x -= x_delta_px
                s.y += y_delta_px # pyglet y axis is reversed
            
            self._x = x
            self._y = y
        
        sprites[0].batch.draw()
    
    def _generate_sprites(self, x, y, w, h):
        
        """ Generate the initial batch of sprites. """
        
        screen_w = self._screenbuf.width
        screen_h = self._screenbuf.height
        tileidx = self._tileidx
        tilemap = self._tilemap        
        tile_dim = self._tiledim
        
        sprites = []
        batch = pyglet.graphics.Batch()

        for (cx, cy, v) in tilemap.get_points(x, y, w, h, skip_zero=False):
            xdelta = cx - x
            ydelta = cy - y
            blitx = xdelta * tile_dim
            blity = screen_h - (tile_dim * (ydelta + 1))
            tile = tileidx[v]

            if (tile):
                sprites.append(pyglet.sprite.Sprite(tile.img, x=blitx, y=blity, batch=batch))
            
        return sprites

    def _construct_tilemap(self):

        """ Construct a tile field containing references into the tile
        index, in turn refering to composite tile graphics. Return both.
        Loop over every coordinate and collect tile types by layer into a
        stack used to construct a key uniquely identifying the composite
        image for the tile.
        """

        dim = self._terrain.dim
        lviews = self._get_usable_layerviews()
        layer_tiles = []
        tilefield = GameFieldLayer(dim, dtype=np.uint32)
        tileidx = {}

        def make_tileidx_key(tts):
            key = "1"
            for i in tts:
                key += "{:02d}".format(i)
            return int(key)

        for i in range(0, len(lviews)):
            layer_tiles.append(lviews[i].get_tiles())

        for (x, y) in itertools.product(range(dim), range(dim)):
            tt_stack = []
            
            # Get a stack of tile types (through layers) at the current
            # coordinate, generate a tile index key.

            for lview in lviews:
                tilemap = lview.terrainlayer.classification
                tt_stack.append(tilemap.matrix[y, x])

            tileidx_key = make_tileidx_key(tt_stack)

            # If key not present in tile index, construct the tile.
            
            if (tileidx_key not in tileidx):
                tile_stack = []

                for i in range(0, len(lviews)):
                    tile = layer_tiles[i][tt_stack[i]]
                    if (tile):
                        tile_stack.append(tile)
                
                composite = functools.reduce(lambda a, b: a.append(b), tile_stack)
                tileidx[tileidx_key] = composite

            tilefield.matrix[y, x] = tileidx_key

        return (tileidx, tilefield)

    def _get_usable_layerviews(self):

        """ Get usable TerrainLayerViews, i.e. ones that have a classification
        and tile image spec.
        """

        used_layerviews = []

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

            used_layerviews.append(lview)

        return used_layerviews
