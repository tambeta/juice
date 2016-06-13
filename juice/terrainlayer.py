
import numpy as np
import random

class TerrainLayer:

    """ A layer of Terrain. The TerrainLayer base class cannot be
    instantiated directly, but upon instantiation of subclasses the new
    TerrainLayer will be added to the passed Terrain.
    """

    def __init__(self, randseed=None):
        if (type(self) is TerrainLayer):
            raise TypeError("Cannot instantiate TerrainLayer directly")
        
        self.matrix = None
        self.terrain = None
        
        random.seed(randseed)
        np.random.seed(randseed)
        
    def generate(self):
        pass
    
    def _init_matrix(self):
        
        """ Init the matrix and return it. """
        
        self.matrix = np.zeros(np.shape(self.terrain.heightmap.matrix), dtype=np.uint8)
        return self.matrix
    
    def _foreach_edge_neighbor(self, cb, x, y, *extra):
        
        """ Convenience routine to loop over all edge neigbors. Excludes invalid
        coordinates. Callback can break by returning False.
        """
        
        dim = self.terrain.dim
        
        for (cx, cy) in ((x, y-1), (x+1, y), (x, y+1), (x-1, y)):
            if (cx >= 0 and cy >= 0 and cx < dim and cy < dim):
                if (cb(cx, cy, *extra) == False):
                    return

class SeaLayer(TerrainLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def generate(self):
        
        """ Generate the sea layer based on sea threshold. """
        
        terrain = self.terrain
        hmatrix = terrain.heightmap.matrix
        self.matrix = np.where(hmatrix <= terrain.SEA_THRESHOLD, 1, 0)
        
class RiverLayer(TerrainLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def generate(self):
        
        """ Generate the river system based on terrain's heightmap. """
        
        terrain = self.terrain
        mthr = terrain.MOUNTAIN_THRESHOLD
        matrix = self._init_matrix()
        hmatrix = terrain.heightmap.matrix
        mtn_coords = np.array([])
        rvr_source_coords = mtn_coords        
        
        # Extract all coordinates above mountain threshold from
        # terrain's heightmap
        
        try:
            mtn_coords = np.dstack(np.where(hmatrix >= mthr))[0]
        except KeyError as e:
            pass
        
        # Shuffle mountain coordinates and pick river sources
        
        if (len(mtn_coords)):
            n_river_tiles = int(len(mtn_coords) * terrain.RIVER_DENSITY)
            
            if (n_river_tiles < terrain.MIN_RIVER_SOURCES):
                n_river_tiles = min(len(mtn_coords), terrain.MIN_RIVER_SOURCES)
            
            np.random.shuffle(mtn_coords)
            rvr_source_coords = mtn_coords[0:n_river_tiles]
        else:
            rvr_source_coords = mtn_coords
        
        # For each river source, generate a river
        
        for (i, p) in enumerate(rvr_source_coords, start=1):
            self._generate_river(p[1], p[0], i)
            

    def _confirm_square_ok(self, x, y, river_id, ok_neighbors, neigh_rivers_threshold, allow_others):
        
        """ Helper routine to confirm that a position is OK for a river. A
        position is suitable if itself or not more than neigh_rivers_threshold
        of its edge neighbors are a river square. If allow_others is true, other
        river IDs are ignored.
        """
        
        matrix = self.matrix
        predicate = None
        n_river_nbrs = 0
        
        if (allow_others):
            predicate = (lambda x, y: matrix[y, x] != river_id)
        else:
            predicate = (lambda x, y: matrix[y, x] == 0)
        
        def confirm_nbrs_not_river(x, y):
            nonlocal n_river_nbrs
            if (not predicate(x, y)):
                n_river_nbrs += 1
        
        self._foreach_edge_neighbor(confirm_nbrs_not_river, x, y)
        
        if (predicate(x, y) and n_river_nbrs <= neigh_rivers_threshold): #*
            ok_neighbors.append((x, y))
            return True
    
    def _is_square_converging(self, x, y, river_id):
        matrix = self.matrix
        is_converging = False
        
        def have_other_river_nbrs(x, y):
            nonlocal is_converging
            if (matrix[y, x] > 0 and matrix[y, x] != river_id):
                is_converging = True
                return False
        
        self._foreach_edge_neighbor(have_other_river_nbrs, x, y)
        return is_converging
    
    def _delete_river(self, river_id):
        matrix = self.matrix
        it = np.nditer(matrix, flags=["multi_index"])
        
        while (not it.finished):
            if (it[0] == river_id):
                p = it.multi_index                
                matrix[p[0], p[1]] = 0
            it.iternext()
    
    def _generate_river(self, x, y, river_id, iteration=1):
        
        """ Generate a river starting from (x, y). Returns true on success,
        false otherwise. Invoked recursively.
        """
        
        hmatrix = self.terrain.heightmap.matrix
        matrix = self.matrix
        ok_neighbors = []
        ret = False
        
        if (iteration == 1 and not self._confirm_square_ok(x, y, river_id, [], 0, False)):
            return False
        elif (hmatrix[y, x] <= self.terrain.SEA_THRESHOLD):
            return True
        elif (self._is_square_converging(x, y, river_id)):
            matrix[y, x] = river_id
            return True
        matrix[y, x] = river_id
        
        # Pick all suitable edge-neighbors for current position, sort by height
        # and use the lowest suitable neighbor point for continuing recursively.
        
        self._foreach_edge_neighbor(
            self._confirm_square_ok, x, y, river_id, ok_neighbors, 1, True)
        ok_neighbors.sort(key=lambda p: hmatrix[p[1], p[0]])
        
        if (len(ok_neighbors)):
            p = ok_neighbors[0]
            ret = self._generate_river(p[0], p[1], river_id, iteration+1)
        
        # Delete river upon final return, if not successful
        
        if (iteration == 1 and not ret):
            self._delete_river(river_id)
        
        return ret
    
