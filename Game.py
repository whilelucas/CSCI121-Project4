from tkinter import *
from geometry import *

FORWARDLEFT  = 'forwardleft'
FORWARDRIGHT = 'forwardright'
BACKLEFT     = 'backleft'
BACKRIGHT    = 'backright'

KEY_UP    = ''
KEY_DOWN  = ''
KEY_LEFT  = ''
KEY_RIGHT = ''

DESCRIPTOR_KEY_UP    = 'the up arrow'
DESCRIPTOR_KEY_DOWN  = 'the down arrow'
DESCRIPTOR_KEY_LEFT  = 'the left arrow'
DESCRIPTOR_KEY_RIGHT = 'the right arrow'

KEY_SHOOT = ' '
KEY_START = 'b'
KEY_PAUSE = 'p'

GAME_BACKGROUND_COLOR = "#000000"

class Agent:

    def __init__(self,position,world):
        self.position = position
        self.world    = world 
        self.world.add(self)

    def color(self):
        return "#000000"

    def shape(self):
        p1 = self.position + Vector2D( 0.125, 0.125)       
        p2 = self.position + Vector2D(-0.125, 0.125)        
        p3 = self.position + Vector2D(-0.125,-0.125)        
        p4 = self.position + Vector2D( 0.125,-0.125)
        return [p1,p2,p3,p4]

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
    def __init__(self, name, w, h, ww, wh, topology = 'wrapped'):
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
        self.root = Tk()
        self.root.title(name)
        Frame.__init__(self, self.root)
        self.canvas = Canvas(self.root, width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT)

        #A set of commands to be read in 'update'.
        self.commands = set()
        
        # Handle keypress events.
        self.bind_all('<KeyPress>',self.handle_keypress)
        self.bind_all('<KeyRelease>',self.handle_keyrelease)

        self.canvas.pack()
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

    #***SHIP CAN NOW HIT ITSELF***
    def get_actual_points(self, shape):
        wh,ww = self.WINDOW_HEIGHT,self.WINDOW_WIDTH
        h = self.bounds.height()
        x = self.bounds.xmin
        y = self.bounds.ymin
        return [ ((p.x - x)*wh/h, wh - (p.y - y)* wh/h) for p in shape ]

    def get_center_point(self,shape):
        points = self.get_actual_points(shape)
        x = 0.0
        y = 0.0
        for p in points:
            x += p[0]
            y += p[1]
        x /= len(points)
        y /= len(points)
        return Point2D(x,y)
    def draw_shape(self, shape, color):
        if type(color) != list:
            points = self.get_actual_points(shape)
            if len(points) > 2:
                first_point = points[0]
                points.append(first_point)
                self.canvas.create_polygon(points, fill=color)
            else:
                x0 = points[0][0]
                y0 = points[0][1]
                x1 = points[1][0]
                y1 = points[1][1]
                self.canvas.create_oval(x0, y0, x1, y1, fill=color)
        else:
            for i in range(len(color)):
                points = self.get_actual_points(shape[i])
                x0 = points[0][0]
                y0 = points[0][1]
                x1 = points[1][0]
                y1 = points[1][1]
                curr_color = color[i]
                self.canvas.create_oval(x0, y0, x1, y1, fill=curr_color)

    def clear(self):
        self.canvas.delete('all')
        self.canvas.create_rectangle(0, 0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, fill=GAME_BACKGROUND_COLOR)

    def handle_keypress(self,event):
        if event.char == KEY_PAUSE and self.GAME_STARTED:
            self.GAME_PAUSED = not self.GAME_PAUSED
        elif len(self.commands) < 2:
            self.commands.add(event.char.lower())

    def handle_keyrelease(self,event):
        if event.char in self.commands:
            self.commands.remove(event.char)