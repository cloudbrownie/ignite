import pygame
import ctypes
import os
import sys
import json
import time
import math
import random
import cProfile
import pstats

gameScale = 1
try:
    with open('data/config.json') as readFile:
        data = json.load(readFile)
        gameScale = data['scale']
except Exception as e:
    print(f'[+] {e}')

from scripts.textures import TextureManager
from scripts.entities import *
from scripts.particles import *
from scripts.chunks import ChunkManager
from scripts.font import Font
from scripts.projectiles import *
from scripts.abilities import *
from scripts.displayObjs import MainGui

def renderText(display, text, loc, scale, background, foreground):
    background.render(display, text, (loc[0], loc[1] + 2), scale)
    background.render(display, text, (loc[0] + 2, loc[1]), scale)
    background.render(display, text, (loc[0] + 2, loc[1] + 2), scale)
    foreground.render(display, text, loc, scale)

def loadSounds(directory):
    soundFiles = [file for file in os.listdir(f'data/sounds/{directory}/') if file.endswith('.wav')]
    return [pygame.mixer.Sound(f'data/sounds/{directory}/{soundFile}') for soundFile in soundFiles]

def main():
    # initialize display and screen ------------------------------------------------
    user32 = ctypes.windll.user32
    clock = pygame.time.Clock()
    pygame.init()
    pygame.display.set_caption('Ignite')
    screen = pygame.display.set_mode((user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)), pygame.FULLSCREEN + pygame.HWSURFACE + pygame.DOUBLEBUF + pygame.SCALED)
    display = pygame.Surface((960, 540))

    pygame.mouse.set_visible(False)

    xRatio = display.get_width() / screen.get_width()
    yRatio = display.get_height() / screen.get_height()

    # initiate the font class
    whiteFont = Font()
    whiteFont.recolor((223, 246, 245))
    blueFont = Font()
    blueFont.recolor((38, 43, 68))

    # laod all map information in a dictionary
    levels = {}
    levelFiles = [file for file in os.listdir('data/levels/') if file.endswith('.json')]
    for levelFile in levelFiles:
        with open(f'data/levels/{levelFile}') as readFile:
            levels[os.path.splitext(levelFile)[0]] = json.load(readFile)

    # load all spritesheets
    sheets = {}
    sheetFiles = [file for file in os.listdir('data/spritesheets/') if file.endswith('.png')]
    for sheetFile in sheetFiles:
        sheets[os.path.splitext(sheetFile)[0]] = pygame.image.load(f'data/spritesheets/{sheetFile}').convert()
    textures = TextureManager(sheets, gameScale)

    # fix the cursor texture
    for i in range(textures.sheets['cursor'][0][0].get_width()):
        for j in range(textures.sheets['cursor'][0][0].get_height()):
            if textures.sheets['cursor'][0][0].get_at((i, j)) == (255, 0, 0, 255):
                textures.sheets['cursor'][0][0].set_at((i, j), (0, 0, 0))


    # load backgrounds
    mountainBackground = pygame.image.load('data/spritesheets/mountain.png').convert()
    mountainBackground.set_colorkey((0, 0, 0))

    pygame.display.set_icon(textures.sheets['player'][0][0])

    currentLevel = 'village'
    levelSwitchTo = 'village'
    levelStarts = {
        'village':(350 * gameScale, -300 * gameScale),
        'level':(32, -44)
        }
    mapTransition = True
    mapTransitionStartTime = time.time()
    loadedNewLevel = False
    loadedNewLevelStartTime = 0
    levelTimer = 0
    exactLevelEndTime = 0
    loadedLevel = False

    # load the chunks of the current level
    chunks = ChunkManager(display.get_width(), display.get_height(), gameScale)
    chunks.load(currentLevel, textures.sheets)

    chunks.fakeLoad(currentLevel)
    # get the boundaries
    boundaries = chunks.getBounds()

    dt = 1
    prevTime = time.time() - .001
    startTime = time.time()

    cameraRect = pygame.Rect(0, 0, display.get_width(), display.get_height())

    particles = []
    leaves = []
    projectiles = []
    sparks = []
    effects = []
    activeTorches = len([torch for torch in chunks.torches if torch.active])
    displayBlazeParticles = []
    lastDisplayBlazeParticleBorn = time.time()
    displayTorchArrows = True

    scroll = [0, 0]
    scrollSpeed = 8
    scrollFocus = [0, 0]
    endPortalFocus = False
    endPortalFocusSetTime = 0
    respawnPlayerAtPortal = False
    timerText = '00:00:00:000'

    windMultiplier = 10

    # load all grass sound effects for the player
    grassSoundEffects = loadSounds('grass')

    # load jump sound effect
    jumpSound = pygame.mixer.Sound('data/sounds/jump.wav')
    jumpSound.set_volume(.65)

    for effect in grassSoundEffects:
        effect.set_volume(.5)

    playerSoundEffects = {
        'grass':grassSoundEffects,
        'jump':jumpSound
    }

    player = Player(levelStarts[currentLevel][0], levelStarts[currentLevel][1], textures.sheets['player'], playerSoundEffects, gameScale)
    resetPlayerPosition = False

    # load the abilites currently used by the player
    abilities = {
        'bolt':FireBolt(textures.sheets['icons'][0][0]),
        'dash':FireDash(textures.sheets['icons'][0][1]),
        'fireball':Fireball(textures.sheets['icons'][0][2]),
        'boost':FireBoost(textures.sheets['icons'][0][3]),
        'shotgun':FireShotgun(textures.sheets['icons'][0][4]),
        'wheel':FireWheel(textures.sheets['icons'][0][5])
    }
    abilityKeys = list(abilities.keys())

    currentAbilities = {
        pygame.K_1:'bolt',
        pygame.K_2:'dash',
        pygame.K_3:'boost'
    }

    # render costs onto the icons
    for ability in abilities:
        # scale down and render the text
        scaledSurface = pygame.Surface((abilities[ability].icon.get_width() / gameScale, abilities[ability].icon.get_height() / gameScale))
        scaledSurface.blit(pygame.transform.scale(abilities[ability].icon, scaledSurface.get_size()), (0, 0))
        scaledSurface.set_colorkey((0, 0, 0))
        blueFont.render(scaledSurface, str(abilities[ability].cost), (3, 4))
        blueFont.render(scaledSurface, str(abilities[ability].cost), (4, 4))
        blueFont.render(scaledSurface, str(abilities[ability].cost), (4, 3))
        whiteFont.render(scaledSurface, str(abilities[ability].cost), (3, 3))
        # scale back up
        abilities[ability].icon.blit(pygame.transform.scale(scaledSurface, abilities[ability].icon.get_size()), (0, 0))

    for i, icon in enumerate(textures.sheets['icons'][0]):
        # scale down
        scaledSurface = pygame.Surface((icon.get_width() / gameScale, icon.get_height() / gameScale))
        scaledSurface.blit(pygame.transform.scale(icon, scaledSurface.get_size()), (0, 0))
        scaledSurface.set_colorkey((0, 0, 0))
        whiteFont.render(scaledSurface, str(abilities[abilityKeys[i]].cost), (3, 3))
        # scale back up
        textures.sheets['icons'][0][i].blit(pygame.transform.scale(scaledSurface, icon.get_size()), (0, 0))

    guiDisplay = MainGui(5 * gameScale, display, textures.sheets['gui'][0], textures.sheets['icons'][0], abilities, blueFont, whiteFont, gameScale, chunks.fakeLoad('level')['torches'])

    # make the diamond display for the blaze value
    blazeDisplayDiamond = pygame.Surface((60, 60))
    diamondCornerPoints = [
        (blazeDisplayDiamond.get_width() / 2, 0),
        (blazeDisplayDiamond.get_width(), blazeDisplayDiamond.get_height() / 2),
        (blazeDisplayDiamond.get_width() / 2, blazeDisplayDiamond.get_height()),
        (0, blazeDisplayDiamond.get_height() / 2)
    ]
    blazeDisplayDiamond.set_colorkey((0, 0, 0))
    pygame.draw.circle(blazeDisplayDiamond, (106, 73, 64), (blazeDisplayDiamond.get_width() / 2, blazeDisplayDiamond.get_height() / 2), blazeDisplayDiamond.get_width() / 2)
    pygame.draw.circle(blazeDisplayDiamond, (192, 192, 192), (blazeDisplayDiamond.get_width() / 2, blazeDisplayDiamond.get_height() / 2), blazeDisplayDiamond.get_width() / 2, 2)

    # game play loop ---------------------------------------------------------------
    running = True
    while running:

        # dt
        dt = (time.time() - prevTime) * 60
        prevTime = time.time()
        fps = 1 / (dt / 60)

        gameTime = time.time() - startTime

        if endPortalFocus:
            scrollFocus = chunks.portal.focus
            if time.time() - endPortalFocusSetTime > 3:
                endPortalFocus = False
        elif player.respawnTime / 2 < time.time() - player.diedTime <= player.respawnTime + .5:
            scrollFocus = player.respawnLocation
        else:
            scrollFocus = player.center

        # scroll value
        scroll[0] += int((scrollFocus[0] - display.get_width() / 2 - scroll[0]) / scrollSpeed)
        scroll[1] += int((scrollFocus[1] - display.get_height() / 2 - scroll[1]) / scrollSpeed)

        scrollOffset = player.center[0] - display.get_width() / 2 - scroll[0], player.center[1] - display.get_height() / 2 - scroll[1]

        # move the camera rect
        cameraRect.x = scroll[0]
        cameraRect.y = scroll[1]

        # background ---------------------------------------------------------------
        screen.fill((0, 0, 0))
        display.fill((56, 180, 224))
        display.blit(pygame.transform.scale(mountainBackground, display.get_size()), (0, -25 * gameScale - scroll[1] / 10))
        pygame.draw.rect(display, (125, 112, 113), (0, mountainBackground.get_height() - 25 * gameScale - scroll[1] / 10, display.get_width(), display.get_height()))

        wind = .5 * ((windMultiplier + 400) / 400 * math.cos(.01 * time.time())) * ((windMultiplier + 400) / 400 * math.sin(.01 * time.time()))

        # leaves
        for i, leaf in enumerate(leaves):
            leaf.update(display, scroll, cameraRect, dt, wind)
            if leaf.dead:
                leaves.pop(i)

        chunks.displayChunks(player, textures.sheets, display, cameraRect, particles, leaves, wind, windMultiplier, sparks, effects, dt, scroll=scroll)

        # glowing particles
        for i, particle in enumerate(particles):
            particle.update(dt)
            # because overhead is stupidly high, draw locally
            # check if the particle is in frame
            if cameraRect.collidepoint((particle.x, particle.y)) and not particle.dead:
                if particle.radius >= 1:
                    # draw the particle
                    scaledSurface = pygame.Surface((particle.radius, particle.radius))
                    scaledSurface.set_colorkey((0, 0, 0))
                    pygame.draw.circle(scaledSurface, particle.particleColor, (particle.radius / 2, particle.radius / 2), particle.radius / 2)
                    display.blit(pygame.transform.scale(scaledSurface, (scaledSurface.get_width() * gameScale, scaledSurface.get_height() * gameScale)), (particle.x - scroll[0] - scaledSurface.get_width() * gameScale // 2, particle.y - scroll[1] - scaledSurface.get_height() * gameScale // 2))
                # draw the glowing surface
                display.blit(pygame.transform.scale(particle.glowSurface, (particle.glowSurface.get_width() * gameScale, particle.glowSurface.get_height() * gameScale)), (particle.x - particle.glowSurface.get_width() - scroll[0], particle.y - particle.glowSurface.get_height() - scroll[1]), special_flags=pygame.BLEND_RGB_ADD)

            if particle.dead:
                particles.pop(i)

        # display particles
        for i, particle in enumerate(displayBlazeParticles):
            particle.update(dt)
            # because overhead is stupidly high, draw locally
            # check if the particle is in frame
            if particle.radius >= 1:
                # draw the particle
                scaledSurface = pygame.Surface((particle.radius, particle.radius))
                scaledSurface.set_colorkey((0, 0, 0))
                pygame.draw.circle(scaledSurface, particle.particleColor, (particle.radius / 2, particle.radius / 2), particle.radius / 2)
                display.blit(pygame.transform.scale(scaledSurface, (scaledSurface.get_width() * gameScale, scaledSurface.get_height() * gameScale)), (particle.x - scaledSurface.get_width() * gameScale // 2, particle.y - scaledSurface.get_height() * gameScale // 2))
            # draw the glowing surface
            display.blit(pygame.transform.scale(particle.glowSurface, (particle.glowSurface.get_width() * gameScale, particle.glowSurface.get_height() * gameScale)), (particle.x - particle.glowSurface.get_width(), particle.y - particle.glowSurface.get_height()), special_flags=pygame.BLEND_RGB_ADD)

            if particle.dead:
                displayBlazeParticles.pop(i)

        # display diamond overlay
        blazeDisplayScale =  gameScale + 2.5 * ((player.totalBlaze + 1) / 11)
        blazeDisplayLocation = 60 - whiteFont.size(str(player.totalBlaze), blazeDisplayScale)[0] / 2, display.get_height() - 60 - whiteFont.size(str(player.totalBlaze), blazeDisplayScale)[1] / 2
        renderText(display, str(player.totalBlaze), blazeDisplayLocation, blazeDisplayScale, blueFont, whiteFont)

        # projectiles
        for i, projectile in enumerate(projectiles):
            if isinstance(projectile, Ball):
                collidables = chunks.torches + chunks.getTileObjectsOfCurrentChunk(projectile.rect.center)
                projectile.update(cameraRect, dt, particles, collidables, effects, sparks)
            elif isinstance(projectile, Wheel):
                projectile.update(player.center, display, scroll, dt, particles, chunks.torches, sparks, effects)
            elif isinstance(projectile, ExplodingOrb):
                projectile.update(chunks.torches, dt, particles, effects, sparks)
            elif isinstance(projectile, Flash):
                projectile.update(dt, particles, chunks.torches)
            else:
                projectile.update(cameraRect, dt, particles, chunks.torches)
            if projectile.dead:
                projectiles.pop(i)

        # effects
        for i, effect in enumerate(effects):
            effect.update(display, scroll, dt)
            if effect.dead:
                effects.pop(i)

        # sparks
        for i, spark in enumerate(sparks):
            spark.move(dt)
            if cameraRect.collidepoint(spark.center):
                spark.draw(display, scroll)
            if spark.dead:
                sparks.pop(i)

        # add blaze particle to the player
        if not player.dead:
            for i in range(player.generateBlaze()):
                # particles around the player
                particles.append(GlowParticle(random.randint(player.rect.left, player.rect.right), random.randint(player.rect.top, player.rect.bottom), (0, random.uniform(-1, -.5)), random.choice([(246, 126, 27), (244, 180, 27), (230, 72, 46)]), random.choice([(24, 12, 2), (24, 18, 2), (23, 7, 4)]), random.randint(1, 4) * gameScale, random.uniform(.1, .25) * gameScale))

        # blaze display particles
        if time.time() - lastDisplayBlazeParticleBorn >= .15 and not mapTransition:
            displayBlazeParticles.append(GlowParticle(30 * gameScale + random.randint(-5, 5), display.get_height() - 30 * gameScale + random.randint(-5, 5) * gameScale, (0, random.uniform(-1, -.5)), random.choice([(246, 126, 27), (244, 180, 27), (230, 72, 46)]), random.choice([(24, 12, 2), (24, 18, 2), (23, 7, 4)]), 30 + random.randint(1, player.totalBlaze + 1) * 2, random.uniform(.25, .5)))
            if random.randint(0, 3) == 1:
                for i in range(random.randint(1, 3)):
                    displayBlazeParticles.append(GlowParticle(30 * gameScale + random.randint(-5, 5), display.get_height() - 30 * gameScale + random.randint(-5, 5) * gameScale, (0, random.uniform(-1.5, -1)), random.choice([(246, 126, 27), (244, 180, 27), (230, 72, 46)]), random.choice([(24, 12, 2), (24, 18, 2), (23, 7, 4)]), 10, random.uniform(.075, .1)))
            lastDisplayBlazeParticleBorn = time.time()

        # add particles if the player is dashing
        if player.dashing:
            for i in range(random.randint(3, 7)):
                particles.append(GlowParticle(random.randint(player.rect.left, player.rect.right), random.randint(player.rect.top, player.rect.bottom), (0, random.uniform(-1, -.5)), random.choice([(246, 126, 27), (244, 180, 27), (230, 72, 46)]), random.choice([(24, 12, 2), (24, 18, 2), (23, 7, 4)]), random.randint(1, 4) * gameScale, random.uniform(.1, .25) * gameScale))

        # try and light torches using the player's blaze
        player.lightNearbyTorches(chunks.torches)

        # only regenerate blaze in the actual level
        player.regenerateBlaze()

        # activating torches gives 1 blaze each
        if len([torch for torch in chunks.torches if torch.active]) > activeTorches:
            activeTorches = len([torch for torch in chunks.torches if torch.active])

        # arrows that point to unlit torches
        if displayTorchArrows:
            for torch in chunks.torches:
                if not torch.active and (72 * gameScale) ** 2 < (player.center[0] - torch.lightHitBox.centerx) ** 2 + (player.center[1] - torch.lightHitBox.centery) ** 2 <= (chunks.tileSize * chunks.chunkSize * 5) ** 2:
                    angle = math.atan2( torch.lightHitBox.centery - player.center[1], torch.lightHitBox.centerx - player.center[0])
                    # create the arrow
                    arrowSurface = pygame.Surface((16, 16))
                    points = [
                        (8, 0),
                        (16, 16),
                        (0, 16)
                    ]
                    pygame.draw.polygon(arrowSurface, (169, 59, 59), points)
                    scaledSurface = pygame.Surface((16 * gameScale, 16 * gameScale))
                    scaledSurface.blit(pygame.transform.scale(arrowSurface, scaledSurface.get_size()), (0, 0))
                    scaledSurface.set_colorkey((0, 0, 0))
                    rotatedSurface = pygame.transform.rotate(scaledSurface, -math.degrees(angle) - 90)
                    whiteOutline = pygame.mask.from_surface(rotatedSurface)
                    whiteOutline = whiteOutline.to_surface(unsetcolor=(0, 0, 0, 0))
                    # outline
                    display.blit(whiteOutline, (player.center[0] + 72 * gameScale * math.cos(angle) - scroll[0] - rotatedSurface.get_width() / 2 + 2, player.center[1] + 72 * gameScale * math.sin(angle) - scroll[1] - rotatedSurface.get_height() / 2 + 2))
                    display.blit(whiteOutline, (player.center[0] + 72 * gameScale * math.cos(angle) - scroll[0] - rotatedSurface.get_width() / 2 + 2, player.center[1] + 72 * gameScale * math.sin(angle) - scroll[1] - rotatedSurface.get_height() / 2 - 2))
                    display.blit(whiteOutline, (player.center[0] + 72 * gameScale * math.cos(angle) - scroll[0] - rotatedSurface.get_width() / 2 - 2, player.center[1] + 72 * gameScale * math.sin(angle) - scroll[1] - rotatedSurface.get_height() / 2 + 2))
                    display.blit(whiteOutline, (player.center[0] + 72 * gameScale * math.cos(angle) - scroll[0] - rotatedSurface.get_width() / 2 - 2, player.center[1] + 72 * gameScale * math.sin(angle) - scroll[1] - rotatedSurface.get_height() / 2 - 2))
                    #actual arrow
                    display.blit(rotatedSurface, (player.center[0] + 72 * gameScale * math.cos(angle) - scroll[0] - rotatedSurface.get_width() / 2, player.center[1] + 72 * gameScale * math.sin(angle) - scroll[1] - rotatedSurface.get_height() / 2))

        # draw ability icons
        if chunks.portal and not chunks.portal.rendermenu:
            width = 32 * gameScale
            numOfAbilities = len([name for name in list(currentAbilities.values()) if name != 'blank'])
            for i, ability in enumerate(currentAbilities):
                if currentAbilities[ability] != 'blank':
                    # key icons
                    #display.blit(textures.sheets['keyicons'][0][i], (display.get_width() / 2 - width + width * i - textures.sheets['keyicons'][0][i].get_width() / 2, display.get_height() * .78 - textures.sheets['keyicons'][0][i].get_height() / 2))
                    # render the bound number for the ability
                    renderText(display, str(i + 1), (display.get_width() / 2 - width + width * i - blueFont.size(str(i+1))[0] / 2, display.get_height() * .95 - blueFont.size(str(i+1))[1] / 2), gameScale, blueFont, whiteFont)

                    # ability icons
                    icon = abilities[currentAbilities[ability]].icon
                    display.blit(icon, (display.get_width() / 2 - width + width * i - icon.get_width() / 2, display.get_height() * .85 - icon.get_height() / 2))
                    # cooldown cover
                    cooldownLeft = time.time() - abilities[currentAbilities[ability]].lastUse
                    if abilities[currentAbilities[ability]].cooldown > cooldownLeft > 0 and abilities[currentAbilities[ability]].lastUse > 0:
                        cooldownCover = pygame.Surface((icon.get_width() - 4 * gameScale, icon.get_height() - 4 * gameScale))
                        cooldownCover.fill((50, 50, 50))
                        cooldownPercentage = (abilities[currentAbilities[ability]].cooldown - cooldownLeft) / abilities[currentAbilities[ability]].cooldown
                        display.blit(pygame.transform.scale(cooldownCover,
                          (cooldownCover.get_width(),
                           int(cooldownCover.get_height() * cooldownPercentage))),
                           (display.get_width() / 2 - width + width * i + 2 * gameScale - icon.get_width() / 2, display.get_height() * .85 + 2 * gameScale + cooldownCover.get_height() - cooldownCover.get_height() * cooldownPercentage - icon.get_height() / 2), special_flags=pygame.BLEND_RGB_SUB)
                    # cover if blaze is too low
                    elif player.totalBlaze < abilities[currentAbilities[ability]].cost:
                        cooldownCover = pygame.Surface((icon.get_width() - 4 * gameScale, icon.get_height() - 4 * gameScale))
                        cooldownCover.fill((50, 50, 50))
                        display.blit(cooldownCover, (display.get_width() / 2 - width + width * i + 2 * gameScale - icon.get_width() / 2, display.get_height() * .85 + 2 * gameScale - icon.get_height() / 2), special_flags=pygame.BLEND_RGB_SUB)

                    # flash the ability icon
                    elif  abilities[currentAbilities[ability]].cooldown + .15 > cooldownLeft > abilities[currentAbilities[ability]].cooldown:
                        cooldownCover = pygame.Surface((icon.get_width() - 4 * gameScale, icon.get_height() - 4 * gameScale))
                        cooldownCover.fill((100, 100, 100))
                        display.blit(cooldownCover, (display.get_width() / 2 - width + width * i + 2 * gameScale - icon.get_width() / 2, display.get_height() * .85 + 2 * gameScale - icon.get_height() / 2), special_flags=pygame.BLEND_RGB_ADD)

        # debug text and rendering it
        debugTexts = [
        ]
        for i, text in enumerate(debugTexts):
            renderText(display, text, (5, 5 + 10 * i), gameScale, blueFont, whiteFont)

        # reset the player back to spawn if out of bounds
        if player.center[0] < boundaries[0] or player.center[0] > boundaries[1] or player.center[1] < boundaries[2] or player.center[1] > boundaries[3]:
            player.die(particles, sparks)

        # turn the portal on if the player is close enough
        if chunks.portal and currentLevel == 'village' and levelSwitchTo == 'village':
            if (player.center[0] - chunks.portal.center[0]) ** 2 + (player.center[1] - chunks.portal.center[1]) ** 2 <= chunks.portal.activeRadius ** 2:
                chunks.portal.setActive(True, sparks, particles, effects)
            else:
                chunks.portal.setActive(False, sparks, particles, effects)

            # render the letter E over the player head
            if (chunks.portal.center[0] - player.center[0]) ** 2 + (chunks.portal.center[1] - player.center[1]) ** 2 <= chunks.portal.interactRadius ** 2:
                text = '[E] Portal'
                renderText(display, text, (player.rect.centerx - scroll[0] - blueFont.size(text, gameScale)[0] / 2, player.rect.top - blueFont.size(text, gameScale)[1] - 1 * gameScale - scroll[1], gameScale), gameScale, blueFont, whiteFont)

        # allow for interaction with the end portal
        if currentLevel == 'level' and levelSwitchTo != 'village' and chunks.portal.active:
            # render the letter E over the player head
            if (chunks.portal.center[0] - player.center[0]) ** 2 + (chunks.portal.center[1] - player.center[1]) ** 2 <= chunks.portal.interactRadius ** 2:
                text = '[E] Leave'
                renderText(display, text, (player.rect.centerx - scroll[0] - blueFont.size(text, gameScale)[0] / 2, player.rect.top - blueFont.size(text, gameScale)[1] - 1 * gameScale - scroll[1], gameScale), gameScale, blueFont, whiteFont)

        # event board interaction
        if chunks.eventboard and (chunks.eventboard.center[0] - player.center[0]) ** 2 + (chunks.eventboard.center[1] - player.center[1]) ** 2 <= chunks.eventboard.interactRadius ** 2:
            text = '[E] Eventboard'
            renderText(display, text, (player.rect.centerx - scroll[0] - blueFont.size(text, gameScale)[0] / 2, player.rect.top - blueFont.size(text, gameScale)[1] - 1 * gameScale - scroll[1], gameScale), gameScale, blueFont, whiteFont)

        # create the portal display screen
        if chunks.portal and chunks.portal.rendermenu:
            guiDisplay.draw(display, textures.sheets['keyicons'][0], currentAbilities)

        # timer
        if currentLevel == 'level' and levelSwitchTo != 'village':
            if levelTimer != 0 and endPortalFocusSetTime == 0:
                elapsedTime = (time.time() - levelTimer)
                hours = int(elapsedTime // 360)
                minutes = int(elapsedTime // 60)
                if minutes >= 60:
                    minutes = int(minutes - hours * 60)
                seconds = int(elapsedTime)
                if seconds >= 60:
                    seconds = int(seconds - minutes * 60)
                ms = int((elapsedTime - int(elapsedTime)) * 1000)
                timerText = ''
                if hours < 10:
                    timerText += f'0{hours}:'
                else:
                    timerText += f'{hours}:'
                if minutes < 10:
                    timerText += f'0{minutes}:'
                else:
                    timerText += f'{minutes}:'
                if seconds < 10:
                    timerText += f'0{seconds}:'
                else:
                    timerText += f'{seconds}:'
                timerText += str(ms)

            renderText(display, timerText, (display.get_width() / 2 - blueFont.size(timerText, gameScale)[0] / 2, 20 * gameScale), gameScale, blueFont, whiteFont)
            # render the amount of torches left
            unlitTorches = len([torch for torch in chunks.torches if not torch.active])
            unlitTorchesText = f'x{unlitTorches} Unlit Torches'
            renderText(display, unlitTorchesText, (display.get_width() / 2 - blueFont.size(unlitTorchesText, gameScale)[0] / 2, 10 * gameScale), gameScale, blueFont, whiteFont)

            # end game if there are 0 unlit torches left
            if unlitTorches == 0 and endPortalFocusSetTime == 0:
                chunks.portal.setActive(True, sparks, particles, effects)
                endPortalFocus = True
                endPortalFocusSetTime = time.time()
                player.die(particles, sparks)
                exactLevelEndTime = time.time()

        # draw the cursor
        mx, my = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed(3)[0]:
            display.blit(textures.sheets['cursor'][0][1], (mx * xRatio - textures.sheets['cursor'][0][1].get_width() / 2, my * yRatio - textures.sheets['cursor'][0][1].get_height() / 2))
        else:
            display.blit(textures.sheets['cursor'][0][0], (mx * xRatio - textures.sheets['cursor'][0][0].get_width() / 2, my * yRatio - textures.sheets['cursor'][0][0].get_height() / 2))

        # create the map transition effect
        if mapTransition or resetPlayerPosition or currentLevel != levelSwitchTo:
            radius = (display.get_width() / 2) - (750 * (time.time() - mapTransitionStartTime))
            blackTransitionScreen = pygame.Surface(display.get_size())
            if radius > 0:
                pygame.draw.circle(blackTransitionScreen, (255, 255, 255), (blackTransitionScreen.get_width() / 2 + scrollOffset[0], blackTransitionScreen.get_height() / 2 + scrollOffset[1]), abs(radius))
                blackTransitionScreen.set_colorkey((255, 255, 255))
                display.blit(blackTransitionScreen, (0, 0))
            elif not loadedNewLevel and mapTransition:
                display.blit(blackTransitionScreen, (0, 0))
                screen.blit(pygame.transform.scale(display, screen.get_size()), (0,0))
                pygame.display.update()
                chunks.load(levelSwitchTo, textures.sheets)
                player.rect.center = levelStarts[levelSwitchTo]
                player.respawnLocation = levelStarts[levelSwitchTo]
                boundaries = chunks.getBounds()
                if levelSwitchTo == 'level':
                    pygame.mixer.music.fadeout(500)
                    pygame.mixer.music.unload()
                    pygame.mixer.music.load('data/sounds/mainv2.wav')
                    pygame.mixer.music.play(-1)
                    loadedLevel = True
                elif levelSwitchTo == 'village':
                    pygame.mixer.music.fadeout(500)
                    pygame.mixer.music.unload()
                    pygame.mixer.music.load('data/sounds/titlescreen2.wav')
                    pygame.mixer.music.play(-1)
                loadedNewLevel = True
                loadedNewLevelStartTime = time.time()
            elif not loadedNewLevel and resetPlayerPosition:
                display.blit(blackTransitionScreen, (0, 0))
                player.rect.center = levelStarts[levelSwitchTo]
                player.respawnLocation = levelStarts[levelSwitchTo]
                loadedNewLevel = True
                loadedNewLevelStartTime = time.time()
            else:
                radius = 750 * (time.time() - loadedNewLevelStartTime)
                pygame.draw.circle(blackTransitionScreen, (255, 255, 255), (blackTransitionScreen.get_width() / 2 + scrollOffset[0], blackTransitionScreen.get_height() / 2 + scrollOffset[1]), radius)
                blackTransitionScreen.set_colorkey((255, 255, 255))
                display.blit(blackTransitionScreen, (0, 0))
                if radius ** 2 > (display.get_width() / 2) ** 2 + (display.get_height() / 2) ** 2:
                    mapTransition = False
                    loadedNewLevel = False
                    resetPlayerPosition = False
                    currentLevel = levelSwitchTo

        # check if the level is changing
        if guiDisplay.play and currentLevel == 'village':
            guiDisplay.play = False
            chunks.portal.rendermenu = False
            chunks.portal.setActive(False, sparks, particles, effects)
            #pygame.mixer.music.fadeout(750) # causes fuckups
            player.totalBlaze = 0
            levelSwitchTo = 'level'
            mapTransition = True
            mapTransitionStartTime = time.time()

        # show fps
        renderText(display, str(round(fps, 0)), (display.get_width() - blueFont.size(str(round(fps, 0)), 2)[0], 0), 2, blueFont, whiteFont)
        renderText(display, str(player.health), (display.get_width() - blueFont.size(str(player.health), 2)[0], 30), 2, blueFont, whiteFont)

        # handle events
        for event in pygame.event.get():

            # key press
            if event.type == pygame.KEYDOWN:

                # quit the game
                if event.key == pygame.K_ESCAPE:
                    if chunks.portal and chunks.portal.rendermenu:
                        chunks.portal.rendermenu = False
                    else:
                        running = False
                        pygame.quit()

                if not mapTransition and not (chunks.portal and chunks.portal.rendermenu) and not (chunks.eventboard and chunks.eventboard.renderboard) and not endPortalFocus:
                    # player movements keys
                    if event.key == pygame.K_w or event.key == pygame.K_SPACE:
                        player.inputs['jump'] = True
                        if levelTimer == 0 and loadedLevel and currentLevel == 'level':
                            levelTimer = time.time()
                    elif event.key == pygame.K_a:
                        player.inputs['left'] = True
                        if levelTimer == 0 and loadedLevel and currentLevel == 'level':
                            levelTimer = time.time()
                    elif event.key == pygame.K_d:
                        player.inputs['right'] = True
                        if levelTimer == 0 and loadedLevel and currentLevel == 'level':
                            levelTimer = time.time()
                    elif event.key == pygame.K_s and player.onPlatform:
                        player.inputs['drop'] = True
                        player.forces[1] += 1
                        if levelTimer == 0 and loadedLevel and currentLevel == 'level':
                            levelTimer = time.time()

                    # abilites
                    elif event.key in currentAbilities and currentAbilities[event.key] != 'blank':
                        if time.time() - abilities[currentAbilities[event.key]].lastUse >= abilities[currentAbilities[event.key]].cooldown and player.totalBlaze >= abilities[currentAbilities[event.key]].cost:
                            mouseScroll = int((player.center[0] - display.get_width() / 2)) - scrollOffset[0],  int((player.center[1] - display.get_height() / 2)) - scrollOffset[1]
                            player.totalBlaze -= abilities[currentAbilities[event.key]].cost
                            if currentAbilities[event.key] in ['bolt', 'fireball', 'shotgun', 'boost']:
                                abilities[currentAbilities[event.key]].use(player.center, ((mx * xRatio) + mouseScroll[0], (my * yRatio) + mouseScroll[1]), projectiles)
                                player.state = 'fire'
                                player.animationUpdateTime = time.time()
                                player.animationIndex = 0
                                # apply knockback if can
                                player.forces[0] += abilities[currentAbilities[event.key]].knockback[0]
                                player.forces[1] += abilities[currentAbilities[event.key]].knockback[1]
                                abilities[currentAbilities[event.key]].resetKnockback()
                                # flip the player
                                player.flip = (mx * xRatio) + mouseScroll[0] < player.center[0]
                            elif currentAbilities[event.key] in ['wheel']:
                                abilities[currentAbilities[event.key]].use(projectiles, player.center, chunks.tileSize)
                            elif currentAbilities[event.key] in ['dash']:
                                player.flip = (mx * xRatio) + mouseScroll[0] < player.center[0]
                                abilities[currentAbilities[event.key]].use(player)
                            if levelTimer == 0 and loadedLevel and currentLevel == 'level':
                                levelTimer = time.time()

                # interactables
                if event.key == pygame.K_e:
                    if currentLevel == 'village':
                        if chunks.portal and (chunks.portal.center[0] - player.center[0]) ** 2 + (chunks.portal.center[1] - player.center[1]) ** 2 <= chunks.portal.interactRadius ** 2:
                            if chunks.portal.rendermenu:
                                chunks.portal.rendermenu = False
                            else:
                                chunks.portal.rendermenu = True
                                player.stopMoving()

                        elif chunks.eventboard and (chunks.eventboard.center[0] - player.center[0]) ** 2 + (chunks.eventboard.center[1] - player.center[1]) ** 2 <= chunks.eventboard.interactRadius ** 2:
                            if chunks.eventboard.renderboard:
                                chunks.eventboard.renderboard = False
                            else:
                                chunks.eventboard.renderboard = True
                                player.stopMoving()

                    elif currentLevel == 'level':
                        if chunks.portal and (chunks.portal.center[0] - player.center[0]) ** 2 + (chunks.portal.center[1] - player.center[1]) ** 2 <= chunks.portal.interactRadius ** 2:
                            # write time to output file
                            exactTime = exactLevelEndTime - levelTimer
                            elapsedTime = (time.time() - levelTimer)
                            hours = int(elapsedTime // 360)
                            minutes = int(elapsedTime // 60)
                            if minutes >= 60:
                                minutes = int(minutes - hours * 60)
                            seconds = int(elapsedTime)
                            if seconds >= 60:
                                seconds = int(seconds - minutes * 60)
                            ms = int((elapsedTime - int(elapsedTime)) * 1000)
                            timerText = ''
                            if hours < 10:
                                timerText += f'0{hours}:'
                            else:
                                timerText += f'{hours}:'
                            if minutes < 10:
                                timerText += f'0{minutes}:'
                            else:
                                timerText += f'{minutes}:'
                            if seconds < 10:
                                timerText += f'0{seconds}:'
                            else:
                                timerText += f'{seconds}:'
                            timerText += str(ms)
                            currentScores = {
                                "1":{"formatted":0, "exact":0},
                                "2":{"formatted":0, "exact":0},
                                "3":{"formatted":0, "exact":0},
                                "4":{"formatted":0, "exact":0},
                                "5":{"formatted":0, "exact":0}
                            }
                            replaced = False
                            with open('data/scores.json') as jsonFile:
                                currentScores = json.load(jsonFile)
                            for score in currentScores:
                                if currentScores[score]['exact'] == 0 and not replaced:
                                    replaced = True
                                    currentScores[score]['exact'] = exactTime
                                    currentScores[score]['formatted'] = timerText
                            if not replaced:
                                # replace the lowest value, which should be the fifth spot
                                if currentScores['5']['exact'] > exactTime:
                                    currentScores['5']['exact'] = exactTime
                                    currentScores['5']['formatted'] = timerText
                                    replaced = True
                            if replaced:
                                # sort the scores, catching if the new score is higher than the rest
                                scores = []
                                for score in currentScores:
                                    scores.append((currentScores[score]['exact'], currentScores[score]['formatted']))
                                # sort the scores
                                for i, score in enumerate(scores):
                                    if score[0] == 0:
                                        scores.pop(i)
                                scores = sorted(scores, key=lambda x: x[0])
                                # replace the scores back in
                                for scoreSlot in currentScores:
                                    currentScores[scoreSlot]['exact'] = 0
                                    currentScores[scoreSlot]['formatted'] = 0
                                    if int(scoreSlot) <= len(scores):
                                        currentScores[scoreSlot]['exact'] = scores[int(scoreSlot) - 1][0]
                                        currentScores[scoreSlot]['formatted'] = scores[int(scoreSlot) - 1][1]
                                with open('data/scores.json', 'w') as jsonFile:
                                    json.dump(currentScores, jsonFile, indent=1)

                            levelSwitchTo = 'village'
                            mapTransition = True
                            mapTransitionStartTime = time.time()
                            particles = []
                            sparks = []
                            effects = []
                            projectiles = []
                            leaves = []
                            displayBlazeParticles = []
                            player.die(particles, sparks)
                            endPortalFocus = False
                            endPortalFocusSetTime = 0
                            respawnPlayerAtPortal = False
                            timerText = '00:00:00:000'
                            levelTimer = 0

                elif event.key == pygame.K_q:
                    displayTorchArrows = not displayTorchArrows

                elif event.key == pygame.K_j and currentLevel == 'level':
                    for torch in chunks.torches:
                        torch.active = True

                elif event.key == pygame.K_f:
                    player.damage(10, particles, sparks)

                # test map transitions
                if event.key == pygame.K_t:
                    if currentLevel == 'level':
                        currentLevel = 'village'
                        mapTransition = True
                        mapTransitionStartTime = time.time()

            # key release
            elif event.type == pygame.KEYUP:

                # player movement keys
                if event.key == pygame.K_a:
                    player.inputs['left'] = False
                elif event.key == pygame.K_d:
                    player.inputs['right'] = False
                elif event.key == pygame.K_w or event.key == pygame.K_SPACE:
                    player.jumpCut = True

            # mouse button press
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if chunks.portal.rendermenu:
                    guiDisplay.buttonPress(mx * xRatio, my * yRatio, currentAbilities)

        # update the screen
        if running:
            screen.blit(pygame.transform.scale(display, screen.get_size()), (0,0))
            pygame.display.update()
            clock.tick(60)

main()
'''
with cProfile.Profile() as pr:
    main()

stats = pstats.Stats(pr)
stats.sort_stats(pstats.SortKey.TIME)
stats.print_stats()
'''