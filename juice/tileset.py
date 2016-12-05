
from pyglet import resource, image

class TileSet:

    """ A class representing a tileset. """

    def __init__(self, filename, tiledim):
        img = resource.texture(filename)

        self.tiledim = tiledim
        self._tw = img.width // tiledim
        self._th = img.height // tiledim
        self._grid = image.ImageGrid(img, self._th, self._tw)

    def get_tile(self, x, y):

        """ Return a tile from the tileset. Uses pyglet.image.ImageGrid for the
        implementation, but converting coordinates into a sensible system.
        """

        return self._grid[self._th - y - 1, x]
