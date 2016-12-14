
import colorsys
import functools
import random

from warnings import warn

import numpy as np
import pyglet

from PIL import Image

from juice.heightmap import Heightmap
from juice.terrainlayer import \
    TerrainLayer, RiverLayer, SeaLayer, BiomeLayer, CityLayer

class Terrain:

    """ Terrain is a compositor class consisting of an underlying Heightmap
    and several TerrainLayers. Note on threshold constants: the condition is
    ruled to apply _at_ threshold as well as above or below. Note on
    nomenclature: "height" means self.heightmap.matrix value at a given
    coordinate.

    Layer constants:

    MOUNTAIN_THRESHOLD       - Height at which or above a point is
                               considered to be a mountain, i.e. suitable
                               for a river source.
    SEA_THRESHOLD            - Height at which or below a point is
                               considered to be suitable for sea.
    MIN_SEA_SIZE             - Minimum size of a contiguous sea layer
                               segment.
    RIVER_DENSITY            - Proportion of river sources to mountain
                               areas.
    BIOME_H_DELTA            - A point is suitable for a biome if its
                               height is lte than
                               MOUNTAIN_THRESHOLD-BIOME_H_DELTA or gte than
                               SEA_THRESHOLD+BIOME_H_DELTA.
    MIN_BIOME_SIZE           - Minimum size of contiguous biome layer
                               segment.
    CITY_DENSITY             - Proportion of cities to land areas.
    MIN_POPSUPPORT_SIZE      - Minimum size of contiguous land are to be
                               considered for city placement.
    CITY_CLOSENESS_FACTOR    - The map dimension is divided by this
                               constant to get the minimum distance between
                               any two cities.
    MAX_CITY_DISALLOW_RADIUS - Maximum value for the minimum distance
                               between any two cities.
    """

    MOUNTAIN_THRESHOLD = 192

    SEA_THRESHOLD = 96
    MIN_SEA_SIZE = 32

    RIVER_DENSITY = 0.025
    MIN_RIVER_SOURCES = 4

    DESERT_ID = 1
    FOREST_ID = 2
    BIOME_H_DELTA = 15
    MIN_BIOME_SIZE = 32

    CITY_DENSITY = 0.005
    MIN_POPSUPPORT_SIZE = 12
    CITY_CLOSENESS_FACTOR = 20
    MAX_CITY_DISALLOW_RADIUS = 40

    def __init__(self, dim, randseed=None):
        self.heightmap = Heightmap(
            dim, randseed=randseed,
            #min_cell_size=4, noise_range=35, blur_sigma=0.8
        )
        self.dim = dim

        self._layers = []
        self._colormap = {}

        random.seed(randseed)

    def generate(self, post_generate_cb=None):
        self.heightmap.generate()

        if (callable(post_generate_cb)):
            post_generate_cb(self.heightmap)

        for layer in (self._layers):
            layer.generate()

            if (callable(post_generate_cb)):
                post_generate_cb(layer)
    
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

    def get_layers(self):

        """ Get layers in order, warn if layer of expected type not found.
        Generator method.
        """

        for ltype in map(type, self._layers):
            layer = None

            try:
                layer = self.get_layer_by_type(ltype)
            except LookupError as e:
                warn("Cannot get " + str(ltype.__name__) + " for composition")
                continue

            yield layer

    def get_map_imgdata(self, scaling=1):

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

        layer_colorers = {}

        def biome_colorer(val):
            if (val == self.DESERT_ID):
                return (230, 230, 0)
            elif (val == self.FOREST_ID):
                return (0, 125, 0)
            raise ValueError("No such biome ID " + str(val))

        def heatmap_colorer(max_value, val):

            """ For use with functools.partial. """

            return (min(255, int(val / max_value * 255)), 0, 0)

        layer_colorers[SeaLayer] = \
            lambda x: (255, 0, 0) if (x == 255) else (0, 0, 200)
        layer_colorers[RiverLayer] = (80, 80, 240)
        layer_colorers[BiomeLayer] = biome_colorer
        layer_colorers[CityLayer] = \
            lambda x: (255, 0, 0) if (x == 1) else (0, 255, 0)

        for layer in self.get_layers():
            colorer = layer_colorers[type(layer)]

            for (x, y, v) in layer.get_points():
                color = colorer(v) if callable(colorer) else colorer
                img.putpixel((x, y), color)
