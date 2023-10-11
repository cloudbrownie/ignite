import pygame
import json

scores = {
    "1":{"formatted":0, "exact":0},
    "2":{"formatted":0, "exact":0},
    "3":{"formatted":0, "exact":0},
    "4":{"formatted":0, "exact":0},
    "5":{"formatted":0, "exact":0}
}
try:
    with open('data/scores.json') as readFile:
        scores = json.load(readFile)
except Exception as e:
    print(e)

class MainGui:
    def __init__(self, y, display, textures, abilityIcons, abilities, backGroundFont, foreGroundFont, gameScale, torchAmount):
        self.play = False
        self.renderpos = display.get_width() / 2 - textures[0].get_width() / 2, y
        self.abilityRects = {}
        # scale down the texture, find the red spots, replace them and blit the ability icons there, 
        scaledTexture = pygame.Surface((textures[0].get_width() / gameScale, textures[0].get_height() / gameScale))
        scaledTexture.blit(pygame.transform.scale(textures[0], scaledTexture.get_size()), (0, 0))

        abilityNames = [abilityName for abilityName in abilities]
        previewPos = 0, 0
        icon = 0
        for i in range(scaledTexture.get_width()):
            for j in range(scaledTexture.get_height()):
                if scaledTexture.get_at((i, j)) == (0, 255, 0, 255):
                    previewPos = i, j
                    scaledTexture.set_at((i, j), (244, 180, 27))
                if scaledTexture.get_at((i, j)) == (255, 0, 0, 255):
                    scaledTexture.set_at((i, j), (38, 43, 60))
                    scaledTexture.blit(pygame.transform.scale(abilityIcons[icon], (int(abilityIcons[icon].get_width() / gameScale), int(abilityIcons[icon].get_height() / gameScale))), (i, j))
                    self.abilityRects[abilityNames[icon]] = pygame.Rect(self.renderpos[0] + i * gameScale, self.renderpos[1] + j * gameScale, abilityIcons[icon].get_width(), abilityIcons[icon].get_height())
                    icon += 1

        bestScore = str(scores['1']['formatted'])
        if bestScore == '0':
            bestScore = '--:--:--:---'

        # render text
        bestTextSize = foreGroundFont.size('Best Time:')
        location = 27 - bestTextSize[0] / 2 + 2, 20
        backGroundFont.render(scaledTexture, 'Best Time:', (location[0], location[1] + 1))
        backGroundFont.render(scaledTexture, 'Best Time:', (location[0] + 1, location[1] + 1))
        backGroundFont.render(scaledTexture, 'Best Time:', (location[0] + 1, location[1]))
        foreGroundFont.render(scaledTexture, 'Best Time:', location)

        size = foreGroundFont.size(bestScore)
        location = 27 - size[0] / 2 + 2, 20 + 1 + bestTextSize[1]
        backGroundFont.render(scaledTexture, bestScore, (location[0], location[1] + 1))
        backGroundFont.render(scaledTexture, bestScore, (location[0] + 1, location[1] + 1))
        backGroundFont.render(scaledTexture, bestScore, (location[0] + 1, location[1]))
        foreGroundFont.render(scaledTexture, bestScore, location)

        torchTextSize = foreGroundFont.size('Torches:')
        location = scaledTexture.get_width() - 27 - torchTextSize[0] / 2 - 2, 20
        backGroundFont.render(scaledTexture, 'Torches:', (location[0], location[1] + 1))
        backGroundFont.render(scaledTexture, 'Torches:', (location[0] + 1, location[1] + 1))
        backGroundFont.render(scaledTexture, 'Torches:', (location[0] + 1, location[1]))
        foreGroundFont.render(scaledTexture, 'Torches:', location)

        size = foreGroundFont.size(f'x{torchAmount}')
        location = scaledTexture.get_width() - 27 - size[0] / 2 - 2, 20 + 1 + torchTextSize[1]
        backGroundFont.render(scaledTexture, f'x{torchAmount}', (location[0], location[1] + 1))
        backGroundFont.render(scaledTexture, f'x{torchAmount}', (location[0] + 1, location[1] + 1))
        backGroundFont.render(scaledTexture, f'x{torchAmount}', (location[0] + 1, location[1]))
        foreGroundFont.render(scaledTexture, f'x{torchAmount}', location)

        self.texture = pygame.Surface(textures[0].get_size())
        self.texture.blit(pygame.transform.scale(scaledTexture, self.texture.get_size()), (0, 0))
        self.texture.set_colorkey((0, 0, 0))


        # create the play button
        playButtonRenderPos = display.get_width() / 2 - textures[1].get_width() / 2, y + self.texture.get_height() + 5 * gameScale
        self.playButton = pygame.Rect(playButtonRenderPos, textures[1].get_size())
        scaledSurface = pygame.Surface((textures[1].get_width() / gameScale, textures[1].get_height() / 2))
        scaledSurface.blit(pygame.transform.scale(textures[1], scaledSurface.get_size()), (0, 0))
        foreGroundFont.render(scaledSurface, 'PLAY', (scaledSurface.get_width() / 2 - foreGroundFont.size('PLAY')[0] / 2, scaledSurface.get_height() / 2 - foreGroundFont.size('PLAY')[1] / 2))
        self.playTexture = pygame.Surface(textures[1].get_size())
        self.playTexture.blit(pygame.transform.scale(scaledSurface, self.playTexture.get_size()), (0, 0))
        self.playTexture.set_colorkey((0, 0, 0))

    def draw(self, display, keyIcons, currentAbilities):
        display.blit(self.texture, self.renderpos)
        display.blit(self.playTexture, self.playButton)

    def buttonPress(self, mx, my, currentAbilities):
        currentAbilityNames = list(currentAbilities.values())
        currentAbilityKeys = list(currentAbilities.keys())
        for ability in self.abilityRects:
            # check if the mouse clicked on a current ability
            if self.abilityRects[ability].collidepoint((mx, my)) and ability in currentAbilityNames:
                currentAbilities[currentAbilityKeys[currentAbilityNames.index(ability)]] = 'blank'
            # check if the mouse clicked on a not current ability, and that there is a current ability that is blank
            elif self.abilityRects[ability].collidepoint((mx, my)) and 'blank' in currentAbilityNames:
                currentAbilities[currentAbilityKeys[currentAbilityNames.index('blank')]] = ability
        # check if mouse clicked the play button
        if self.playButton.collidepoint((mx, my)):
            self.play = True

class MainGuiv2:
    def __init__(self):
        pass