#!/usr/bin/env python3

import argparse
import array
import logging
import pickle
import pprint
import random
import sys
import time

from logging import debug, info, warning, error

import numpy as np
import pyglet
import pyglet.window.key as key
import pyglet.gl as gl

from juice.gameview         import GameView
from juice.heightmap        import Heightmap
from juice.terrain          import Terrain
from juice.terrainlayer     import \
    TerrainLayer, RiverLayer, SeaLayer, BiomeLayer, CityLayer
from juice.tileclassifier   import TileClassifier
from juice.tileset          import TileSet

GAME_WIDTH = 832
GAME_HEIGHT = 640
TERRAIN_DIM = 2**6
TILE_DIM = 32

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
    parser.add_argument(
        "-L", "--log-level", type=str, default="INFO",
        help="Log level, one of CRITICAL, ERROR, WARNING, INFO, DEBUG."
    )    
    parser.add_argument(
        "-m", "--map", action="store_true",
        help="Display overview map instead of entering the game"
    )
    parser.add_argument(
        "-s", "--save", type=str, help="Save a map to file")
    parser.add_argument(
        "-l", "--load", type=str, help="Load a saved map")
    return parser.parse_args()

def setup_logging(loglevel_str):
    handler = logging.StreamHandler()
    loglevel = getattr(logging, loglevel_str.upper())
    logformat = "%(asctime)s %(levelname)7s: %(message)s"    
    
    logging.basicConfig(level=loglevel, format=logformat, handlers=[handler])

def save_state(obj, fn):
    f = open(fn, "wb")
    pickle.dump(obj, f)

def load_state(fn):
    f = open(fn, "rb")
    return pickle.load(f)

def generate(randseed=None):

    """ Generate a Terrain and return it. """

    terr = Terrain(TERRAIN_DIM, randseed=randseed)
    terr.add_layer(SeaLayer(randseed=randseed))
    terr.add_layer(RiverLayer(randseed=randseed))
    terr.add_layer(BiomeLayer(randseed=randseed))
    #terr.add_layer(CityLayer(randseed=randseed))
    terr.generate(post_generate_cb=timed_print)

    return terr

def main():
    args = parse_command_line()
    randseed = args.random_seed \
        if args.random_seed \
        else random.randint(1, 10000)
    
    scaling = min(GAME_WIDTH, GAME_HEIGHT) // TERRAIN_DIM
    w_tiles = GAME_WIDTH // TILE_DIM
    h_tiles = GAME_HEIGHT // TILE_DIM
    
    window = pyglet.window.Window(GAME_WIDTH, GAME_HEIGHT)
    terr = None
    view = None
    display_img = None

    viewport_x = 0
    viewport_y = 0
    np.set_printoptions(threshold=float("nan"))
    setup_logging(args.log_level)
    
    info("random seed: %d", randseed)
    info("scaling: %d", scaling)

    pyglet.gl.glEnable(gl.GL_BLEND)
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)

    if (not args.load):
        terr = generate(randseed)
        if (args.save):
            save_state(terr, args.save)
    else:
        info("Loading map from `{}`".format(args.load))
        terr = load_state(args.load)
    
    if (args.timing):
        sys.exit(0)

    if (args.map):
        display_img = terr.get_map_imgdata(scaling=scaling)
    
    tileset = TileSet("assets/img/tileset.png", TILE_DIM)
    view = GameView(terr, tileset)

    def constrain_vpcoords(x, y):
        dim = terr.dim
        max_x = dim - w_tiles
        max_y = dim - h_tiles
        
        if (x < 0): x = 0
        elif (x > max_x): x = max_x
        
        if (y < 0): y = 0
        elif (y > max_y): y = max_y
            
        return (x, y)

    @window.event
    def on_draw():
        window.clear()
        
        if (display_img):
            display_img.blit(0, 0)
        else:
            view.blit(viewport_x, viewport_y, w_tiles, h_tiles)
    
    @window.event
    def on_text_motion(motion):
        nonlocal viewport_x
        nonlocal viewport_y
        
        if (motion == key.MOTION_UP):
            viewport_y -= 1
        elif (motion == key.MOTION_DOWN):
            viewport_y += 1
        elif (motion == key.MOTION_LEFT):
            viewport_x -= 1
        elif (motion == key.MOTION_RIGHT):
            viewport_x += 1
            
        (viewport_x, viewport_y) = constrain_vpcoords(viewport_x, viewport_y)

    #window.push_handlers(pyglet.window.event.WindowEventLogger())
    pyglet.app.run()

main()
