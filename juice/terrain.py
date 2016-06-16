
import colorsys
import random
from warnings import warn

import numpy as np
import pyglet
from PIL import Image

from juice.heightmap import Heightmap
from juice.terrainlayer import TerrainLayer, RiverLayer, SeaLayer

class Terrain:

    """ Terrain is a compositor class consisting of an underlying Heightmap
    and several TerrainLayers. Note on threshold constants: the condition is
    ruled to apply _at_ threshold as well as above or below.
    """
    
    MOUNTAIN_THRESHOLD = 192
    
    SEA_THRESHOLD = 96
    MIN_SEA_SIZE = 32
    
    RIVER_DENSITY = 0.05
    MIN_RIVER_SOURCES = 4
    
    def __init__(self, dim, randseed=None):
        self.heightmap = Heightmap(
            dim, randseed=randseed,
            min_cell_size=4, noise_range=35, blur_sigma=1.5
        )
        self.dim = dim
        
        self._layers = []
        self._colormap = {}
        
        random.seed(randseed)
    
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
    
    def generate(self, post_generate_cb=None):
        self.heightmap.generate()

        if (callable(post_generate_cb)):
            post_generate_cb(self.heightmap)
        
        for layer in (self._layers):
            layer.generate()
            
            if (callable(post_generate_cb)):
                post_generate_cb(layer)
        
    def get_imgdata(self, scaling=1):
        
        """ Get the terrain as pyglet ImageData. """
        
        imatrix = self.heightmap.matrix
        dim = self.dim
        scaling = int(scaling)
        
        # Turn Heightmap into an RGB image
        
        img = Image.frombytes("L", (dim, dim), imatrix).convert(mode="RGB")
        
        # Apply layers
        
        self._apply_layers_to_image(img)
        
        # Scale if requested; output (flipped to match coordinate systems)
        
        if (scaling != 1):
            img = img.resize((dim*scaling, dim*scaling))
            dim *= scaling
        
        return pyglet.image.ImageData(
            dim, dim, "RGB",
            img.transpose(Image.FLIP_TOP_BOTTOM).tobytes()
        )
    
    def _get_colormap_entry(self, key):
        
        """ Convenience routine to return a random "good-looking" color (an RGB
        tuple with values [0 .. 255]) according to a given key, storing it if
        not already present.
        """
        
        colormap = self._colormap
        
        if (key == 255):
            return (255, 0, 0)
        
        if (key in colormap):
            color = colormap[key]
        else:                
            h = random.random()
            s = random.uniform(0.5, 1)
            l = random.uniform(0.35, 0.65)
            color = tuple(map(lambda x: int(x*255), colorsys.hls_to_rgb(h, l, s)))
            colormap[key] = color        
        
        return color
    
    def _apply_layers_to_image(self, img):
        
        """ Apply all TerrainLayers to the passed Image in order """
        
        layer_types = (SeaLayer, RiverLayer)
        layer_colorers = {}
        
        #layer_colorers[SeaLayer] = (0, 0, 255)
        layer_colorers[SeaLayer] = self._get_colormap_entry
        layer_colorers[RiverLayer] = (0, 200, 0)
        #layer_colorers[RiverLayer] = self._get_colormap_entry

        for ltype in layer_types:
            layer = None
            colorer = layer_colorers[ltype]
            
            try:
                layer = self.get_layer_by_type(ltype)
            except LookupError as e:
                warn("Cannot get " + str(ltype.__name__) + " for composition")
                continue
            
            it = np.nditer(layer.matrix, flags=["multi_index"])
            
            while (not it.finished):
                v = int(it[0])
                
                if (v > 0):                
                    p = it.multi_index
                    color = colorer(v) if callable(colorer) else colorer
                    img.putpixel((p[1], p[0]), color)
                
                it.iternext()
