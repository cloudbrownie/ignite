import pygame
import math

class CircleEffect:
    def __init__(self, center, color, glowColor, radius, rate):
        self.center = center
        self.color = color
        self.glowColor = glowColor
        self.radius = radius
        self.width = radius
        self.rate = rate
        self.dead = False

    def update(self, display, scroll, dt):
        # increase the radius
        self.radius += self.rate * dt
        self.width -= self.rate * 1.5 * dt
        if self.width < 0:
            self.dead = True
        else:
            # draw to a surface
            circleSurface = pygame.Surface((self.radius, self.radius))
            pygame.draw.circle(circleSurface, self.color, (circleSurface.get_width() / 2, circleSurface.get_height() / 2), int(self.radius / 2), int(self.width))
            circleSurface.set_colorkey((0, 0, 0))
            # draw to display
            display.blit(circleSurface, (self.center[0] - circleSurface.get_width() / 2 - scroll[0], self.center[1] - circleSurface.get_height() / 2 - scroll[1]))

            # glow surface
            glowOuterRadius = self.radius * 1.5
            glowCircleSurface = pygame.Surface((glowOuterRadius, glowOuterRadius))
            pygame.draw.circle(glowCircleSurface, self.glowColor, (glowCircleSurface.get_width() / 2, glowCircleSurface.get_height() / 2), int(glowOuterRadius / 2), int(self.width * 1.5))
            glowCircleSurface.set_colorkey((0, 0, 0))
            # draw to display
            display.blit(glowCircleSurface, (self.center[0] - glowCircleSurface.get_width() / 2 - scroll[0], self.center[1] - glowCircleSurface.get_height() / 2 - scroll[1]), special_flags=pygame.BLEND_RGB_ADD)

class Spark:
    def __init__(self, center, angle, speed, color, scale=1, glowColor=(0, 0, 0)):
        self.center = list(center)
        self.angle = angle
        self.speed = speed
        self.size = speed
        self.color = color
        self.scale = scale
        self.dead = False
        self.glowColor = glowColor
    
    def point_towards(self, angle, rate):
        rotate_direction = ((angle - self.angle + math.pi * 3) % (math.pi * 2)) - math.pi
        try:
            rotate_sign = abs(rotate_direction) / rotate_direction
        except ZeroDivisionError:
            rotate_sing = 1
        if abs(rotate_direction) < rate:
            self.angle = angle
        else:
            self.angle += rate * rotate_sign

    def calculate_movement(self, dt):
        return [math.cos(self.angle) * self.speed * dt, math.sin(self.angle) * self.speed * dt]

    def move(self, dt, rotate=False, decay=True):
        movement = self.calculate_movement(dt)
        self.center[0] += movement[0]
        self.center[1] += movement[1]

        # a bunch of options to mess around with relating to angles...
        #self.point_towards(math.pi / 2, .1)
        #self.velocity_adjust(0.975, 0.2, 8, dt)

        if rotate:
            self.angle += 1 * dt

        if decay:
            self.speed -= .1 * dt

        if self.speed <= 0:
            self.dead = True

    def draw(self, display, scroll):
        if not self.dead:
            points = [
                [self.center[0] + math.cos(self.angle) * self.speed * self.scale - scroll[0], 
                    self.center[1] + math.sin(self.angle) * self.speed * self.scale - scroll[1]],
                [self.center[0] + math.cos(self.angle + math.pi / 2) * self.speed * self.scale * 0.3 - scroll[0], 
                    self.center[1] + math.sin(self.angle + math.pi / 2) * self.speed * self.scale * 0.3 - scroll[1]],
                [self.center[0] - math.cos(self.angle) * self.speed * self.scale * 3.5 - scroll[0], 
                    self.center[1] - math.sin(self.angle) * self.speed * self.scale * 3.5 - scroll[1]],
                [self.center[0] + math.cos(self.angle - math.pi / 2) * self.speed * self.scale * 0.3 - scroll[0], 
                    self.center[1] - math.sin(self.angle + math.pi / 2) * self.speed * self.scale * 0.3 - scroll[1]],
                ]
            pygame.draw.polygon(display, self.color, points)