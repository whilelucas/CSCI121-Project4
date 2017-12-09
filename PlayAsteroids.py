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
        self.accel     = self.steer()
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

    def is_hit_by_ship(self, ship):
        for p in ship.shape():        
            if (self.position - p).magnitude() < self.radius:
                return True
        return False

    def explode(self):
        self.world.score += self.WORTH
        self.world.total_score += self.WORTH
        if self.world.score >= 200:
            self.world.level += 1            
            self.world.score = 0            
        if self.SHRAPNEL_CLASS == None:
            return
        for _ in range(self.SHRAPNEL_PIECES):
            self.SHRAPNEL_CLASS(self.position,self.world)
        self.leave()

class Asteroid(Shootable):
    WORTH      = 5
    MIN_SPEED  = 0.1
    MAX_SPEED  = 0.2
    SIZE       = 3.0
    HEALTH_ADV = 0

    def __init__(self, position0, velocity0, world):
        Shootable.__init__(self,position0, velocity0, self.SIZE, world)
        self.make_shape()

    def choose_velocity(self):
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
    HEALTH_ADV      = 1
    MIN_SPEED       = Asteroid.MIN_SPEED * 2.0
    MAX_SPEED       = Asteroid.MAX_SPEED * 2.0
    SIZE            = Asteroid.SIZE / 3.0    
    SHRAPNEL_CLASS  = Ember
    SHRAPNEL_PIECES = 20
    disappear_ticks = 1000

 
    def color(self):
        return "#45F207"

    def update(self):
        ShrapnelAsteroid.update(self)
        self.disappear_ticks -= 1
        if self.disappear_ticks == 0:
            self.explode()

class NegHealthAsteroid(HealthAsteroid):
    WORTH      = 0
    HEALTH_ADV = -2
    MAX_SPEED  = Asteroid.MAX_SPEED * 1.5
    SIZE       = Asteroid.SIZE / 1.5
 
    def color(self):
        return "#FF07FF"

class SmallAsteroid(ShrapnelAsteroid):
    WORTH           = 20
    HEALTH          = 0
    MIN_SPEED       = Asteroid.MIN_SPEED * 2.0
    MAX_SPEED       = Asteroid.MAX_SPEED * 2.0
    SIZE            = Asteroid.SIZE / 2.0
    SHRAPNEL_PIECES = 3
    
    def explode(self):        
        if random.randint(0,10)==1:  
            self.SHRAPNEL_CLASS  = HealthAsteroid
            self.SHRAPNEL_PIECES = 1
        elif random.randint(0,5)==1:
            self.SHRAPNEL_CLASS = NegHealthAsteroid
            self.SHRAPNEL_PIECES = 2
        else:
            self.SHRAPNEL_CLASS = Ember
            self.SHRAPNEL_PIECES = 20
        ShrapnelAsteroid.explode(self)
  
    def color(self):
          return "#A8B0C0"

class MediumAsteroid(ShrapnelAsteroid):
    WORTH           = 10
    HEALTH_ADV      = 0
    MIN_SPEED       = Asteroid.MIN_SPEED * math.sqrt(2.0)
    MAX_SPEED       = Asteroid.MAX_SPEED * math.sqrt(2.0)
    SIZE            = Asteroid.SIZE / math.sqrt(2.0)
    SHRAPNEL_PIECES = 3

    def color(self):
        return "#7890A0"

    def explode(self):        
        if random.randint(0,10) == 1:  
            self.SHRAPNEL_CLASS  = HealthAsteroid
            self.SHRAPNEL_PIECES = 1
        elif random.randint(0,5) == 1:
            self.SHRAPNEL_CLASS = NegHealthAsteroid
            self.SHRAPNEL_PIECES = 2
        else:
            self.SHRAPNEL_CLASS  = SmallAsteroid
            self.SHRAPNEL_PIECES = 3
        ShrapnelAsteroid.explode(self)

class LargeAsteroid(ParentAsteroid):
    SHRAPNEL_CLASS  = MediumAsteroid
    SHRAPNEL_PIECES = 2

    def color(self):
        return "#9890A0"

class Photon(MovingBody):
    INITIAL_SPEED = 2.0 * SmallAsteroid.MAX_SPEED       

    def __init__(self,source,world):
        self.age  = 0
        self.source = source
        #If shooting while moving backward, photons velocity is doubled for a natural appearance
        sourceSpeed = source.get_heading() if source.forward else (source.get_heading() * 2)
        v0 = source.velocity + (sourceSpeed * self.INITIAL_SPEED)
        #Originate from front of the ship
        sourceShape = source.shape()
        MovingBody.__init__(self, sourceShape[0], v0, world) 

    #Life-time dependant on level
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
    #Color based on level (does it stay one color from level 5 onwards?)
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
                    if type(t) != Ship and type(t) != MegaBonusBomb:
                        self.source.health += t.HEALTH_ADV
                    else:
                        t.IS_HIT = True
                    self.leave()
                    return

class MegaBonusBomb(Shootable):
    MIN_SPEED = 0.1
    MAX_SPEED = 0.2
    def __init__(self, world):
        randomPosition = world.bounds.point_at(random.random(),random.random())
        randomVelocity = Vector2D.random() * random.uniform(self.MIN_SPEED,self.MAX_SPEED) 
        Shootable.__init__(self, randomPosition, randomVelocity, 2, world)

    def color(self):
        return "#38EDE4"

    def shape(self):
        p1 = self.position
        p2 = Point2D(p1.x+self.radius, p1.y+self.radius)
        return [p1,p2]

    def explode(self):
        chance = random.randint(0,1)
        if chance == 0:
            for agent in self.world.agents:
                if issubclass(type(agent), Asteroid) and not issubclass(type(agent), HealthAsteroid) and agent != self:
                    agent.explode()
        else:
            self.world.ship.has_shield_ticks = self.world.ship.DELAY_SHIELD
            self.world.ship.HAS_SHIELD = True
        self.leave()

class Wormhole(Shootable):
    NUMBER_OF_RINGS = 3

    def __init__(self, world):
        randomPosition = world.bounds.point_at(random.random(), random.random())
        v0 = Vector2D()
        Shootable.__init__(self,randomPosition, v0, self.NUMBER_OF_RINGS, world)

    def shape(self):
        shapes = []
        i = self.NUMBER_OF_RINGS
        while i > 0:
            p0 = self.position
            p1 = Point2D(p0.x-i, p0.y-i)
            p2 = Point2D(p0.x+i, p0.y+i)
            shapes.append([p1,p2]) 
            i -= 1
        return shapes

    def color(self):
        return ['yellow','green','blue']

    def is_hit_by(self, photon):
        return False

    def is_hit_by_ship(self, ship):
        for p in ship.shape():        
            if (self.position - p).magnitude() < self.radius:
                return True
        return False

    def explode(self):
        pass

class Ship(Shootable):
    TURNS_IN_360       = 24
    IS_HIT             = False
    forward            = True
    DELAY_INVULNERABLE = 120
    DELAY_SINGLE_BOT_MOVEMENT = 400
    DELAY_SHIELD = 1000

    def __init__(self,world, bot=False):
        position0    = Point2D(0, -60)
        velocity0    = Vector2D()
        Shootable.__init__(self,position0,velocity0,2.0,world)
        self.IS_BOT = bot
        self.bot_movement_ticks = self.DELAY_SINGLE_BOT_MOVEMENT
        self.current_bot_movement = 0
        self.restart()

    def restart(self):
        self.speed   = 0.0
        self.angle   = 90.0
        self.health  = 5
        self.position = Point2D(0, -60)
        self.velocity = Vector2D()
        self.IS_HIT = False
        self.got_hit_ticks = self.DELAY_INVULNERABLE
        self.has_shield_ticks = self.DELAY_SHIELD
        self.photon_number = 100
        self.HAS_SHIELD = False

    def color(self):
        if not self.IS_HIT:
            if self.health <= 2:
                return "#B22222"
            else:
                return "#F0C080"
        else:
            if self.health <= 2:
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

    def moveCircular(self, direction):
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

    def stop(self):
        # *** Which is better? Slow down or stop altogether? ***
        #self.velocity = Vector2D()
        if self.velocity == Vector2D():
            return
        self.velocity /= 1.005
        if self.velocity.magnitude() < 0.75:
            self.velocity = Vector2D()
            self.forward = True

    def randomMovement(self):
        if self.bot_movement_ticks > 0 and self.current_bot_movement != None:
            self.bot_movement_ticks -= 1
        else:
            self.bot_movement_ticks = self.DELAY_SINGLE_BOT_MOVEMENT
            self.current_bot_movement = random.randint(1,6)
        prob = self.current_bot_movement
        if prob == 1:
            self.moveCircular(SET_FORWARDLEFT)
        elif prob == 2:
            self.moveCircular(SET_FORWARDRIGHT)
        elif prob == 3:
            self.moveCircular(SET_BACKLEFT)
        elif prob == 4:
            self.moveCircular(SET_BACKRIGHT)
        elif prob == 5:
            self.normalMovement(False)
        elif prob == 6:
            self.normalMovement(True)
        if random.randint(1,10) <= 2:
            self.shoot()

    def shoot(self):
        if self.photon_number > 0:
            Photon(self, self.world)
            if self.world.GAME_STARTED and not self.world.GAME_PAUSED:
                self.photon_number -= 1

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

    def explode(self):
        if not self.IS_HIT:
            self.IS_HIT = True
            self.health -= 1
        if self == self.world.ship:
            print("I got hit!")
        else:
            print("Hit the enemy!")

    def draw_shield(self):
        if self.HAS_SHIELD:
            self.IS_HIT = True
            point = self.world.get_center_point(self.shape())
            self.world.canvas.create_oval(point.x-25,point.y-25,point.x+25,point.y+25, outline = 'green')
            self.has_shield_ticks -= 1
            if self.has_shield_ticks == 0:
                self.HAS_SHIELD = False
                self.IS_HIT = False
                self.has_shield_ticks = self.DELAY_SHIELD

    def update(self):
        if self.IS_BOT:
            self.randomMovement()
        self.position += self.velocity * TIME_STEP if not self.IS_BOT else self.velocity * 0.2
        self.world.trim(self)
        if self.IS_HIT and not self.HAS_SHIELD:
            self.got_hit_ticks -= 1
            if self.got_hit_ticks == 0:
                self.IS_HIT = False
                self.got_hit_ticks = self.DELAY_INVULNERABLE
        else:
            targets = [a for a in self.world.agents if (isinstance(a,Shootable) and a != self)]
            for t in targets:
                if t.is_hit_by_ship(self) and not self.IS_HIT and type(t) != Wormhole:
                    t.explode()
                    self.IS_HIT = True
                    if type(t) == NegHealthAsteroid:
                        self.health -= 2
                    elif type != HealthAsteroid:
                        self.health -= 1
                    if self.health <= 0:
                        self.world.remove(self)          
                    return 
                elif type(t) == Wormhole and t.is_hit_by_ship(self):
                    t.leave()
                    self.position = self.world.bounds.point_at(random.random(),random.random())     

class PlayAsteroids(Game):
    MAX_ASTEROIDS      = 6
    INTRODUCE_CHANCE   = 0.01
    highScorePlayers = []
    DELAY_PHOTON_RUN_OUT = 300
    
    def __init__(self):
        Game.__init__(self, "Asteroids - The Game",60.0,45.0,800,600,topology='wrapped')
        self.ship = Ship(self)
        self.readHighScores(SCORES_FILE)
        self.restart()

    def readHighScores(self, file):
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
        self.total_score = 0
        self.agents = [self.ship]
        self.GAME_OVER = False
        self.GAME_STARTED = False
        self.nomore_photon_ticks = self.DELAY_PHOTON_RUN_OUT

    def reportStr(self):
        level = str(self.level)
        total_score = str(self.total_score)
        health = str(self.ship.health)
        photonsLeft = str(self.ship.photon_number)
        reportStr = "Score: " + total_score + "\n" + "Level: " + level + "\n" + "Health: " + health + "\n" + "Photons Left: " + photonsLeft
        return reportStr

    def max_asteroids(self):
        return min(3 + self.level,self.MAX_ASTEROIDS)

    def movement(self):
        #If there 2 keys being pressed at once (e.g. up & left or down & right), the Ship moves in a circular motion
        if len(self.commands) == 2 and ((self.commands == SET_FORWARDLEFT) or (self.commands == SET_FORWARDRIGHT) or (self.commands == SET_BACKLEFT) or (self.commands == SET_BACKRIGHT)):
            self.ship.moveCircular(self.commands)
        #Otherwise, there is either normal forward/backward movement or rotation.
        elif len(self.commands) == 1:
            if self.commands == {KEY_UP}:
                self.ship.normalMovement(True)
            elif self.commands == {KEY_LEFT}:
                self.ship.rotate(True)
            elif self.commands == {KEY_RIGHT}:
                self.ship.rotate(False)
            elif self.commands == {KEY_DOWN}:
                self.ship.normalMovement(False)

    def font(self, size):
        return font.Font(family='Lucida Sans Typewriter',size=size)

    def createText(self, position, font, text, width):
        self.canvas.create_text(position.x,position.y,text=text,fill='white',font=font,width=width)

    def gameOver(self):
        self.clear()
        self.GAME_OVER = True

        #Save the player's high score (if it is high enough)
        currentPlayer = Player(PLAYER_NAME, self.total_score, strftime("%a, %d %b %Y %H:%M", localtime()))
        if currentPlayer.score > self.highScorePlayers[len(self.highScorePlayers)-1].score:
            self.highScorePlayers.append(currentPlayer)
            self.highScorePlayers.sort(key=lambda x: x.score, reverse=True)
            while len(self.highScorePlayers) > 5:
                self.highScorePlayers.pop()
            scoresFile = open(SCORES_FILE, 'w')
            for plyr in self.highScorePlayers:
                scoresFile.write(str(plyr) + "\n")
            scoresFile.close()

        #Write out the end-of-game information
        textPosition = Point2D(self.WINDOW_WIDTH/2,100)
        self.createText(textPosition, self.font(36), 'GAME OVER', textPosition.x/2)
        self.createText(Point2D(textPosition.x, textPosition.y + 100), self.font(20), "High Scores", self.WINDOW_WIDTH)
        self.createText(Point2D(textPosition.x, textPosition.y + 130), self.font(16), "Your Score: " + str(currentPlayer.score), self.WINDOW_WIDTH)
        scoreOutput = ""
        for plyr in self.highScorePlayers:
            scoreOutput += str(self.highScorePlayers.index(plyr) + 1) + ". " + str(plyr) + "\n"
        self.createText(Point2D(textPosition.x, textPosition.y + 200), self.font(12), scoreOutput, self.WINDOW_WIDTH)
        self.createText(Point2D(textPosition.x, textPosition.y + 275), self.font(20), "Press the space bar to restart!", self.WINDOW_WIDTH)

    def runGame(self):
        self.restart()
        while not self.GAME_OVER and self.ship in self.agents:
            time.sleep(0.5/60.0)
            self.update()

    def pauseGame(self):
        textPosition = Point2D(self.WINDOW_WIDTH/2,self.WINDOW_HEIGHT/2)
        self.createText(textPosition, self.font(36), 'GAME PAUSED', textPosition.x)

    def update(self):
        if not self.GAME_PAUSED:
            #If there are commands keyed in, move accordingly. If not, automatically slow down.
            if len(self.commands) > 0:
                self.movement()
            else:
                self.ship.stop()
            #Update and redraw all agents. Do not draw asteroids if game hasn't started.
            for agent in self.agents:
                if issubclass(type(agent), MovingBody):
                    agent.update()
            self.clear()
            for agent in self.agents:
                if self.GAME_STARTED or type(agent) == Ship or type(agent) == Photon:
                    self.draw_shape(agent.shape(), agent.color())
            self.ship.draw_shield()
            chance = random.randint(1,3000)
            if chance == 1000:
                MegaBonusBomb(self)
            elif chance == 2000:
                Wormhole(self)
            #Draw score/level/health/photon no. update
            textPosition = Point2D(self.WINDOW_WIDTH - 120,50)
            self.createText(textPosition, self.font(12), self.reportStr(), 120)
            #Replacing Photons if needed
            if self.GAME_STARTED:
                self.nomore_photon_ticks -= 1
                if self.nomore_photon_ticks == 0:
                    self.nomore_photon_ticks = self.DELAY_PHOTON_RUN_OUT
                    if self.ship.photon_number < 200:
                        self.ship.photon_number += min(10, 200 - self.ship.photon_number)

            #Welcome the player before the game starts.
            if not self.GAME_STARTED:
                textPosition = Point2D(self.WINDOW_WIDTH/2,self.WINDOW_HEIGHT/2)
                self.createText(textPosition, self.font(14), GAME_WELCOME_TEXT, textPosition.x*1.5)
            #Initialise asteroids
            else:
                tense = (self.number_of_asteroids >= self.max_asteroids())
                tense = tense or (self.number_of_shrapnel >= 2*self.level)
                if not tense and random.random() < self.INTRODUCE_CHANCE:
                    LargeAsteroid(self)
                #Check the player's health, and kill the game if needed.
                if self.ship.health <= 0:
                    self.gameOver()
        else:
            self.pauseGame()
        Frame.update(self)

    def handle_keypress(self,event):
        if event.char == '5':
            print("# of As: ", self.number_of_asteroids)
            print("Max: ", self.max_asteroids())
        if not self.GAME_STARTED and event.char == KEY_START:
            self.GAME_STARTED = True
            return
        Game.handle_keypress(self, event)
        if self.GAME_OVER and event.char == KEY_SHOOT:
            self.runGame()
        elif event.char == KEY_SHOOT:
            self.ship.shoot()

PLAYER_NAME = input("Hi! I'm AstroShip. I DESTROY Asteroids. And you are? ")
while PLAYER_NAME == "":
    print("Sorry!😞  We're gonna need a name.")
    PLAYER_NAME = input("Go on, tell us! ")
dexterity = input("Thanks %(name)s! Now, are you left-handed (y/n)? "%{'name':PLAYER_NAME.title()})
while dexterity != 'y' and dexterity != 'n':
    dexterity = input("Whoops! Didn't catch that. Are you left-handed (y/n)? ")
if dexterity == 'y':
    KEY_UP    = 'w'
    KEY_DOWN  = 's'
    KEY_LEFT  = 'a'
    KEY_RIGHT = 'd'
    DESCRIPTOR_KEY_UP    = "'w'"
    DESCRIPTOR_KEY_DOWN  = "'s'"
    DESCRIPTOR_KEY_LEFT  = "'a'"
    DESCRIPTOR_KEY_RIGHT = "'d'"
SET_FORWARDLEFT  = {KEY_UP,KEY_LEFT}
SET_FORWARDRIGHT = {KEY_UP,KEY_RIGHT}
SET_BACKLEFT     = {KEY_DOWN,KEY_LEFT}
SET_BACKRIGHT    = {KEY_DOWN,KEY_RIGHT}
GAME_WELCOME_TEXT = "Welcome, %(name)s!\n\nAsteroids are bad. Your job is to destroy them ALL. And remember, crashing into asteroids damgages your ship!\n\nUse %(left)s and %(right)s to turn left and right, %(forward)s to move forward, %(backward)s to move backwards, and the space bar to shoot.\nGive the controls a try if you want!\n\nOh, and look out for special asteroids.\nGreen ones increase your health if you destroy 'em, but pink ones will decrease it! Hopefully your ship doesn't die...\n\nAlso, use your ship's photons wisely, they're a limited resource.\nYou can press '%(pause)s' if you need to pause the game at any time.\n\nNow, let's see if you can beat the high score :-)\nPress '%(start)s' to begin!"%{'name':PLAYER_NAME.title(), 'left':DESCRIPTOR_KEY_LEFT, 'right':DESCRIPTOR_KEY_RIGHT, 'forward':DESCRIPTOR_KEY_UP, 'backward':DESCRIPTOR_KEY_DOWN, 'pause':KEY_PAUSE, 'start':KEY_START}
game = PlayAsteroids()
game.runGame()