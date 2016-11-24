
import numpy as np
import scipy.ndimage as ndi

#from juice.tileset import TileSet
#from juice.terrainlayer import \
#    TerrainLayer, RiverLayer, SeaLayer, BiomeLayer, CityLayer

class GameFieldLayer:

    """ A class representing any matrix associated with the game field.
    Notably subclassed by TerrainLayer.
    """

    def __init__(self, dim, fill=0):
        self.matrix = np.full((dim, dim), fill, dtype=np.uint8)

    def get_points(self, x=0, y=0, w=None, h=None, skip_zero=True):

        """ A generator method to loop over a subset of coordinates of a layer's
        matrix. If skip_zero is true, only positions with a nonzero value are
        returned. If x, y (offsets of a rectangle), w, h (dimensions of a
        rectangle) are not passed, yields all coordinates.
        """

        it = None

        if (not w and not h):
            it = np.nditer(self.matrix, flags=["multi_index"])
        else:
            it = np.nditer(self.matrix[y:y+h, x:x+w], flags=["multi_index"])

        while (not it.finished):
            v = int(it[0])

            if (not skip_zero or v > 0):
                p = it.multi_index
                yield (x + p[1], y + p[0], v)

            it.iternext()

    def foreach_neighbor(self, cb, x, y, *extra):

        """ Convenience routine to loop over all (edge and corner) neigbors. The
        documentation for foreach_edge_neighbor applies otherwise.
        """

        dim = self.terrain.dim

        if (self.foreach_edge_neighbor(cb, x, y, *extra) == False):
            return False

        # Loop over corner neighbors

        for (cx, cy) in ((x+1, y-1), (x+1, y+1), (x-1, y+1), (x-1, y-1)):
            if (cx >= 0 and cy >= 0 and cx < dim and cy < dim):
                if (cb(cx, cy, *extra) == False):
                    return False

        return True

    def foreach_edge_neighbor(self, cb, x, y, *extra):

        """ Convenience routine to loop over all edge neigbors. Excludes invalid
        coordinates. Callback can break by returning False, in which case the
        method returns False. Upon completion of iterating over all neighbors,
        returns True.
        """

        dim = self.terrain.dim

        for (cx, cy) in ((x, y-1), (x+1, y), (x, y+1), (x-1, y)):
            if (cx >= 0 and cy >= 0 and cx < dim and cy < dim):
                if (cb(cx, cy, *extra) == False):
                    return False

        return True

    def label_segments(self, min_size=0):

        """ Object method variant of label_matrix_segments, operates on
        self.matrix.
        """

        (self.matrix, n_labels) = \
            self.label_matrix_segments(self.matrix, min_size)
        return n_labels

    @staticmethod
    def label_matrix_segments(matrix, min_size=0):

        """ Static method. Label contiguous segments of a matrix and label these
        with successive integers starting with 1. Optionally leave only segments
        with size at least min_size. Returns a tuple (matrix, original number of
        labels).
        """

        labels = ndi.label(matrix)
        matrix = labels[0]
        n_labels = labels[1]

        if (min_size > 0):
            for i in range(1, n_labels + 1):
                label_indices = np.where(matrix == i)
                n = len(label_indices[0])

                if (n < min_size):
                    matrix[label_indices] = 0

        return (matrix, n_labels)
