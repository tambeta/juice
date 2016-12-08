
import pyglet.window as window
import pyglet.window.key as key
import pyglet.window.mouse as mouse

from juice.gameview import GameView

class DisallowedInstantiation(Exception):
    pass

class Window(window.Window):
    
    """ A basic window that can display an image as a convenience, if
    `image` is set. Upon setting `gameview`, self is cast into the
    _GameViewWindow subclass. The reason for the slightly convoluted
    mechanism is that a Window must be constructed before a GameView, as
    otherwise various crucial windowing / OpenGL init tasks have not been
    run, notably the color buffer will be botched.
    """
    
    def __init__(self, w, h, *args, **kwargs):
        super().__init__(w, h, *args, **kwargs)
        
        self._viewport_x = 0
        self._viewport_y = 0
        self._tiledim = None        
        self._gameview = None
        
        self.image = None

    def on_draw(self):
        if (self.image):
            self.image.blit(0, 0)
    
    @property
    def gameview(self):
        return self._gameview
        
    @gameview.setter
    def gameview(self, gv):
        self._gameview = gv
        self._tiledim = gv.tileset.tiledim
        self.__class__ = _GameViewWindow

class _GameViewWindow(Window):
    
    """ A Window with a bound GameView. """
    
    def __init__(self, *args, **kwargs):
        raise DisallowedInstantiation(
            "Cannot instantiate {} directly".format(type(self).__name__))
    
    def on_draw(self):
        (self._viewport_x, self._viewport_y) = \
            self._gameview.blit(self._viewport_x, self._viewport_y)
    
    def on_text_motion(self, motion):
        if (motion == key.MOTION_UP):
            self._viewport_y -= self._tiledim
        elif (motion == key.MOTION_DOWN):
            self._viewport_y += self._tiledim
        elif (motion == key.MOTION_LEFT):
            self._viewport_x -= self._tiledim
        elif (motion == key.MOTION_RIGHT):
            self._viewport_x += self._tiledim
    
    def on_mouse_release(self, x, y, button, mods):
        if (button != mouse.LEFT):
            return
        
        gv = self._gameview
        terrain = gv.terrain
        (tx, ty) = gv.get_tile_coords(x, y)
        istr = ""
        
        for tlayer in terrain.get_layers():
            istr += type(tlayer).__name__ + ": " + str(tlayer[tx, ty]) + "\t"
        print("x:", tx, "y:", ty, istr)
    
    def on_mouse_drag(self, x, y, dx, dy, button, mods):
        if (button != mouse.RIGHT):
            return
        
        self._viewport_x -= dx
        self._viewport_y += dy # pyglet has a reversed y-axis
