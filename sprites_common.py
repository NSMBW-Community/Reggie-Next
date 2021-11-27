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
from PyQt5 import QtCore, QtGui
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

    def paint(self, painter):
        if self.image is None:
            return

        painter.save()

        painter.setOpacity(self.alpha)
        painter.setRenderHint(painter.SmoothPixmapTransform)

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
                self.xOffset -= 1
                self.yOffset -= 1
        else:
            self.image = ImageCache[self.switchType + 'Switch' + style]
            if self.switchType == 'E':
                self.yOffset -= 3
            else:
                self.yOffset -= 2

        super().dataChanged()
