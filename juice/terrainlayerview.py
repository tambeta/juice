
import re

from juice.terrainlayer import \
    TerrainLayer, SeaLayer, BiomeLayer

class TerrainLayerView:

    """ A factory class returning a suitable subclass upon instantiation
    parametrized by a TerrainLayer subclass. This is a parallel structure to
    the TerrainLayer hierarchy for loose coupling.
    """

    def __new__(cls, tlayer):
        tltype = type(tlayer)
        tlname = tltype.__name__

        if (cls is not TerrainLayerView):
            raise TypeError("Cannot instantiate TerrainLayerView subclasses directly")
        if (not issubclass(tltype, TerrainLayer)):
            raise TypeError("Subclass of TerrainLayer expected")

        for subclass in cls.__subclasses__():
            m = re.match(r"_(\w+)View", subclass.__name__)

            if (m and m.group(1) == tlname):
                class dummyclass: pass
                r = dummyclass()
                r.__class__ = subclass
                return r

        raise TypeError("No matching TerrainLayerView subclass for " + str(type(tlayer).__name__))

    def __init__(self, *args):
        raise RuntimeError("Cannot instantiate TerrainLayerView")

class _SeaLayerView(TerrainLayerView):
    def __init__(self, *args):
        pass

class _RiverLayerView(TerrainLayerView):
    def __init__(self, *args):
        pass

class _BiomeLayerView(TerrainLayerView):
    def __init__(self, *args):
        pass

class _CityLayerView(TerrainLayerView):
    def __init__(self, *args):
        pass


