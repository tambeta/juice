
# geany: ts=4

from PIL import Image
from pyglet import resource, image

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

        imagedata = image.ImageData(self._w, self._h, "RGBA", self._pitch)
        comp = Image.alpha_composite(self.get_pil_img(), other.get_pil_img())

        imagedata.set_data("RGBA", self._pitch, comp.tobytes())
        return Tile(imagedata)

    def get_pil_img(self):

        """ Return a PIL Image. """

        imagedata = self.img.get_image_data()
        raw_bytes = imagedata.get_data("RGBA", self._pitch)

        return Image.frombytes("RGBA", (self._w, self._h), raw_bytes)

class PlaceholderTile:
    def __init__(self):
        pass

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
