import pygame
import json

from scripts.entities import *

# manages the chunks
class ChunkManager:
    def __init__(self, displayWidth, displayHeight, gameScale):
        # chunks contain both tile data and decoration data
        self.chunks = {}

        # entities contain the layers for each entity
        self.trees = {}
        self.torches = []
        self.portal = None
        self.eventboard = None

        # store max layers for each chunk
        self.chunkLayerAmounts = {}

        # display measurements
        self.displayWidth = displayWidth
        self.displayHeight = displayHeight

        # store game scale
        self.scale = gameScale

        # tile and chunk size
        self.tileSize = 16 * gameScale
        self.chunkSize = 8

        self.distance = (self.tileSize * 7) ** 2

    def load(self, levelname, textures):
        # reset entities
        self.trees = {}
        self.torches = []
        self.portal = None
        self.eventboard = None

        # find the file
        dirname = f'data/levels/{levelname}.json'

        # load data from the json
        with open(dirname, 'r') as readFile:
            data = json.load(readFile)
            
            # save chunks directly
            self.chunks = data['chunks']

            # apply scaling to render positions of all chunks and the tiles and decor inside of them
            for chunkID in self.chunks:
                for layer in self.chunks[chunkID]['tiles']:
                    for i, tile in enumerate(self.chunks[chunkID]['tiles'][layer]):
                        # fix the tile pos, renderpos, and size
                        tilePos = tile['tilepos'][0] * self.scale, tile['tilepos'][1] * self.scale
                        size = tile['size'][0] * self.scale, tile['size'][1] * self.scale
                        renderPos = tile['renderpos'][0] * self.scale, tile['renderpos'][1] * self.scale
                        self.chunks[chunkID]['tiles'][layer][i] = {
                            'sheet':tile['sheet'],
                            'type':tile['type'],
                            'size':size,
                            'renderpos':renderPos,
                            'tilepos':tilePos
                            }
                    for i, decor in enumerate(self.chunks[chunkID]['decor'][layer]):
                        self.chunks[chunkID]['decor'][layer][i]['renderpos'] = self.chunks[chunkID]['decor'][layer][i]['renderpos'][0] * self.scale, self.chunks[chunkID]['decor'][layer][i]['renderpos'][1] * self.scale

            # create objects out of each entity
            for layer in data['entities']:
                for entity in data['entities'][layer]:
                    # torch entities
                    if entity['sheet'][0] == 'torch':
                        self.torches.append(Torch(entity['renderpos'][0] * self.scale, entity['renderpos'][1] * self.scale, textures['torch'][0][0]))

                    # tree entities
                    elif entity['sheet'][0] == 'trees':
                        if layer not in self.trees:
                            self.trees[layer] = []
                        self.trees[layer].append(Tree(entity['renderpos'][0] * self.scale, entity['renderpos'][1] * self.scale, textures['trees'][entity['sheet'][1]][entity['sheet'][2]]))

                    # teleporter entity
                    elif entity['sheet'][0] == 'portal':
                        self.portal = Portal((entity['renderpos'][0] * self.scale, entity['renderpos'][1] * self.scale), textures['portal'][0][0])

                    # event board entity
                    elif entity['sheet'][0] == 'eventboard':
                        self.eventboard = EventBoard(entity['renderpos'][0] * self.scale, entity['renderpos'][1] * self.scale, textures['eventboard'][0][0])


        # calculate max layers for each chunk
        for chunkID in self.chunks:
            tileLayers = [tileLayerReference for tileLayerReference in self.chunks[chunkID]['tiles']]
            decorLayers = [decorLayerReference for decorLayerReference in self.chunks[chunkID]['decor']]
            self.chunkLayerAmounts[chunkID] = max([len(tileLayers), len(decorLayers)])

    def fakeLoad(self, levelname):
        torches = 0
        portals = 0
        eventboards = 0
        chunkIDs = []

        with open(f'data/levels/{levelname}.json', 'r') as readFile:
            data = json.load(readFile)

            chunks = data['chunks']

            chunkIDs = [chunkID for chunkID in chunks]
            for layer in data['entities']:
                for entity in data['entities'][layer]:
                    if entity['sheet'][0] == 'torch':
                        torches += 1

                    elif entity['sheet'][0] == 'portal':
                        portals += 1
                    
                    elif entity['sheet'][0] == 'eventboard':
                        eventboards += 1

        return {'torches':torches, 'portals':portals, 'eventboards':eventboards, 'chunkIDs':chunkIDs}

    def displayChunks(self, player, textures, display, cameraRect, particles, leaves, wind, windMultiplier, sparks, effects, dt, scroll=[0, 0]):

        # draw chunk border lines
        """
        # horizontal lines
        for y in range(4):
            chunky = y - 1 +int(round(scroll[1]/128))
            chunky *= 128

            pygame.draw.line(display, (255, 255, 255), (0 - scroll[0], chunky - scroll[1]), (display.get_width() - scroll[0], chunky - scroll[1]), 1)

        for x in range(5):
            chunkx = x - 1 + int(round(scroll[0]/128))
            chunkx *= 128

            pygame.draw.line(display, (255, 255, 255), (chunkx - scroll[0], 0 - scroll[1]), (chunkx - scroll[0], display.get_height() - scroll[1]))
        """

        chunkIDs = []
        for x in range(6):
            for y in range(4):

                # chunk references based on the scroll
                chunkx = x - 1 + int(round(scroll[0]/(128 * self.scale)))
                chunky = y - 1 + int(round(scroll[1]/(128 * self.scale)))
                chunkID = f'{chunkx};{chunky}'

                # check if the layer exists
                if chunkID not in self.chunks:
                    continue
                
                chunkIDs.append(chunkID)

        # display trees
        for layer in self.trees:
            for tree in self.trees[layer]:
                tree.update(display, scroll, cameraRect, leaves, wind, windMultiplier)

        # display decor
        for chunkID in chunkIDs:
            for layer in self.chunks[chunkID]['decor']:
                for decor in self.chunks[chunkID]['decor'][layer]:
                    display.blit(textures[decor['sheet'][0]][decor['sheet'][1]][decor['sheet'][2]], (decor['renderpos'][0] - scroll[0], decor['renderpos'][1] - scroll[1]))

        if self.portal:
            self.portal.draw(cameraRect, display, scroll, particles, dt)
        if self.eventboard:
            self.eventboard.draw(display, scroll)

        for torch in self.torches:
            torch.update(display, scroll, cameraRect, particles, effects, sparks)

        player.update(display, scroll, self.getTileObjectsOfCurrentChunk(player.center, addNeighbors=True), particles, sparks, effects, dt)

        # display tiles
        for chunkID in chunkIDs:
            for layer in self.chunks[chunkID]['tiles']:
                for tile in self.chunks[chunkID]['tiles'][layer]:
                    display.blit(textures[tile['sheet'][0]][tile['sheet'][1]][tile['sheet'][2]], (tile['renderpos'][0] - scroll[0], tile['renderpos'][1] - scroll[1]))


        # draw boxes over the tiles
        """
        for tile in self.getTileObjectsOfCurrentChunk(player.center, addNeighbors=True):
            pygame.draw.rect(display, (255, 255, 255), (tile[0].x - scroll[0], tile[0].y - scroll[1], tile[0].w, tile[0].h))
        """

    def getTileObjectsOfCurrentChunk(self, objCenter, addNeighbors=False):

        # find the chunk player is in
        chunkx = objCenter[0] // (128 * self.scale)
        chunky = objCenter[1] // (128 * self.scale)
        playerChunkID = f'{chunkx};{chunky}'
        tiles = []
        
        # get the tiles from the current chunk
        if playerChunkID in self.chunks:
            chunkLayers = self.chunks[playerChunkID]['tiles']
            chunkTiles = []
            for layer in chunkLayers:
                chunkTiles.extend(chunkLayers[layer])
            tiles.extend([(pygame.Rect(tile['tilepos'], tile['size']), tile['type'], tile['sheet'][0]) for tile in chunkTiles])

        # check neighboring chunks
        if addNeighbors:
            neighbors = []
            for neighborx, neighbory in [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, 1), (1, 1), (-1, -1), (1, -1)]:
                newchunkx = chunkx + neighborx
                newchunky = chunky + neighbory
                newchunkID = f'{newchunkx};{newchunky}'
                if newchunkID in self.chunks:
                    if (objCenter[0] - (128  * self.scale * newchunkx + 64 * self.scale)) ** 2 + (objCenter[1] - (128 * self.scale * newchunky + 64 * self.scale)) ** 2 <= self.distance:
                        neighbors.append(newchunkID)

            for neighborID in neighbors:
                if neighborID in self.chunks:
                    chunkLayers = self.chunks[neighborID]['tiles']
                    chunkTiles = []
                    for layer in chunkLayers:
                        chunkTiles.extend(chunkLayers[layer])
                    tiles.extend([(pygame.Rect(tile['tilepos'], tile['size']), tile['type'], tile['sheet'][0]) for tile in chunkTiles])

        return tiles

    def getBounds(self):
        # find x range
        xMin = yMin = 1000
        xMax = yMax = -1000
        for chunkID in self.chunks:
            x = int(chunkID.split(';')[0])
            y = int(chunkID.split(';')[1])
            if x < xMin:
                xMin = x
            elif x > xMax:
                xMax = x
            if y < yMin:
                yMin = y
            elif y > yMax:
                yMax = y
        return xMin * self.chunkSize * self.tileSize - self.chunkSize * self.tileSize * 2, xMax * self.chunkSize * self.tileSize + self.chunkSize * self.tileSize * 2, yMin * self.chunkSize * self.tileSize - self.chunkSize * self.tileSize * 2, yMax * self.chunkSize * self.tileSize + self.chunkSize * self.tileSize * 2