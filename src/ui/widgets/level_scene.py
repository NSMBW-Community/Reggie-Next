from PyQt6 import QtCore, QtGui, QtWidgets

import globals_


class LevelScene(QtWidgets.QGraphicsScene):
    """
    GraphicsScene subclass for the level scene
    """

    def __init__(self, *args):
        QtWidgets.QGraphicsScene.__init__(self, *args)
        self.setBackgroundBrush(QtGui.QBrush(globals_.theme.color('bg')))

    def drawBackground(self, painter, rect):
        """
        Draws all visible tiles
        """
        QtWidgets.QGraphicsScene.drawBackground(self, painter, rect)
        if not hasattr(globals_.Area, 'layers'): return

        drawrect = QtCore.QRectF(rect.x() / 24, rect.y() / 24, rect.width() / 24 + 1, rect.height() / 24 + 1)
        isect = drawrect.intersects

        layer0 = []
        layer1 = []
        layer2 = []

        x1 = 1024
        y1 = 512
        x2 = 0
        y2 = 0

        # iterate through each object
        funcs = [layer0.append, layer1.append, layer2.append]
        show = [globals_.Layer0Shown, globals_.Layer1Shown, globals_.Layer2Shown]
        for layer, add, process in zip(globals_.Area.layers, funcs, show):
            if not process:
                continue

            for item in layer:
                if not isect(item.LevelRect):
                    continue

                add(item)
                x1 = min(x1, item.objx)
                x2 = max(x2, item.objx + item.width)
                y1 = min(y1, item.objy)
                y2 = max(y2, item.objy + item.height)

        width = x2 - x1
        height = y2 - y1

        # Assigning global variables to local variables for performance
        tiles = globals_.Tiles
        odefs = globals_.ObjectDefinitions
        unkn_tile = globals_.Overrides[globals_.OVERRIDE_UNKNOWN].getCurrentTile()

        # create and draw the tilemaps
        for layer_idx, layer in enumerate([layer2, layer1, layer0]):
            if not layer:
                continue

            tmap = [[None] * width for _ in range(height)]

            for item in layer:
                startx = item.objx - x1
                desty = item.objy - y1

                if odefs[item.tileset] is None or \
                        odefs[item.tileset][item.object_num] is None:
                    # This is an unknown object, so place -1 in the tile map.
                    for i, row in enumerate(item.objdata, desty):
                        destrow = tmap[i]
                        for j in range(startx, startx + len(row)):
                            destrow[j] = -1

                    continue

                # This is not an unkown object, so update the tile map normally.
                for i, row in enumerate(item.objdata, desty):
                    destrow = tmap[i]
                    for j, tile in enumerate(row, startx):
                        if tile > 0:
                            destrow[j] = tile

            painter.save()
            painter.translate(x1 * 24, y1 * 24)

            desty = -24
            for row in tmap:
                desty += 24
                destx = -24
                for tile in row:
                    destx += 24
                    if tile == -1:
                        # Draw unknown tiles
                        painter.drawPixmap(destx, desty, unkn_tile)
                    elif tile is not None:
                        # Only show collisions on layer 1 (i.e. layer_idx == 1)
                        pixmap = tiles[tile].getCurrentTile(layer_idx == 1)
                        painter.drawPixmap(destx, desty, pixmap)

            painter.restore()

    def getMainWindow(self):
        return globals_.mainWindow
