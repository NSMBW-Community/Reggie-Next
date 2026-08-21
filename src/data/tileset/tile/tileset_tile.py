from PyQt6 import QtCore, QtGui

import globals_
from libs import tpl


class TilesetTile:
    """
    Class that represents a single tile in a tileset
    """

    def __init__(self, main: QtGui.QPixmap):
        """
        Initializes the TilesetTile
        """
        self.main = main
        self.isAnimated = False
        self.animFrame = 0
        self.animTiles = []
        self.collData = (0, 0, 0, 0, 0, 0, 0, 0)
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
            img = QtGui.QImage(newdata, 32, 32, 128, QtGui.QImage.Format.Format_ARGB32)
            pix = QtGui.QPixmap.fromImage(img.copy(4, 4, 24, 24))
            animTiles.append(pix)

        if reverse:
            animTiles = list(reversed(animTiles))

        self.animTiles = animTiles
        self.isAnimated = True

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

    def getCurrentTile(self, showCollision = False):
        """
        Returns the current tile based on the current animation frame
        """
        result = None
        if (not globals_.TilesetsAnimating) or (not self.isAnimated):
            result = self.main
        else:
            result = self.animTiles[self.animFrame]
        result = QtGui.QPixmap(result)

        if globals_.CollisionsShown and showCollision and (self.collOverlay is not None):
            p = QtGui.QPainter(result)
            p.drawPixmap(0, 0, self.collOverlay)
            del p

        return result

    def setCollisions(self, colldata: tuple[int, int, int, int, int, int, int, int]):
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
        # Heavily based on Puzzle
        CD = self.collData

        # Get the color for the overlay
        if CD[2] & 16: # Spike core type
            color = QtGui.QColor(255, 0, 0, 120)
        elif CD[5] >= 1 or CD[5] <= 15:
            colors = [ # Terrain types
                QtGui.QColor(0, 0, 255, 120),     # Ice
                QtGui.QColor(0, 0, 255, 120),     # Snow
                QtGui.QColor(128, 64, 0, 120),    # Quicksand
                QtGui.QColor(128, 128, 128, 120), # Conveyor (Left)
                QtGui.QColor(128, 128, 128, 120), # Conveyor (Right)
                QtGui.QColor(128, 0, 255, 120),   # Rope
                QtGui.QColor(128, 0, 255, 120),   # Anti Wall Jumps
                QtGui.QColor(128, 0, 255, 120),   # Ledge
                QtGui.QColor(128, 0, 255, 120),   # Ladder
                QtGui.QColor(255, 0, 0, 120),     # Staircase
                QtGui.QColor(255, 0, 0, 120),     # Carpet
                QtGui.QColor(128, 64, 0, 120),    # Desert Sand ("Dusty")
                QtGui.QColor(0, 255, 0, 120),     # Grass
                QtGui.QColor(255, 0, 0, 120),     # Muffled
                QtGui.QColor(128, 64, 0, 120),    # Beach Sand
            ]

            color = colors[CD[5]-1]
        else: # Others
            color = QtGui.QColor(64, 30, 0, 120)

        # Sets Brush style for fills
        if CD[2] & 4: # Climbing Grid
            style = QtCore.Qt.BrushStyle.DiagCrossPattern
        elif (CD[3] & 16) or (CD[3] & 4) or (CD[3] & 8): # Breakable
            style = QtCore.Qt.BrushStyle.Dense5Pattern
        else:
            style = QtCore.Qt.BrushStyle.SolidPattern

        brush = QtGui.QBrush(color, style)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 128))
        collPix = QtGui.QPixmap(24, 24)
        collPix.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(collPix)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setOpacity(1.0)

        # Paint specific shapes

        # Ground slopes
        if CD[3] & 32:
            slopes = [
                [QtCore.QPoint(0, 24), QtCore.QPoint(24, 24), QtCore.QPoint(24, 0)], # 1x1 up
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 24), QtCore.QPoint(0, 24)],  # 1x1 down
                # 2x1 up
                [QtCore.QPoint(0, 24), QtCore.QPoint(24, 24), QtCore.QPoint(24, 12)],
                [QtCore.QPoint(0, 24), QtCore.QPoint(0, 12), QtCore.QPoint(24, 0), QtCore.QPoint(24, 24)],
                # 2x1 down
                [QtCore.QPoint(0, 24), QtCore.QPoint(0, 0), QtCore.QPoint(24, 12), QtCore.QPoint(24, 24)],
                [QtCore.QPoint(0, 12), QtCore.QPoint(24, 24), QtCore.QPoint(0, 24)],
                # 1x2 up
                [QtCore.QPoint(0, 24), QtCore.QPoint(12, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 24)],
                [QtCore.QPoint(12, 24), QtCore.QPoint(24, 0), QtCore.QPoint(24, 24)],
                # 1x2 down
                [QtCore.QPoint(0, 0), QtCore.QPoint(12, 0), QtCore.QPoint(24, 24), QtCore.QPoint(0, 24)],
                [QtCore.QPoint(0, 0), QtCore.QPoint(0, 24), QtCore.QPoint(12, 24)],
                # Slope edge
                [QtCore.QPoint(0, 0), QtCore.QPoint(0, 24), QtCore.QPoint(24, 24), QtCore.QPoint(24, 0)],
                # 4x1 up
                [QtCore.QPoint(0, 24), QtCore.QPoint(24, 18), QtCore.QPoint(24, 24)],
                [QtCore.QPoint(24, 24), QtCore.QPoint(24, 12), QtCore.QPoint(0, 18), QtCore.QPoint(0, 24)],
                [QtCore.QPoint(24, 24), QtCore.QPoint(24, 6), QtCore.QPoint(0, 12), QtCore.QPoint(0, 24)],
                [QtCore.QPoint(24, 24), QtCore.QPoint(24, 0), QtCore.QPoint(0, 6), QtCore.QPoint(0, 24)],
                # 4x1 down
                [QtCore.QPoint(24, 24), QtCore.QPoint(24, 6), QtCore.QPoint(0, 0), QtCore.QPoint(0, 24)],
                [QtCore.QPoint(24, 24), QtCore.QPoint(24, 12), QtCore.QPoint(0, 6), QtCore.QPoint(0, 24)],
                [QtCore.QPoint(24, 24), QtCore.QPoint(24, 18), QtCore.QPoint(0, 12), QtCore.QPoint(0, 24)],
                [QtCore.QPoint(24, 24), QtCore.QPoint(0, 18), QtCore.QPoint(0, 24)]
            ]

            if CD[7] <= 18:
                painter.drawPolygon(QtGui.QPolygon(slopes[CD[7]]))

        # Ceiling slopes
        elif CD[3] & 64:
            slopes = [
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 24), QtCore.QPoint(24, 0)], # 1x1 down
                [QtCore.QPoint(0, 24), QtCore.QPoint(0, 0), QtCore.QPoint(24, 0)],  # 1x1 up
                # 2x1 down
                [QtCore.QPoint(24, 0), QtCore.QPoint(0, 0), QtCore.QPoint(24, 12)],
                [QtCore.QPoint(0, 0), QtCore.QPoint(0, 12), QtCore.QPoint(24, 24), QtCore.QPoint(24, 0)],
                # 2x1 up
                [QtCore.QPoint(0, 24), QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 12)],
                [QtCore.QPoint(0, 12), QtCore.QPoint(0, 0), QtCore.QPoint(24, 0)],
                # 1x2 down
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 24), QtCore.QPoint(12, 24)],
                [QtCore.QPoint(12, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 24)],
                # 1x2 up
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(12, 24), QtCore.QPoint(0, 24)],
                [QtCore.QPoint(0, 0), QtCore.QPoint(12, 0), QtCore.QPoint(0, 24)],
                # Slope edge
                [QtCore.QPoint(0, 0), QtCore.QPoint(0, 24), QtCore.QPoint(24, 24), QtCore.QPoint(24, 0)],
                # 4x1 down
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 6)],
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 12), QtCore.QPoint(0, 6)],
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 18), QtCore.QPoint(0, 12)],
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 24), QtCore.QPoint(0, 18)],
                # 4x1 up
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 18), QtCore.QPoint(0, 24)],
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 12), QtCore.QPoint(0, 18)],
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 6), QtCore.QPoint(0, 12)],
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(0, 6)],
            ]

            if CD[7] <= 18:
                painter.drawPolygon(QtGui.QPolygon(slopes[CD[7]]))

        # Partial tiles
        elif CD[2] & 8:
            parts = [
                # Top left
                [QtCore.QPoint(0, 0), QtCore.QPoint(12, 0), QtCore.QPoint(12, 12), QtCore.QPoint(0, 12)],
                # Top right
                [QtCore.QPoint(12, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 12), QtCore.QPoint(12, 12)],
                # Top half
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 12), QtCore.QPoint(0, 12)],
                # Bottom left
                [QtCore.QPoint(0, 12), QtCore.QPoint(12, 12), QtCore.QPoint(12, 24), QtCore.QPoint(0, 24)],
                # Left half
                [QtCore.QPoint(0, 0), QtCore.QPoint(12, 0), QtCore.QPoint(12, 24), QtCore.QPoint(0, 24)],
                # Diagonal upward
                [QtCore.QPoint(0, 24), QtCore.QPoint(12, 24), QtCore.QPoint(12, 0), QtCore.QPoint(24, 0),
                 QtCore.QPoint(24, 12), QtCore.QPoint(0, 12)],
                # 3/4 (no BR)
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 12), QtCore.QPoint(12, 12),
                 QtCore.QPoint(12, 24), QtCore.QPoint(0, 24)],
                # Bottom right
                [QtCore.QPoint(12, 12), QtCore.QPoint(24, 12), QtCore.QPoint(24, 24), QtCore.QPoint(12, 24)],
                # Diagonal downward
                [QtCore.QPoint(0, 0), QtCore.QPoint(12, 0), QtCore.QPoint(12, 24), QtCore.QPoint(24, 24),
                 QtCore.QPoint(24, 12), QtCore.QPoint(0, 12)],
                # Right half
                [QtCore.QPoint(12, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 24), QtCore.QPoint(12, 24)],
                # 3/4 (no BL)
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 24), QtCore.QPoint(12, 24),
                 QtCore.QPoint(12, 12), QtCore.QPoint(0, 12)],
                # Bottom half
                [QtCore.QPoint(0, 12), QtCore.QPoint(24, 12), QtCore.QPoint(24, 24), QtCore.QPoint(0, 24)],
                # 3/4 (no TR)
                [QtCore.QPoint(0, 0), QtCore.QPoint(12, 0), QtCore.QPoint(12, 12), QtCore.QPoint(24, 12),
                 QtCore.QPoint(24, 24), QtCore.QPoint(0, 24)],
                # 3/4 (no TL)
                [QtCore.QPoint(24, 24), QtCore.QPoint(24, 0), QtCore.QPoint(12, 0), QtCore.QPoint(12, 12),
                 QtCore.QPoint(0, 12), QtCore.QPoint(0, 24)],
                # Full block
                [QtCore.QPoint(0, 0), QtCore.QPoint(24, 0), QtCore.QPoint(24, 24), QtCore.QPoint(0, 24)],
            ]

            if CD[7] > 0 and CD[7] <= 15:
                painter.drawPolygon(QtGui.QPolygon(parts[CD[7] - 1]))

        # Solid-on-bottom
        elif CD[2] & 0x20:
            # Platform
            painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                QtCore.QPoint(24, 24),
                                                QtCore.QPoint(24, 18),
                                                QtCore.QPoint(0, 18)]))
            # Arrow
            painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(15, 0),
                                                QtCore.QPoint(15, 12),
                                                QtCore.QPoint(18, 12),
                                                QtCore.QPoint(12, 17),
                                                QtCore.QPoint(6, 12),
                                                QtCore.QPoint(9, 12),
                                                QtCore.QPoint(9, 0)]))

        # Solid-on-top
        elif CD[2] & 0x80:
            # Platform
            painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                QtCore.QPoint(24, 0),
                                                QtCore.QPoint(24, 6),
                                                QtCore.QPoint(0, 6)]))
            # Arrow
            painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(15, 24),
                                                QtCore.QPoint(15, 12),
                                                QtCore.QPoint(18, 12),
                                                QtCore.QPoint(12, 7),
                                                QtCore.QPoint(6, 12),
                                                QtCore.QPoint(9, 12),
                                                QtCore.QPoint(9, 24)]))

        # Spikes
        elif CD[2] & 16:
            if CD[7] == 0: # 2 left spikes
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(0, 6)]))
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(24, 12),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(0, 18)]))
            if CD[7] == 1: # 2 right spikes
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(24, 6)]))
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 12),
                                                    QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(24, 18)]))
            if CD[7] == 2: # 2 up spikes
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 24),
                                                    QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(6, 0)]))
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(12, 24),
                                                    QtCore.QPoint(24, 24),
                                                    QtCore.QPoint(18, 0)]))
            if CD[7] == 3: # 2 down spikes
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(6, 24)]))
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(12, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(18, 24)]))
            if CD[7] == 4: # 1x2 spike base
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(18, 24),
                                                    QtCore.QPoint(6, 24)]))
            if CD[7] == 5: # 1x2 spike point
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(6, 0),
                                                    QtCore.QPoint(18, 0),
                                                    QtCore.QPoint(12, 24)]))
            if CD[7] == 6: # 1x1 spike
                painter.drawPolygon(QtGui.QPolygon([QtCore.QPoint(0, 0),
                                                    QtCore.QPoint(24, 0),
                                                    QtCore.QPoint(12, 24)]))
            if CD[7] == 7: # Full spike
                # Center Fill
                painter.drawRect(7, 7, 10, 10)

                spikes = [
                    [QtCore.QPoint(0, 0), QtCore.QPoint(10, 6), QtCore.QPoint(6, 10)],     # Top left
                    [QtCore.QPoint(24, 0), QtCore.QPoint(14, 6), QtCore.QPoint(18, 10)],   # Top right
                    [QtCore.QPoint(0, 24), QtCore.QPoint(10, 18), QtCore.QPoint(6, 14)],   # Bottom left
                    [QtCore.QPoint(24, 24), QtCore.QPoint(14, 18), QtCore.QPoint(18, 14)], # Bottom right
                    [QtCore.QPoint(12, -1), QtCore.QPoint(8, 8), QtCore.QPoint(16, 8)],    # Top
                    [QtCore.QPoint(12, 25), QtCore.QPoint(8, 16), QtCore.QPoint(16, 16)],  # Bottom
                    [QtCore.QPoint(-1, 12), QtCore.QPoint(8, 8), QtCore.QPoint(8, 16)],    # Left
                    [QtCore.QPoint(25, 12), QtCore.QPoint(16, 8), QtCore.QPoint(16, 16)],  # Right
                ]

                for spike in spikes:
                    painter.drawPolygon(QtGui.QPolygon(spike))

        # Donut Blocks
        elif CD[1] & 2:
            painter.setOpacity(0.471) # A:120
            donut_override = globals_.Overrides[26 * 1 + 12]
            if donut_override is not None:
                painter.drawPixmap(0, 0, donut_override.main)

        # Solid, question or brick
        elif (CD[3] & 1) or (CD[3] in (5, 0x10)) or (CD[3] & 4) or (CD[3] & 8):
            painter.drawRect(0, 0, 24, 24)

        self.collOverlay = collPix
