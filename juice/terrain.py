
import numpy as np
import pyglet

from PIL import Image

from juice.heightmap import Heightmap
from juice.terrainlayer import TerrainLayer
from juice.terrainlayer import RiverLayer

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
        
        # Do not allow several layers of same type
        
        try:
            self.get_layer_by_type(type(layer))
            raise TypeError(\
                "Cannot add more than one layer of given type (" + str(type(layer)) + ")")
        except LookupError as e:
            pass
        
        layer.terrain = self
        self._layers.append(layer)
        
    def get_layer_by_type(self, ltype):
        for layer in self._layers:
            if (isinstance(layer, (ltype,))):
                return layer
        
        raise LookupError("Layer of type " + str(ltype) + " not found") 
    
    def generate(self):
        self.heightmap.generate()
        
        for layer in (self._layers):
            layer.generate()
        
    def get_imgdata(self, scaling=1):
        
        """ Get the terrain as pyglet ImageData. """
        
        imatrix = self.heightmap.matrix
        dim = self.dim
        scaling = int(scaling)
        
        # Turn Heightmap into an RGB image
        
        img = Image.frombytes("L", (dim, dim), imatrix).convert(mode="RGB")
        
        # Apply layers
        
        rlayer = self.get_layer_by_type(RiverLayer)
        
        # TODO HERE -> img.putpixel((0, 0), (255, 0, 0))
        
        # Scale if requested; output (flipped to match coordinate systems)
        
        if (scaling != 1):
            img = img.resize((dim*scaling, dim*scaling))
            dim *= scaling
        
        return pyglet.image.ImageData(
            dim, dim, "RGB",
            img.transpose(Image.FLIP_TOP_BOTTOM).tobytes()
        )
