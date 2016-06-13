#!/usr/bin/env python3

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

def main():
    GAME_WIDTH = 800
    GAME_HEIGHT = 600
    
    window = pyglet.window.Window(GAME_WIDTH, GAME_HEIGHT)
    randseed = None
    
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
    pyglet.app.run()

main()
