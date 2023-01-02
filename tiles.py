# done

################################################################################
################################################################################
################################################################################

from PyQt5 import QtCore, QtGui, QtWidgets
import os
import struct


import globals_
import spritelib as SLib
import archive


# Load libraries
from libs import lh
from libs import lz77
from libs import tpl

################################################################################
################################################################################
################################################################################

class ObjectDef:
    """
    Class for the object definitions
    """

    def __init__(self):
        """
        Constructor
        """
        self.width = 0
        self.height = 0
        self.rows = []

    def load(self, source, offset, tileoffset):
        """
        Load an object definition
        """
        i = offset
        row = []

        while True:
            cbyte = source[i]

            if cbyte == 0xFE:
                self.rows.append(row)
                i += 1
                row = []
            elif cbyte == 0xFF:
                break
            elif (cbyte & 0x80) != 0:
                row.append([cbyte, ])
                i += 1
            else:
                extra = source[i + 2]
                tile = [cbyte, source[i + 1] | ((extra & 3) << 8), extra >> 2]
                row.append(tile)
                i += 3

        # Newer has this any-tileset-slot hack in place, so let's add it here
        for row in self.rows:
            for tile in row:
                if len(tile) == 1 and tile[0] != 0:
                    tile[0] = (tile[0] & 0xFF) + tileoffset
                elif len(tile) == 3 and tile[1] != 0:
                    tile[1] = (tile[1] & 0xFF) + tileoffset


class TilesetTile:
    """
    Class that represents a single tile in a tileset
    """

    def __init__(self, main):
        """
        Initializes the TilesetTile
        """
        self.main = main
        self.isAnimated = False
        self.animFrame = 0
        self.animTiles = []
        self.collData = ()
        self.collOverlay = None

    def addAnimationData(self, data, reverse=False):
        """
        Applies Newer-style animation data to the tile
        """
        animTiles = []
        numberOfFrames = len(data) // 2048

        for frame in range(numberOfFrames):
            framedata = data[frame * 2048: (frame * 2048) + 2048]
            newdata = tpl.decodeRGB4A3(framedata, 32, 32, False)
            img = QtGui.QImage(newdata, 32, 32, 128, QtGui.QImage.Format_ARGB32)
            pix = QtGui.QPixmap.fromImage(img.copy(4, 4, 24, 24))
            animTiles.append(pix)

        if reverse:
            animTiles = list(reversed(animTiles))

        self.animTiles = animTiles
        self.isAnimated = True

        # This NSMBLib method crashes.
        ##padded = str(data)
        ##padded += ' ' * (0x80000 - len(data))
        ### It'll crash on this next line
        ##rgbdata = NSMBLib.decodeTileAnims(padded)
        ##tilesImg = QtGui.QImage(rgbdata, 32, (len(rgbdata)/4)/32, 32*4, QtGui.QImage.Format_ARGB32_Premultiplied)
        ##tilesPix = QtGui.QPixmap.fromImage(tilesImg)

        ##self.isAnimated = True
        ##self.animTiles = []
        ##self.animTiles.append(tilesPix.copy(0, 0, 31, 31).scaled(24, 24))

    def nextFrame(self):
        """
        Increments to the next frame
        """
        if not self.isAnimated:
            return

        self.animFrame += 1

        if self.animFrame == len(self.animTiles):
            self.animFrame = 0

    def resetAnimation(self):
        """
        Resets the animation frame
        """
        self.animFrame = 0

    def getCurrentTile(self, show_collision = False):
        """
        Returns the current tile based on the current animation frame
        """
        result = None
        if (not globals_.TilesetsAnimating) or (not self.isAnimated):
            result = self.main
        else:
            result = self.animTiles[self.animFrame]
        result = QtGui.QPixmap(result)

        if globals_.CollisionsShown and show_collision and (self.collOverlay is not None):
            p = QtGui.QPainter(result)
            p.drawPixmap(0, 0, self.collOverlay)
            del p

        return result

    def setCollisions(self, colldata):
        """
        Sets the collision data for this tile
        """
        self.collData = tuple(colldata)
        self.updateCollisionOverlay()

    def setQuestionCollisions(self):
        """
        Sets the collision data to that of a question block
        """
        self.setCollisions((0, 0, 0, 5, 0, 0, 0, 0))

    def setBrickCollisions(self):
        """
        Sets the collision data to that of a brick block
        """
        self.setCollisions((0, 0, 0, 0x10, 0, 0, 0, 0))

    def updateCollisionOverlay(self):
        """
        Updates the collisions overlay for this pixmap
        """
        # This is completely stolen from Puzzle. Only minor
        # changes have been made. Thanks, Treeki!
        CD = self.collData
        if CD[2] & 16:  # Red
            color = QtGui.QColor(255, 0, 0, 120)
        elif CD[5] == 1:  # Ice
            color = QtGui.QColor(0, 0, 255, 120)
        elif CD[5] == 2:  # Snow
            color = QtGui.QColor(0, 0, 255, 120)
        elif CD[5] == 3:  # Quicksand
            color = QtGui.QColor(128, 64, 0, 120)
        elif CD[5] == 4:  # Conveyor
            color = QtGui.QColor(128, 128, 128, 120)
        elif CD[5] == 5:  # Conveyor
            color = QtGui.QColor(128, 128, 128, 120)
        elif CD[5] == 6:  # Rope
            color = QtGui.QColor(128, 0, 255, 120)
        elif CD[5] == 7:  # Half Spike
            color = QtGui.QColor(128, 0, 255, 120)
        elif CD[5] == 8:  # Ledge
            color = QtGui.QColor(128, 0, 255, 120)
        elif CD[5] == 9:  # Ladder
            color = QtGui.QColor(128, 0, 255, 120)
        elif CD[5] == 10:  # Staircase
            color = QtGui.QColor(255, 0, 0, 120)
        elif CD[5] == 11:  # Carpet
            color = QtGui.QColor(255, 0, 0, 120)
        elif CD[5] == 12:  # Dust
            color = QtGui.QColor(128, 64, 0, 120)
        elif CD[5] == 13:  # Grass
            color = QtGui.QColor(0, 255, 0, 120)
        elif CD[5] == 14:  # Unknown
            color = QtGui.QColor(255, 0, 0, 120)
        elif CD[5] == 15:  # Beach Sand
            color = QtGui.QColor(128, 64, 0, 120)
        else:  # Brown?
            color = QtGui.QColor(64, 30, 0, 120)

        # Sets Brush style for fills
        if CD[2] & 4:  # Climbing Grid
            style = QtCore.Qt.DiagCrossPattern
        elif (CD[3] & 16) or (CD[3] & 4) or (CD[3] & 8):  # Breakable
            style = QtCore.Qt.Dense5Pattern
        else:
            style = QtCore.Qt.SolidPattern

        brush = QtGui.QBrush(color, style)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 128))
        collPix = QtGui.QPixmap(24, 24)
        collPix.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(collPix)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Paints shape based on other stuff
        if CD[3] & 32:  # Slope
            if CD[7] == 0:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 0)]))
            elif CD[7] == 1:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 2:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 12)]))
            elif CD[7] == 3:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 24)]))
            elif CD[7] == 4:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(24, 24)]))
            elif CD[7] == 5:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 10:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 0)]))
            elif CD[7] == 11:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(24, 18),
                                                    QtCore.QPoint(24, 24)]))
            elif CD[7] == 12:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(0, 18),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 13:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 6),
                                                    QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 14:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(0, 6),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 15:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 6),
                                                    QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 16:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(0, 6),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 17:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 18),
                                                    QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 18:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(0, 18),
                                                    QtCore.QPoint(0, 24)]))

        elif CD[3] & 64:  # Reverse Slope
            if CD[7] == 0:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 0)]))
            elif CD[7] == 1:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0)]))
            elif CD[7] == 2:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 12)]))
            elif CD[7] == 3:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 0)]))
            elif CD[7] == 4:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12)]))
            elif CD[7] == 5:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0)]))
            elif CD[7] == 10:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 0)]))
            elif CD[7] == 11:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 6)]))
            elif CD[7] == 12:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(0, 6)]))
            elif CD[7] == 13:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 18),
                                                    QtCore.QPoint(0, 12)]))
            elif CD[7] == 14:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(0, 18)]))
            elif CD[7] == 15:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 18),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 16:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(0, 18)]))
            elif CD[7] == 17:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 6),
                                                    QtCore.QPoint(0, 12)]))
            elif CD[7] == 18:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(0, 6)]))

        elif CD[2] & 8:  # Partial
            if CD[7] == 1:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(12, 12),
                                                    QtCore.QPoint(0, 12)]))
            elif CD[7] == 2:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(12, 12)]))
            elif CD[7] == 3:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(0, 12)]))
            elif CD[7] == 4:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(12, 12),
                                                    QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 5:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 6:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(0, 12)]))
            elif CD[7] == 7:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(12, 12),
                                                    QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 8:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(12, 12),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(12, 24)]))
            elif CD[7] == 9:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(12, 0)]))
            elif CD[7] == 10:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(12, 24)]))
            elif CD[7] == 11:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(12, 12),
                                                    QtCore.QPoint(0, 12)]))
            elif CD[7] == 12:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 13:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(12, 12),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 14:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(12, 12),
                                                    QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(0, 24)]))
            elif CD[7] == 15:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(0, 24)]))

        elif CD[2] & 0x20:  # Solid-on-bottom
            painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                QtCore.QPoint(24, 24),
                                                QtCore.QPoint(24, 18),
                                                QtCore.QPoint(0, 18)]))

            painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(15, 0),
                                                QtCore.QPoint(15, 12),
                                                QtCore.QPoint(18, 12),
                                                QtCore.QPoint(12, 17),
                                                QtCore.QPoint(6, 12),
                                                QtCore.QPoint(9, 12),
                                                QtCore.QPoint(9, 0)]))

        elif CD[2] & 0x80:  # Solid-on-top
            painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                QtCore.QPoint(24, 0),
                                                QtCore.QPoint(24, 6),
                                                QtCore.QPoint(0, 6)]))

            painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(15, 24),
                                                QtCore.QPoint(15, 12),
                                                QtCore.QPoint(18, 12),
                                                QtCore.QPoint(12, 7),
                                                QtCore.QPoint(6, 12),
                                                QtCore.QPoint(9, 12),
                                                QtCore.QPoint(9, 24)]))

        elif CD[2] & 16:  # Spikes
            if CD[7] == 0:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(0, 6)]))
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(0, 18)]))
            if CD[7] == 1:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(24, 6)]))
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(24, 18)]))
            if CD[7] == 2:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(6, 0)]))
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(18, 0)]))
            if CD[7] == 3:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(6, 24)]))
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(18, 24)]))
            if CD[7] == 4:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(18, 24),
                                                    QtCore.QPoint(6, 24)]))
            if CD[7] == 5:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(6, 0),
                                                    QtCore.QPoint(18, 0),
                                                    QtCore.QPoint(12, 24)]))
            if CD[7] == 6:
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(12, 24)]))

            ##        elif CD[3] & 4: # QBlock
            ##            if CD[7] == 0:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/FireF.png'))
            ##            if CD[7] == 1:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Star.png'))
            ##            if CD[7] == 2:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Coin.png'))
            ##            if CD[7] == 3:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Vine.png'))
            ##            if CD[7] == 4:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/1up.png'))
            ##            if CD[7] == 5:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Mini.png'))
            ##            if CD[7] == 6:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Prop.png'))
            ##            if CD[7] == 7:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/Peng.png'))
            ##            if CD[7] == 8:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'QBlock/IceF.png'))
            ##
            ##        elif CD[3] & 2: # Coin
            ##            if CD[7] == 0:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Coin/Coin.png'))
            ##            if CD[7] == 4:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Coin/POW.png'))
            ##
            ##        elif CD[3] & 8: # Exploder
            ##            if CD[7] == 1:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Explode/Stone.png'))
            ##            if CD[7] == 2:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Explode/Wood.png'))
            ##            if CD[7] == 3:
            ##                painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Explode/Red.png'))
            ##
            ##        elif CD[1] & 2: # Falling
            ##            painter.drawPixmap(option.rect, QtGui.QPixmap(path + 'Prop/Fall.png'))

            #                elif CD[5] == 4 or 5: # Conveyor
            #                    d

        elif (CD[3] & 1) or (CD[3] in (5, 0x10)) or (CD[3] & 4) or (CD[3] & 8):  # Solid, question or brick
            painter.drawRect(0, 0, 24, 24)

        else:  # No fill
            pass

        self.collOverlay = collPix


def RenderObject(tileset, objnum, width, height, fullslope=False):
    """
    Render a tileset object into an array
    """
    # allocate an array
    dest = [[0] * width for _ in range(height)]

    # ignore non-existent objects
    try:
        tileset_defs = globals_.ObjectDefinitions[tileset]
    except:
        tileset_defs = None

    if tileset_defs is None:
        return dest

    try:
        obj = tileset_defs[objnum]
    except:
        obj = None

    if obj is None or not obj.rows:
        return dest

    # diagonal objects are rendered differently
    if (obj.rows[0][0][0] & 0x80) != 0:
        RenderDiagonalObject(dest, obj, width, height, fullslope)
        return dest

    # standard object
    repeatFound = False
    beforeRepeat = []
    inRepeat = []
    afterRepeat = []

    for row in obj.rows:
        if not row: continue

        if (row[0][0] & 2) != 0:
            repeatFound = True
            inRepeat.append(row)
        else:
            if repeatFound:
                afterRepeat.append(row)
            else:
                beforeRepeat.append(row)

    bc = len(beforeRepeat)
    ic = len(inRepeat)
    ac = len(afterRepeat)
    if ic == 0:
        for y in range(height):
            RenderStandardRow(dest[y], beforeRepeat[y % bc], y, width)
    else:
        afterthreshold = height - ac - 1
        for y in range(height):
            if y < bc:
                RenderStandardRow(dest[y], beforeRepeat[y], y, width)
            elif y > afterthreshold:
                RenderStandardRow(dest[y], afterRepeat[y - height + ac], y, width)
            else:
                RenderStandardRow(dest[y], inRepeat[(y - bc) % ic], y, width)

    return dest


def RenderStandardRow(dest, row, y, width):
    """
    Render a row from an object
    """
    repeatFound = False
    beforeRepeat = []
    inRepeat = []
    afterRepeat = []

    for tile in row:
        tiling = (tile[0] & 1) != 0

        if tiling:
            repeatFound = True
            inRepeat.append(tile)
        else:
            if repeatFound:
                afterRepeat.append(tile)
            else:
                beforeRepeat.append(tile)

    bc = len(beforeRepeat)
    ic = len(inRepeat)
    ac = len(afterRepeat)
    if ic == 0:
        for x in range(width):
            dest[x] = beforeRepeat[x % bc][1]
    else:
        afterthreshold = width - ac - 1
        for x in range(width):
            if x < bc:
                dest[x] = beforeRepeat[x][1]
            elif x > afterthreshold:
                dest[x] = afterRepeat[x - width + ac][1]
            else:
                dest[x] = inRepeat[(x - bc) % ic][1]


def RenderDiagonalObject(dest, obj, width, height, fullslope):
    """
    Render a diagonal object
    """
    # set all to empty tiles
    for row in dest:
        for x in range(width):
            row[x] = -1

    # get sections
    mainBlock, subBlock = GetSlopeSections(obj)
    cbyte = obj.rows[0][0][0]

    # get direction
    goLeft = ((cbyte & 1) != 0)
    goDown = ((cbyte & 2) != 0)

    # base the amount to draw by seeing how much we can fit in each direction
    if fullslope:
        drawAmount = max(height // len(mainBlock), width // len(mainBlock[0]))
    else:
        drawAmount = min(height // len(mainBlock), width // len(mainBlock[0]))

    # if it's not goingLeft and not goingDown:
    if not goLeft and not goDown:
        # slope going from SW => NE
        # start off at the bottom left
        x = 0
        y = height - len(mainBlock) - (0 if subBlock is None else len(subBlock))
        xi = len(mainBlock[0])
        yi = -len(mainBlock)

    # ... and if it's goingLeft and not goingDown:
    elif goLeft and not goDown:
        # slope going from SE => NW
        # start off at the top left
        x = 0
        y = 0
        xi = len(mainBlock[0])
        yi = len(mainBlock)

    # ... and if it's not goingLeft but it's goingDown:
    elif not goLeft and goDown:
        # slope going from NW => SE
        # start off at the top left
        x = 0
        y = (0 if subBlock is None else len(subBlock))
        xi = len(mainBlock[0])
        yi = len(mainBlock)

    # ... and finally, if it's goingLeft and goingDown:
    else:
        # slope going from SW => NE
        # start off at the bottom left
        x = 0
        y = height - len(mainBlock)
        xi = len(mainBlock[0])
        yi = -len(mainBlock)

    # finally draw it
    for i in range(drawAmount):
        PutObjectArray(dest, x, y, mainBlock, width, height)
        if subBlock is not None:
            xb = x
            if goLeft: xb = x + len(mainBlock[0]) - len(subBlock[0])
            if goDown:
                PutObjectArray(dest, xb, y - len(subBlock), subBlock, width, height)
            else:
                PutObjectArray(dest, xb, y + len(mainBlock), subBlock, width, height)
        x += xi
        y += yi


def PutObjectArray(dest, xo, yo, block, width, height):
    """
    Places a tile array into an object
    """
    # for y in range(yo,min(yo+len(block),height)):
    for y in range(yo, yo + len(block)):
        if y < 0: continue
        if y >= height: continue
        drow = dest[y]
        srow = block[y - yo]
        # for x in range(xo,min(xo+len(srow),width)):
        for x in range(xo, xo + len(srow)):
            if x < 0: continue
            if x >= width: continue
            drow[x] = srow[x - xo][1]


def GetSlopeSections(obj):
    """
    Sorts the slope data into sections
    """
    sections = []
    currentSection = None

    for row in obj.rows:
        if row and (row[0][0] & 0x80) != 0:  # begin new section
            if currentSection is not None:
                sections.append(CreateSection(currentSection))
            currentSection = []
        currentSection.append(row)

    if currentSection is not None:  # end last section
        sections.append(CreateSection(currentSection))

    if len(sections) == 1:
        return (sections[0], None)
    else:
        return (sections[0], sections[1])


def CreateSection(rows):
    """
    Create a slope section
    """
    # calculate width
    width = 0
    for row in rows:
        thiswidth = CountTiles(row)
        if width < thiswidth: width = thiswidth

    # create the section
    section = []
    for row in rows:
        drow = [0] * width
        x = 0
        for tile in row:
            if (tile[0] & 0x80) == 0:
                drow[x] = tile
                x += 1
        section.append(drow)

    return section


def CountTiles(row):
    """
    Counts the amount of real tiles in an object row
    """
    res = 0
    for tile in row:
        if (tile[0] & 0x80) == 0:
            res += 1
    return res


def CreateTilesets():
    """
    Blank out the tileset arrays
    """
    globals_.Tiles = [None] * 0x200 * 4
    globals_.Tiles += globals_.Overrides
    globals_.TilesetFilesLoaded = [None, None, None, None]
    globals_.TilesetAnimTimer = QtCore.QTimer()
    globals_.TilesetAnimTimer.timeout.connect(IncrementTilesetFrame)
    globals_.TilesetAnimTimer.start(90)
    globals_.ObjectDefinitions = [None] * 4
    SLib.Tiles = globals_.Tiles


def LoadTileset(idx, name, reload_=False):
    """
    Load in a tileset into a specific slot
    """
    if not name:
        return False

    # find the tileset path
    tileset_paths = reversed(globals_.gamedef.GetTexturePaths())

    found = False
    for path in tileset_paths:
        if path is None: break

        arcname = os.path.join(path, name + ".arc.LH")

        # Prioritise .arc.LH over regular .arc, just like the game does.
        if os.path.isfile(arcname):
            compressed = True
            found = True
            break

        arcname = os.path.splitext(arcname)[0]  # strip away the .LH suffix
        if os.path.isfile(arcname):
            compressed = False
            found = True
            break

    # warning if not found
    if not found:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingTileset', 0),
                                      globals_.trans.string('Err_MissingTileset', 1, '[file]', name))
        return False

    # if this file's already loaded, return
    if globals_.TilesetFilesLoaded[idx] == arcname and not reload_: return

    # get the data
    with open(arcname, 'rb') as fileobj:
        arcdata = fileobj.read()

    if compressed:
        if (arcdata[0] & 0xF0) == 0x40:  # If LH-compressed
            try:
                arcdata = lh.UncompressLH(arcdata)
            except IndexError:
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Decompress', 0),
                                              globals_.trans.string('Err_Decompress', 1, '[file]', name))
                return False

    arc = archive.U8.load(arcdata)

    def exists(fn):
        nonlocal arc
        try:
            arc[fn]
        except:
            return False
        return True

    # decompress the textures
    found = exists('BG_tex/%s_tex.bin.LZ' % name)
    found2 = exists('BG_chk/d_bgchk_%s.bin' % name)

    if found and found2:
        comptiledata = arc['BG_tex/%s_tex.bin.LZ' % name]
        colldata = arc['BG_chk/d_bgchk_%s.bin' % name]
    else:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_CorruptedTilesetData', 0),
                                      globals_.trans.string('Err_CorruptedTilesetData', 1, '[file]', name))
        return False

    # load in the textures
    img = LoadTexture_NSMBW(lz77.UncompressLZ77(comptiledata))

    # Divide it into individual tiles and
    # add collisions at the same time
    dest = QtGui.QPixmap.fromImage(img)
    sourcex = 4
    sourcey = 4
    tileoffset = idx * 256
    for i in range(tileoffset, tileoffset + 256):
        T = TilesetTile(dest.copy(sourcex, sourcey, 24, 24))
        T.setCollisions(struct.unpack_from('>8B', colldata, (i - tileoffset) * 8))
        globals_.Tiles[i] = T
        sourcex += 32
        if sourcex >= 1024:
            sourcex = 4
            sourcey += 32

    # Load the tileset animations, if there are any
    tileoffset = idx * 256
    row = 0
    col = 0

    containsConveyor = ['Pa1_toride', 'Pa1_toride_sabaku', 'Pa1_toride_kori', 'Pa1_toride_yogan', 'Pa1_toride_soto']

    isAnimated, prefix = CheckTilesetAnimated(arc)

    for i in range(tileoffset,tileoffset+256):
        if idx == 0:
            if globals_.Tiles[i].collData[3] == 5:
                fn = 'BG_tex/hatena_anime.bin'
                found = exists(fn)

                if found:
                    globals_.Tiles[i].addAnimationData(arc[fn])

            elif globals_.Tiles[i].collData[3] == 0x10:
                fn = 'BG_tex/block_anime.bin'
                found = exists(fn)

                if found:
                    globals_.Tiles[i].addAnimationData(arc[fn])

            elif globals_.Tiles[i].collData[7] == 0x28:
                fn = 'BG_tex/tuka_coin_anime.bin'
                found = exists(fn)

                if found:
                    globals_.Tiles[i].addAnimationData(arc[fn])

        elif idx == 1 and name in containsConveyor:
            for x in range(2):
                if i == 320+x*16:
                    fn = 'BG_tex/belt_conveyor_L_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn], True)

                elif i == 321+x*16:
                    fn = 'BG_tex/belt_conveyor_M_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn], True)

                elif i == 322+x*16:
                    fn = 'BG_tex/belt_conveyor_R_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn], True)

                elif i == 323+x*16:
                    fn = 'BG_tex/belt_conveyor_L_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn])

                elif i == 324+x*16:
                    fn = 'BG_tex/belt_conveyor_M_anime.bin'
                    found = exists(fn)

                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn])

                elif i == 325+x*16:
                    fn = 'BG_tex/belt_conveyor_R_anime.bin'
                    found = exists(fn)
                    if found:
                        globals_.Tiles[i].addAnimationData(arc[fn])

        if isAnimated:
            filenames = []
            filenames.append('%s_%d%s%s.bin' % (prefix, idx, hex(row)[2].lower(), hex(col)[2].lower()))
            filenames.append('%s_%d%s%s.bin' % (prefix, idx, hex(row)[2].upper(), hex(col)[2].upper()))

            if filenames[0] == filenames[1]:
                item = filenames[0]
                filenames = []
                filenames.append(item)

            for fn in filenames:
                fn = 'BG_tex/' + fn
                found = exists(fn)

                if found:
                    globals_.Tiles[i].addAnimationData(arc[fn])

        col += 1

        if col == 16:
            col = 0
            row += 1

    # load the object definitions
    defs = [None] * 256

    indexfile = arc['BG_unt/%s_hd.bin' % name]
    deffile = arc['BG_unt/%s.bin' % name]
    objcount = len(indexfile) // 4
    indexstruct = struct.Struct('>HBB')

    for i in range(objcount):
        data = indexstruct.unpack_from(indexfile, i << 2)
        obj = ObjectDef()
        obj.width = data[1]
        obj.height = data[2]
        obj.load(deffile, data[0], tileoffset)
        defs[i] = obj

    globals_.ObjectDefinitions[idx] = defs

    ProcessOverrides(idx, name)

    # Keep track of this filepath
    globals_.TilesetFilesLoaded[idx] = arcname

    # Add Tiles to spritelib
    SLib.Tiles = globals_.Tiles

    return True


def LoadTexture_NSMBW(tiledata):
    data = tpl.decodeRGB4A3(tiledata, 1024, 256, False)
    img = QtGui.QImage(data, 1024, 256, 4096, QtGui.QImage.Format_ARGB32)
    return img


def IncrementTilesetFrame():
    """
    Moves each tileset to the next frame
    """
    if not globals_.TilesetsAnimating: return
    for tile in globals_.Tiles:
        if tile is not None: tile.nextFrame()
    globals_.mainWindow.scene.update()
    globals_.mainWindow.objPicker.update()


def CheckTilesetAnimated(tileset):
    """Checks if a tileset contains Newer-style animations, and if so, returns
    (True, prefix) where prefix is the animation prefix. If not, (False, None).
    tileset should be a Wii.py U8 object."""
    # Find the animation files, if any
    excludes = (
        'block_anime.bin',
        'hatena_anime.bin',
        'tuka_coin_anime.bin',
    )
    texFiles = tileset['BG_tex']
    animFiles = []
    for f in texFiles:
        # Determine if it's likely an animation file
        if f.lower() in excludes: continue
        if f[-4:].lower() != '.bin': continue
        namelen = len(f)
        if namelen == 9:
            if f[1] != '_': continue
            if f[2] not in '0123': continue
            if f[3].lower() not in '0123456789abcdef': continue
            if f[4].lower() not in '0123456789abcdef': continue
        elif namelen == 10:
            if f[2] != '_': continue
            if f[3] not in '0123': continue
            if f[4].lower() not in '0123456789abcdef': continue
            if f[5].lower() not in '0123456789abcdef': continue
        animFiles.append(f)

    # Quit if there's no animation
    if not animFiles:
        return False, None
    else:
        # This makes so many assumptions
        fn = animFiles[0]
        prefix = fn[0] if len(fn) == 9 else fn[:2]
        return True, prefix


def UnloadTileset(idx):
    """
    Unload the tileset from a specific slot
    """
    tileoffset = idx * 256
    globals_.Tiles[tileoffset:tileoffset + 256] = [None] * 256
    globals_.ObjectDefinitions[idx] = [None] * 256
    globals_.TilesetFilesLoaded[idx] = None


def ProcessOverrides(idx, name):
    """
    Load overridden tiles if there are any
    """

    if globals_.OverriddenTilesets is None:
        raise ValueError("Overridden tilesets not yet initialised")

    def overlay(base, overlay):
        img = QtGui.QPixmap(base.width(), base.height())
        img.fill(QtCore.Qt.transparent)

        p = QtGui.QPainter(img)
        p.drawPixmap(0, 0, base)
        p.drawPixmap(0, 0, overlay)

        return img

    tsidx = globals_.OverriddenTilesets

    # Automatically apply the Pa0 override if the tileset name starts with 'Pa0_'
    # and the tileset is not excluded by setting 'override="no-Pa0"'
    if name in tsidx["Pa0"] or (name.startswith("Pa0_") and name not in tsidx["no-Pa0"]):
        defs = globals_.ObjectDefinitions[idx]
        t = globals_.Tiles

        # 0: invisibg
        ## Items:
        # 1:coin, 2:fire, 3:star, 4:stoi, 5:vine,
        # 6:spri, 7:mini, 8:prop, 9:ping, 10:yosh,
        # 11:ice, 12:10c, 13:1up,

        # Invisible blocks
        invisiblocks = (3, 4, 5, 6, 7, 8, 9, 10, 13)
        replacement = (1, 2, 3, 13, 5, 7, 8, 9, 11)
        # coin, fire, star, 1up, vine, mini, prop, ping, ice
        baseblock = globals_.Overrides_safe[0].main
        for i, replace in zip(invisiblocks, replacement):
            t[i].main = overlay(baseblock, globals_.Overrides_safe[replace].main)

        # Question and brick blocks
        # these don't have their own tiles so we have to do them by objects
        rangeA, rangeB = range(39, 49), range(27, 38)
        replace = 2048 + 10
        baseblock = t[defs[39].rows[0][0][1]].main

        # question blocks
        for i, a in zip(rangeA, range(2, 12)):
            t[replace].main = overlay(baseblock, globals_.Overrides_safe[a].main)
            defs[i].rows[0][0] = (0, replace, 0)
            replace += 1

        replace += 1
        baseblock = t[defs[26].rows[0][0][1]].main
        # brick block
        for i, a in zip(rangeB, (1, 12, 2, 3, 13, 5, 7, 8, 9, 10, 11)):
            t[replace].main = overlay(baseblock, globals_.Overrides_safe[a].main)
            defs[i].rows[0][0] = (0, replace, 0)
            replace += 1

        # now the extra stuff (invisible collisions etc)
        # @ row i, col j => globals_.Overrides[25 * i + j]

        t[1].main = globals_.Overrides[26 * 4].main  # solid
        t[2].main = globals_.Overrides[26 + 10].main  # vine stopper
        t[11].main = globals_.Overrides[26 * 3 + 13].main  # jumpthrough platform
        t[12].main = globals_.Overrides[26 * 3 + 12].main  # 16x8 roof platform

        t[16].main = globals_.Overrides[26 * 4 + 11].main  # 1x1 slope going up
        t[17].main = globals_.Overrides[26 * 4 + 12].main  # 1x1 slope going down
        t[18].main = globals_.Overrides[26 * 4 + 1].main  # 2x1 slope going up (part 1)
        t[19].main = globals_.Overrides[26 * 4 + 2].main  # 2x1 slope going up (part 2)
        t[20].main = globals_.Overrides[26 * 4 + 3].main  # 2x1 slope going down (part 1)
        t[21].main = globals_.Overrides[26 * 4 + 4].main  # 2x1 slope going down (part 2)
        t[22].main = globals_.Overrides[26 * 4 + 21].main  # 4x1 slope going up (part 1)
        t[23].main = globals_.Overrides[26 * 4 + 22].main  # 4x1 slope going up (part 2)
        t[24].main = globals_.Overrides[26 * 4 + 23].main  # 4x1 slope going up (part 3)
        t[25].main = globals_.Overrides[26 * 4 + 24].main  # 4x1 slope going up (part 4)
        t[26].main = globals_.Overrides[26 * 4 + 25].main  # 4x1 slope going down (part 1)
        t[27].main = globals_.Overrides[26 * 4 - 3].main   # 4x1 slope going down (part 2)
        t[28].main = globals_.Overrides[26 * 4 - 2].main   # 4x1 slope going down (part 3)
        t[29].main = globals_.Overrides[26 * 4 - 1].main   # 4x1 slope going down (part 4)
        t[30].main = globals_.Overrides[1].main    # coin

        t[32].main = globals_.Overrides[26 * 4 + 9].main  # 1x1 roof going down
        t[33].main = globals_.Overrides[26 * 4 + 10].main  # 1x1 roof going up
        t[34].main = globals_.Overrides[26 * 4 + 5].main  # 2x1 roof going down (part 1)
        t[35].main = globals_.Overrides[26 * 4 + 6].main  # 2x1 roof going down (part 2)
        t[36].main = globals_.Overrides[26 * 4 + 7].main  # 2x1 roof going up (part 1)
        t[37].main = globals_.Overrides[26 * 4 + 8].main  # 2x1 roof going up (part 2)
        t[38].main = globals_.Overrides[26 * 4 + 13].main  # 4x1 roof going down (part 1)
        t[39].main = globals_.Overrides[26 * 4 + 14].main  # 4x1 roof going down (part 2)
        t[40].main = globals_.Overrides[26 * 4 + 15].main  # 4x1 roof going down (part 3)
        t[41].main = globals_.Overrides[26 * 4 + 16].main  # 4x1 roof going down (part 4)
        t[42].main = globals_.Overrides[26 * 4 + 17].main  # 4x1 roof going up (part 1)
        t[43].main = globals_.Overrides[26 * 4 + 18].main  # 4x1 roof going up (part 2)
        t[44].main = globals_.Overrides[26 * 4 + 19].main  # 4x1 roof going up (part 3)
        t[45].main = globals_.Overrides[26 * 4 + 20].main  # 4x1 roof going up (part 4)
        t[46].main = globals_.Overrides[26 + 11].main  # P-switch coins

        t[53].main = globals_.Overrides[26 + 12].main  # donut lift
        t[61].main = globals_.Overrides[26 + 9].main  # multiplayer coin
        t[63].main = globals_.Overrides[26 * 2 + 13].main  # instant death tile

    elif name in tsidx["Flowers"] or name in tsidx["Forest Flowers"]:
        # flowers
        t = globals_.Tiles
        t[416].main = globals_.Overrides_safe[26 + 4].main  # grass
        t[417].main = globals_.Overrides_safe[26 + 5].main
        t[418].main = globals_.Overrides[26 + 6].main
        t[419].main = globals_.Overrides[26 + 7].main
        t[420].main = globals_.Overrides[26 + 8].main

        if name in tsidx["Flowers"]:
            t[432].main = globals_.Overrides[26 * 2 + 9].main  # flowers
            t[433].main = globals_.Overrides[26 * 2 + 10].main  # flowers
            t[434].main = globals_.Overrides[26 * 2 + 11].main  # flowers

            t[448].main = globals_.Overrides[26 * 2 + 6].main  # flowers on grass
            t[449].main = globals_.Overrides[26 * 2 + 7].main
            t[450].main = globals_.Overrides[26 * 2 + 8].main
        elif name in tsidx["Forest Flowers"]:
            # forest flowers
            t[432].main = globals_.Overrides[26 * 3 + 9].main  # flowers
            t[433].main = globals_.Overrides[26 * 3 + 10].main  # flowers
            t[434].main = globals_.Overrides[26 * 3 + 11].main  # flowers

            t[448].main = globals_.Overrides[26 * 3 + 6].main  # flowers on grass
            t[449].main = globals_.Overrides[26 * 3 + 7].main
            t[450].main = globals_.Overrides[26 * 3 + 8].main

    elif name in tsidx["Lines"] or name in tsidx["Full Lines"]:
        # These are the line guides
        # normal lines have fewer though

        t = globals_.Tiles

        # use Overrides_safe here because the beginning of Overrides is overwritten
        t[768].main = globals_.Overrides_safe[26].main  # horizontal line
        t[769].main = globals_.Overrides_safe[26 + 1].main  # vertical line
        t[770].main = globals_.Overrides_safe[26 + 2].main  # bottom-right corner
        t[771].main = globals_.Overrides_safe[26 + 3].main  # top-left corner

        t[784].main = globals_.Overrides[26 * 2].main  # left red blob (part 1)
        t[785].main = globals_.Overrides[26 * 2 + 1].main  # top red blob (part 1)
        t[786].main = globals_.Overrides[26 * 2 + 2].main  # top red blob (part 2)
        t[787].main = globals_.Overrides[26 * 2 + 3].main  # right red blob (part 1)
        t[788].main = globals_.Overrides[26 * 2 + 4].main  # top-left red blob
        t[789].main = globals_.Overrides[26 * 2 + 5].main  # top-right red blob

        t[800].main = globals_.Overrides[26 * 3].main  # left red blob (part 2)
        t[801].main = globals_.Overrides[26 * 3 + 1].main  # bottom red blob (part 1)
        t[802].main = globals_.Overrides[26 * 3 + 2].main  # bottom red blob (part 2)
        t[803].main = globals_.Overrides[26 * 3 + 3].main  # right red blob (part 2)
        t[804].main = globals_.Overrides[26 * 3 + 4].main  # bottom-left red blob
        t[805].main = globals_.Overrides[26 * 3 + 5].main  # bottom-right red blob

        # Those are all for normal lines
        if name in tsidx["Lines"]: return

        t[816].main = globals_.Overrides_safe[14].main  # 1x2 diagonal going up (top edge)
        t[817].main = globals_.Overrides_safe[15].main  # 1x2 diagonal going down (top edge)

        t[832].main = globals_.Overrides[26 + 14].main  # 1x2 diagonal going up (part 1)
        t[833].main = globals_.Overrides[26 + 15].main  # 1x2 diagonal going down (part 1)
        t[834].main = globals_.Overrides[26 * 2 + 19].main  # 1x1 diagonal going up
        t[835].main = globals_.Overrides[26 * 2 + 20].main  # 1x1 diagonal going down
        #t[836].main = globals_.Overrides[ + 1058].main  # 2x1 diagonal going up (part 1) nothing
        t[837].main = globals_.Overrides[20].main  # 2x1 diagonal going up (part 2)
        t[838].main = globals_.Overrides_safe[21].main  # 2x1 diagonal going down (part 1)
        #t[839].main = globals_.Overrides[ + 1061].main  # 2x1 diagonal going down (part 2) nothing

        t[848].main = globals_.Overrides[26 * 2 + 14].main  # 1x2 diagonal going up (part 2)
        t[849].main = globals_.Overrides[26 * 2 + 15].main  # 1x2 diagonal going down (part 2)
        t[850].main = globals_.Overrides[26 * 3 + 14].main  # 1x1 diagonal going up
        t[851].main = globals_.Overrides[26 * 3 + 15].main  # 1x1 diagonal going down
        t[852].main = globals_.Overrides[26 + 19].main  # 2x1 diagonal going up (part 1)
        t[853].main = globals_.Overrides[26 + 20].main  # 2x1 diagonal going up (part 2)
        t[854].main = globals_.Overrides[26 + 21].main  # 2x1 diagonal going down (part 1)
        t[855].main = globals_.Overrides[26 + 22].main  # 2x1 diagonal going down (part 2)

        t[866].main = globals_.Overrides[26 * 3 + 17].main  # big circle piece 1st row
        t[867].main = globals_.Overrides[26 * 3 + 18].main  # big circle piece 1st row
        t[870].main = globals_.Overrides_safe[17].main  # medium circle piece 1st row
        t[871].main = globals_.Overrides_safe[18].main  # medium circle piece 1st row

        t[881].main = globals_.Overrides[26 * 3 + 20].main  # big circle piece 2nd row
        t[882].main = globals_.Overrides_safe[23].main  # big circle piece 2nd row
        t[883].main = globals_.Overrides_safe[24].main  # big circle piece 2nd row
        t[884].main = globals_.Overrides_safe[25].main  # big circle piece 2nd row
        t[885].main = globals_.Overrides[26 + 16].main  # medium circle piece 2nd row
        t[886].main = globals_.Overrides[26 + 17].main  # medium circle piece 2nd row
        t[887].main = globals_.Overrides[26 + 18].main  # medium circle piece 2nd row
        t[888].main = globals_.Overrides[26 + 13].main  # small circle

        t[896].main = globals_.Overrides[26 * 2 + 21].main  # big circle piece 3rd row
        t[897].main = globals_.Overrides[26 * 2 + 22].main  # big circle piece 3rd row
        t[900].main = globals_.Overrides[26 * 2 + 24].main  # big circle piece 3rd row
        t[901].main = globals_.Overrides[26 * 2 + 16].main  # medium circle piece 3rd row
        t[902].main = globals_.Overrides[26 * 2 + 17].main  # medium circle piece 3rd row
        t[903].main = globals_.Overrides[26 * 2 + 18].main  # medium circle piece 3rd row

        t[912].main = globals_.Overrides[26 * 3 + 21].main  # big circle piece 4th row
        t[913].main = globals_.Overrides[26 * 3 + 22].main  # big circle piece 4th row
        t[916].main = globals_.Overrides[26 * 2 + 25].main  # big circle piece 4th row

        t[929].main = globals_.Overrides[26 * 2 + 23].main  # big circle piece 5th row
        t[930].main = globals_.Overrides[26 + 23].main  # big circle piece 5th row
        t[931].main = globals_.Overrides[26 + 24].main  # big circle piece 5th row
        t[932].main = globals_.Overrides[26 + 25].main  # big circle piece 5th row

    elif name in tsidx["Minigame Lines"]:
        t = globals_.Tiles

        t[832].main = globals_.Overrides_safe[26].main  # horizontal line
        t[833].main = globals_.Overrides_safe[26 + 2].main  # bottom-right corner
        t[834].main = globals_.Overrides_safe[26].main  # horizontal line

        t[848].main = globals_.Overrides_safe[26 + 1].main  # vertical line
        t[849].main = globals_.Overrides_safe[26 + 1].main  # vertical line
        t[850].main = globals_.Overrides_safe[26 + 3].main  # top-left corner

        t[835].main = globals_.Overrides[26 * 2].main  # left red blob (part 1)
        t[836].main = globals_.Overrides[26 * 2 + 1].main  # top red blob (part 1)
        t[837].main = globals_.Overrides[26 * 2 + 2].main  # top red blob (part 2)
        t[838].main = globals_.Overrides[26 * 2 + 3].main  # right red blob (part 1)

        t[851].main = globals_.Overrides[26 * 3].main  # left red blob (part 2)
        t[852].main = globals_.Overrides[26 * 3 + 1].main  # bottom red blob (part 1)
        t[853].main = globals_.Overrides[26 * 3 + 2].main  # bottom red blob (part 2)
        t[854].main = globals_.Overrides[26 * 3 + 3].main  # right red blob (part 2)

        t[866].main = globals_.Overrides[26 * 3 + 17].main  # big circle piece 1st row
        t[867].main = globals_.Overrides[26 * 3 + 18].main  # big circle piece 1st row
        t[870].main = globals_.Overrides_safe[17].main  # medium circle piece 1st row
        t[871].main = globals_.Overrides_safe[18].main  # medium circle piece 1st row

        t[881].main = globals_.Overrides[26 * 3 + 20].main  # big circle piece 2nd row
        t[882].main = globals_.Overrides_safe[23].main  # big circle piece 2nd row
        t[883].main = globals_.Overrides_safe[24].main  # big circle piece 2nd row
        t[884].main = globals_.Overrides_safe[25].main  # big circle piece 2nd row
        t[885].main = globals_.Overrides[26 + 16].main  # medium circle piece 2nd row
        t[886].main = globals_.Overrides[26 + 17].main  # medium circle piece 2nd row
        t[887].main = globals_.Overrides[26 + 18].main  # medium circle piece 2nd row

        t[896].main = globals_.Overrides[26 * 2 + 21].main  # big circle piece 3rd row
        t[897].main = globals_.Overrides[26 * 2 + 22].main  # big circle piece 3rd row
        t[900].main = globals_.Overrides[26 * 2 + 24].main  # big circle piece 3rd row
        t[901].main = globals_.Overrides[26 * 2 + 16].main  # medium circle piece 3rd row
        t[902].main = globals_.Overrides[26 * 2 + 17].main  # medium circle piece 3rd row
        t[903].main = globals_.Overrides[26 * 2 + 18].main  # medium circle piece 3rd row

        t[912].main = globals_.Overrides[26 * 3 + 21].main  # big circle piece 4th row
        t[913].main = globals_.Overrides[26 * 3 + 22].main  # big circle piece 4th row
        t[916].main = globals_.Overrides[26 * 2 + 25].main  # big circle piece 4th row

        t[929].main = globals_.Overrides[26 * 2 + 23].main  # big circle piece 5th row
        t[930].main = globals_.Overrides[26 + 23].main  # big circle piece 5th row
        t[931].main = globals_.Overrides[26 + 24].main  # big circle piece 5th row
        t[932].main = globals_.Overrides[26 + 25].main  # big circle piece 5th row


def LoadOverrides():
    """
    Load overrides
    """
    globals_.Overrides = [None] * (5 * 26)
    globals_.Overrides_safe = [None] * (5 * 26)
    globals_.OVERRIDE_UNKNOWN = 2 * 26 + 12

    OverrideBitmap = QtGui.QPixmap(globals_.theme.overridesFile)
    idx = 0
    xcount = OverrideBitmap.width() // 24
    ycount = OverrideBitmap.height() // 24
    sourcex = 0
    sourcey = 0

    for y in range(ycount):
        for x in range(xcount):
            bmp = OverrideBitmap.copy(sourcex, sourcey, 24, 24)
            globals_.Overrides[idx] = TilesetTile(bmp)
            globals_.Overrides_safe[idx] = TilesetTile(bmp)

            # Set collisions if it's a brick or question
            if y <= 4:
                if 8 < x < 20:
                    globals_.Overrides[idx].setQuestionCollisions()
                    globals_.Overrides_safe[idx].setQuestionCollisions()
                elif 20 <= x < 32:
                    globals_.Overrides[idx].setBrickCollisions()
                    globals_.Overrides_safe[idx].setBrickCollisions()

            idx += 1
            sourcex += 24
        sourcex = 0
        sourcey += 24

