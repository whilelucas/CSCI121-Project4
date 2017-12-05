from tkinter import *
from geometry import *
import sys

FORWARDLEFT  = 'forwardleft'
FORWARDRIGHT = 'forwardright'
BACKLEFT     = 'backleft'
BACKRIGHT    = 'backright'

KEY_UP    = 'w'
KEY_DOWN  = 's'
KEY_LEFT  = 'a'
KEY_RIGHT = 'd'
KEY_SHOOT = ' '
KEY_START = 'b'
KEY_PAUSE = 'p'

SET_FORWARDLEFT  = {KEY_UP,KEY_LEFT}
SET_FORWARDRIGHT = {KEY_UP,KEY_RIGHT}
SET_BACKLEFT     = {KEY_DOWN,KEY_LEFT}
SET_BACKRIGHT    = {KEY_DOWN,KEY_RIGHT}

class Agent:

    INTENSITIES = [4,5,6,7,8,7,6,5,4,3,2,1,0,1,2,3]

    def __init__(self,position,world):
        self.position = position
        self.world    = world 
        self.world.add(self)
        self.ticks    = 0

    def color(self):
        a = self.ticks % len(self.INTENSITIES)
        return "#0000"+str(self.INTENSITIES[a])+"0"

    def shape(self):
        p1 = self.position + Vector2D( 0.125, 0.125)       
        p2 = self.position + Vector2D(-0.125, 0.125)        
        p3 = self.position + Vector2D(-0.125,-0.125)        
        p4 = self.position + Vector2D( 0.125,-0.125)
        return [p1,p2,p3,p4]

    def update(self):
        self.ticks += 1

    def leave(self):
        self.world.remove(self)

class Game(Frame):

    # Game(name,w,h,ww,wh)
    #
    # Creates a world with a coordinate system of width w and height
    # h, with x coordinates ranging between -w/2 and w/2, and with y
    # coordinates ranging between -h/2 and h/2.
    # 
    # Creates a corresponding graphics window, for rendering 
    # the world, with pixel width ww and pixel height wh.
    #
    # The window will be named by the string given in name.
    #
    # The topology string is used by the 'trim' method to (maybe) keep
    # bodies within the frame of the world. (For example, 'wrapped' 
    # yields "SPACEWAR" topology, i.e. a torus.)
    #
    def __init__(self, root, name, w, h, ww, wh, topology = 'wrapped', console_lines = 0):
        # Register the world coordinate and graphics parameters.
        self.WINDOW_WIDTH = ww
        self.WINDOW_HEIGHT = wh
        self.bounds = Bounds(-w/2,-h/2,w/2,h/2)
        self.topology = topology

        # Populate the world with creatures
        self.agents = []
        self.GAME_OVER = False
        self.GAME_PAUSED = False
        self.GAME_STARTED = False

        # Initialize the graphics window.
        self.root = root

        #A set of commands to be read in 'update'.
        self.commands = set()

        Frame.__init__(self, self.root)

        #Canvas: Where drawing happens!
        self.canvas = Canvas(self.root, width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)

        # Handle mouse pointer motion and keypress events.
        #self.mouse_position = Point2D(0.0,0.0)
        #self.mouse_down     = False
        #self.bind_all('<Motion>',self.handle_mouse_motion)
        #self.canvas.bind('<Button-1>',self.handle_mouse_press)
        #self.canvas.bind('<ButtonRelease-1>',self.handle_mouse_release)
        self.bind_all('<KeyPress>',self.handle_keypress)
        self.bind_all('<KeyRelease>',self.handle_keyrelease)

        self.canvas.pack()
        if console_lines > 0:
            self.text = Text(self.root,height=console_lines,bg="#000000",fg="#A0F090",width=115)
            self.text.pack()
        else:
            self.text = None
        self.pack()

    def trim(self,agent):
        if self.topology == 'wrapped':
            agent.position = self.bounds.wrap(agent.position)
        elif self.topology == 'bound':
            agent.position = self.bounds.clip(agent.position)

    def add(self, agent):
        self.agents.append(agent)

    def remove(self, agent):
        self.agents.remove(agent)

    def draw_shape(self, shape, color):
        wh,ww = self.WINDOW_HEIGHT,self.WINDOW_WIDTH
        h = self.bounds.height()
        x = self.bounds.xmin
        y = self.bounds.ymin
        points = [ ((p.x - x)*wh/h, wh - (p.y - y)* wh/h) for p in shape ]
        first_point = points[0]
        points.append(first_point)
        self.canvas.create_polygon(points, fill=color)

    def clear(self):
        self.canvas.delete('all')
        self.canvas.create_rectangle(0, 0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, fill="#000000")

    def handle_keypress(self,event):
        if event.char == KEY_PAUSE and self.GAME_STARTED:
            self.GAME_PAUSED = not self.GAME_PAUSED
        elif not event.char in self.commands and len(self.commands) < 2 and event.char != ' ':
            self.commands.add(event.char.lower())

    def handle_keyrelease(self,event):
        if event.char in self.commands:
            self.commands.remove(event.char)
