
import collections

_config = dict(
    tileset = "assets/img/tileset.png",
    tiledim = 32
)

config = collections.namedtuple("Config", _config.keys())(**_config)
