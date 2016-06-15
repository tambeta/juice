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
from juice.terrainlayer import TerrainLayer, RiverLayer, SeaLayer

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
	return parser.parse_args()

def main():
    GAME_WIDTH = 800
    GAME_HEIGHT = 600
    
    args = parse_command_line()
    window = pyglet.window.Window(GAME_WIDTH, GAME_HEIGHT)
    randseed = args.random_seed \
        if args.random_seed \
        else random.randint(1, 10000)
    
    terr = Terrain(256, randseed=randseed)
    terr.add_layer(SeaLayer(randseed=randseed))
    terr.add_layer(RiverLayer(randseed=randseed))
    terr.generate(post_generate_cb=timed_print)

    img = terr.get_imgdata(scaling=2)

    @window.event
    def on_draw():
        window.clear()
        img.blit(0, 0)
    
    #window.push_handlers(pyglet.window.event.WindowEventLogger())
    print("random seed:", randseed)
    pyglet.app.run()

main()
