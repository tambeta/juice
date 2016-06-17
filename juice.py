#!/usr/bin/env python3

import argparse
import array
import pprint
import random
import sys
import time

import pyglet

from juice.heightmap import Heightmap
from juice.terrain import Terrain
from juice.terrainlayer import TerrainLayer, RiverLayer, SeaLayer, BiomeLayer

_g = {}



def timed_print(*args):
    msg = ""
    delta = 0
    t = time.process_time()
    
    if ("timer_last_t" not in _g):
        delta = t
    else:
        delta = t - _g["timer_last_t"]
    
    for i in args:
        msg += str(i) + " "
    
    _g["timer_last_t"] = t
    print("{:.4f} {:.4f} {}".format(t, delta, msg))

def parse_command_line():
	parser = argparse.ArgumentParser(description = "Juice: the power grid game")
	parser.add_argument(
		"-r", "--random-seed", type=int, help="Specify random seed")
	parser.add_argument(
		"-t", "--timing", action="store_true",
        help="Timing / profiling mode, exit after terrain generation"
    )
	return parser.parse_args()

def main():
    GAME_WIDTH = 800
    GAME_HEIGHT = 600
    TERRAIN_DIM = 2**7
    
    args = parse_command_line()
    randseed = args.random_seed \
        if args.random_seed \
        else random.randint(1, 10000)
    scaling = min(GAME_WIDTH, GAME_HEIGHT) // TERRAIN_DIM
    window = pyglet.window.Window(GAME_WIDTH, GAME_HEIGHT)
    
    print("random seed:", randseed)
    
    terr = Terrain(TERRAIN_DIM, randseed=randseed)
    terr.add_layer(SeaLayer(randseed=randseed))
    terr.add_layer(RiverLayer(randseed=randseed))
    terr.add_layer(BiomeLayer(randseed=randseed))
    terr.generate(post_generate_cb=timed_print)
    
    if (args.timing):
        sys.exit(0)
    
    img = terr.get_imgdata(scaling=scaling)

    @window.event
    def on_draw():
        window.clear()
        img.blit(0, 0)
    
    #window.push_handlers(pyglet.window.event.WindowEventLogger())    
    pyglet.app.run()

main()
