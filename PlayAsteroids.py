from tkinter import font
from Game import *
import time
from time import localtime, strftime

TIME_STEP = 0.5
BIG_FONT = "bigfont"
SMALL_FONT = "smallfont"
SCORES_FILE = "scores.txt"

class Player:

    @classmethod
    def fromString(cls,s):
        name = s.split(': ')[0]
        score = int(s.split(' ')[1])
        date = s.split(' on ')[1]
        return Player(name, score, date)

    def __init__(self, name, score, date):
        self.name = name
        self.score = score
        self.date = date

    def to_string(self):
        return str(self.name) + ": " + str(self.score) + " points, on " + self.date

    __str__ = to_string
    __repr__ = to_string


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
        self.world.HealthFromAsteroids+=self.HEALTH_ADV
        if self.world.score>=500:
            self.world.level+=1            
            self.world.score=0            
        if self.SHRAPNEL_CLASS == None:
            return
        for _ in range(self.SHRAPNEL_PIECES):
            self.SHRAPNEL_CLASS(self.position,self.world)
        self.leave()

class Asteroid(Shootable):
    WORTH     = 5
    HEALTH_ADV=0
    MIN_SPEED = 0.1
    MAX_SPEED = 0.2
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
        for i in range(10):
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
    HEALTH_ADV         = 1
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
    SIZE            = Asteroid.SIZE / 2.0
    SHRAPNEL_CLASS  = Ember
    SHRAPNEL_PIECES = 8
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
    HEALTH_ADV=0
    MIN_SPEED       = Asteroid.MIN_SPEED * math.sqrt(2.0)
    MAX_SPEED       = Asteroid.MAX_SPEED * math.sqrt(2.0)
    SIZE            = Asteroid.SIZE / math.sqrt(2.0)
    SHRAPNEL_CLASS  = SmallAsteroid
    SHRAPNEL_PIECES = 3

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
    DELAY_INVULNERABLE = 200
    got_hit_ticks = DELAY_INVULNERABLE
    def __init__(self,world):
        got_hit_ticks = self.DELAY_INVULNERABLE
        position0    = Point2D(0,-60)
        velocity0    = Vector2D(0.0,0.0)
        MovingBody.__init__(self,position0,velocity0,world)
        self.restart()

    def restart(self):
        self.speed   = 0.0
        self.angle   = 90.0
        self.impulse = 0
        self.health=10
        self.position = Point2D(0,-60)
        self.velocity = Vector2D()

    def color(self):
        if self.got_hit_ticks == self.DELAY_INVULNERABLE:
            if self.health<=5:
                return "#B22222"
            else:
                return "#F0C080"
        else:
            if self.health <= 5:
                return "#B22222" if self.got_hit_ticks%10==0 else "#4C0D0D"
            else:
                return "#F0C080" if self.got_hit_ticks%10==0 else "#ED9521"
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
        # *** Which is better? Slow down or stop altogether? ***
        self.velocity = Vector2D()
        #if self.velocity == Vector2D():
        #    return
        #self.velocity /= 1.005
        #if self.velocity.magnitude() < 0.75:
        #    self.velocity = Vector2D()
        #    self.forward = True

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

    def update(self):
        self.position += self.velocity * TIME_STEP
        self.world.trim(self)
        if self.IS_HIT:
            self.got_hit_ticks -= 1
            if self.got_hit_ticks == 0:
                self.IS_HIT = False
                self.got_hit_ticks = self.DELAY_INVULNERABLE
        else:
            targets = [a for a in self.world.agents if isinstance(a,Shootable)]
            for t in targets:
                if t.is_hit_by_poly(self) and not self.IS_HIT:
                    t.explode()
                    self.IS_HIT=True
                    self.health-=1               
                    return

class PlayAsteroids(Game):

    MAX_ASTEROIDS      = 6
    INTRODUCE_CHANCE   = 0.01
    
    def __init__(self,root):
        Game.__init__(self,root,"ASTEROIDS!!!",60.0,45.0,800,600,topology='wrapped')
        self.ship = Ship(self)

        self.highScorePlayers = []

        self.makeScores(SCORES_FILE)

        self.restart()

    def makeScores(self, file):
        scoresFile = open(file,"r")
        nextLine = scoresFile.readline().strip()
        while nextLine != '':
            self.highScorePlayers.append(Player.fromString(nextLine))
            nextLine = scoresFile.readline().strip()
        scoresFile.close()

    def restart(self):
        self.ship.restart()
        self.number_of_asteroids = 0
        self.number_of_shrapnel = 0
        self.level = 1
        self.score = 0
        self.HealthFromAsteroids = 0       
        self.tot_score = 0
        self.clear()
        self.GAME_OVER = False
        self.GAME_STARTED = False

    def reportStr(self):
        level = str(self.level)
        tot_score = str(self.tot_score)
        health = str(self.ship.health+self.HealthFromAsteroids)
        reportStr = "Score: " + tot_score + "\n" + "Level: " + level + "\n" + "Health: " + health
        return reportStr

    def max_asteroids(self):
        return min(3 + self.level,self.MAX_ASTEROIDS)

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

    def font(self, size):
        return font.Font(family='Lucida Sans Typewriter',size=size)
    def createText(self, position, font, text, width):
        self.canvas.create_text(position.x,position.y,text=text,fill='white',font=font,width=width)

    def gameOver(self):
        self.clear()
        self.GAME_OVER = True
        currentPlayer = Player(Player_Name, self.tot_score, strftime("%a, %d %b %Y %H:%M", localtime()))
        self.highScorePlayers.append(currentPlayer)
        self.highScorePlayers.sort(key=lambda x: x.score, reverse=True)
        while len(self.highScorePlayers) > 5:
            self.highScorePlayers.pop()
        scoresFile = open(SCORES_FILE, 'w')
        for plyr in self.highScorePlayers:
            scoresFile.write(str(plyr) + "\n")
        scoresFile.close()
        textPosition = Point2D(game.WINDOW_WIDTH/2,100)
        game.createText(textPosition, game.font(36), 'GAME OVER', textPosition.x/2)
        game.createText(Point2D(textPosition.x, textPosition.y + 100), game.font(20), "High Scores", game.WINDOW_WIDTH)
        scoreOutput = ""
        for plyr in self.highScorePlayers:
            scoreOutput += str(self.highScorePlayers.index(plyr) + 1) + ". " + str(plyr) + "\n"
        game.createText(Point2D(textPosition.x, textPosition.y + 200), game.font(12), scoreOutput, game.WINDOW_WIDTH)
        game.createText(Point2D(textPosition.x, textPosition.y + 300), game.font(20), "Press the space bar to restart!", game.WINDOW_WIDTH)


    def update(self):
        if not self.GAME_PAUSED:
            if len(self.commands) > 0:
                self.movement()
            else:
                self.ship.auto_slowdown()
            for agent in self.agents:
                agent.update()
            self.clear()
            for agent in self.agents:
                if self.GAME_STARTED or type(agent) == Ship:
                    self.draw_shape(agent.shape(), agent.color())
                    textPosition = Point2D(self.WINDOW_WIDTH - 70,40)
                    self.createText(textPosition, self.font(12), self.reportStr(), 70)
            if not self.GAME_STARTED:
                text = "Welcome, "+Player_Name.title()+"!\n\n"
                text += "Asteroids are bad. Your job is to destroy them ALL. And remember, touching crashing into asteroids damgages your ship!\n\n"
                text += "Hit 'a' and 'd' to turn left and right, 'w' to move forward, 's' to move backwards, and the space bar to shoot.\nGive the controls a try if you want!\n\n"
                text += "Look out for special pink asteroids.\nThey increase your health if you destroy 'em!\n\n"
                text += "Press 'p' if you need to pause the game at any time.\n\n"
                text += "Now, press 'b' to begin!"
                textPosition = Point2D(self.WINDOW_WIDTH/2,self.WINDOW_HEIGHT/2)
                self.createText(textPosition, self.font(14), text, textPosition.x*1.5)
            else:
                tense = (self.number_of_asteroids >= self.max_asteroids())
                tense = tense or (self.number_of_shrapnel >= 2*self.level)
                if not tense and random.random() < self.INTRODUCE_CHANCE:
                    LargeAsteroid(self)
                if self.ship.health == 0:
                    self.gameOver()
        else:
            textPosition = Point2D(self.WINDOW_WIDTH/2,self.WINDOW_HEIGHT/2)
            self.createText(textPosition, self.font(36), 'GAME PAUSED', textPosition.x)
        Frame.update(self)

    def handle_keypress(self,event):
        if not self.GAME_STARTED and event.char == KEY_START:
            self.GAME_STARTED = True
            return
        Game.handle_keypress(self, event)
        if self.GAME_OVER and event.char == KEY_SHOOT:
            runGame(self)
        elif event.char == KEY_SHOOT:
            self.ship.shoot()
def runGame(game):
    game.restart()
    while not game.GAME_OVER and game.ship in game.agents:
        time.sleep(1.0/60.0)
        game.update()

Player_Name=input("Hi! I'm AstroShip. I DESTROY Asteroids. And you are? ")
root = Tk()
root.title("Asteroids - The Game")
game = PlayAsteroids(root)
runGame(game)
