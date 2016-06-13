
import array
import numpy as np
import random

from random import randint

class Heightmap:

    """
    A class representing a heightmap and a method to generate one
    procedurally using the diamond-square algorithm.
    """

    INITIAL_RANGE = (0x40, 0xBF)
    PETURB_RANGE = 256
    PETURB_DECREASE = 0.35

    def __init__(
        self, dim,
        peturb_range=PETURB_RANGE, peturb_decrease=PETURB_DECREASE,
        randseed = None
    ):
        self.peturb_range = peturb_range
        self.peturb_decrease = peturb_decrease

        self.matrix = None
        self._dim = dim

        self._assert_dim()
        random.seed(randseed)

    def generate(self):

        """ Generate a heightmap using the diamond-square algorithm """

        square_dim = dim = self._dim
        rand_range = self.peturb_range
        t = self.matrix = np.zeros((dim, dim), dtype=np.uint8)
        x = 0
        y = 0

        # Init corner values

        t[0, 0] = randint(*self.INITIAL_RANGE)
        t[0, dim-1] = randint(*self.INITIAL_RANGE)
        t[dim-1, 0] = randint(*self.INITIAL_RANGE)
        t[dim-1, dim-1] = randint(*self.INITIAL_RANGE)

        # Run the algorithm with iteratively smaller squares

        while (square_dim > 2):
            while (y < dim - 1):
                while (x < dim - 1):
                    sq_average = self._set_square_average(x, y, square_dim, rand_range)
                    d_averages = self._set_diamond_averages(x, y, square_dim, rand_range)
                    x += (square_dim - 1)
                x = 0
                y += (square_dim - 1)
            y = 0
            square_dim = square_dim // 2 + 1
            rand_range -= int(rand_range * self.peturb_decrease)

        self._stretch_levels()
        return self.matrix

    def _set_point_perturbed_value(self, x, y, val, perturb_range):
        t = self.matrix
        half_range = perturb_range // 2
        val = val + randint(-half_range, half_range)

        if (val < 0):
            val = 0
        elif (val > 255):
            val = 255

        t[x, y] = val

    def _set_square_average(self, x, y, square_dim, rand_range):
        t = self.matrix

        p1 = t[x, y]
        p2 = t[x + square_dim - 1, y]
        p3 = t[x, y + square_dim - 1]
        p4 = t[x + square_dim - 1, y + square_dim - 1]

        avg = np.sum([p1, p2, p3, p4]) // 4
        midpoint = (square_dim - 1) // 2

        self._set_point_perturbed_value(x + midpoint, y + midpoint, avg, rand_range)

    def _set_diamond_average(self, x, y, halfsquare, rand_range):

        # This function receives the center point of a diamond

        t = self.matrix
        total = 0
        nval = 0
        coords = (
            (x, y - halfsquare),
            (x + halfsquare, y),
            (x, y + halfsquare),
            (x - halfsquare, y)
        )

        for p in coords:
            try:
                px = p[0]
                py = p[1]

                if (px < 0 or py < 0):
                    raise IndexError()
                total += t[px, py]
                nval += 1
            except IndexError as e:
                pass

        self._set_point_perturbed_value(x, y, total // nval, rand_range)

    def _set_diamond_averages(self, x, y, square_dim, rand_range):

        # This function receives the offsets and dimension of a square

        midpoint = (square_dim - 1) // 2

        self._set_diamond_average(x + midpoint, y, midpoint, rand_range)
        self._set_diamond_average(x + square_dim - 1, y + midpoint, midpoint, rand_range)
        self._set_diamond_average(x + midpoint, y + square_dim - 1, midpoint, rand_range)
        self._set_diamond_average(x, y + midpoint, midpoint, rand_range)

    def _stretch_levels(self):

        """
        Stretch the levels so that the lowest value would be 0 and the
        highest at 255. TODO: numpy-ify this.
        """

        t = self.matrix
        maxv = 0
        minv = 255

        for col in t:
            curr_max = max(col)
            curr_min = min(col)

            if (curr_max > maxv):
                maxv = curr_max
            if (curr_min < minv):
                minv = curr_min

        if (minv > 0 or maxv < 255):
            scale = 255 / (maxv - minv)

            for x in range(self._dim):
                for y in range(self._dim):
                    v = t[x, y]
                    t[x, y] = int((v - minv) * scale)

    def _assert_dim(self):

        # Assert the heightmap's dimension is a power of two plus one.

        dim = self._dim

        for i in range(1000):
            if (dim == 2**i + 1):
                return

        raise ValueError("Heightmap dimension must be a power of two + 1")

    def __str__(self):
        return str(self.matrix)
