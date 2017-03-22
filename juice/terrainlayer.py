
import abc
import heapq
import math
import random
import re
import functools

from logging import debug, info, warning, error

import numpy as np
import scipy.signal

from juice.city             import City
from juice.heightmap        import Heightmap
from juice.gamefieldlayer   import GameFieldLayer
from juice.tileclassifier   import \
    TileClassifierSolid, TileClassifierLine, TileClassifierDelta, TileClassifierSimple

class RequirementError(Exception):
    pass

class TerrainLayer(GameFieldLayer, metaclass=abc.ABCMeta):

    """ A layer of Terrain. The TerrainLayer base class cannot be
    instantiated directly. Subclasses must call __init__ from their
    constructors. Subclasses' generate method is wrapped by
    _check_requirements. Subclasses can list generation requirements in
    self._require (satisfied if the associated Terrain has the listed layers
    and these have been generated).
    """

    def __init__(self, terrain, randseed=None):
        if (type(self) is TerrainLayer):
            raise TypeError("Cannot instantiate TerrainLayer directly")

        self.matrix = None
        self.terrain = terrain
        self.classification = None

        self._require = None
        self._randseed = randseed
        self._generate = self.generate
        self.generate = self._check_requirements

        random.seed(randseed)
        np.random.seed(randseed)

    @abc.abstractmethod
    def generate(self):
        pass

    def _init_matrix(self):

        """ Init the matrix and return it. """

        self.matrix = np.zeros(np.shape(self.terrain.heightmap.matrix), dtype=np.uint8)
        return self.matrix

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
    
    @staticmethod
    def classified(fn):

        """ Decorator for generate methods. Applies tile classification /
        normalization after generation and stores it in the `classification`
        attribute. Object's classify_X attribute controls TileClassifier's X
        option. The classifier attribute specifies the TileClassifier subclass,
        by default TileClassifierSolid is used.
        """

        @functools.wraps(fn)
        def wrapped(tlayer):
            cfier_args = {}
            
            for (k, v) in vars(tlayer).items():
                m = re.match(r"classify_(.*)", k)
                if (not m):
                    continue
                cfier_args[m.group(1)] = v

            try:
                cfier = tlayer.classifier
            except AttributeError:
                cfier = TileClassifierSolid

            fn(tlayer)
            cx = cfier(tlayer, **cfier_args).classify()
            tlayer.classification = cx

        return wrapped
        
    @staticmethod
    def defer_classified(fn):
        
        """ Sister decorator for `classified`; this variation applies
        classification to the layer only after all layers have been
        generated. TODO.
        """
        
        pass

class SeaLayer(TerrainLayer):

    """ NOTE: SeaLayer classification is currently reversed, i.e. represents
    the ground.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classify_rev = True

    @TerrainLayer.classified
    def generate(self):

        """ Generate the sea layer based on sea threshold. Disallow seas
        (contiguous areas of water) below a fixed size.
        """

        terrain = self.terrain
        hmatrix = terrain.heightmap.matrix

        self.matrix = \
            np.where(hmatrix <= terrain.SEA_THRESHOLD, 1, 0)
        self.label_segments(terrain.MIN_SEA_SIZE)

class RiverLayer(TerrainLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._require = (SeaLayer,)        
        self.classifier = TileClassifierLine
        self.classify_extend = False

    @TerrainLayer.classified
    def generate(self):

        """ Generate the river system based on terrain's heightmap. Rivers flow
        from mountains (highest locations on the heighmap) towards the sea.
        Rivers that fail (e.g. run into itself) are removed.
        """

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
                matrix[y, x] = river_id # For DeltaLayer generation, removed therein
                return True
            elif (self._is_square_converging(x, y, river_id)):
                matrix[y, x] = river_id
                return True
            matrix[y, x] = river_id

            # Pick all suitable edge-neighbors for current position, sort by height
            # and use the lowest suitable neighbor point for continuing. Delete river
            # and fail if no suitabe neighbors.

            self.foreach_edge_neighbor(
                self._confirm_square_ok, x, y, river_id, ok_neighbors, 1, True)
            random.shuffle(ok_neighbors)
            ok_neighbors.sort(key=lambda p: hmatrix[p[1], p[0]])

            if (len(ok_neighbors)):
                p = ok_neighbors[0]
                x = p[0]
                y = p[1]
            else:
                matrix[matrix == river_id] = 0
                return False

        raise RuntimeError("Should never execute this line")

    def _confirm_square_ok(
        self, x, y, river_id, ok_neighbors, neigh_rivers_threshold, allow_others):

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

        self.foreach_edge_neighbor(confirm_nbrs_not_river, x, y)

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

        self.foreach_edge_neighbor(have_other_river_nbrs, x, y)
        return is_converging

class DeltaLayer(TerrainLayer):

    """ The layer of river deltas. Marks the boundaries where river becomes
    the sea, yielding neighboring pairs of DELTA_SEA and DELTA_RIVER for the
    classifier.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._require = (RiverLayer,)        
        self.classifier = TileClassifierDelta
        self.classify_terrain = self.terrain
    
    @TerrainLayer.classified
    def generate(self):
        
        """ Let SD be a matrix > 0 where rivers and seas ovelap. Let C be a
        convolution of SD with an edge neighbor detecting kernel. Let RD be a
        matrix > 0 where C and rivers overlap. The delta matrix is the
        combination of SD and RD.
        
        Note that this method is tightly coupled to RiverLayer: river tiles
        extending into the sea and used solely for delta construction are
        removed from its matrix and classification.
        """
        
        matrix = self._init_matrix()
        
        terrain = self.terrain
        rlayer = terrain.get_layer_by_type(RiverLayer)
        smatrix = terrain.get_layer_by_type(SeaLayer).matrix
        rmatrix = rlayer.matrix        
        conv_matrix = np.array(((0, 1, 0), (1, 0, 1), (0, 1, 0)))
            
        sdelta_coords = np.nonzero(np.logical_and(smatrix > 0, rmatrix > 0))
        matrix[sdelta_coords] = terrain.DELTA_SEA
        
        rmatrix[sdelta_coords] = 0                      # Remove from river matrix
        rlayer.classification.matrix[sdelta_coords] = 0 # Remove from river cxion matrix
        
        conv = scipy.signal.convolve2d(matrix, conv_matrix, mode="same")        
        rdelta_coords = np.nonzero(np.logical_and(rmatrix > 0, conv > 0))        
        matrix[rdelta_coords] = terrain.DELTA_RIVER
        
        self._matrix = matrix

class BiomeLayer(TerrainLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._require = (SeaLayer, RiverLayer)

    @TerrainLayer.classified
    def generate(self):

        """ Biomes are generated based on the heightmap, allowed in intermediate
        heights between sea and mountains. Contiguous biome segments are
        assigned a random ID (desert or forest). Note that MIN_BIOME_SIZE is
        enforced _before_ classification / normalization.
        """

        terrain = self.terrain
        hmatrix = terrain.heightmap.matrix
        smatrix = terrain.get_layer_by_type(SeaLayer).matrix
        rmatrix = terrain.get_layer_by_type(RiverLayer).matrix
        biome_ids = (terrain.BIOME_FOREST, terrain.BIOME_DESERT)

        # Set a height range to biome

        self.matrix = np.where(np.logical_and(
            hmatrix > terrain.SEA_THRESHOLD + terrain.BIOME_H_DELTA,
            hmatrix < terrain.MOUNTAIN_THRESHOLD - terrain.BIOME_H_DELTA
        ), 1, 0)

        # Unset areas under rivers and next to the sea. Use a 3x3 convolution
        # filter on the sea matrix to find beach tiles.

        sconv = scipy.signal.convolve2d(smatrix, np.ones((3, 3)), mode="same")

        self.matrix = np.where(
            np.logical_and(np.logical_and(rmatrix == 0, smatrix == 0), sconv == 0),
            self.matrix, 0
        )

        # Assign random types to contiguous segments

        n_segments = \
            self.label_segments(terrain.MIN_BIOME_SIZE)

        for segment_id in range(1, n_segments + 1):
            segment_size = len(np.where(self.matrix == segment_id)[0])

            if (segment_size):
                biome_id = random.sample(biome_ids, 1)[0]
                self.matrix[self.matrix == segment_id] = biome_id

class CityLayer(TerrainLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._require = (SeaLayer, RiverLayer, BiomeLayer)
        self.classifier = TileClassifierSimple
        
        self.cities = []
        self._cityindex = {}
        
    @TerrainLayer.classified
    def generate(self):

        """ Generate city layer by assigning a score to each allowed land square
        (e.g. by biome and proximity to water), then picking n_cities weighed by
        score.
        """

        terrain = self.terrain

        matrix = self._init_matrix()
        hmatrix = terrain.heightmap.matrix
        smatrix = terrain.get_layer_by_type(SeaLayer).matrix
        rmatrix = terrain.get_layer_by_type(RiverLayer).matrix
        bmatrix = terrain.get_layer_by_type(BiomeLayer).matrix

        landmatrix = self.label_matrix_segments(
            np.where(smatrix == 0, 1, 0), terrain.MIN_POPSUPPORT_SIZE)[0]
        landmatrix = \
            np.where(np.logical_and(landmatrix != 0, rmatrix == 0), 1, 0)

        n_coords = len(np.nonzero(landmatrix)[0])
        n_cities = int(n_coords * terrain.CITY_DENSITY)
        coord_i = 0
        coords = []
        score_vec = np.empty([n_coords])
        coord_i_vec = np.arange(n_coords)

        def check_river_adjacency(x, y):
            if (rmatrix[y, x] != 0):
                return False

        def check_sea_adjacency(x, y):
            if (smatrix[y, x] != 0):
                return False

        it = np.nditer(matrix, flags=["multi_index"])

        while (not it.finished):
            p = it.multi_index
            x = p[1]; y = p[0]
            score = 1

            if (landmatrix[y, x] == 0):
                it.iternext()
                continue

            if (self.foreach_neighbor(check_river_adjacency, x, y) == False):
                score += 3
            if (self.foreach_neighbor(check_sea_adjacency, x, y) == False):
                score += 3

            if (bmatrix[y, x] == terrain.BIOME_DESERT):
                score -= 0.9
            elif (bmatrix[y, x] == terrain.BIOME_FOREST):
                score -= 0.5

            score_vec[coord_i] = score
            coords.append((x, y))
            coord_i += 1
            it.iternext()

        assert(coord_i == n_coords == len(coords))

        score_vec /= np.sum(score_vec)
        city_coord_is = \
            np.random.choice(coord_i_vec, size=n_cities, p=score_vec)

        for i in np.nditer(city_coord_is):
            p = coords[i]; x = p[0]; y = p[1]
            self.matrix[p[1], p[0]] = 1

        self._remove_close_cities()
        self._create_objects()

    def _remove_close_cities(self):

        """ After layer generation, iterate over cities pair-wise and remove one
        in every pair whose distance is lower than a threshold.

        TODO: possibly use convolution for a massive speedup.
        """

        matrix = self.matrix
        terrain = self.terrain
        coords = np.dstack(np.nonzero(self.matrix))[0]
        d_threshold = min(
            terrain.dim // terrain.CITY_CLOSENESS_FACTOR,
            terrain.MAX_CITY_DISALLOW_RADIUS
        )

        def foreach_coord(coords, cb, *extra):
            x = 0
            y = 0

            for (i, c) in enumerate(np.nditer(coords, order="C")):
                if (i % 2 == 0):
                    y = c
                else:
                    x = c
                    cb(x, y, *extra)

        def remove_close_dests(src_x, src_y, coords, matrix):
            def check_and_remove(dst_x, dst_y):
                if (src_x == dst_x and src_y == dst_y):
                    return
                elif (matrix[dst_y, dst_x] == 0 or matrix[src_y, src_x] == 0):
                    return
                elif (abs(src_x - dst_x) > d_threshold or abs(src_y - dst_y) > d_threshold):
                    return
                elif (math.sqrt((src_x - dst_x)**2 + (src_y - dst_y)**2) > d_threshold):
                    return

                matrix[dst_y, dst_x] = 0

            foreach_coord(coords, check_and_remove)

        foreach_coord(coords, remove_close_dests, coords, matrix)
        self.matrix = matrix
    
    def _create_objects(self):
        
        """ Create the City objects. """
        
        i = 0        
        m = self.matrix
        coords = np.transpose(np.nonzero(m))
        
        self.cities = []
        
        for c in coords:
            x = c[1]
            y = c[0]
            
            self.cities.append(City(x, y))
            
            try:
                self._cityindex[x]
            except KeyError:
                self._cityindex[x] = {}
            
            self._cityindex[x][y] = i
            i += 1

class RoadLayer(TerrainLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._require = (CityLayer,)
        self.classifier = TileClassifierLine
        
        self._weightmap = None
        
    @TerrainLayer.classified
    def generate(self):
        terrain = self.terrain
        cities = terrain.get_layer_by_type(CityLayer).cities
        n_roads = len(cities) // 2
        
        self._init_matrix()
        self._init_weightmap()
        
        debug("Generating {} roads between {} cities".format(n_roads, len(cities)))
        
        for i in range(n_roads):
            self._generate_road(*random.sample(cities, 2))

    def _init_weightmap(self):
        
        """ Create the matrix of weigths, or movement points for the terrain,
        used in pathfinding.
        """
        
        terrain = self.terrain
        smatrix = terrain.get_layer_by_type(SeaLayer).matrix        
        bmatrix = terrain.get_layer_by_type(BiomeLayer).matrix
        
        rlayer = terrain.get_layer_by_type(RiverLayer)
        rmatrix = terrain.get_layer_by_type(RiverLayer).matrix
        rcxion_matrix = rlayer.classification.matrix
        
        wm = np.zeros((terrain.dim, terrain.dim), dtype=np.floating)
        
        # Sea is impassable
        
        wm = np.where(smatrix, float("inf"), 1.0)
        
        # Biomes incur penalties
        
        wm = np.where(bmatrix == terrain.BIOME_DESERT,
            wm + terrain.MP_PENALTY_DESERT, wm)
        wm = np.where(bmatrix == terrain.BIOME_FOREST,
            wm + terrain.MP_PENALTY_FOREST, wm)
        
        # Rivers are passable only through straight sections and incur a
        # high penalty
        
        wm = np.where(rcxion_matrix, float("inf"), wm)
        wm = np.where(
            np.logical_or(
                rcxion_matrix == TileClassifierLine.TT_STRAIGHT_WE, 
                rcxion_matrix == TileClassifierLine.TT_STRAIGHT_NS
            ), terrain.MP_BRIDGE, wm)
        
        self._weightmap = wm

    def _generate_road(self, start_city, end_city):
        
        """ Generate a road between two Cities using Dijkstra's algorithm. """
        
        cx = start_city.x
        cy = start_city.y
        ex = end_city.x
        ey = end_city.y
        
        inf = float("inf")
        terrain = self.terrain
        dim = terrain.dim                
        distm = np.full((dim, dim), inf, dtype=np.floating)        
        hmatrix = terrain.heightmap.matrix
        wm = self._weightmap
        m = self.matrix
        to_visit = []
        
        distm[cy, cx] = 0
        debug("Generating road from ({}, {}) -> ({}, {})".format(cx, cy, ex, ey))        

        while (True):
            curr_d = distm[cy, cx]
            
            def neighbor_callback(nx, ny):
                
                # Consider every edge neighbor of current position: if distance is smaller
                # than stored in the distance matrix, update distance and add position to
                # the priority queue of unvisited positions. A dynamic pqueue works as
                # long as there are no negative penalties in the weight matrix. Elevation
                # penalties are added to the underlying weightmap here. If a road already
                # exists, there is a low, fixed movement cost instead to encourage re-
                # using existing roads.
                
                if (m[ny, nx] > 0):
                    d = curr_d + terrain.MP_ROAD
                else:
                    elev_penalty = abs(int(hmatrix[cy, cx]) - int(hmatrix[ny, nx]))
                    elev_penalty *= terrain.MP_PENALTY_ELEV
                    d = curr_d + wm[ny, nx] + elev_penalty
                
                if (d < distm[ny, nx]):
                    distm[ny, nx] = d
                    heapq.heappush(to_visit, (d, nx, ny))
            
            GameFieldLayer.foreach_matrix_edge_neighbor(wm, neighbor_callback, cx, cy)
                
            try:
                (d, cx, cy) = heapq.heappop(to_visit)
            except IndexError:
                d = inf
            
            if (d == inf):
                debug("\tno route to endpoint")
                break
            if (cx == ex and cy == ey):
                self._traceback_road(end_city, distm)
                debug("\troute to endpoint found, distance {}".format(distm[ey, ex]))
                break
        
    def _traceback_road(self, end_city, distm):
        
        """ After running Dijkstra, trace back road from endpoint to start point
        and store it in the layer matrix.
        """
        
        distl = GameFieldLayer(distm)
        cx = end_city.x
        cy = end_city.y
        d = distl[cx, cy]
        m = self.matrix
        
        m[cy, cx] = 1

        while(d > 0):
            def find_min_d_neighbor(nx, ny):
                nonlocal d, cx, cy
                
                if (distl[nx, ny] < d):
                    d = distl[nx, ny]
                    cx = nx
                    cy = ny            
            
            distl.foreach_edge_neighbor(find_min_d_neighbor, cx, cy)
            m[cy, cx] = 1
