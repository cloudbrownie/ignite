import pygame
import math
import random
import time
import json

gameScale = 1
try:
    with open('data/config.json') as readFile:
        gameScale = json.load(readFile)['scale']
except Exception as e:
    print(f'[+] {e}')

greenColors = (60, 89, 86), (57, 123, 58), (113, 170, 52), (182, 213, 60)
stoneColors = (38, 43, 68), (24, 20, 37), (58, 68, 102)
fireColors = (244, 180, 27), (244, 126, 27), (230, 72, 46)
fireGlowColors = (24, 12, 2), (24, 18, 2), (23, 7, 4)

from scripts.particles import GlowParticle
from scripts.entities import *
from scripts.effects import CircleEffect, Spark

class Bolt:
    def __init__(self, x, y, motion):
        # hit box for the bolt
        self.rect = pygame.Rect(x, y, 2 * gameScale, 2 * gameScale)
        self.origin = x, y

        self.motion = motion

        # keep track for spawning particles
        self.lastParticleSpawn = time.time()
        self.dead = False

    def update(self, cameraRect, dt, particles, torches):
        if not self.dead:
            if self.rect.colliderect(cameraRect) and time.time() - self.lastParticleSpawn >= .005:
                for i in range(1, 2):
                    particles.append(GlowParticle(self.rect.centerx, self.rect.centery, (0, 0), random.choice([(246, 126, 27), (244, 180, 27), (230, 72, 46)]), random.choice([(24, 12, 2), (24, 18, 2), (23, 7, 4)]), 7, random.uniform(.1, .5)))
                self.lastParticleSpawn = time.time()
            if (self.rect.centerx - self.origin[0]) ** 2 + (self.rect.centery - self.origin[1]) ** 2 > (32 * gameScale) ** 2:
                self.dead = True
            self.rect.centerx += self.motion[0] * dt
            self.rect.centery += self.motion[1] * dt
            for torch in torches:
                if torch.lightHitBox.colliderect(self.rect) and random.randint(1, 2) == 1:
                    torch.active = True

class Ball:
    def __init__(self, x, y, motion):
        self.rect = pygame.Rect(x, y, 6 * gameScale, 6 * gameScale)
        self.torchHitbox = pygame.Rect(x - self.rect.w, y - self.rect.h, self.rect.w * 2.75, self.rect.h * 2.75)
        self.motion = motion
        self.origin = x, y

        self.lastParticleSpawn = time.time()
        self.dead = False

    def update(self, cameraRect, dt, particles, collidables, effects, sparks):
        if not self.dead:
            if  time.time() - self.lastParticleSpawn >= .01:
                self.lastParticleSpawn = time.time()
                for i in range(1, 3):
                    particles.append(GlowParticle(random.randint(self.rect.left, self.rect.right), random.randint(self.rect.top, self.rect.bottom), (0, 0), random.choice([(246, 126, 27), (244, 180, 27), (230, 72, 46)]), random.choice([(24, 12, 2), (24, 18, 2), (23, 7, 4)]), random.randint(self.rect.w, self.torchHitbox.w), random.uniform(.5, .75)))
            for collidable in collidables:
                if isinstance(collidable, Torch) and self.torchHitbox.colliderect(collidable.lightHitBox):
                    collidable.active = True
                elif not isinstance(collidable, Torch) and self.rect.colliderect(collidable[0]) and collidable[1] == 'tiles':
                    self.dead = True
            self.rect.centerx += self.motion[0] * dt
            self.rect.centery += self.motion[1] * dt
            self.torchHitbox.center = self.rect.center
            # check if traveled way too far
            if (self.origin[0] - self.rect.centerx) ** 2 + (self.origin[1] - self.rect.centery) ** 2 >= (16 * 8 * 100) ** 2:
                self.dead = True
        if self.dead:
            # explodes on death, creates a big rect to light torches
            self.torchHitbox.w *= 3.5
            self.torchHitbox.h *= 3.5
            self.torchHitbox.center = self.rect.center
            for collidable in collidables:
                if isinstance(collidable, Torch) and self.torchHitbox.colliderect(collidable.lightHitBox):
                    collidable.active = True
            for i in range(random.randint(20, 25)):
                particles.append(GlowParticle(self.rect.centerx, self.rect.centery, (random.uniform(-3, 3), random.uniform(-3, 3)), random.choice([(246, 126, 27), (244, 180, 27), (230, 72, 46)]), random.choice([(24, 12, 2), (24, 18, 2), (23, 7, 4)]), random.uniform(7, 10) * gameScale, random.uniform(.15, .25) * gameScale))
            effects.append(CircleEffect(self.rect.center, random.choice(fireColors), random.choice(fireGlowColors), math.sqrt(2 * ((self.torchHitbox.w / 2) ** 2)), 1 * gameScale))
            for i in range(random.randint(50, 75)):
                sparks.append(Spark(self.rect.center, math.radians(random.randint(0, 360)), random.uniform(1, 2.75) * gameScale, (255, 255, 255), scale=.75 * gameScale))

class Flash:
    def __init__(self, x, y, motion):
        self.glowRadius = 15
        self.center = [x, y]
        self.motion = motion
        self.aliveValue = 10
        self.decayRate = .5

        self.lastParticleSpawn = time.time()
        self.dead = False

    def update(self, dt, particles, torches):
        if not self.dead:
            # create visual effect
            if  time.time() - self.lastParticleSpawn >= .01:
                self.lastParticleSpawn = time.time()
                for i in range(1, 3):
                    particles.append(GlowParticle(self.center[0], self.center[1], (0, 0), random.choice(fireColors), random.choice(fireGlowColors), self.glowRadius, 1))
                # create glow particles that kinda fling around
                if random.randint(0, 5) == 0:
                    angle = math.radians(random.randint(0, 360))
                    particles.append(GlowParticle(self.center[0], self.center[1], (2 * math.cos(angle), 2 * math.sin(angle)), random.choice(fireColors), random.choice(fireGlowColors), self.glowRadius * random.uniform(.5, .75), .1))
            # check for collisions for torches
            for torch in torches:
                if (torch.lightHitBox.centerx - self.center[0]) ** 2 + (torch.lightHitBox.centery - self.center[1]) ** 2 <= (self.glowRadius * 2) ** 2:
                    torch.active = True
            # move the flash
            self.center[0] += self.motion[0] * dt
            self.center[1] += self.motion[1] * dt
            # reduce the size
            self.aliveValue -= self.decayRate * dt

            # check if dead
            if self.aliveValue <= 0:
                self.dead = True
                

class Wheel:
    def __init__(self, playerCenter, tileSize):
        self.duration = 8
        self.born = time.time()
        self.radius = 3 * tileSize
        self.orbs = []
        self.dead = False
        self.angles = []
        orbs = 5
        self.particleAngles = []
        self.particles = []
        # create orbs
        for i in range(orbs):
            # bigger background orbs
            self.orbs.append(GlowParticle(0, 0, [0, 0], (255, 255, 255), random.choice(fireGlowColors), 17, 0))
            self.orbs[i].lastSpawn = 0
            angle = (360 / orbs) * i
            self.angles.append(angle)
            self.particleAngles.append([])
            self.particles.append([])
            for j in range(5):
                self.particleAngles[i].append(angle - (5 * (j + 1)))
                self.particles[i].append(GlowParticle(0, 0, [0, 0], random.choice(fireColors), random.choice(fireGlowColors), (17 - 2 * (j + 1)), 0))

    def update(self, playerCenter, display, scroll, dt, particles, torches, sparks, effects):
        if time.time() - self.born < self.duration:
            for torch in torches:
                if (torch.lightHitBox.centerx - playerCenter[0]) ** 2 + (torch.lightHitBox.centery - playerCenter[1]) ** 2 <= (self.radius * (.5 * abs(math.sin(time.time() - self.born)) + .5) + self.orbs[0].radius) ** 2:
                    torch.active = True
            for i, orb in enumerate(self.orbs):
                self.angles[i] += 8 * dt
                orb.x = playerCenter[0] + self.radius * math.cos(math.radians(self.angles[i])) * (.5 * abs(math.sin(time.time() - self.born)) + .5)
                orb.y = playerCenter[1] + self.radius * math.sin(math.radians(self.angles[i])) * (.5 * abs(math.sin(time.time() - self.born)) + .5)
                # spawn past images
                if time.time() - orb.lastSpawn >= .001:
                    for i in range(random.randint(1, 2)):
                        particles.append(GlowParticle(orb.x + random.randint(-5, 5) * gameScale, orb.y + random.randint(-5, 5) * gameScale, [0, 0], random.choice(fireColors), random.choice(fireGlowColors), orb.radius * .75, .3 * gameScale))
                    orb.lastSpawn = time.time()
                # draw the particle
                scaledSurface = pygame.Surface((orb.radius, orb.radius))
                scaledSurface.set_colorkey((0, 0, 0))
                pygame.draw.circle(scaledSurface, orb.particleColor, (orb.radius / 2, orb.radius / 2), orb.radius / 2) 
                display.blit(pygame.transform.scale(scaledSurface, (scaledSurface.get_width() * gameScale, scaledSurface.get_height() * gameScale)), (orb.x - scroll[0] - scaledSurface.get_width() * gameScale // 2, orb.y - scroll[1] - scaledSurface.get_height() * gameScale // 2))
                # draw the glowing surface
                display.blit(pygame.transform.scale(orb.glowSurface, (orb.glowSurface.get_width() * gameScale, orb.glowSurface.get_height() * gameScale)), (orb.x - orb.glowSurface.get_width() - scroll[0], orb.y - orb.glowSurface.get_height() - scroll[1]), special_flags=pygame.BLEND_RGB_ADD)
        else:
            self.dead = True
            # explode the obrs
            for orb in self.orbs:
                for i in range(random.randint(20, 25)):
                    sparks.append(Spark((orb.x, orb.y), math.radians(random.randint(0, 360)), random.uniform(1, 2.75) * gameScale, (255, 255, 255), scale=1 * gameScale))
            effects.append(CircleEffect(playerCenter, random.choice(fireColors), random.choice(fireGlowColors), self.radius * (.5 * abs(math.sin(time.time() - self.born)) + .5) * 1.5, 3 * gameScale))

class ExplodingOrb:
    def __init__(self, center, angle, speed, radius, distance):
        self.center = center
        self.origin = center.copy()
        self.motion = (speed * math.cos(angle), speed * math.sin(angle))
        self.radius = radius
        self.distance = distance ** 2
        self.dead = False
        self.born = time.time()
        self.lastSpawn = time.time()

    def update(self, torches, dt, particles, effects, sparks):
        if (self.center[0] - self.origin[0]) ** 2 + (self.center[1] - self.origin[1]) ** 2 <= self.distance:
            for torch in torches:
                if (torch.lightHitBox.center[0] - self.center[0]) ** 2 + (torch.lightHitBox.center[1] - self.center[1]) ** 2 <= self.radius ** 2:
                    torch.active = True
            # create glowing orbs
            particles.append(GlowParticle(self.center[0], self.center[1], [0, 0], random.choice(fireColors), random.choice(fireGlowColors), self.radius, random.uniform(1, 2) * gameScale))
            # move orb
            self.center[0] += self.motion[0] * dt
            self.center[1] += self.motion[1] * dt
        elif time.time() - self.born <= 1:
            # wait and expand
            radius = self.radius
            radius *= 1 + .5 * (time.time() - self.born)
            # particles are this big
            if time.time() - self.lastSpawn >= .15:
                self.lastSpawn = time.time()
                particles.append(GlowParticle(self.center[0], self.center[1], [0, 0], random.choice(fireColors), random.choice(fireGlowColors), radius, random.uniform(.5, 1) * gameScale))
        else:
            # sparks
            for i in range(random.randint(5, 8)):
                sparks.append(Spark(self.center, math.radians(random.randint(0, 360)), random.uniform(1, 2.75) * gameScale, (255, 255, 255), scale=.75 * gameScale))
            # explosion effect
            effects.append(CircleEffect(self.center, random.choice(fireColors), random.choice(fireGlowColors), self.radius * 2.5, 2 * gameScale))
            # particles
            for i in range(random.randint(2, 5)):
                particles.append(GlowParticle(self.center[0], self.center[1], (random.uniform(-3, 3), random.uniform(-3, 3)), random.choice([(246, 126, 27), (244, 180, 27), (230, 72, 46)]), random.choice([(24, 12, 2), (24, 18, 2), (23, 7, 4)]), random.uniform(7, 10) * gameScale, random.uniform(.15, .25) * gameScale))
            # circle effect is pretty big
            for torch in torches:
                if (torch.lightHitBox.center[0] - self.center[0]) ** 2 + (torch.lightHitBox.center[1] - self.center[1]) ** 2 <= (self.radius * 2.5) ** 2:
                    torch.active = True
            self.dead = True