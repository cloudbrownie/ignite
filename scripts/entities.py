import pygame
import random
import math
import time
import json

from scripts.particles import GlowParticle, LeafParticle
from scripts.effects import *

gameScale = 1
try:
    with open('data/config.json') as readFile:
        gameScale = json.load(readFile)['scale']
except Exception as e:
    print(f'[+] {e}')

def mostFrequentPixelColor(pixels):
    counter = 0
    color = pixels[0]

    for i in pixels:
        currentFreq = pixels.count(i)
        if (currentFreq > counter):
            counter = currentFreq
            color = i

    return color

def collisionTest(testRect, tiles):
    return [rect for rect in tiles if rect[0].colliderect(testRect)]

def cap(value, maxVal):
    if value > maxVal:
        value = maxVal
    elif value < -maxVal:
        value = -maxVal
    return value

greenColors = (60, 89, 86), (57, 123, 58), (113, 170, 52), (182, 213, 60)
stoneColors = (38, 43, 68), (24, 20, 37), (58, 68, 102)
fireColors = (244, 180, 27), (244, 126, 27), (230, 72, 46)
fireGlowColors = (24, 12, 2), (24, 18, 2), (23, 7, 4)

class Torch:
    def __init__(self, topleftx, toplefty, texture):
        self.surface = texture.copy()
        self.rect = pygame.Rect(topleftx, toplefty, texture.get_width(), texture.get_height())
        # define the point for creating particles
        self.particleSpawn = -3 * gameScale, -2 * gameScale
        # active switch
        self.active = False
        # particle spawn time
        self.spawnTime = 0
        # torch light hit box
        self.lightHitBox = pygame.Rect(topleftx - 1 * gameScale, toplefty - 1 * gameScale, 8 * gameScale, 7 * gameScale)
        self.lastSpawnTime = time.time()
        self.boom = False

    def update(self, display, scroll, cameraRect, particles, effects, sparks):
        # check if the torch is in render distance
        if self.rect.colliderect(cameraRect):
            # draw the torch
            display.blit(self.surface, (self.rect.x - scroll[0], self.rect.y - scroll[1]))

        # create particles            
        distance = (self.rect.center[0] - cameraRect.center[0]) ** 2 + (self.rect.center[1] - cameraRect.center[1]) ** 2
        if self.active and time.time() - self.lastSpawnTime > self.spawnTime and distance < (cameraRect.width * .75) ** 2:
            # create the particle
            particleColor = random.choice(fireColors)
            glowColor = random.choice(fireGlowColors)
            particles.append(GlowParticle(self.rect.x - self.particleSpawn[0], self.rect.y - self.particleSpawn[1], (random.uniform(-.01, .01), random.uniform(-.075, -.05)), particleColor, glowColor, random.randint(2, 5) * gameScale, random.uniform(.01, .02) * gameScale))

            # reset spawn time
            self.spawnTime = random.uniform(250, 500) / 1000
            self.lastSpawnTime = time.time()

        # create boom
        if self.active and not self.boom:
            self.boom = True
           # effects.append(CircleEffect(self.lightHitBox.center, random.choice(fireColors), random.choice(fireGlowColors), random.uniform(32, 64) * gameScale, 2 * gameScale))
            for i in range(20, 25):
                sparks.append(Spark(self.lightHitBox.center, math.radians(random.randint(0, 360)), random.uniform(1, 2) * gameScale, (255, 255, 255), scale=2 * gameScale))
            for i in range(15, 20):
                angle = math.radians(random.randint(0, 360))
                particles.append(GlowParticle(self.lightHitBox.centerx, self.lightHitBox.centery, (2.5 * math.cos(angle) * gameScale, 2.5 * math.sin(angle) * gameScale), random.choice(fireColors), random.choice(fireGlowColors), random.uniform(5, 10) * gameScale, random.uniform(.25, .5) * gameScale))

class Tree:
    def __init__(self, topleftx, toplefty, texture):
        self.surface = texture.copy()
        self.rect = pygame.Rect(topleftx, toplefty, texture.get_width(), texture.get_height())
        # use the red spots for wobbling
        self.wobblespots = []
        # scale the tree down to 1 if the gamescale is greater than 1
        if gameScale > 1:
            self.surface = pygame.Surface((texture.get_width() // gameScale, texture.get_height() // gameScale))
            self.surface.blit(pygame.transform.scale(texture, self.surface.get_size()), (0, 0))

        # find the red spots
        for i in range(self.surface.get_width()):
            for j in range(self.surface.get_height()):
                if self.surface.get_at((i, j)) == (255, 0, 0, 255):
                    # use the neighboring colors to convert this red pixel to a different color
                    neighboringColors = [self.surface.get_at((i + 1, j)), self.surface.get_at((i - 1, j)), self.surface.get_at((i, j + 1)), self.surface.get_at((i, j - 1))]
                    self.surface.set_at((i, j), mostFrequentPixelColor(neighboringColors))

                    # cut out the tree at that point
                    radius = random.randint(2, 4)

                    # make leaf mask
                    leafMask = pygame.Surface((self.surface.get_width(), self.surface.get_height()))
                    pygame.draw.circle(leafMask, (255, 255, 255), (i, j), radius)
                    leafMask.set_colorkey((255, 255, 255))

                    # copy the texture
                    treeCopy = self.surface.copy()

                    # draw mask onto copy
                    treeCopy.blit(leafMask, (0, 0))
                    treeCopy.set_colorkey((0, 0, 0))

                    # get only the masked region
                    leafMask = pygame.mask.from_surface(treeCopy)
                    leafMask = treeCopy.subsurface(leafMask.get_bounding_rects()[0])

                    # scale the leaf mask
                    if gameScale > 1:
                        newSurf = pygame.Surface((leafMask.get_width() * gameScale, leafMask.get_height() * gameScale))
                        newSurf.blit(pygame.transform.scale(leafMask, newSurf.get_size()), (0, 0))
                        leafMask = newSurf.copy()
                        leafMask.set_colorkey((0, 0, 0))

                    # store
                    self.wobblespots.append((leafMask, (self.rect.x + i * gameScale - leafMask.get_width() / 2, self.rect.y + j * gameScale - leafMask.get_height() / 2)))

        # rescale the tree
        if gameScale > 1:
            newSurf = pygame.Surface((texture.get_width(), texture.get_height()))
            newSurf.blit(pygame.transform.scale(self.surface, newSurf.get_size()), (0, 0))
            self.surface = newSurf.copy()
            self.surface.set_colorkey((0, 0, 0))

        self.spawnTime = 0

    def update(self, display, scroll, cameraRect, particleList, wind, windMultiplier):
        # check if in frame
        if cameraRect.colliderect(self.rect):
            # blit the tree
            display.blit(self.surface, (self.rect.x - scroll[0], self.rect.y - scroll[1]))

            # iterate through wobble spots
            for wobble in self.wobblespots:
                # blit wobble 
                mod = (math.cos(((wobble[1][0] + 500) / 400) * time.time()) + math.sin(((wobble[1][1] + 500) / 400) * time.time())) * wind * gameScale
                display.blit(wobble[0], (wobble[1][0] - scroll[0] - mod, wobble[1][1] - scroll[1] + mod))
                # create leaves
                if random.randint(1, 1000) < 2 * (windMultiplier * .1):
                    particleList.append(LeafParticle(wobble[1][0], wobble[1][1], random.choice(greenColors), random.randint(1, 2)))

class Player:
    def __init__(self, startx, starty, textures, soundEffects, gameScale):
        # player hitbox 
        self.rect = pygame.Rect(startx, starty, 1, 1)
        self.feetRect = pygame.Rect(startx, starty, 1, 1)
        self.scale = gameScale

        # player movements variables
        self.inputs = {
            'left':False,
            'right':False,
            'jump':False,
            'drop':False
        }
        self.movements = [0, 0]
        self.forces = [0, 0]
        self.speed = 2 * gameScale
        self.maxSpeed = 5 * gameScale
        self.jumps = 2 
        self.jumpHeight = -5 * gameScale
        self.gravity = 2 * gameScale
        self.lastGroundTouch = 0
        self.onPlatform = False
        self.jumpCut = False

        # animation frame dictionary
        self.animationFrames = {
            'idle':textures[0],
            'run':textures[1],
            'jump':textures[2],
            'float':textures[3],
            'fall':textures[4],
            'land':textures[5],
            'fire':textures[6]
            }
        # animation state frame lengths
        self.animationInfo = {
            'idle':200,
            'run':75,
            'jump':100000,
            'float':100000,
            'fall':125,
            'land':125,
            'fire':125
        }
        self.animationIndex = 0
        self.animationUpdateTime = time.time()
        self.state = 'idle'
        self.flip = False
        self.layer = 0

        # collisions
        self.collisions = {
            'bottom':False,
            'top':False,
            'left':False,
            'right':False
        }

        # ability vars
        self.totalBlaze = 0
        self.lastBlazeRegeneration = 0
        self.blazeLastSpawnTime = 0
        self.blazeSpawnDelay = random.uniform(300 / (self.totalBlaze + 1), 500 / (self.totalBlaze + 1))
        self.dashDistance = 16 * gameScale * 12
        self.dashing = False
        self.dashTo = (0, 0)
        self.dashFrom = (0, 0)

        # sound effects
        self.soundEffects = soundEffects
        self.lastGroundSound = time.time()

        # other
        self.currentGroundColors = ()

        # die
        self.dead = False
        self.diedTime = 0
        self.respawnTime = 2
        self.health = 20
        self.iTime = 0 # invincibility frames, player flashes transparentely
        self.iDuration = 1.5
        self.respawnLocation = 0, 0

    def dash(self):
        self.dashing = True
        self.dashFrom = self.center
        if self.flip:
            self.dashTo = self.center[0] - self.dashDistance, self.center[1]
        else:
            self.dashTo = self.center[0] + self.dashDistance, self.center[1]

    def stateMachine(self):
        newState = 'idle'
        if self.state == 'land':
            newState = 'land'
        if self.state == 'fire':
            newState = 'fire'
        if self.dashing:
            newState = 'run'
        # landing is declared in the updateRect function
        if self.state != 'land' and self.state != 'fire' and not self.dashing:
            # running
            if abs(self.movements[0]) > 0 and (self.inputs['left'] or self.inputs['right']) and self.collisions['bottom']:
                newState = 'run'
            # floating
            elif self.movements[1] < self.jumpHeight + 3:
                newState = 'float'
            # jumping 
            elif self.movements[1] < 0:
                newState = 'jump'
            # falling
            elif self.movements[1] > 1 and not self.collisions['bottom']:
                newState = 'fall'
        # check running
        elif self.state != 'fire' and abs(self.movements[0]) > 0 and (self.inputs['left'] or self.inputs['right']) and self.collisions['bottom']:
            newState = 'run'
            
        # update animation info and stuff if the newstate is not the current state
        if newState != self.state:
            self.animationIndex = 0
            self.state = newState
            self.animationUpdateTime = time.time()    
            if self.state == 'fall' and self.inputs['drop']:
                self.onPlatform = False
                self.inputs['drop'] = False

    def die(self, particles, sparks):
        if not self.dead:
            self.movements = [0, 0]
            self.forces = [0, 0]
            self.totalBlaze = 0
            self.dashing = False
            self.dead = True
            self.diedTime = time.time()
            for i in range(random.randint(20, 30)):
                particles.append(GlowParticle(self.center[0], self.center[1], [random.uniform(-3, 3), random.randint(-3, 3)] * gameScale, random.choice(fireColors), random.choice(fireGlowColors), random.uniform(10, 1), random.uniform(.1, .5)))
            for i in range(random.randint(20, 30)):
                sparks.append(Spark(self.center, math.radians(random.randint(0, 360)), random.uniform(3, 5), (255, 255, 255)))

    def damage(self, damage, particles, sparks):
        if time.time() - self.iTime >= self.iDuration:
            self.iTime = time.time()
            self.health -= damage
            if self.health < 0:
                self.health = 0
            if self.health == 0:
                self.die(particles, sparks)

    def respawn(self, particles):
        self.health = 20
        self.dead = False
        self.rect.center = self.respawnLocation
        for i in range(12):
            angle = math.radians(360 / 12) * i
            motion = 3 * math.cos(angle), 3 * math.sin(angle)
            offset = 75 * math.cos(angle), 75 * math.sin(angle)
            particles.append(GlowParticle(self.center[0] - offset[0], self.center[1] - offset[1], motion, random.choice(fireColors), random.choice(fireGlowColors), 23, .75))

    @property
    def center(self):
        return self.rect.center 

    @property
    def size(self):
        return self.surface.get_size()

    @property
    def surface(self):
        # just return the surface
        surface = self.animationFrames[self.state][self.animationIndex].copy()
        if time.time() - self.iTime < self.iDuration:
            whiteChance = round(abs(math.sin(21 * (time.time() - self.iTime))))
            if whiteChance == 1:
                whiteMask = pygame.mask.from_surface(surface)
                surface = whiteMask.to_surface(setcolor=(255, 255, 255))
                surface.set_colorkey((0, 0, 0))
                return surface
        return surface

    def draw(self, display, scroll):
        # update the frame index
        if time.time() - self.animationUpdateTime >= self.animationInfo[self.state] / 1000:
            self.animationIndex = (self.animationIndex + 1) % len(self.animationFrames[self.state])
            self.animationUpdateTime = time.time()
            # check if we are landing
            if (self.state == 'land' or self.state == 'fire') and self.animationIndex == 0:
                self.state = 'idle'
                self.animationUpdateTime = time.time()

        # mask the surface and find the offsets
        surfaceMask = pygame.mask.from_surface(self.surface)
        surfaceTextureSize = surfaceMask.get_bounding_rects()[0] # theres only one bounding rect

        xDiff = self.rect.w - self.surface.get_width()
        yDiff = self.rect.h - self.surface.get_height()
        self.rect.w = surfaceTextureSize.w
        self.feetRect.w = surfaceTextureSize.w
        self.rect.h = surfaceTextureSize.h
        self.rect.y += yDiff

        # draw the player
        # flipped
        if self.flip:
            flippedSurface = pygame.transform.flip(self.surface, True, False)
            flippedSurface.set_colorkey((0, 0, 0))
            display.blit(flippedSurface, (self.rect.x - scroll[0], self.rect.y - scroll[1]))
        else:
            display.blit(self.surface, (self.rect.right - scroll[0] - self.rect.w, self.rect.y - scroll[1]))

        # pygame.draw.rect(display, (255, 255, 255), (self.rect.x - scroll[0], self.rect.y - scroll[1], self.rect.w, self.rect.h), 1)

    def generateSoundEffects(self):
        if self.state == 'run' and self.currentGroundColors == greenColors and time.time() - self.lastGroundSound >= .25 - (.1 * (self.totalBlaze / 10)) and not self.dashing:
            self.soundEffects['grass'][random.randint(0, len(self.soundEffects['grass']) - 1)].play()
            self.lastGroundSound = time.time()

    def updateRect(self, tiles):
        # reset collisions
        collisions = {
            'bottom':False,
            'top':False,
            'left':False,
            'right':False
        }

        # horizontal movements
        if self.movements[0] != 0:
            if self.movements[0] > 0:
                self.movements[0] = math.ceil(self.movements[0])
            elif self.movements[0] < 0:
                self.movements[0] = math.floor(self.movements[0])

            chunks = int(abs(self.movements[0]) // (self.rect.w / 2))
            for i in range(chunks):
                self.rect.x += (self.rect.w / 2) * (self.movements[0] / abs(self.movements[0]))
                hitList = collisionTest(self.rect, tiles)
                for tile in hitList:
                    if tile[1] != 'platforms':
                        self.forces[0] = 0
                        self.dashing = False
                        if self.movements[0] > 0:
                            self.rect.right = tile[0].left
                            collisions['right'] = True
                        elif self.movements[0] < 0:
                            self.rect.left = tile[0].right
                            collisions['left'] = True
            leftovers = abs(self.movements[0]) - abs(chunks * (self.rect.w / 2))
            self.rect.x += leftovers * (self.movements[0] / abs(self.movements[0]))
            hitList = collisionTest(self.rect, tiles)
            for tile in hitList:
                if tile[1] != 'platforms':
                    self.forces[0] = 0
                    self.dashing = False
                    if self.movements[0] > 0:
                        self.rect.right = tile[0].left
                        collisions['right'] = True
                    elif self.movements[0] < 0:
                        self.rect.left = tile[0].right
                        collisions['left'] = True

        # vertical movements
        if self.movements[1] != 0:
            chunks = int(abs(self.movements[1]) // (self.rect.h / 2))
            for i in range(chunks):
                self.rect.y += (self.rect.h / 2) * (self.movements[1] / abs(self.movements[1]))
                hitList = collisionTest(self.rect, tiles)
                for tile in hitList:
                    if self.movements[1] > 0:
                        # check if trying to drop through
                        if tile[1] == 'platforms' and (self.inputs['drop'] or self.feetRect.top > tile[0].bottom):
                            pass
                        else:
                            # normal collision stuff
                            self.rect.bottom = tile[0].top
                            collisions['bottom'] = True
                            self.lastGroundTouch = time.time()
                            self.jumpCut = False
                            # check if falling, if so we are now landing
                            if self.state == 'fall':
                                self.state = 'land'
                                self.animationIndex = 0
                                self.animationUpdateTime = time.time()
                            # check if a platform
                            if tile[1] == 'platforms':
                                self.onPlatform = True
                            else:
                                self.onPlatform = False
                            # check for ground colors
                            self.currentGroundColors = ()
                            if tile[2] == 'grass':
                                self.currentGroundColors = greenColors
                            elif tile[2] == 'stone':
                                self.currentGroundColors = stoneColors
                            self.forces[1] = 0
                    elif self.movements[1] < 0 and tile[1] != 'platforms':
                        self.rect.top = tile[0].bottom
                        collisions['top'] = True
                        self.forces[1] = 0
            leftovers = abs(self.movements[1]) - abs(chunks * (self.rect.h / 2))
            self.rect.y += leftovers * (self.movements[1] / abs(self.movements[1]))
            hitList = collisionTest(self.rect, tiles)
            for tile in hitList:
                if self.movements[1] > 0:
                    # check if trying to drop through
                    if tile[1] == 'platforms' and (self.inputs['drop'] or self.feetRect.top > tile[0].bottom):
                        pass
                    else:
                        # normal collision stuff
                        self.rect.bottom = tile[0].top
                        collisions['bottom'] = True
                        self.lastGroundTouch = time.time()
                        self.jumpCut = False
                        # check if falling, if so we are now landing
                        if self.state == 'fall':
                            self.state = 'land'
                            self.animationIndex = 0
                            self.animationUpdateTime = time.time()
                        # check if a platform
                        if tile[1] == 'platforms':
                            self.onPlatform = True
                        else:
                            self.onPlatform = False
                        # check for ground colors
                        self.currentGroundColors = ()
                        if tile[2] == 'grass':
                            self.currentGroundColors = greenColors
                        elif tile[2] == 'stone':
                            self.currentGroundColors = stoneColors
                        self.forces[1] = 0
                elif self.movements[1] < 0 and tile[1] != 'platforms':
                    self.rect.top = tile[0].bottom
                    collisions['top'] = True
                    self.forces[1] = 0

        self.collisions = collisions.copy()      
        self.feetRect.y = self.rect.bottom

    def move(self, sparks, dt):
        if self.totalBlaze > 0:
            moddedSpeed = self.speed + (self.speed * self.totalBlaze) * .05
        else:
            moddedSpeed = self.speed

        # not dashing movement stuff
        if not self.dashing:
            # check the inputs
            self.movements = [0, 0]
            if self.inputs['left']:
                self.movements[0] -= moddedSpeed * dt
                self.flip = True
            if self.inputs['right']:
                self.movements[0] += moddedSpeed * dt
                self.flip = False
            
            # modify gravity
            if abs(self.forces[1]) < 5:
                self.gravity += .3 * dt * self.scale
                self.gravity = min(5 * self.scale, self.gravity)

                # apply some gravity
                self.movements[1] = self.gravity * dt


            if self.collisions['bottom']:
                self.jumps = 2
                self.gravity = 1 

            # ceiling bonk
            if self.collisions['top']:
                self.gravity = 1 

            # apply jump
            if self.inputs['jump'] and (self.jumps > 0 or time.time() - self.lastGroundTouch <= .25):
                if self.flip:
                    for i in range(5, 10):
                        sparks.append(Spark(self.rect.midbottom, math.radians(random.randint(55, 125) - 30), random.randint(2, 3), (223, 246, 245), scale=1 * gameScale))
                else:
                    for i in range(5, 10):
                        sparks.append(Spark(self.rect.midbottom, math.radians(random.randint(55, 125) + 30), random.randint(2, 3), (223, 246, 245), scale=1 * gameScale))
                self.jumps -= 1
                self.gravity = self.jumpHeight
                self.inputs['jump'] = False
                self.movements[1] = self.gravity * dt
                self.jumpCut = False
                self.soundEffects['jump'].play()
                self.forces[0] = self.movements[0] * .2
            else:
                self.inputs['jump'] = False

            # apply jumpcut
            if self.jumpCut and self.gravity < 0:
                self.gravity /= 2

            # cap the movements
            self.movements[0] = cap(self.movements[0], self.maxSpeed + moddedSpeed)
            self.movements[1] = cap(self.movements[1], self.maxSpeed + moddedSpeed)

            # apply external forces
            self.movements[0] += self.forces[0] * dt
            self.movements[1] += self.forces[1] * dt

            # decrease external forces
            # horizontal
            if self.forces[0] > 0:
                self.forces[0] -= ((.05 * dt + .005 * abs(self.forces[0])) * dt)
                if self.forces[0] < 0:
                    self.forces[0] = 0
            elif self.forces[0] < 0:
                self.forces[0] += ((.05 * dt + .005 * abs(self.forces[0])) * dt)
                if self.forces[0] > 0:
                    self.forces[0] = 0
            # friction for horizontal
            if self.collisions['bottom'] and abs(self.forces[0]) > 0:
                if self.forces[0] > 0:
                    self.forces[0] -= (.15 * dt + abs(self.forces[0]) * .1)
                    if self.forces[0] < 0:
                        self.forces[0] = 0
                elif self.forces[0] < 0:
                    self.forces[0] += (.15 * dt + abs(self.forces[0]) * .1)
                    if self.forces[0] > 0:
                        self.forces[0] = 0
            # vertical
            if self.forces[1] > 0:
                self.forces[1] -= ((.05 * dt + .005 * abs(self.forces[1])) * dt)
                if self.forces[1] < 0:
                    self.forces[1] = 0
            elif self.forces[1] < 0:
                self.forces[1] += ((.05 * dt + .005 * abs(self.forces[1])) * dt)
                if self.forces[1] > 0:
                    self.forces[1] = 0

            # sparks while running
            if random.randint(1, 20) <= 1 * self.totalBlaze and self.state == 'run' and not self.onPlatform and self.currentGroundColors != ():
                if self.flip:
                    sparks.append(Spark(self.rect.midbottom, math.radians(random.randint(250, 360)), random.randint(2, 3), random.choice(self.currentGroundColors), scale=1 * gameScale))
                else:
                    sparks.append(Spark(self.rect.midbottom, math.radians(random.randint(180, 250)), random.randint(2, 3), random.choice(self.currentGroundColors), scale=1 * gameScale))

        # dashing
        else:
            self.movements = [((self.dashTo[0] - self.center[0]) / self.maxSpeed) * dt, 0]
            if abs(self.movements[0]) < 3:
                self.dashing = False 
            if self.flip and self.center[0] < self.dashTo[0]:
                self.rect.centerx = self.dashTo[0]
                self.dashing = False
            elif not self.flip and self.center[0] > self.dashTo[0]:
                self.rect.centerx = self.dashTo[0]
                self.dashing = False

    def update(self, display, scroll, collidables, particles, sparks, effects, dt):
        if not self.dead:
            if time.time() - self.diedTime >= self.respawnTime + .5:
                self.move(sparks, dt)

                self.updateRect(collidables)

            # iframes when first respawn
            elif time.time() - self.iTime >= self.iDuration:
                self.iTime = time.time()

                effects.append(CircleEffect(self.center, random.choice(fireColors), random.choice(fireGlowColors), 100, 5))

                for i in range(random.randint(10, 20)):
                    sparks.append(Spark(self.center, math.radians(random.randint(0, 360)), random.uniform(3, 5), (255, 255, 255)))

            self.stateMachine()

            if time.time() - self.diedTime >= self.respawnTime + .25:
                self.draw(display, scroll)

            self.generateSoundEffects()
        
            return
        
        if time.time() - self.diedTime >= self.respawnTime:
            self.respawn(particles)

    def generateBlaze(self):
        if self.totalBlaze > 0 and time.time() - self.blazeLastSpawnTime >= self.blazeSpawnDelay / 1000:
           self.blazeSpawnDelay = random.uniform(700 / self.totalBlaze, 1000 / self.totalBlaze)
           self.blazeLastSpawnTime = time.time()
           return random.randint(0, int((self.totalBlaze / 2) + 1))
        return 0

    def lightNearbyTorches(self, torches):
        # calculate the radius for this chance
        radius = self.totalBlaze ** 2
        for torch in torches:
            # this is a very rare chance
            if (self.center[0] - torch.lightHitBox.centerx) ** 2 + (self.center[1] - torch.lightHitBox.centery) ** 2 < radius and random.randint(1, 100000) < 10 + self.totalBlaze * 10:
                torch.active = True
            # these are from dashing
            elif self.dashing and self.flip and self.dashFrom[0] > torch.lightHitBox.centerx > self.center[0] and abs(torch.lightHitBox[1] - self.center[1]) <= self.rect.h * 2:
                torch.active = True
            elif self.dashing and not self.flip and self.dashFrom[0] < torch.lightHitBox.centerx < self.center[0] and abs(torch.lightHitBox[1] - self.center[1]) <= self.rect.h * 2:
                torch.active = True

    def regenerateBlaze(self):
        if self.totalBlaze < 10 and time.time() - self.lastBlazeRegeneration >= (1.75 - .025 * self.totalBlaze):
            self.totalBlaze += 1
            self.lastBlazeRegeneration = time.time()
        elif self.totalBlaze >= 10:
            self.lastBlazeRegeneration = time.time()

    def stopMoving(self):
        for inputKey in self.inputs:
            self.inputs[inputKey] = False

class Portal:
    def __init__(self, topleft, texture):
        self.center = topleft[0] + texture.get_width() / 2, topleft[1] + texture.get_height() / 2 
        self.focus = self.center[0], self.center[1] - 10
        self.active = False
        self.rendermenu = False
        self.particles = {
            0:[],
            1:[]
        }
        self.angles = {
            0:[],
            1:[]
        }
        self.interactRadius = 16 * gameScale
        self.activeRadius = 80 * gameScale

        # scale the teleporter down to 1 if the gamescale is greater than 1
        scaledTexture = pygame.Surface((texture.get_width() / gameScale, texture.get_height() / gameScale))
        scaledTexture.blit(pygame.transform.scale(texture, scaledTexture.get_size()), (0, 0))

        self.glowSpots = []

        # find the glowing spots
        for i in range(scaledTexture.get_width()):
            for j in range(scaledTexture.get_height()):
                # find the red spots
                if scaledTexture.get_at((i, j)) == (255, 0, 0, 255):
                    # record them and replace them
                    self.glowSpots.append((self.center[0] - (scaledTexture.get_width() * gameScale) / 2 + i * gameScale, self.center[1] - (scaledTexture.get_height() * gameScale) / 2 + j * gameScale))
                    scaledTexture.set_at((i, j), (38, 43, 68))

        # rescale texture and save
        self.texture = pygame.Surface((texture.get_width(), texture.get_height()))
        self.texture.blit(pygame.transform.scale(scaledTexture, self.texture.get_size()), (0, 0))
        self.texture.set_colorkey((0, 0, 0))

    def setActive(self, boolValue, sparks, particles, effects):
        if boolValue and not self.active:
            self.active = True
            # show sparks
            for i in range(random.randint(10, 15)):
                sparks.append(Spark((self.center[0], self.center[1] - 24 * gameScale),  math.radians(random.randint(0, 360)), random.uniform(1, 2) * gameScale, (255, 255, 255), scale=1 * gameScale))
            # outer particles
            for ring in self.particles:
                for i in range(20 - 10 * ring):
                    self.particles[ring].append(GlowParticle(self.center[0], self.center[1] - 36 * gameScale, [0, 0], random.choice(fireColors), random.choice(fireGlowColors), 3 * gameScale + 3 * abs(ring - 1), 0))
                    self.angles[ring].append(math.radians((360 / 10) * i))
            effects.append(CircleEffect((self.center[0], self.center[1] - 24 * gameScale), random.choice(fireColors), random.choice(fireGlowColors), 32 * gameScale, random.uniform(1, 2) * gameScale))
        elif not boolValue and self.active:
            self.active = False
            for ring in self.particles:
                for i, particle in enumerate(self.particles[ring]):
                    particle.decayRate = random.uniform(.1, .2) * gameScale
                    particle.motion = 2 * math.cos(self.angles[ring][i] + math.pi * .65) * gameScale, 2 * math.sin(self.angles[ring][i] + math.pi * .65) * gameScale
                    particles.append(particle)
            self.particles = {
                0:[],
                1:[]
            }
            self.angles = {
                0:[],
                1:[]
            }

    def draw(self, cameraRect, display, scroll, particles, dt):
        # update each particle if active
        if self.active:
            for ring in self.particles:
                for i, particle in enumerate(self.particles[ring]):
                    # move the particles
                    if ring == 0:
                        self.angles[ring][i] += .5 * dt
                        particle.x = self.center[0] + (3 * abs(math.sin(time.time())) * gameScale + 9 * gameScale) * gameScale * math.cos(self.angles[ring][i])
                        particle.y = self.center[1] - 24 * gameScale + (3 * abs(math.sin(time.time())) * gameScale + 9 * gameScale) * math.sin(self.angles[ring][i]) * gameScale
                    elif ring == 1:
                        self.angles[ring][i] -= .5 * dt
                        particle.x = self.center[0] + (3 * abs(math.sin(time.time())) * gameScale + 3 * gameScale) * gameScale * math.cos(self.angles[ring][i])
                        particle.y = self.center[1] - 24 * gameScale + (3 * abs(math.sin(time.time())) * gameScale + 3 * gameScale) * math.sin(self.angles[ring][i]) * gameScale
                    # draw the particles
                    scaledSurface = pygame.Surface((particle.radius, particle.radius))
                    scaledSurface.set_colorkey((0, 0, 0))
                    pygame.draw.circle(scaledSurface, particle.particleColor, (particle.radius / 2, particle.radius / 2), particle.radius / 2)
                    display.blit(pygame.transform.scale(scaledSurface, (scaledSurface.get_width() * gameScale, scaledSurface.get_height() * gameScale)), (particle.x - scroll[0] - scaledSurface.get_width() * gameScale // 2, particle.y - scroll[1] - scaledSurface.get_height() * gameScale // 2))
                    # glow surface
                    display.blit(pygame.transform.scale(particle.glowSurface, (particle.glowSurface.get_width() * gameScale, particle.glowSurface.get_height() * gameScale)), (particle.x - particle.glowSurface.get_width() - scroll[0], particle.y - particle.glowSurface.get_height() - scroll[1]), special_flags=pygame.BLEND_RGB_ADD)
                    # chance to add a random particle
                    if random.randint(1, 200) == 1:
                        particles.append(GlowParticle(particle.x, particle.y, (-3 * math.cos(self.angles[ring][i] + math.pi / 2), -3 * math.sin(self.angles[ring][i] + math.pi / 2)), random.choice(fireColors), random.choice(fireGlowColors), particle.radius, random.uniform(.1, .15) * gameScale))

            # draw a fire colored pixel over the glow spots
            for glowSpot in self.glowSpots:
                # possibly add a particle here
                if random.randint(1, 100) == 1:
                    particles.append(GlowParticle(glowSpot[0], glowSpot[1], (0, -random.uniform(0, 1) * gameScale), random.choice(fireColors), random.choice(fireGlowColors), random.uniform(2, 4) * gameScale, random.uniform(.05, .075) * gameScale))

        # blit the texture
        display.blit(self.texture, (self.center[0] - self.texture.get_width() / 2 - scroll[0], self.center[1] - self.texture.get_height() / 2 - scroll[1]))

class EventBoard:

    def __init__(self, topleftx, toplefty, texture):
        self.renderpos = topleftx, toplefty
        self.texture = texture
        self.interactRadius = 16 * gameScale
        self.renderboard = False

    @ property
    def center(self):
        return self.renderpos[0] + self.texture.get_width() / 2, self.renderpos[1] + self.texture.get_height() / 2

    def draw(self, display, scroll):

        display.blit(self.texture, (self.renderpos[0] - scroll[0], self.renderpos[1] - scroll[1]))

class Golem:
    def __init__(self):
        pass

class Wisp:
    def __init__(self):
        pass