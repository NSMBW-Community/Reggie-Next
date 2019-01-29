#!/usr/bin/python
# -*- coding: latin-1 -*-

# Reggie Next - New Super Mario Bros. Wii Level Editor
# Milestone 3
# Copyright (C) 2009-2014 Treeki, Tempus, angelsl, JasonP27, Kamek64,
# MalStar1000, RoadrunnerWMC, 2017 Stella/AboodXD, John10v10

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

        tile = self.getTileFromType(type_)

        if tile:
            self.image = tile.main
        else:
            self.image = SLib.Tiles[0x800 + 108].main

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
            painter.drawTiledPixmap(0, 0, self.width * 1.5, self.height * 1.5, self.image)
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
