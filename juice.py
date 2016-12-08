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
import pyglet.gl as gl

from juice.config           import config
from juice.gameview         import GameView
from juice.terrain          import Terrain
from juice.terrainlayer     import \
    TerrainLayer, RiverLayer, SeaLayer, BiomeLayer, CityLayer
from juice.window           import Window

GAME_WIDTH      = 1184
GAME_HEIGHT     = 736
TERRAIN_DIM     = 2**6
DEBUG_EVENTS    = False
DEBUG_GL        = True

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

def setup_misc():

    """ Miscellaneous global setup tasks. """
    
    if (not DEBUG_GL):
        pyglet.options['debug_gl'] = False
        
    np.set_printoptions(threshold=float("nan"))
    pyglet.gl.glEnable(gl.GL_BLEND)
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)

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
    window = Window(GAME_WIDTH, GAME_HEIGHT)

    setup_misc()
    setup_logging(args.log_level)
    info("random seed: %d", randseed)

    if (not args.load):
        terr = generate(randseed)
        if (args.save):
            save_state(terr, args.save)
    else:
        info("Loading map from `{}`".format(args.load))
        terr = load_state(args.load)
        
    if (args.timing):
        sys.exit(0)
    if (DEBUG_EVENTS):
        window.push_handlers(pyglet.window.event.WindowEventLogger())
    
    if (args.map):
        window.image = terr.get_map_imgdata(scaling=min(GAME_WIDTH, GAME_HEIGHT) // terr.dim)
    else:      
        window.gameview = GameView(terr)

    pyglet.app.run()

main()
