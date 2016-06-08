
import numpy as np
import pyglet

from PIL import Image

from juice.heightmap import Heightmap
from juice.terrainlayer import TerrainLayer

class Terrain:

    """ Terrain is a compositor class consisting of an underlying Heightmap
    and several TerrainLayers.
    """
    
    WATER_THRESHOLD = 30
    MOUNTAIN_THRESHOLD = 200
    
    RIVER_DENSITY = 0.15
    
    def __init__(self, dim):
        self.heightmap = Heightmap(dim)
        self.dim = dim
        
        self._layers = []        
    
    def add_layer(self, layer):
        if (not isinstance(layer, (TerrainLayer,))):
            raise TypeError("layer must be a TerrainLayer")
        
        layer.terrain = self
        self._layers.append(layer)
    
    def generate(self):
        self.heightmap.generate()
        
        for layer in (self._layers):
            layer.generate()
        
    def get_imgdata(self, scaling=1):
        
        """ Get the terrain as pyglet ImageData. The optional scaling value uses
        PIL to scale up the resulting image. TODO: this can be done in scipy
        directly (scipy.misc.imresize).
        """
        
        hmatrix = self.heightmap.matrix
        dim = self.dim
        scaling = int(scaling)
        
        if (scaling != 1):
            hmatrix = Image.frombytes("L", (dim, dim), hmatrix) \
                .resize((dim*scaling, dim*scaling))
            dim *= scaling
        
        return pyglet.image.ImageData(dim, dim, "L", hmatrix.tobytes())
    
