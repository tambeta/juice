
import functools
import itertools

from logging import debug, info, warning, error
from warnings import warn

import numpy as np
import pyglet
import pyglet.sprite
import pyglet.graphics
import pyglet.image

from juice.config           import config
from juice.terrainlayer     import TerrainLayer
from juice.terrainlayerview import TerrainLayerView
from juice.gamefieldlayer   import GameFieldLayer
from juice.tileset          import TileSet

class GameView:

    """ A class representing a rendering of the game state onto the main
    viewport.
    
    Mechanism: Initially, the whole game field is canvassed layer by layer
    to construct a tile gfx store and the tile field, i.e. a GameFieldLayer
    containing a reference to the tile store for each terrain coordinate.
    Then, an array of pyglet Sprites covering a slightly larger area than
    the viewport (VIEW_PADDING is the buffer width in tiles on each side)
    are constructed; this set remains constant throughout the life of the
    GameView. Upon scrolling (i.e. a request to blit() with different
    coordinates than previously), the sprites are simply given new
    (viewport) coordinates. Invalidated sprites (those outside of the padded
    viewport) are recycled with new tile graphics to the opposite side of
    the viewport.
    
    Note on coordinates: Game coordinates have x, y originating in the upper
    left corner. Pyglet coordinates have x, y originating in the lower left
    corner. The former are used as extensively as possible, converting to
    the latter only before calls to pyglet.
    """

    VIEW_PADDING = 1

    def __init__(self, terrain, x=0, y=0):

        """ Initialize the view at given coordinates. """

        screenbuf = pyglet.image.get_buffer_manager().get_color_buffer()
        tileset = TileSet(config.tileset, config.tiledim)
        tiledim = tileset.tiledim
        dim = terrain.dim
        
        self.tileset = tileset
        self.terrain = terrain
        
        self._screenbuf = screenbuf
        self._tiledim = tiledim
        self._layerviews = []

        self._x = x
        self._y = y
        self._max_x = dim * tiledim - screenbuf.width
        self._max_y = dim * tiledim - screenbuf.height

        for tl in terrain.get_layers():
            self._layerviews.append(TerrainLayerView(tl, tileset))

        (self._tileidx, self._tilemap) = self._construct_tilemap()
        self._sprites = self._generate_sprites()

    def blit(self, x, y):

        """ Blit a portion of the rendered map onto the active buffer. Offsets
        and dimensions given in game pixel coordinates. Returns new x and y
        coordinates which may be different from those passed due to hitting the
        map edge.
        """

        tiledim = self._tiledim
        tileidx = self._tileidx
        tilemap = self._tilemap
        sprites = self._sprites
        padding = self.VIEW_PADDING
        dim = self.terrain.dim

        old_x = self._x
        old_y = self._y

        if (x < 0): x = 0
        elif (x > self._max_x): x = self._max_x

        if (y < 0): y = 0
        elif (y > self._max_y): y = self._max_y

        if (old_x != x or old_y != y):
            dx = x - old_x
            dy = y - old_y
            padding_px = padding * tiledim
            vpw = self._screenbuf.width
            vph = self._screenbuf.height
            vpw_padded = vpw + padding_px * 2
            vph_padded = vph + padding_px * 2
            max_sx = vpw + padding_px - 1
            max_sy = vph + padding_px - 1
            min_sx = -tiledim - padding_px + 1
            min_sy = min_sx
            pyglet_y = y + vph - tiledim

            for s in sprites:
                s.x -= dx
                s.y += dy # pyglet y axis is reversed

                if (s.x < min_sx or s.y < min_sy or s.x > max_sx or s.y > max_sy):

                    # A sprite has been invalidated (offscreen)

                    if (s.x < min_sx): s.x += vpw_padded
                    elif (s.x > max_sx): s.x -= vpw_padded

                    if (s.y < min_sy): s.y += vph_padded
                    elif (s.y > max_sy): s.y -= vph_padded

                    tx = (x + s.x) // tiledim
                    ty = (pyglet_y - s.y) // tiledim
                    
                    if (tx < 0 or ty < 0 or tx >= dim or ty >= dim):
                        continue

                    s.image = tileidx[tilemap[tx, ty]].img

            self._x = x
            self._y = y

        sprites[0].batch.draw()
        return (x, y)

    def blit_delta(self, dx, dy):
        return self.blit(self._x + dx, self._y + dy)

    def get_tile_coords(self, x, y):
        
        """ Get the game tile coordinates from _pyglet_ viewpoint
        coordinates.
        """
        
        gpx = self._x
        gpy = self._y
        vph = self._screenbuf.height
        
        rx = (gpx + x) // self._tiledim
        ry = (gpy - y + vph) // self._tiledim
        return (rx, ry)

    def _construct_tilemap(self):

        """ Construct a tile field containing references into the tile
        index, in turn refering to composite tile graphics. Return both.
        Loop over every coordinate and collect tile types by layer into a
        stack used to construct a key uniquely identifying the composite
        image for the tile.
        """

        dim = self.terrain.dim
        lviews = self._get_usable_layerviews()
        layer_tiles = []
        tilefield = GameFieldLayer(dim, dtype=np.uint64)
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
                tt_stack.append(tilemap[x, y])

            tileidx_key = make_tileidx_key(tt_stack)

            # If key not present in tile index, construct the tile.

            if (tileidx_key not in tileidx):
                tile_stack = []
                debug("Generating composite tile {}".format(tileidx_key))

                for i in range(0, len(lviews)):
                    tile = layer_tiles[i][tt_stack[i]]
                    if (tile):
                        tile_stack.append(tile)

                composite = functools.reduce(lambda a, b: a.append(b), tile_stack)
                tileidx[tileidx_key] = composite

            tilefield[x, y] = tileidx_key

        return (tileidx, tilefield)

    def _generate_sprites(self):

        """ Generate the initial batch of sprites. """

        screen_w = self._screenbuf.width
        screen_h = self._screenbuf.height
        tileidx = self._tileidx
        tilemap = self._tilemap
        tile_dim = self._tiledim

        tile_x = self._x // tile_dim
        tile_y = self._y // tile_dim
        tile_w = screen_w // tile_dim + (self.VIEW_PADDING * 2)
        tile_h = screen_h // tile_dim + (self.VIEW_PADDING * 2)

        sprites = []
        batch = pyglet.graphics.Batch()

        for (cx, cy, v) in tilemap.get_points(tile_x, tile_y, tile_w, tile_h, skip_zero=False):
            xdelta = cx - tile_x
            ydelta = cy - tile_y
            blitx = xdelta * tile_dim
            blity = screen_h - (tile_dim * (ydelta + 1))
            tile = tileidx[v]

            if (tile):
                sprites.append(pyglet.sprite.Sprite(tile.img, x=blitx, y=blity, batch=batch))

        return sprites

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
