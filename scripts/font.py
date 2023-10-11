import pygame

class Font:
    def __init__(self):
        # load the font sheet
        fontsheet = pygame.image.load('data/font.png').convert()

        # chars in the font sheet
        chars = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p',
        'q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H',
        'I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
        '1','2','3','4','5','6','7','8','9','0','!','@','#','$','%','(',')','-',
        '_','+','=','[',']','{','}','/',':',';',"'",'"','.',',','<','>','?']
        self.characters = {}

        # cutout and save each character in the character dictionary
        width = 0
        index = 0
        for i in range(fontsheet.get_width()):
            if index < len(chars):
                if fontsheet.get_at((i, 0)) == (255, 0, 0, 255):
                    charSurf = fontsheet.subsurface(pygame.Rect(i - width, 0, width, fontsheet.get_height())).copy()
                    self.characters[chars[index]] = charSurf.copy()
                    index += 1
                    width = 0
                else:
                    width += 1

        # constants for rendering text
        self.SPACEWIDTH = self.characters['a'].get_width()
        self.SPACING = 1
        self.NEWLINEHEIGHT = self.characters['a'].get_height()

        # make the background of the text transparent
        for char in self.characters:
            self.characters[char].set_colorkey((0, 0, 0))

    def size(self, text, scale=1):
        # vars for the size, widths is a list used in the case that their are \n characters
        width = 0
        height = int(self.NEWLINEHEIGHT * scale)
        widths = []

        # iterate through each character and add to the width or height and stuff
        for char in text:
            if char == '\n':
                height += int(self.NEWLINEHEIGHT * scale)
                widths.append(width)
                width = 0
            elif char == ' ':
                width += int((self.SPACEWIDTH + self.SPACING) * scale)
            else: 
                charSurf = self.characters[char]
                width += pygame.transform.scale(charSurf, (int(charSurf.get_width() * scale), int(charSurf.get_height() * scale))).get_width() + int(self.SPACING * scale)

        # if there no are \n characters, return the regular width 
        if widths == []:
            return width, height

        # else, return widest width
        return max(widths), height

    def render(self, display, text, loc, scale=1):
        # offsets when rendering each character
        xOffset = 0
        yOffset = 0

        # this function also performs the size function and returns it
        width = 0
        height = int(self.NEWLINEHEIGHT * scale)
        widths = []

        # iterate through the text
        for char in text:
            if char == '\n':
                # move the offset values
                xOffset = 0
                yOffset += int(self.NEWLINEHEIGHT * scale)
                
                height += int(self.NEWLINEHEIGHT * scale)
                widths.append(width)
                width = 0
            elif char == ' ':
                xOffset += int((self.SPACEWIDTH + self.SPACING) * scale)

                width += int((self.SPACEWIDTH + self.SPACING) * scale)
            else:
                # scale the image properly and blit it in the right place
                scaledSize = int(self.characters[char].get_width() * scale), int(self.characters[char].get_height() * scale)
                charSurf = pygame.transform.scale(self.characters[char], scaledSize) 
                display.blit(charSurf, (loc[0] + xOffset, loc[1] + yOffset))
                xOffset += int((self.characters[char].get_width() + self.SPACING) * scale)

                width += charSurf.get_width() + int(self.SPACING * scale)

        # return size stuff
        if widths == []:
            return width, height

        return max(widths), height

    def centerRender(self, display, text, loc, scale=1):
        # renders the text where the text's center is the location, also return size because why not
        size = self.size(text, scale)
        newLocation = loc[0] - size[0] / 2, loc[1] - size[1] / 2
        return self.render(display, text, newLocation, scale)
    
    def recolor(self, newcolor):
        # only change color if the new color is not black
        if newcolor != (0, 0, 0):
            updatedChars = self.characters.copy()

            # iterate through each character and then through each pixel of the character, changing non black pixels to the new color
            for char in updatedChars:
                for i in range(updatedChars[char].get_width()):
                    for j in range(updatedChars[char].get_height()):
                        if updatedChars[char].get_at((i, j)) != (0, 0, 0):
                            updatedChars[char].set_at((i, j), newcolor)

            # store updated
            self.characters = updatedChars.copy()
        