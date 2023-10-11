import pygame

class TextureManager:
    def __init__(self, unparsedSheets, gameScale):
        self.sheets = self.parseSheets(unparsedSheets, gameScale)

    def parseSheets(self, unparsedSheets, gameScale):
        parsedSheets = {}

        for name in unparsedSheets:
            loadedSheet = unparsedSheets[name]
            textures = []
            for i in range(loadedSheet.get_height()):
                if loadedSheet.get_at((0, i)) == (166, 255, 0, 255):
                    row = []
                    for j in range(loadedSheet.get_width()):
                        if loadedSheet.get_at((j, i)) == (255, 41, 250, 255):
                            width = 0
                            height = 0
                            for x in range(j + 1, loadedSheet.get_width()):
                                if loadedSheet.get_at((x, i)) == (0, 255, 255, 255):
                                    width = x - j - 1
                                    break
                            for y in range(i + 1, loadedSheet.get_height()):
                                if loadedSheet.get_at((j, y)) == (0, 255, 255, 255):
                                    height = y - i - 1
                                    break
                            texture = pygame.Surface((width, height))
                            texture.blit(loadedSheet, (0, 0), (j + 1, i + 1, width, height))
                            scaledTexture = pygame.Surface((texture.get_width() * gameScale, texture.get_height() * gameScale))
                            scaledTexture.blit(pygame.transform.scale(texture, scaledTexture.get_size()), (0, 0))
                            scaledTexture.set_colorkey((0, 0, 0))
                            row.append(scaledTexture.copy())
                    textures.append(row)

            parsedSheets[name] = textures
        
        return parsedSheets