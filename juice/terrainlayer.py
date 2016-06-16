
import random

import numpy as np
import scipy.ndimage as ndi

class RequirementError(Exception):
    pass

class TerrainLayer:

    """ A layer of Terrain. The TerrainLayer base class cannot be
    instantiated directly. Subclasses must call __init__ from their
    constructors. Subclasses' generate method is wrapped by
    _check_requirements. Subclasses can list generation requirements in
    self._require (satisfied if the associated Terrain has the listed layers
    and these have been generated).
    """

    def __init__(self, randseed=None):
        if (type(self) is TerrainLayer):
            raise TypeError("Cannot instantiate TerrainLayer directly")

        self.matrix = None
        self.terrain = None
        self._require = None

        self._generate = self.generate
        self.generate = self._check_requirements

        random.seed(randseed)
        np.random.seed(randseed)

    def _check_requirements(self):

        """ A wrapper for checking the generation requirements, i.e. layers that
        need to have a generated matrix beforehand.
        """

        if (self._require):
            for r in self._require:
                try:
                    layer = self.terrain.get_layer_by_type(r)
                    if (not isinstance(layer.matrix, np.ndarray)):
                        raise LookupError()
                except LookupError as e:
                    raise RequirementError(\
                        "Requirement " + str(r) + " not satisfied for " + str(self))
        
        # Call the wrapped method, invalidate matrix in case of any exceptions
        
        try:
            self._generate()
        except Exception as e:
            self.matrix = None
            raise e

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

        """ Generate the sea layer based on sea threshold. Disallow seas
        (contiguous areas of water) below a fixed size.
        """

        terrain = self.terrain
        hmatrix = terrain.heightmap.matrix

        matrix = \
            np.where(hmatrix <= terrain.SEA_THRESHOLD, 1, 0)
        labels = ndi.label(matrix)
        matrix = labels[0]
        n_labels = labels[1]

        # Filter seas below threshold size

        for i in range(1, n_labels + 1):
            sea_indices = np.where(matrix == i)
            n = len(sea_indices[0])

            if (n < terrain.MIN_SEA_SIZE):
                matrix[sea_indices] = 0

        self.matrix = matrix

class RiverLayer(TerrainLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._require = (SeaLayer,)

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
            if (i > 255):
                break
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
        matrix[matrix == river_id] = 0

    def _generate_river(self, x, y, river_id):

        """ Generate a river starting from (x, y). Returns True on success,
        False otherwise.
        """

        hmatrix = self.terrain.heightmap.matrix
        smatrix = self.terrain.get_layer_by_type(SeaLayer).matrix
        matrix = self.matrix

        if (not self._confirm_square_ok(x, y, river_id, [], 0, False)):
            return False
        if (river_id >= 2 ** (matrix.dtype.itemsize * 8)):
            raise ValueError(
                "River ID {} is larger than can be held by {}".format(river_id, matrix.dtype))
            
        while True:
            ok_neighbors = []
            
            if (smatrix[y, x] > 0):
                return True
            elif (self._is_square_converging(x, y, river_id)):
                matrix[y, x] = river_id
                return True
            matrix[y, x] = river_id

            # Pick all suitable edge-neighbors for current position, sort by height
            # and use the lowest suitable neighbor point for continuing. Delete river
            # and fail if no suitabe neighbors.

            self._foreach_edge_neighbor(
                self._confirm_square_ok, x, y, river_id, ok_neighbors, 1, True)
            ok_neighbors.sort(key=lambda p: hmatrix[p[1], p[0]])

            if (len(ok_neighbors)):
                p = ok_neighbors[0]
                x = p[0]
                y = p[1]
            else:
                self._delete_river(river_id)
                return False

        raise RuntimeError("Should never execute this line")

