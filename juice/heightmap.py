
import array
import pyglet

from random import randint

class Heightmap:
	
	PETURB_RANGE = 50
	PETURB_DECREASE = 0.5
	
	def __init__(self, dim):
		self._terrain = []
		self._dim = dim
		
		# TODO: assert w == 2**n + 1
	
	def generate(self):

		"""	Generate a heightmap using the diamond-square algorithm """

		t = self._terrain = []
		square_dim = dim = self._dim
		rand_range = self.PETURB_RANGE
		x = 0
		y = 0
		
		# Init the matrix
		
		for i in range(self._dim):
			col = []
			for j in range(self._dim):
				col.append(0)
			t.append(col)
		
		# Init corner values
		
		t[0][0] = randint(0, 255)
		t[0][dim-1] = randint(0, 255)
		t[dim-1][0] = randint(0, 255)
		t[dim-1][dim-1] = randint(0, 255)
		
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
			rand_range -= int(rand_range * 0.5)
		
		return t
			
	def get_imgdata(self):
		t = self._terrain
		imgdata = []
		w = len(t[0])
		h = len(t)
		
		for col in t:
			for v in col:
				for i in range(3):
					imgdata.append(v)
		
		return pyglet.image.ImageData(w, h, "RGB", array.array("B", imgdata).tostring())

	def _set_point_perturbed_value(self, x, y, val, perturb_range):
		t = self._terrain
		half_range = perturb_range // 2
		val = val + randint(-half_range, half_range)
		
		if (val < 0):
			val = 0
		elif (val > 255):
			val = 255
			
		t[x][y] = val

	def _set_square_average(self, x, y, square_dim, rand_range):
		t = self._terrain
		
		p1 = t[x][y]
		p2 = t[x + square_dim - 1][y]
		p3 = t[x][y + square_dim - 1]
		p4 = t[x + square_dim - 1][y + square_dim - 1]
		avg = int((p1 + p2 + p3 + p4) / 4)
		midpoint = (square_dim - 1) // 2
		
		self._set_point_perturbed_value(x + midpoint, y + midpoint, avg, rand_range)

	def _set_diamond_average(self, x, y, halfsquare, rand_range):
		
		# This function receives the center point of a diamond
		
		t = self._terrain
		values = []
		coords = [
			(x, y - halfsquare), 
			(x + halfsquare, y),
			(x, y + halfsquare),
			(x - halfsquare, y)
		]
		
		for p in coords:
			try:
				px = p[0]; py = p[1]
				values.append(t[px][py])
			except IndexError as e:
				pass
		
		avg = int(sum(values) / len(values))
		self._set_point_perturbed_value(x, y, avg, rand_range)

	def _set_diamond_averages(self, x, y, square_dim, rand_range):
		
		# This function receives the offsets and dimension of a square

		midpoint = (square_dim - 1) // 2
		
		self._set_diamond_average(x + midpoint, y, midpoint, rand_range)
		self._set_diamond_average(x + square_dim - 1, y + midpoint, midpoint, rand_range)
		self._set_diamond_average(x + midpoint, y + square_dim - 1, midpoint, rand_range)
		self._set_diamond_average(x, y + midpoint, midpoint, rand_range)
		
	def __str__(self):
		t = self._terrain
		dim = self._dim
		matrix = ""
		
		for i in range(dim):
			for j in range(dim):
				matrix += str(t[j][i]).ljust(4)
			matrix += "\n"
		
		return matrix
		
