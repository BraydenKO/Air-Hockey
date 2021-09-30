import os

from pygame.constants import K_DOWN, KEYDOWN
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import math
import numpy as np
from pygame.sprite import collide_circle
import pickle
import matplotlib.pyplot as plt
import time
from copy import deepcopy

# Define whether you want to create a pickle file for the new q_table
# You will often want this to be True, but its default is False
# To prevent tons of pickle files forming
create_pickle = False

# How many episodes (rounds) to train for
HM_EPISODES = 100_000
# Display a round every {SHOW_EVERY} rounds
SHOW_EVERY = 1_000

start_q_table = r"Docs\2AH_table-1632959342.pickle"

# The variables above are encouraged to be changed depeding on what the user wants
#----------------------------------------------------------------#

LOSS_PENALTY = -300
WIN_REWARD = 400
MOVE_PENALTY = -1
ENEMY_SIDE_REWARD = 1
epsilon = 0.9
EPS_DECAY = 0.999999

LEARNING_RATE = 0.1
DISCOUNT = 0.95

# The board is a square 1000 x 1000. Doesn't have to be but the pre-trained
# AI's were trained on a 1000 x 1000 table and may or may not be able to 
# extrapolate to different dimension. If you want the board to be a rectangle
# get_discrete_state() needs editing
SIZE = 1000

#--------------------------------------------------------------------#

pygame.init()
screen = pygame.display.set_mode((SIZE,SIZE))
table = pygame.image.load(r"photos/AirHockeyBoard.png").convert()
table = pygame.transform.scale(table, (SIZE, SIZE))
clock = pygame.time.Clock()

'''
Rotates the velocity vectors to line up with the radius that
passes through the point of contact between the striker and puck

Its use is so that the puck and striker velocity vectors can be lined
up and added to eachother
'''
def rotate(vector1,vector2):
  vector3 = [0,0]
  v1mag = math.sqrt(vector1[0]**2 + vector1[1]**2)
  v2mag = math.sqrt(vector2[0]**2 + vector2[1]**2)

  if vector2[1] >= 0:
    try:
      theta = math.acos(vector2[0]/v2mag)
    except ZeroDivisionError:
      return [0,0]
  elif vector2[1] < 0:
    try:
      theta = -1 * math.acos(vector2[0]/v2mag)
    except ZeroDivisionError:
      return [0,0]
  

  vector3[0] = v1mag * math.cos(theta)
  vector3[1] = v1mag * math.sin(theta)
  return vector3

'''
 - The Puck object.
move(self) first checks if it collides with either striker 
then rotates their speed vectors to line up with the lines
that passes through the point of contact. It adds their velocities 
to calculate the puck's new velocity after being hit.

After that it makes checks to make sure the puck doesn't leave the
arena unless it was knocked into the goal.
'''
class Puck(pygame.sprite.Sprite):
  def __init__(self):
    super().__init__()

    puckimg = pygame.image.load(r"photos/puck.png")
    self.image = pygame.transform.scale(puckimg, (83,83))
    self.radius = 83/2
    self.rect = self.image.get_rect()
    self.rect.center = (SIZE/2,SIZE/2)
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

    if self.rect.top <= 0: 
      self.speed[1] *= -1
    elif self.rect.bottom >= SIZE:
      self.speed[1] *= -1
    if self.rect.right >= SIZE and (self.rect.top < 285 or self.rect.bottom > 612):
      self.speed[0] *= -1
    elif self.rect.left <= 0 and (self.rect.top < 285 or self.rect.bottom > 612):
      self.speed[0] *= -1

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

    if self.rect.top <= 0:
      self.rect.top = 0
    elif self.rect.bottom >= SIZE:
      self.rect.bottom = SIZE
    if self.rect.right >= SIZE and (self.rect.top < 285 or self.rect.bottom > 612):
      self.rect.right = SIZE
    elif self.rect.left <= 0 and (self.rect.top < 285 or self.rect.bottom > 612):
      self.rect.left = 0

'''
- Striker object.
There are two types the blue one (right), and red (left)
action() is fed a choice 0-4 and the side the striker is on and it
calls move() to move in the corresponding direction that the choice says to
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
    

  def __str__(self):
    print(f"{self.rect.center}")

  def action(self,choice,side):
    if choice == 0: #right
      self.move(x=50, y=0, side=side)
    elif choice == 1: #left
      self.move(x=-50,y=0, side=side)
    elif choice == 2: #up
      self.move(x=0, y=-50, side=side)
    elif choice == 3: #down
      self.move(x=0,y=50, side=side)
    elif choice == 4: #don't move
      self.move(x=0,y=0, side=side)

  def move(self,x,y,side):
    # The speed is assigned and then the position is updated based on the speed
    # instead of updating the position directly because collisions will be based
    # on the speed and so the speed needs to exist.
    self.speed = [x,y]

    self.rect.x += self.speed[0]
    self.rect.y += self.speed[1]
    
    if self.rect.top < 0:
      self.rect.top = 0
    elif self.rect.bottom > SIZE:
      self.rect.bottom = SIZE

    if side == "left":
      if self.rect.right > SIZE/2:
        self.rect.right = SIZE/2
      
      if self.rect.left < 0:
        self.rect.left = 0

    else:
      if self.rect.left < SIZE/2:
        self.rect.left = SIZE/2
      
      if self.rect.right > SIZE:
        self.rect.right = SIZE

table_size = 30

'''
On the board there are 1000 x positions and 1000 y positions. 
This can lead to an enormous q_table with reduntant points. This compresses
things from a given range, {possible_values} to a range of 0-30. State can be 
either an integer or a tuple.
'''
def get_discrete_state(state,possible_values):
  is_int = False
  if len(state) == 1:
    is_int = True

  discrete_state = np.array(state) * 29 / possible_values
  discrete_state = discrete_state.astype(int)

  if not is_int:
    for idx, val in enumerate(discrete_state):
      
      if val < 0:
        discrete_state[idx] = 0
      elif val > 29:
        discrete_state[idx] = 29
    
    
  return tuple(discrete_state)

'''
Checks if {start_q_table} is defined above. If not, it creates a
q_table of dimension [30][30][30][30][5] with random q_values ranging
from -1 to 1.
If it exists, just load the pickle file.
'''
def get_q_table(start_q_table):
  if start_q_table == None:
    q_table = np.random.uniform(low = -1, high=1, size = [table_size]*4 + [5])
    if create_pickle == True:
      with open(f"Docs/AHrand-{int(time.time())}.pickle", "wb") as f:
        pickle.dump(q_table, f)
    print("q_table made")

  else:
    with open(start_q_table, "rb") as f:
      q_table = pickle.load(f)
    print(f"q_table used {start_q_table}")
  return q_table


q_table = get_q_table(start_q_table)


episode_rewards = []

# Run the simulation here:
# Go through each episode and begin by setting the environment up
for episode in range(HM_EPISODES):

  puck = Puck()
  striker2 = Striker("BLUE", (3*SIZE/4+100,SIZE/2))
  striker1 = Striker("RED", (SIZE/4-100,SIZE/2))
  all_sprites_list = pygame.sprite.Group()
  all_sprites_list.add(puck,striker1,striker2)

  if episode % SHOW_EVERY == 0:
    print(f"on # {episode}, epsilon: {epsilon}")
    print(f"{SHOW_EVERY} ep mean {np.mean(episode_rewards[-SHOW_EVERY:])}")
    render = True
  else:
    render = False
  
  episode_reward = 0
  
  end = False

  # The user can press the down arrow to end the simulation early
  for event in pygame.event.get():
    if event.type == KEYDOWN:
      if event.key == K_DOWN:
        end = True
  if end:
    break

  # The sim will run for 300 frames.
  for i in range(300):
    # Get the observation and action for the left striker
    puck_center = get_discrete_state(puck.rect.center, SIZE)
    self_center = get_discrete_state([striker1.rect.centerx], SIZE/2) + get_discrete_state([striker1.rect.centery], SIZE)
    obs = puck_center + self_center

    # Based on epsilon, the action may or may not be random
    if np.random.random() > epsilon:
      action = np.argmax(q_table[obs])
    else:
      action = np.random.randint(0,5)
    
    striker1.action(action,"left")
    
    # Get the observation and action for the right striker
    # No exploration
    puck_center_op = ((table_size - 1) - puck_center[0], puck_center[1])
    self_center_op = get_discrete_state([SIZE - striker2.rect.centerx], SIZE/2) + get_discrete_state([striker2.rect.centery], SIZE)
    obs_op = puck_center_op + self_center_op

    # Get action (note: because this is flipped, actions left and right have to be flipped back)
    action_op = np.argmax(q_table[obs_op])

    if action_op == 0: # right
      action_op = 1 # go left

    elif action_op == 1: #left
      action_op = 0 # go right

    striker2.action(action_op, "right")

    puck.move()

    # Looks at future observation and q_values and based on the reward for the given
    # state, create a new q_value ({new_q}) and put it in the table
    puck_center = get_discrete_state(puck.rect.center, SIZE)
    self_center = (get_discrete_state([striker1.rect.centerx], SIZE/2) + get_discrete_state([striker1.rect.centery], SIZE))
    new_obs = puck_center + self_center
    
    assert all(idx < 30 for idx in new_obs), f"{new_obs} contains an index > 29 \npuck : {puck.rect.center}\nstriker : {striker1.rect.center}"

    max_future_q = np.max(q_table[new_obs])
    
    current_q = q_table[obs][action] 


    if puck.rect.centerx <= 0:
      reward = LOSS_PENALTY
      new_q = LOSS_PENALTY
    elif puck.rect.centerx >= SIZE:
      reward = WIN_REWARD
      new_q = WIN_REWARD
    elif puck.rect.centerx > SIZE/2:
      reward = ENEMY_SIDE_REWARD
      new_q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (reward + DISCOUNT * max_future_q)
    else:
      reward = MOVE_PENALTY
      new_q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (reward + DISCOUNT * max_future_q)


    q_table[obs][action] = new_q

    # Render the game
    if render == True:
      screen.blit(table,(0,0))
      all_sprites_list.draw(screen)
      pygame.display.flip()
      clock.tick(60)
    
    episode_reward += reward
    if reward == LOSS_PENALTY or reward == WIN_REWARD:
      break

  if render == True: print(f"rendered reward was {episode_reward}")
  episode_rewards.append(episode_reward)
  epsilon *= EPS_DECAY

# After the sim is complete, a graph will show up displaying 
# the moving average for the total rewards in each episode
moving_avg = np.convolve(episode_rewards, np.ones((SHOW_EVERY,))/SHOW_EVERY, mode='valid')

plt.plot([i for i in range(len(moving_avg))], moving_avg)
plt.ylabel(f"Reward {SHOW_EVERY}ma")
plt.xlabel("episode #")
plt.show()

# Creates a new q_table file and increases the starting number by 1
if create_pickle == True:
  if start_q_table is not None:
    number = int(start_q_table[5]) + 1
  else:
    number = 0
  with open(f"Docs/{number}AH_table-{int(time.time())}.pickle", "wb") as f:
      pickle.dump(q_table, f)


