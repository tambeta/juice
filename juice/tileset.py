
# geany: ts=4

import itertools

from PIL import Image, ImageDraw
from pyglet import resource, image

from juice.config import config

class Tile:

    """ A class representing a single element of a TileSet. """

    def __init__(self, img):

        """ img is a pyglet.image.AbstractImage, a region of a tileset. """

        if (not issubclass(type(img), image.AbstractImage)):
            raise TypeError("img must be an AbstractImage")

        self.img = img

        self._pitch = img.width * 4
        self._w = img.width
        self._h = img.height

    def append(self, other):

        """ Get a composite of two tiles; return the new tile """

        comp = Image.alpha_composite(self._get_pil_img(), other._get_pil_img())
        return Tile(self._get_pyglet_img(comp))

    def _get_pil_img(self):

        """ Return a PIL Image. """

        imagedata = self.img.get_image_data()
        raw_bytes = imagedata.get_data("RGBA", self._pitch)

        return Image.frombytes("RGBA", (self._w, self._h), raw_bytes)
        
    def _get_pyglet_img(self, pimg=None, pitch_dir=1):
        
        """ Return a pyglet.image.ImageData converted from a passed PIL image,
        or an empty ImageData if none passed. pitch_dir is for compatibility
        between PIL / game and pyglet coordinate systems (flipped y-axis).
        """
        
        imagedata = image.ImageData(self._w, self._h, "RGBA", self._pitch)
        
        if (pimg):
            imagedata.set_data("RGBA", pitch_dir * self._pitch, pimg.tobytes())        
        return imagedata

class PlaceholderTile(Tile):
    
    """ A tile not read from a tileset, but generated on the fly based on a
    simple layout specification. The layout is expected to be a sequence of
    sequences which are all of the same length, representing a square
    matrix. The tile is sectioned into a grid with each segment representing
    an element in the matrix. The segments corresponding to elements
    evaluating to true are filled with the passed color.
    """
    
    def __init__(self, layout=None, color="black"):
        tiledim = config.tiledim
        pimg = Image.new("RGBA", (tiledim, tiledim))
        
        self._w = tiledim
        self._h = tiledim
        self._pitch = tiledim * 4
        
        if (layout):
            self._construct_tile(pimg, layout, color)
        self.img = self._get_pyglet_img(pimg, -1)

    def _construct_tile(self, pimg, layout, color):
        draw = ImageDraw.Draw(pimg)
        lo_dim = len(layout[0])
        el_dim = self._w / lo_dim
        
        for (y, x) in itertools.product(range(lo_dim), range(lo_dim)):
            if (layout[y][x]):
                px = x * el_dim
                py = y * el_dim
                draw.rectangle((px, py, px+el_dim-1, py+el_dim-1), color)

class TileSet:

    """ A class representing a tileset. """

    def __init__(self, filename, tiledim):
        img = resource.texture(filename)

        self.tiledim = tiledim
        self._tw = img.width // tiledim
        self._th = img.height // tiledim
        self._grid = image.ImageGrid(img, self._th, self._tw)

    def get_tile(self, x, y):

        """ Return a tile from the tileset (AbstractImage). Uses
        pyglet.image.ImageGrid for the implementation, but converting
        coordinates into a sensible system.
        """

        return Tile(self._grid[self._th - y - 1, x])
