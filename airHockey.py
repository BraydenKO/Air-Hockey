"""
airHockey v. AI:
note: the ai does not take into account that
if it hits the puck at the wrong angle, the puck
can fly into its goal.
"""


import pygame
from pygame.constants import KEYDOWN, K_DOWN, K_UP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from pygame.sprite import collide_circle
import math
import numpy as np
RUNNING = True
follow_mouse = False
pygame.init()
clock = pygame.time.Clock()
ai_wins = '0'
player_wins = '0'

width = 1500
height = 900
screen = pygame.display.set_mode((width,height))

#This creates the background of the Air Hockey Table and scales it
table = pygame.image.load(r"photos/AirHockeyBoard.png").convert()
table = pygame.transform.scale(table, (width, height))

#The font is used for displaying the scores
myfont = pygame.font.SysFont('Comic Sans MS', 30, bold=True)
pygame.display.set_caption("Air Hockey")

#The strikers and puck are stored as sprites, the target is just a rect
all_sprites_list = pygame.sprite.Group()
target = pygame.Rect(0,0,50,50)

#This function takes vector1 and rotates it to the same angle
#as vector 2. When a puck and a cirlce collide at point P. The puck should
#travel along the axis perpendicular to the tangent of the cirlces at point P
#The speed is determined by adding the speed of the striker and opposite of the puck
def rotate(vector1,vector2):
  vector3 = [0,0]
  v1mag = math.sqrt(vector1[0]**2 + vector1[1]**2)
  v2mag = math.sqrt(vector2[0]**2 + vector2[1]**2)

  if vector2[1] >= 0:
    theta = math.acos(vector2[0]/v2mag)
  elif vector2[1] < 0:
    theta = -1 * math.acos(vector2[0]/v2mag)
  

  vector3[0] = v1mag * math.cos(theta)
  vector3[1] = v1mag * math.sin(theta)
  return vector3

#This function prints the winner to the terminal
#and adds to their respective score
def win(winner,puck):
  global ai_wins,player_wins
  puck.rect.center = (width/2,height/2)
  puck.speed = [0,0]
  print(winner, "won")
  if winner == "ai":
    ai_wins = str(int(ai_wins) + 1)
  else:
    player_wins = str(int(player_wins)+1)

'''
Puck Sprite -
Image is a green circle
Starting position is in the center
It's radius is 83/2

move(self) determines if the puck hits a striker and calculates
the proper rotations to determine it's new speed (represented as a vector (xspeed,yspeed)).

This function also makes sure the puck bounces off of walls and can go through
the goal of height 285->612 and determines if a goal was made.

Lastly, this function makes the speed of the puck decay in both axii by 2%
and will put it to a halt in either axis if the absolute value of its speed
is less than 0.5 pixels per frame.
'''
class Puck(pygame.sprite.Sprite):
  def __init__(self):
    super().__init__()

    puckimg = pygame.image.load(r"photos/puck.png")
    self.image = pygame.transform.scale(puckimg, (83,83))
    self.radius = 83/2
    self.rect = self.image.get_rect()
    self.rect.center = (width/2,height/2)
    #horizontal speed - vertical speed
    self.speed = [0,0]

  def move(self):
    if collide_circle(self,striker1) == True:

      #the vector that connects the center of the striker to the center of the puck
      connected = [self.rect.center[0]-striker1.rect.center[0],self.rect.center[1]-striker1.rect.center[1]]

      proj1 = rotate(striker1.speed,connected)
      self.speed = [-self.speed[i] if self.speed[i]*striker1.speed[i] <= 0 else self.speed[i] for i in range(2)]
      proj2 = rotate(self.speed,connected)
      self.speed = [i+j for i,j in zip(proj1,proj2)]

    if collide_circle(self,striker2) == True:
      connected = [self.rect.center[0]-striker2.rect.center[0],self.rect.center[1]-striker2.rect.center[1]]
      proj1 = rotate(striker2.speed,connected)
      self.speed = [-self.speed[i] if self.speed[i]*striker2.speed[i] <= 0 else self.speed[i] for i in range(2)]
      proj2 = rotate(self.speed,connected)
      self.speed = [i+j for i,j in zip(proj1,proj2)]




    if self.rect.top < 0:
      self.rect.top = 0
      self.speed[1] *= -1

    elif self.rect.bottom > height:
      self.rect.bottom = height
      self.speed[1] *= -1

    if self.rect.right > width and (self.rect.top < 285 or self.rect.bottom > 612):
      self.rect.right = width
      self.speed[0] *= -1

    elif self.rect.left < 0 and (self.rect.top < 285 or self.rect.bottom > 612):
      self.rect.left = 0
      self.speed[0] *= -1

    if self.rect.center[0] < 0:
      win("player",self)
    elif self.rect.center[0] > width:
      win("ai",self)


    self.rect.x += self.speed[0]
    self.rect.y += self.speed[1]

    self.speed[0] -= self.speed[0]/50
    self.speed[1] -= self.speed[1]/50
    if abs(self.speed[0]) < 0.5:
      self.speed[0] = 0
    elif abs(self.speed[0]) > 100:
      self.speed[0] = np.sign(self.speed[0]) * 100
    if abs(self.speed[1]) < 0.5:
      self.speed[1] = 0
    elif abs(self.speed[1]) > 100:
      self.speed[1] = np.sign(self.speed[1]) * 100

'''
Striker Sprite - 
Image can be a blue or red striker
has a radius of 133/2 (greater than the puck)
and is manually centered when this sprite is created

calc_decay(self,puck) is not used (may be one day)
but calculates roughly where the puck will be when it stops moving.
Better accuracy can probably be obtained by decreasing the 1 in the n equation
to a number closer to 0.5 (the puck's full stop)

ai_move(self,puckspeed,puckpos,puck) doesn't need those arguments
but I gave it them and am too lazy to change it. It works.
This calculates the puck's future position and acts accordingly to
intercept it. 

  First it determines if and which direction its moving. Based on that
  it determins where the puck will be when it hits either the top or bottom
  walls.
  If it's not moving, it has slope = 0.
  If it hits a top/bottom wall inside the ai's play range,
  It creates a line from that 'bounce point' that the puck will travel.
  If it bounces outside the ai's play range, do nothing as there's no way
  to predict what it's opponent (you) will do.
  If it never bounces and goes straight for the backwall
  create a line that the puck will travel.

  After this, if the slope isn't 0, create a perpendicular line
  from the striker to the puck's line to determine the fastest way to
  intersect that line. Put a marker there.
  However, if the slope is 0, creat a vertical line of underfined slope
  to create a perpendicular line for the same reason.
  But if the puck isn't moving, put the target onto the puck because there
  is no trajectory to intersect.

  The rest of the function determines speed of the ai and makes sure it
  doesn't leave its play range.
'''
class Striker(pygame.sprite.Sprite):
  def __init__(self, color,pos):
    super().__init__()

    if color == "BLUE":
      strikerimg = pygame.image.load(r"photos/striker1.png")
    elif color == "RED":
      strikerimg = pygame.image.load(r"photos/striker2.png")
    self.image = pygame.transform.scale(strikerimg, (133,133))
    self.radius = 133/2
    self.rect = self.image.get_rect()
    self.rect.center = pos
    self.speed = [0,0]
  
  def calc_decay(self,puck):
    if abs(puck.speed[0]) > 0:
      n = math.log(1/abs(puck.speed[0]))/(-0.020202707317519466)
      S = puck.speed[0]*((1-0.98**n)/(1-0.98))
      X = puck.rect.center[0] + S
      target.centerx = X
    else:
      target.centerx = puck.rect.centerx
    if abs(puck.speed[1]) > 0:
      n = math.log(1/abs(puck.speed[1]))/(-0.020202707317519466)
      S = puck.speed[0]*((1-0.98**n)/(1-0.98))
      Y = puck.rect.center[1] + S
      target.centery = Y
    else:
      target.centery = puck.rect.centery

  def ai_move(self,puckspeed, puckpos,puck):
    if puckspeed[1] < 0: #going up
      new_x = puckpos[0] + (-1 * puckpos[1])/puckspeed[1] * puckspeed[0]
      new_y = 0
    elif puckspeed[1] > 0: #going down
      new_x = puckpos[0] + (height-puckpos[1])/puckspeed[1] * puckspeed[0]
      new_y = height
    else:
      new_x = -1
      new_y = puckpos[1]

    if abs(puckspeed[0]) + abs(puckspeed[1]) < 4 and puckpos[0] < width/2: 
      slope = 0
    elif 0 < new_x < width/2:
      #bounce
      try:
        slope = (puckspeed[1] * -1)/puckspeed[0]
      except ZeroDivisionError:
        slope = 0
      intercept = slope*(-1 * new_x) + new_y

    elif new_x > width/2:
      #self.ai_move(puckspeed,(new_x,-new_y))
      return

    else:
      #no bounce
      try:
        slope = (puckspeed[1])/puckspeed[0]
      except ZeroDivisionError:
        slope = 0
      intercept = slope*(-1 * puckpos[0]) + puckpos[1]

    if slope != 0:
      pslope = -1/slope
      pintercept = slope*(-1*self.rect.center[0])+self.rect.center[1]
      intersectx = (intercept - pintercept)/(pslope - slope)
      intersecty = intersectx*slope + intercept
      target.center = intersectx,intersecty
    else:
      if abs(puckspeed[0]) + abs(puckspeed[1]) < 4 and puckpos[0] < width/2: 
        target.center = puckpos
      else:
        intersectx = self.rect.center[0]
        intersecty = intercept
        self.speed = [0,np.sign(intersectx-puckpos[0])*10]
        target.center = intersectx,intersecty

    if target.centerx < 0:
      target.center = 0,intercept


    self.speed[0] = (target.center[0]-self.rect.center[0])/4
    self.speed[1] = (target.center[1]-self.rect.center[1])/4
    self.rect.x += self.speed[0]
    self.rect.y += self.speed[1]

    if self.rect.top < 0:
      self.rect.top = 0
    elif self.rect.bottom > height:
      self.rect.bottom = height
    if self.rect.left < 0:
      self.rect.left = 0
    elif self.rect.right > width/2:
      self.rect.right = width/2

'''
Player(Striker) Sprite -
Is a striker, and has access to ai_move,
despite the fact it wont work for the player

move(self, followmouse) just makes sure the striker
follows the mouse when clicked but doesn't go outside of
it's play range (even if the mouse does)
'''    
class Player(Striker):
  def __init__(self,color,pos):
    super().__init__(color,pos)

  def move(self,follow_mouse):
    if follow_mouse == True:
      self.rect.center = pygame.mouse.get_pos()
    if self.rect.top < 0:
      self.rect.top = 0
    elif self.rect.bottom > height:
      self.rect.bottom = height
    if self.rect.right > width:
      self.rect.right = width
    elif self.rect.left < width/2:
      self.rect.left = width/2

puck = Puck()
striker1 = Player("BLUE", (3*width/4+100,height/2))
striker2 = Striker("RED", (width/4-100,height/2))

all_sprites_list.add(puck,striker1,striker2)


#This is where the game is ran
while RUNNING:
  for event in pygame.event.get():
    #Required to easily exit the game
    if event.type== pygame.QUIT:
      RUNNING = False
    if event.type == KEYDOWN:
      #Fixes soft locks and you can award points as you'd like
      if event.key == K_DOWN:
        win("player",puck)
      if event.key == K_UP:
        win("ai",puck)
    #If you left click on your striker, make it follow you
    if event.type == MOUSEBUTTONDOWN and event.button == 1:
      mouse_pos = pygame.mouse.get_pos()
      if striker1.rect.collidepoint(mouse_pos) == True:
        follow_mouse = True
    #If you release left click, make the striker stop following you
    elif event.type == MOUSEBUTTONUP and event.button == 1:
       follow_mouse = False
       striker1.speed = [0,0]
    
    #Calculate speed of the mouse in order to give that speed to the striker
    #Speed really matters when calculating how much force to apply to the puck
    #on impact.
    if event.type == MOUSEMOTION and follow_mouse == True:
      dx,dy = event.rel
      striker1.speed[0]=dx
      striker1.speed[1]=dy
      
    
  #If the mouse leaves the screen, set the striker speed to 0.
  #If this isn't done, then the striker could be on a wall, motionless
  #but still can have a vertical/horizontal speed, which would mess up
  #puck-striker collisions
  if pygame.mouse.get_focused() == False:
    striker1.speed = [0,0]

  #Game Logic
  puck.move()
  striker1.move(follow_mouse)
  striker2.ai_move(puck.speed,puck.rect.center,puck)

  #renders the scoredisplays
  lossdisplay = myfont.render(ai_wins, False, (255,200,200))
  windisplay = myfont.render(player_wins, False, (255,200,200))

  #updates and displays everything
  screen.blit(table,(0,0))
  screen.blit(lossdisplay, (50,20))
  screen.blit(windisplay,(width-50,20))
  all_sprites_list.draw(screen)
  pygame.draw.rect(screen, (0,0,0), target, 3)
  
  pygame.display.flip()
  clock.tick(60)
