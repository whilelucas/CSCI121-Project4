from tkinter import *
from tkinter import font
from tkinter import ttk
from Game import *
from geometry import Point2D, Vector2D
import math
import random
import time

TIME_STEP = 0.5

class MovingBody(Agent):

    def __init__(self, p0, v0, world):
        self.velocity = v0
        self.accel    = Vector2D(0.0,0.0)
        Agent.__init__(self,p0,world)

    def color(self):
        return "#000080"

    def shape(self):
        p1 = self.position + Vector2D( 0.125, 0.125)       
        p2 = self.position + Vector2D(-0.125, 0.125)        
        p3 = self.position + Vector2D(-0.125,-0.125)        
        p4 = self.position + Vector2D( 0.125,-0.125)
        return [p1,p2,p3,p4]

    def steer(self):
        return Vector2D(0.0)

    def update(self):
        self.position += self.velocity * TIME_STEP
        self.velocity += self.accel * TIME_STEP
        self.accel    = self.steer()
        self.world.trim(self)

class Shootable(MovingBody):
    SHRAPNEL_CLASS  = None
    SHRAPNEL_PIECES = 0
    WORTH           = 1

    def __init__(self, position0, velocity0, radius, world):
        self.radius = radius
        MovingBody.__init__(self, position0, velocity0, world)

    def is_hit_by(self, photon):
        return ((self.position - photon.position).magnitude() < self.radius)

    def is_hit_by_poly(self, photon):
        photon.shape()
        for p in photon.shape():        
            if (self.position - p).magnitude() < self.radius:
                return True
        return False

    def explode(self):
        self.world.score += self.WORTH
        self.world.tot_score+=self.WORTH
        self.world.auxiliaryHealth+=self.HEALTH
        if self.world.score>=70:
            self.world.level+=1            
            self.world.score=0            
        if self.SHRAPNEL_CLASS == None:
            return
        for _ in range(self.SHRAPNEL_PIECES):
            self.SHRAPNEL_CLASS(self.position,self.world)
        self.leave()

class Asteroid(Shootable):
    WORTH     = 5
    HEALTH    = 0
    MIN_SPEED = 0.1
    MAX_SPEED = 0.3
    SIZE      = 3.0

    def __init__(self, position0, velocity0, world):
        Shootable.__init__(self,position0, velocity0, self.SIZE, world)
        self.make_shape()

    def choose_velocity(self):
        #if self.world.level==2:
            #return Vector2D.random() * random.uniform(self.MIN_SPEED,self.MAX_SPEED+1) 
        return Vector2D.random() * random.uniform(self.MIN_SPEED,self.MAX_SPEED) 
        
    def make_shape(self):
        angle = 0.0
        dA = 2.0 * math.pi / 15.0
        center = Point2D(0.0,0.0)
        self.polygon = []
        for i in range(15):
            if i % 3 == 0 and random.random() < 0.2:
                r = self.radius/2.0 + random.random() * 0.25
            else:
                r = self.radius - random.random() * 0.25
            dx = math.cos(angle)
            dy = math.sin(angle)
            angle += dA
            offset = Vector2D(dx,dy) * r
            self.polygon.append(offset)

    def shape(self):
        return [self.position + offset for offset in self.polygon]

class ParentAsteroid(Asteroid):
    def __init__(self,world):
        world.number_of_asteroids += 1
        velocity0 = self.choose_velocity()
        position0 = world.bounds.point_at(random.random(),random.random())
        if abs(velocity0.dx) >= abs(velocity0.dy):
            if velocity0.dx > 0.0:
                # LEFT SIDE
                position0.x = world.bounds.xmin
            else:
                # RIGHT SIDE
                position0.x = world.bounds.xmax
        else:
            if velocity0.dy > 0.0:
                # BOTTOM SIDE
                position0.y = world.bounds.ymin
            else:
                # TOP SIDE
                position0.y = world.bounds.ymax
        Asteroid.__init__(self,position0,velocity0,world)

    def explode(self):
        Asteroid.explode(self)
        self.world.number_of_asteroids -= 1



class Ember(MovingBody):
    INITIAL_SPEED = 2.0
    SLOWDOWN      = 0.2
    TOO_SLOW      = INITIAL_SPEED / 20.0

    def __init__(self, position0, world):
        velocity0 = Vector2D.random() * self.INITIAL_SPEED
        MovingBody.__init__(self, position0, velocity0, world)        

    def color(self):
        white_hot  = "#FFFFFF"
        burning    = "#FF8080"
        smoldering = "#808040"
        speed = self.velocity.magnitude()
        if speed / self.INITIAL_SPEED > 0.5:
            return white_hot
        if speed / self.INITIAL_SPEED > 0.25:
            return burning
        return smoldering

    def steer(self):
        return -self.velocity.direction() * self.SLOWDOWN

    def update(self):
        MovingBody.update(self)              
        if self.velocity.magnitude() < self.TOO_SLOW:
            self.leave()

class ShrapnelAsteroid(Asteroid):
    def __init__(self, position0, world):
        world.number_of_shrapnel += 1
        velocity0 = self.choose_velocity()
        Asteroid.__init__(self, position0, velocity0, world)

    def explode(self):         
        Asteroid.explode(self)
        self.world.number_of_shrapnel -= 1


class HealthAsteroid(ShrapnelAsteroid):
    WORTH           = 0
    HEALTH          = 1
    MIN_SPEED       = Asteroid.MIN_SPEED * 2.0
    MAX_SPEED       = Asteroid.MAX_SPEED * 2.0
    SIZE            = Asteroid.SIZE / 3.0    
    SHRAPNEL_CLASS  = Ember
    SHRAPNEL_PIECES = 20


    def color(self):
        return "#FF07FF"

class SmallAsteroid(ShrapnelAsteroid):
    WORTH           = 20
    HEALTH          = 0
    MIN_SPEED       = Asteroid.MIN_SPEED * 2.0
    MAX_SPEED       = Asteroid.MAX_SPEED * 2.0
    SIZE            = Asteroid.SIZE / 2    
    def explode(self):        
        if random.randint(0,10)==1:  
            self.SHRAPNEL_CLASS  = HealthAsteroid
            self.SHRAPNEL_PIECES = 1
        else:
            self.SHRAPNEL_CLASS = Ember
            self.SHRAPNEL_PIECES = 20
        ShrapnelAsteroid.explode(self)

    def color(self):
        return "#A8B0C0"


class MediumAsteroid(ShrapnelAsteroid):
    WORTH           = 10
    HEALTH          = 0
    MIN_SPEED       = Asteroid.MIN_SPEED * math.sqrt(2.0)
    MAX_SPEED       = Asteroid.MAX_SPEED * math.sqrt(2.0)
    SIZE            = Asteroid.SIZE / math.sqrt(2.0)       
    SHRAPNEL_CLASS  = SmallAsteroid 
    SHRAPNEL_PIECES = 4

    def color(self):
        return "#7890A0"

class LargeAsteroid(ParentAsteroid):
    SHRAPNEL_CLASS  = MediumAsteroid
    SHRAPNEL_PIECES = 2

    def color(self):
        return "#9890A0"

class Photon(MovingBody): 
    INITIAL_SPEED = 2.0 * SmallAsteroid.MAX_SPEED         
    
    def __init__(self,source,world):
        self.age  = 0
        sourceSpeed = source.get_heading() if source.forward else (source.get_heading() * 2)
        v0 = source.velocity + (sourceSpeed * self.INITIAL_SPEED)
        sourceShape = source.shape()
        MovingBody.__init__(self, sourceShape[0], v0, world)     

    def lifetime(self):
        if self.world.level == 2:
            return 45
        elif self.world.level == 3:
            return 40
        elif self.world.level == 4:
            return 25
        elif self.world.level == 5:
            return 10
        else:
            return 50

    def color(self):
        if self.world.level == 2:            
            return "#FF0000"
        elif self.world.level == 3:            
            return "#00FF00"
        elif self.world.level == 4:          
            return "#0000FF"
        elif self.world.level == 5:            
            return "#FFEAEA"
        else:
            return "#FFEDFF"

    def update(self):
        MovingBody.update(self)
        self.age += 1
        if self.age >= self.lifetime():
            self.leave()
        else:
            targets = [a for a in self.world.agents if isinstance(a,Shootable)]
            for t in targets:
                if t.is_hit_by(self):
                    t.explode()
                    self.leave()
                    return


class Ship(MovingBody):
    TURNS_IN_360   = 24
    IS_HIT=False
    forward = True
    ACTIVE= True
    
    def __init__(self,world):
        position0    = Point2D()
        velocity0    = Vector2D(0.0,0.0)
        MovingBody.__init__(self,position0,velocity0,world)
        self.speed   = 0.0
        self.angle   = 90.0
        self.impulse = 0
        self.health=10

    def color(self):
        if self.health<=5:
            return "#B22222"
        return "#F0C080"

    def get_heading(self):
        angle = self.angle * math.pi / 180.0
        return Vector2D(math.cos(angle), math.sin(angle))

    #Manoeuvring Methods
    def rotate(self, left, freeze=True):
        if freeze:
            self.velocity = Vector2D()
        rotation = 360.0 / self.TURNS_IN_360
        rotation = rotation if left else -rotation
        self.angle += rotation

    def circular(self, direction):
        if direction == SET_BACKRIGHT:
            self.forward = False
            self.rotate(False,False)
            self.velocity = -self.get_heading()
        elif direction == SET_BACKLEFT:
            self.forward = False
            self.rotate(True,False)
            self.velocity = -self.get_heading()
        elif direction == SET_FORWARDRIGHT:
            self.forward = True
            self.rotate(False,False)
            self.velocity = self.get_heading()
        elif direction == SET_FORWARDLEFT:
            self.forward = True
            self.rotate(True,False)
            self.velocity = self.get_heading()

    def normalMovement(self, forward):
        self.forward = forward
        self.velocity = self.get_heading() if forward else -self.get_heading()

    def auto_slowdown(self):
        if self.velocity == Vector2D():
            return
        self.velocity /= 1.005
        if self.velocity.magnitude() < 0.75:
            self.velocity = Vector2D()
            self.forward = True

    def shoot(self):
        Photon(self, self.world)
    
    def shape(self):
        h  = self.get_heading()
        hp = h.perp()
        p1 = self.position + h * 2
        p2 = self.position + hp * 0.75
        p3 = self.position - hp * 0.75
        p4x = (p1.x + p2.x + p3.x) / 3
        p4y = (p1.y + p2.y + p3.y) / 3
        p4 = Point2D(p4x, p4y)
        return [p1,p2,p4,p3]

    def steer(self):
        if self.impulse > 0:
            self.impulse -= 1            
            return self.get_heading() * self.ACCELERATION
        else:
            return Vector2D(0.0,0.0)

    #def trim_physics(self):
    #    MovingBody.trim_physics(self)
    #    m = self.velocity.magnitude()
    #    if m > self.MAX_SPEED:
    #        self.velocity = self.velocity * (self.MAX_SPEED / m)
    #        self.impulse = 0

    def update(self):
        self.position += self.velocity * TIME_STEP
        self.world.trim(self)          
        if self.health <= 0:
            self.leave()
        else:
            targets = [a for a in self.world.agents if isinstance(a,Shootable)]
            for t in targets:
                if t.is_hit_by_poly(self) and self.ACTIVE==True:
                    t.explode()                    
                    self.health-=1  
                    self.ACTIVE==False             
                    return

class PlayAsteroids(Game):

    DELAY_START      = 150
    MAX_ASTEROIDS    = 6
    INTRODUCE_CHANCE = 0.01
    
    def __init__(self,root):
        Game.__init__(self,root,"ASTEROIDS!!!",60.0,45.0,800,600,topology='wrapped',console_lines=7)

        self.report("Welcome, "+Player_Name.title()+"!")
        self.report("Hit 'j' and 'l' to turn, 'i' to create thrust, 'k' to move backwards and the spacebar to shoot. Press 'q' to pause.")
        self.report("Press 'a' to start!")
        self.report()

        self.number_of_asteroids = 0
        self.number_of_shrapnel = 0
        self.level = 1
        self.score = 0       
        self.tot_score = 0
        self.before_start_ticks = self.DELAY_START
        self.started = False
        self.auxiliaryHealth=0

        self.ship = Ship(self)
        

    def max_asteroids(self):
        return min(2 + self.level,self.MAX_ASTEROIDS)

    def movement(self):
        if len(self.commands) == 2 and ((self.commands == SET_FORWARDLEFT) or (self.commands == SET_FORWARDRIGHT) or (self.commands == SET_BACKLEFT) or (self.commands == SET_BACKRIGHT)):
            self.ship.circular(self.commands)
        elif len(self.commands) == 1:
            command = list(self.commands)[0]
            if command == KEY_UP:
                self.ship.normalMovement(True)
            elif command == KEY_LEFT:
                self.ship.rotate(True)
            elif command == KEY_RIGHT:
                self.ship.rotate(False)
            elif command == KEY_DOWN:
                self.ship.normalMovement(False)        
    

    def start(self,event):
        if event.char==KEY_START:
            return True              

    def give_score(self):
        return self.report("Current Score: "+str(self.score))

    def give_level(self):
        return self.report("Current Level: "+str(self.level))

    def give_health(self):
        if self.ship.health<=0:
            self.GAME_OVER=True
            return self.report("HEALTH ZERO! GAME OVER!!!")            
        else:
            return self.report("Current Health: "+str(self.ship.health+self.auxiliaryHealth))

    def give_tot_score(self):
        return self.report(Player_Name.title()+", Your Total Score is: "+str(self.tot_score))
        
    def update(self):
        if not self.GAME_OVER:
            if len(self.commands) > 0:
                self.movement()
            else:
                self.ship.auto_slowdown()
            #Are we waiting to toss asteroids out?
            #if self.before_start_ticks > 0:
            #    self.before_start_ticks -= 1
            #else:
            #    self.started = True
            
            #Should we toss a new asteroid out?
            if self.started:
                tense = (self.number_of_asteroids >= self.max_asteroids())
                tense = tense or (self.number_of_shrapnel >= 2*self.level)
                if not tense and random.random() < self.INTRODUCE_CHANCE:
                    LargeAsteroid(self)
    
            Game.update(self)  
            if self.started:
                self.give_score()
                self.give_level()
                self.give_health()
                self.give_tot_score()
                self.report()
        else:
            Frame.update(self)

    def handle_keypress(self,event):
        Game.handle_keypress(self, event)
        if event.char == KEY_START:
            self.started = True
        elif event.char == KEY_SHOOT:
            self.ship.shoot()

class StartPage(Frame):
    game = None
    def __init__(self):
        self.root = Tk()
        Frame.__init__(self, self.root, width=800, height=600) 

        self.grid_propagate(0)
        self.grid(column=0, row=0)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  

        startGameButton = Button(self, text="Start Game", command=self.startGame)
        startGameButton.grid(column=0, row=0,sticky = (N,S))

        titleFont = font.Font(family='Helvetica', size=36, weight='bold')
        self.titleLabel = Label(self, font = titleFont, text='ASTEROIDS')
        self.titleLabel.grid(column=0, row=0,sticky=N)

    def startGame(self):
        self.game = PlayAsteroids(self)
        self.game.tkraise()

Player_Name=input("Hi! I'm AstroShip. I DESTROY Asteroids. And you are? ")
root = Tk()
root.title("Asteroids - The Game")
game = PlayAsteroids(root)
while not game.GAME_OVER:
    time.sleep(1.0/60.0)
    game.update()
#s = StartPage()
