#!/usr/bin/env python3

import argparse
import array
import pprint
import pyglet
import random

from juice.heightmap import Heightmap
from juice.terrain import Terrain
from juice.terrainlayer import TerrainLayer, RiverLayer, SeaLayer

def draw_point(x, y):
    pyglet.graphics.draw(1, pyglet.gl.GL_POINTS,
            ("v2i", (x, y)),
            ('c3B', (255, 0, 0))
        )   

def parse_command_line():
	parser = argparse.ArgumentParser(description = "Juice: the power grid game")
	parser.add_argument(
		"-r", "--random-seed", type=int, help="Specify random seed")
	return parser.parse_args()

def main():
    GAME_WIDTH = 800
    GAME_HEIGHT = 600
    
    args = parse_command_line()
    window = pyglet.window.Window(GAME_WIDTH, GAME_HEIGHT)
    randseed = args.random_seed \
        if args.random_seed \
        else random.randint(1, 10000)
    
    terr = Terrain(65, randseed=randseed)
    terr.add_layer(SeaLayer(randseed=randseed))
    terr.add_layer(RiverLayer(randseed=randseed))
    terr.generate()

    img = terr.get_imgdata(scaling=8)

    @window.event
    def on_draw():
        window.clear()
        img.blit(0, 0)
    
    #window.push_handlers(pyglet.window.event.WindowEventLogger())
    print("random seed:", randseed)
    pyglet.app.run()

main()
