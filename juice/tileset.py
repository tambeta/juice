
from pyglet import resource, image

class TileSet:
    
    """ A class representing a tileset. """
    
    def __init__(self, filename, tiledim):
        img = resource.texture(filename)
        
        self.tw = img.width // tiledim
        self.th = img.height // tiledim
        self.grid = image.ImageGrid(img, self.th, self.tw)
        self.tiledim = tiledim

    def get_tile(self, x, y):

        """ Return a tile from the tileset. Uses pyglet.image.ImageGrid for the
        implementation, but converting coordinates into a sensible system.
        """
        
        return self.grid[self.th - y - 1, x]
