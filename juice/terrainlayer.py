
import numpy as np

class TerrainLayer:

    """ A layer of Terrain. The TerrainLayer base class cannot be
    instantiated directly, but upon instantiation of subclasses the new
    TerrainLayer will be added to the passed Terrain.
    """

    def __init__(self):
        if (type(self) is TerrainLayer):
            raise TypeError("Cannot instantiate TerrainLayer directly")
        
        self.matrix = None
        self.terrain = None
        
    def generate(self):
        pass

class RiverLayer(TerrainLayer):
    def __init__(self, *args):
        super().__init__(*args)
        
    def generate(self):
        
        """ Generate the river system based on terrain's heightmap. """
        
        terrain = self.terrain
        dim = terrain.dim
        mthr = terrain.MOUNTAIN_THRESHOLD
        hmatrix = terrain.heightmap.matrix
        mtn_coords = np.array([])
        
        self.matrix = matrix = np.zeros(np.shape(hmatrix), dtype=np.uint8)
        
        # Extract all coordinates above mountain threshold from
        # terrain's heightmap
        
        try:
            mtn_coords = np.dstack(np.where(hmatrix >= mthr))[0]
            #mtn_coords = np.where(hmatrix >= mthr)
        except KeyError as e:
            pass
        
        # Shuffle mountain coordinates and pick river start points
        
        if (len(mtn_coords)):
            n_river_tiles = int(len(mtn_coords) * terrain.RIVER_DENSITY)
            np.random.shuffle(mtn_coords)
            mtn_coords = mtn_coords[0:n_river_tiles]
        
        for p in mtn_coords:
            x = p[0]
            y = p[1]
            matrix[x, y] = 1
