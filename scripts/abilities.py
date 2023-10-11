import pygame
import math

from scripts.projectiles import *

def findAngle(dy, dx):
    return math.atan2(dy, dx)

class FireBolt:
    def __init__(self, icon):
        self.cooldown = 1 # seconds
        self.lastUse = 0
        self.knockback = [0, 0]
        self.cost = 1
        self.icon = icon.copy()

    def use(self, origin, mouseposition, projectiles):
        #projectiles.append(Bolt(origin[0], origin[1], (7 * math.cos(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0]))), 7 * math.sin(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0]))))))
        projectiles.append(Flash(origin[0], origin[1], (10 * math.cos(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0]))), 10 * math.sin(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0]))))))
        self.lastUse = time.time()
        self.knockback[0] *= -math.cos(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0])))
        self.knockback[1] *= -math.sin(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0])))

    def resetKnockback(self):
        self.knockback = [0, 0]

class FireBoost:
    def __init__(self, icon):
        self.cooldown = 3
        self.lastUse = 0
        self.knockback = [-12, -12]
        self.cost = 3
        self.icon = icon.copy()

    def use(self, origin, mouseposition, projectiles):
        for i in range(5):
            projectiles.append(ExplodingOrb(list(origin), findAngle(origin[1] - mouseposition[1], origin[0] - mouseposition[0]) + math.radians(random.randint(-30, 30)), random.randint(2, 4) * gameScale, random.randint(3, 5) * gameScale, random.randint(16, 32) * gameScale))
        
        angle = findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0]))
        self.knockback[0] *= -math.cos(angle)
        self.knockback[1] *= -math.sin(angle)
        self.lastUse = time.time()

    def resetKnockback(self):
        self.knockback = [-12, -12]

class FireDash:
    def __init__(self, icon):
        self.cooldown = 2
        self.lastUse = 0
        self.duration = 10
        self.cost = 2
        self.icon = icon.copy()
        
    def use(self, player):
        player.dash()
        self.lastUse = time.time()

class Fireball:
    def __init__(self, icon):
        self.cooldown = 5
        self.lastUse = 0
        self.knockback = [14, 14]
        self.cost = 7
        self.icon = icon.copy()
        
    def use(self, origin, mouseposition, projectiles):
        projectiles.append(Ball(origin[0], origin[1], (4 * math.cos(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0]))), 4 * math.sin(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0]))))))
        self.lastUse = time.time()
        self.knockback[0] *= -math.cos(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0])))
        self.knockback[1] *= -math.sin(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0])))

    def resetKnockback(self):
        self.knockback = [8, 8]

class FireWheel:
    def __init__(self, icon):
        self.cooldown = 16
        self.lastUse = 0
        self.cost = 8
        self.icon = icon.copy()

    def use(self, projectiles, playerCenter, tileSize):
        projectiles.append(Wheel(playerCenter, tileSize))
        self.lastUse = time.time()

class FireShotgun:
    def __init__(self, icon):
        self.cooldown = 7
        self.lastUse = 0
        self.knockback = [10, 10]
        self.cost = 6
        self.icon = icon.copy()

    def use(self, origin, mouseposition, projectiles):
        for i in range(20):
            projectiles.append(ExplodingOrb(list(origin), findAngle(mouseposition[1] - origin[1], mouseposition[0] - origin[0]) + math.radians(random.randint(-60, 60)), random.randint(2, 4) * gameScale, random.randint(7, 10) * gameScale, random.randint(48, 64) * gameScale))
        self.knockback[0] *= -math.cos(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0])))
        self.knockback[1] *= -math.sin(findAngle((mouseposition[1] - origin[1]), (mouseposition[0] - origin[0])))
        self.lastUse = time.time()

    def resetKnockback(self):
        self.knockback = [10, 10]