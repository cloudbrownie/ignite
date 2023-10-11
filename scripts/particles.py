import pygame
import time
import math
import random
import json

gameScale = 1
try:
    with open('data/config.json') as readFile:
        gameScale = json.load(readFile)['scale']
except Exception as e:
    print(f'[+] {e}')

class GlowParticle:
    def __init__(self, x, y, motion, particleColor, glowColor, radius, decayRate, angle=0, revolvingRadius=0):
        self.x = x
        self.y = y
        self.particleColor = particleColor
        self.glowColor = glowColor
        self.radius = radius
        self.decayRate = decayRate
        self.motion = motion
        self.dead = False
        self.sinFrequencyConstant = random.randint(4, 10)
        self.angle = angle
        self.revolvingRadius = revolvingRadius
        if self.revolvingRadius != 0:
            self.origin = self.x, self.y

    @property
    def glowSurface(self):
        radius = int(abs(self.radius * 2 + 5 * abs(math.sin(self.sinFrequencyConstant * time.time()))))
        glowSurface = pygame.Surface((radius, radius))
        pygame.draw.circle(glowSurface, self.glowColor, (radius / 2, radius / 2), radius / 2)
        glowSurface.set_colorkey((0, 0, 0))
        return glowSurface

    def update(self, dt):
        # check if dead
        if not self.dead:
            # make the thing move based on an angle
            if self.revolvingRadius != 0:
                self.x = self.origin[0] + self.revolvingRadius * math.cos(self.angle)
                self.y = self.origin[1] + self.revolvingRadius * math.sin(self.angle)
                
            # move the particle normally
            else:
                self.x += self.motion[0] * dt
                self.y += self.motion[1] * dt

            # update the radius of the particle
            self.radius -= self.decayRate * dt
            if self.radius < 1:
                self.dead = True

class LeafParticle:
    def __init__(self, x, y, color, radius):
        self.x = x
        self.y = y
        self.color = color
        self.radius = radius
        self.dead = False
        self.sinFreqMultiplier = random.uniform(.5, 2.5)
        self.aliveTime = random.uniform(.5, 2)
        self.birthed = time.time()

    def update(self, display, scroll, cameraRect, dt, wind):
        # check if dead
        if not self.dead:
            # move the particle based on a sin wave
            self.x += .3 * math.sin(self.sinFreqMultiplier * time.time()) * dt + (wind * 10)
            self.y += 1 * dt

            # check if the leaf is in the frame
            if cameraRect.collidepoint((self.x, self.y)):
                # draw the particle
                pygame.draw.circle(display, self.color, (self.x - scroll[0], self.y - scroll[1]), self.radius)
        
            # kill leaf
            if time.time() - self.birthed >= self.aliveTime:
                self.dead = True