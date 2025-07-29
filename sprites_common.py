#!/usr/bin/python
# -*- coding: latin-1 -*-

# Reggie Next - New Super Mario Bros. Wii Level Editor
# Milestone 4
# Copyright (C) 2009-2020 Treeki, Tempus, angelsl, JasonP27, Kamek64,
# MalStar1000, RoadrunnerWMC, AboodXD, John10v10, TheGrop, CLF78,
# Zementblock, Danster64

# This file is part of Reggie Next.

# Reggie Next is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Reggie Next is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Reggie Next.  If not, see <http://www.gnu.org/licenses/>.


# sprites_common.py
# Contains code to render sprite images from different gamedefs.
# Use this for base classes


################################################################
################################################################

# Imports
from PyQt6 import QtCore, QtGui
Qt = QtCore.Qt

import spritelib as SLib
ImageCache = SLib.ImageCache

class SpriteImage_TileEvent(SLib.SpriteImage_StaticMultiple):  # 191
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.alpha = 0.5
        self.aux.append(SLib.AuxiliaryRectOutline(parent, 0, 0))

    def dataChanged(self):
        super().dataChanged()

        self.width = (self.parent.spritedata[5] >> 4) << 4
        self.height = (self.parent.spritedata[5] & 0xF) << 4
        self.pattern = self.parent.spritedata[3] & 3
        self.creationtype = self.parent.spritedata[4] & 1
        self.noeffect = self.parent.spritedata[3] & 4 == 4
        self.pattern = self.parent.spritedata[3] & 3
        self.permanent = self.parent.spritedata[2] & 16 == 16
        self.shouldTile = True

        if self.pattern == 3:
            self.pattern = 0

        if self.creationtype == 0: # destroys
            if self.permanent or self.noeffect:
                self.aux[0].setColor(None)
                self.shouldTile = False
            else:
                self.aux[0].setColor("#f00000")
        else:
            self.aux[0].setColor("#00f000")

        if self.width == 0:
            self.width = 16

        if self.height == 0:
            self.height = 16

        self.aux[0].setSize(self.width * 1.5, self.height * 1.5)

        type_ = self.parent.spritedata[4] >> 4
        if type_ in self.notAllowedTypes:
            self.spritebox.shown = True
            self.image = None

            if self.width == self.height == 16:
                self.aux[0].setSize(0, 0)

            return

        self.spritebox.shown = False
        self.image = self.getTileFromType(type_)

    def getTileFromType(self, type):
        """
        Returns the correct tile from SLib.Tiles for the given
        type, or None if no tile should be shown.
        """
        raise NotImplementedError(
            "Class inheriting SpriteImage_TileEvent does not override " \
            "getTileFromType method."
        )

    def paint(self, painter: QtGui.QPainter):
        if self.image is None:
            return

        painter.save()

        painter.setOpacity(self.alpha)
        painter.setRenderHint(painter.RenderHint.SmoothPixmapTransform)

        if self.pattern == 0 and self.shouldTile:
            painter.drawTiledPixmap(QtCore.QRectF(0, 0, self.width * 1.5, self.height * 1.5), self.image)
        elif self.pattern == 1 and self.shouldTile:
            for y_ in range(self.height >> 4):
                y = y_ * 24
                start = (y_ & 1) * 24
                for x in range(int(start), int(self.width * 1.5), 48):
                    painter.drawPixmap(x, y, self.image)
        elif self.shouldTile:
            for y_ in range(self.height >> 4):
                y = y_ * 24
                start = 24 * ((y_ & 1) ^ 1)
                for x in range(int(start), int(self.width * 1.5), 48):
                    painter.drawPixmap(x, y, self.image)

        self.aux[0].paint(painter, None, None)

        painter.restore()


class SpriteImage_Switch(SLib.SpriteImage_StaticMultiple):  # 40, 41, 42, 153
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.switchType = ''
        self.styleType = 0

    @staticmethod
    def loadImages():

        if 'QSwitch' not in ImageCache:
            q = SLib.GetImg('q_switch.png', True)
            ImageCache['QSwitch'] = QtGui.QPixmap.fromImage(q)
            ImageCache['QSwitchU'] = QtGui.QPixmap.fromImage(q.mirrored(True, True))

        if 'PSwitch' not in ImageCache:
            p = SLib.GetImg('p_switch.png', True)
            ImageCache['PSwitch'] = QtGui.QPixmap.fromImage(p)
            ImageCache['PSwitchU'] = QtGui.QPixmap.fromImage(p.mirrored(True, True))

        if 'ESwitch' not in ImageCache:
            e = SLib.GetImg('e_switch.png', True)
            ImageCache['ESwitch'] = QtGui.QPixmap.fromImage(e)
            ImageCache['ESwitchU'] = QtGui.QPixmap.fromImage(e.mirrored(True, True))

    def dataChanged(self):

        upsideDown = self.parent.spritedata[5] & 1

        if self.styleType != 0:
            style = str(self.styleType)
        else:
            style = ''

        if upsideDown:
            self.image = ImageCache[self.switchType + 'SwitchU' + style]

            if self.switchType != 'E':
                self.yOffset -= 1
        else:
            self.image = ImageCache[self.switchType + 'Switch' + style]
            if self.switchType == 'E':
                self.yOffset -= 3
            else:
                self.yOffset -= 3

        super().dataChanged()


class SpriteImage_LineBlock(SLib.SpriteImage):  # 219
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.spritebox.shown = False

        self.aux.append(SLib.AuxiliaryImage(parent, 24, 24))
        self.aux[0].setPos(0, 32)

    def setLineBlockImage(self, block_img):
        """
        Sets the correct images for the line block, given the image of a single
        block.
        """

        direction = self.parent.spritedata[4] >> 4
        width_a = self.parent.spritedata[5] & 0xF
        width_b = self.parent.spritedata[5] >> 4
        distance = self.parent.spritedata[4] & 0xF

        # maybe flip _a and _b so _a is opaque, _b is not opaque
        if direction & 1:
            width_a, width_b = width_b, width_a

        # If any width is set to 0, decrease the opacity of that line and draw
        # at least 1 block
        no_width_a = width_a == 0
        if no_width_a:
            width_a = 1
            alpha_a = 0.25
        else:
            alpha_a = 1

        no_width_b = width_b == 0
        if no_width_b:
            width_b = 1
            alpha_b = 0.25
        else:
            alpha_b = 0.5

        num_blocks = max(width_a, width_b)

        # Create two images, one for each line of blocks.
        img_a = QtGui.QPixmap(width_a * 24, 24)
        img_b = QtGui.QPixmap(width_b * 24, 24)
        img_a.fill(Qt.GlobalColor.transparent)
        img_b.fill(Qt.GlobalColor.transparent)

        painter_a = QtGui.QPainter(img_a)
        painter_b = QtGui.QPainter(img_b)
        painter_a.setOpacity(alpha_a)
        painter_b.setOpacity(1)  # The alpha value of this is set later

        if num_blocks == 1:
            # special-case to avoid dividing by 0
            painter_a.drawPixmap(0, 0, block_img)
            painter_b.drawPixmap(0, 0, block_img)

        else:
            squish_factor_a = (width_a - 1) / (num_blocks - 1)
            squish_factor_b = (width_b - 1) / (num_blocks - 1)

            for i in range(num_blocks):
                # The pixmaps are not drawn linearly, so the smaller side has
                # blocks that are on top of each other, similar to how they are
                # rendered in-game.
                if i & 1:
                    j = num_blocks - 1 - (i // 2)
                else:
                    j = i // 2

                painter_a.drawPixmap(QtCore.QPointF(j * 24 * squish_factor_a, 0), block_img)
                painter_b.drawPixmap(QtCore.QPointF(j * 24 * squish_factor_b, 0), block_img)

        del painter_a, painter_b

        xposA = (1 - width_a) * 8
        xposB = (width_a - width_b) * 12

        # Use the direction to position the platform that is less opaque
        if direction & 1:
            # going down, so the opaque platform should be on top
            yposB = distance * 24
        else:
            # going up, so the opaque platform should be below
            yposB = -distance * 24

        self.image = img_a
        self.width = width_a * 16
        self.xOffset = xposA

        self.aux[0].setSize(img_b.width(), img_b.height(), xposB, yposB)
        self.aux[0].image = img_b
        self.aux[0].alpha = alpha_b

    def paint(self, painter):
        super().paint(painter)
        painter.drawPixmap(0, 0, self.image)
