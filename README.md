
# Juice

Juice is an experiment in terrain generation algorithms and the beginnings of
a top-down scolling engine built on Python 3, [NumPy /
SciPy](https://scipy.org/), 
[pyglet](https://bitbucket.org/pyglet/pyglet/wiki/Home) (and OpenGL,
transitively).

![Screenshot](http://i.imgur.com/eBnm5sB.png)

## Terrain generation

Terrain generation is relatively feature-complete, including:

* An underlying heightmap for various purposes, e.g. river and sea generation.
* Various terrain layers generated on top of the heightmap (seas, rivers,
  biomes, roads and city locations).
* Normalization of the terrain layers so their elements would be presentable
  with a standard tile set (four straight edges, four convex corners, four
  concave corners and a solid tile).

This is mostly isolated into the Terrain, TerrainLayer (and subclasses
thereof) and HeightMap classes. Juice was initially envisoned as a standalone
game, hence there has been no effort to package this functionality into a
library, but the codebase could be a solid starting point for a game utilizing
a 2D terrain. The resulting map can be visualized by passing the `-m` flag to
`juice.py`.

## Scrolling engine

This project also includes basic final rendering of the game world onto a
scrollable pyglet / OpenGL viewport. The [LPC Tile
Atlas](http://lpc.opengameart.org/) is utilized (see LICENSE for details), but
as this is missing some graphics (rivers, roads,
cities), these features are represented by runtime-generated mock tiles. For a
demo, simply run `juice.py` without arguments.

## Usage

```
$ ./juice.py --help
usage: juice.py [-h] [-r RANDOM_SEED] [-d DIMENSION] [-t] [-L LOG_LEVEL] [-m]
                [-s SAVE] [-l LOAD]

Juice: the power grid game

optional arguments:
  -h, --help            show this help message and exit
  -r RANDOM_SEED, --random-seed RANDOM_SEED
                        Specify random seed
  -d DIMENSION, --dimension DIMENSION
                        Game field side length
  -t, --timing          Timing / profiling mode, exit after terrain generation
  -L LOG_LEVEL, --log-level LOG_LEVEL
                        Log level, one of CRITICAL, ERROR, WARNING, INFO,
                        DEBUG.
  -m, --map             Display overview map instead of entering the game
  -s SAVE, --save SAVE  Save a map to file
  -l LOAD, --load LOAD  Load a saved map
```

## Notes

There is no documentation besides the commented source. This project is not
under active development. It was imported to GitHub mainly in the hope of
possibly becoming a somewhat rough building block for a game needing terrain
generation and possibly a rough skeleton of a scrollable game world rendering.

