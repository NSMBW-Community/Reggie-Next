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


# actors.py
# Contains code to render actor images from New Super Mario Bros. Wii


################################################################
################################################################

# Imports
import math
import random

from PyQt6 import QtCore, QtGui

import data.common.actors as common
import actorlib
from data import globals_

from data.level.items.zone import ZoneItem

Qt = QtCore.Qt
ImageCache = actorlib.ImageCache


################################################################
################################################################
# ---- Low-Level Classes ----

class ActorImage_WoodenPlatform(actorlib.ActorImage):  # 23, 31, 50, 103, 106, 122
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False
        self.xOffset = -2 / 1.5
        self.color = 0

    @staticmethod
    def loadImages():
        # Load the two batches separately because another actor only
        # loads the first three.
        if 'WoodenPlatformL' not in ImageCache:
            ImageCache['WoodenPlatformL'] = actorlib.GetPixmap('wood_platform_left.png')
            ImageCache['WoodenPlatformM'] = actorlib.GetPixmap('wood_platform_middle.png')
            ImageCache['WoodenPlatformR'] = actorlib.GetPixmap('wood_platform_right.png')
        if 'StonePlatformL' not in ImageCache:
            ImageCache['StonePlatformL'] = actorlib.GetPixmap('stone_platform_left.png')
            ImageCache['StonePlatformM'] = actorlib.GetPixmap('stone_platform_middle.png')
            ImageCache['StonePlatformR'] = actorlib.GetPixmap('stone_platform_right.png')
            ImageCache['BonePlatformL'] = actorlib.GetPixmap('bone_platform_left.png')
            ImageCache['BonePlatformM'] = actorlib.GetPixmap('bone_platform_middle.png')
            ImageCache['BonePlatformR'] = actorlib.GetPixmap('bone_platform_right.png')


    def paint(self, painter):
        color = 'Wooden'
        if self.color == 0:
            color = 'Wooden'
        elif self.color == 1:
            color = 'Stone'
        elif self.color == 2:
            color = 'Bone'

        if self.width > 32:
            x = 25 if color == 'Bone' else 26
            painter.drawTiledPixmap(x, 0, int((self.width * 1.5) - 44), int(self.height * 1.5), ImageCache[color + 'PlatformM'])

        if self.width == 24:
            # replicate glitch effect for some platforms
            painter.drawPixmap(0, 0, ImageCache[color + 'PlatformR'])
            painter.drawPixmap(10, 0, ImageCache[color + 'PlatformL'])
        else:
            # normal rendering
            offs = 4 if color == 'Bone' else 3
            painter.drawPixmap(round((self.width - 16) * 1.5 - offs), 0, ImageCache[color + 'PlatformR'])
            painter.drawPixmap(0, 0, ImageCache[color + 'PlatformL'])


class ActorImage_DSStoneBlock(actorlib.ActorImage):  # 27, 28
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'DSBlockTopLeft' in ImageCache:
            return
        ImageCache['DSBlockTopLeft'] = actorlib.GetPixmap('dsblock_topleft.png')
        ImageCache['DSBlockTop'] = actorlib.GetPixmap('dsblock_top.png')
        ImageCache['DSBlockTopRight'] = actorlib.GetPixmap('dsblock_topright.png')
        ImageCache['DSBlockLeft'] = actorlib.GetPixmap('dsblock_left.png')
        ImageCache['DSBlockRight'] = actorlib.GetPixmap('dsblock_right.png')
        ImageCache['DSBlockBottomLeft'] = actorlib.GetPixmap('dsblock_bottomleft.png')
        ImageCache['DSBlockBottom'] = actorlib.GetPixmap('dsblock_bottom.png')
        ImageCache['DSBlockBottomRight'] = actorlib.GetPixmap('dsblock_bottomright.png')

    def dataChanged(self):
        # get size
        width = self.parent.actordata[5] & 7
        if width == 0:
            width = 1
        byte5 = self.parent.actordata[4]
        self.width = (16 + (width << 4))
        self.height = (16 << ((byte5 & 0x30) >> 4)) - 4

    def paint(self, painter):
        middle_width = int((self.width - 32) * 1.5)
        middle_height = int((self.height * 1.5) - 16)
        bottom_y = int((self.height * 1.5) - 8)
        right_x = int((self.width - 16) * 1.5)

        painter.drawPixmap(0, 0, ImageCache['DSBlockTopLeft'])
        painter.drawTiledPixmap(24, 0, middle_width, 8, ImageCache['DSBlockTop'])
        painter.drawPixmap(right_x, 0, ImageCache['DSBlockTopRight'])

        painter.drawTiledPixmap(0, 8, 24, middle_height, ImageCache['DSBlockLeft'])
        painter.drawTiledPixmap(right_x, 8, 24, middle_height, ImageCache['DSBlockRight'])

        painter.drawPixmap(0, bottom_y, ImageCache['DSBlockBottomLeft'])
        painter.drawTiledPixmap(24, bottom_y, middle_width, 8, ImageCache['DSBlockBottom'])
        painter.drawPixmap(right_x, bottom_y, ImageCache['DSBlockBottomRight'])


class ActorImage_StarCoin(actorlib.ActorImage_Static):  # 32, 155, 389
    def __init__(self, parent, scale=1.5):
        super().__init__(
            parent,
            scale,
            ImageCache['StarCoin'],
            (0, 3),
        )


class ActorImage_OldStoneBlock(actorlib.ActorImage):  # 30, 81, 82, 83, 84, 85, 86
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal))
        self.spikesL = False
        self.spikesR = False
        self.spikesT = False
        self.spikesB = False

        self.hasMovementAux = True

    @staticmethod
    def loadImages():
        if 'OldStoneTL' in ImageCache:
            return
        ImageCache['OldStoneTL'] = actorlib.GetPixmap('oldstone_tl.png')
        ImageCache['OldStoneT'] = actorlib.GetPixmap('oldstone_t.png')
        ImageCache['OldStoneTR'] = actorlib.GetPixmap('oldstone_tr.png')
        ImageCache['OldStoneL'] = actorlib.GetPixmap('oldstone_l.png')
        ImageCache['OldStoneM'] = actorlib.GetPixmap('oldstone_m.png')
        ImageCache['OldStoneR'] = actorlib.GetPixmap('oldstone_r.png')
        ImageCache['OldStoneBL'] = actorlib.GetPixmap('oldstone_bl.png')
        ImageCache['OldStoneB'] = actorlib.GetPixmap('oldstone_b.png')
        ImageCache['OldStoneBR'] = actorlib.GetPixmap('oldstone_br.png')
        ImageCache['SpikeU'] = actorlib.GetPixmap('spike_up.png')
        ImageCache['SpikeL'] = actorlib.GetPixmap('spike_left.png')
        ImageCache['SpikeR'] = actorlib.GetPixmap('spike_right.png')
        ImageCache['SpikeD'] = actorlib.GetPixmap('spike_down.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        size = self.parent.actordata[5]
        height = (size & 0xF0) >> 4
        width = size & 0xF
        height = 1 if height == 0 else height
        width = 1 if width == 0 else width

        self.width = width * 16 + 16
        self.height = height * 16 + 16

        if self.spikesL:  # left spikes
            self.xOffset = -16
            self.width += 16
        if self.spikesT:  # top spikes
            self.yOffset = -16
            self.height += 16
        if self.spikesR:  # right spikes
            self.width += 16
        if self.spikesB:  # bottom spikes
            self.height += 16

        # now set up the track
        if self.hasMovementAux:
            direction = self.parent.actordata[2] & 3
            distance = (self.parent.actordata[4] & 0xF0) >> 4
            if direction > 3:
                direction = 0

            if direction <= 1:  # horizontal
                self.aux[0].direction = 1
                self.aux[0].setSize(self.width + (distance * 16), self.height)
            else:  # vertical
                self.aux[0].direction = 2
                self.aux[0].setSize(self.width, self.height + (distance * 16))

            if direction == 0 or direction == 3:  # right, down
                self.aux[0].setPos(0, 0)
            elif direction == 1:  # left
                self.aux[0].setPos(-distance * 24, 0)
            elif direction == 2:  # up
                self.aux[0].setPos(0, -distance * 24)
        else:
            self.aux[0].setSize(0, 0)

    def paint(self, painter):
        blockX = 0
        blockY = 0
        width = self.width * 1.5
        height = self.height * 1.5

        if self.spikesL:  # left spikes
            painter.drawTiledPixmap(0, 0, 24, int(height), ImageCache['SpikeL'])
            blockX = 24
            width -= 24
        if self.spikesT:  # top spikes
            painter.drawTiledPixmap(0, 0, int(width), 24, ImageCache['SpikeU'])
            blockY = 24
            height -= 24
        if self.spikesR:  # right spikes
            painter.drawTiledPixmap(int(blockX + width - 24), 0, 24, int(height), ImageCache['SpikeR'])
            width -= 24
        if self.spikesB:  # bottom spikes
            painter.drawTiledPixmap(0, int(blockY + height - 24), int(width), 24, ImageCache['SpikeD'])
            height -= 24

        column2x = blockX + 24
        column3x = int(blockX + width - 24)
        row2y = blockY + 24
        row3y = int(blockY + height - 24)

        painter.drawPixmap(blockX, blockY, ImageCache['OldStoneTL'])
        painter.drawTiledPixmap(column2x, blockY, int(width - 48), 24, ImageCache['OldStoneT'])
        painter.drawPixmap(column3x, blockY, ImageCache['OldStoneTR'])

        painter.drawTiledPixmap(blockX, row2y, 24, int(height - 48), ImageCache['OldStoneL'])
        painter.drawTiledPixmap(column2x, row2y, int(width - 48), int(height - 48), ImageCache['OldStoneM'])
        painter.drawTiledPixmap(column3x, row2y, 24, int(height - 48), ImageCache['OldStoneR'])

        painter.drawPixmap(blockX, row3y, ImageCache['OldStoneBL'])
        painter.drawTiledPixmap(column2x, row3y, int(width - 48), 24, ImageCache['OldStoneB'])
        painter.drawPixmap(column3x, row3y, ImageCache['OldStoneBR'])


class ActorImage_LiquidOrFog(actorlib.ActorImage):  # 53, 64, 138, 139, 216, 358, 374, 435
    def __init__(self, parent):
        super().__init__(parent)

        self.crest: QtGui.QPixmap | None = None
        self.mid: QtGui.QPixmap | None = None
        self.rise: QtGui.QPixmap | None = None
        self.riseCrestless: QtGui.QPixmap | None = None

        self.top = 0

        self.drawCrest = False
        self.risingHeight = 0

        self.locId = 0
        self.findZone()

    def findZone(self):
        if globals_.Area.areanum == -1:
            return

        self.zoneId = actorlib.MapPositionToZoneID(globals_.Area.zones, self.parent.objx, self.parent.objy, True)

    def positionChanged(self):
        self.findZone()
        scene = self.parent.scene()
        if scene is not None:
            scene.update()

    def dataChanged(self):
        scene = self.parent.scene()
        if scene is not None:
            scene.update()

    def paintZone(self):
        return self.locId == 0 and self.zoneId != -1

    def realViewZone(self, painter, zoneRect):
        """
        Real view zone painter for liquids/fog
        """
        drawRise = self.risingHeight != 0
        drawCrest = self.drawCrest

        crest_rect = QtCore.QRectF()
        rise_rect = QtCore.QRectF()

        # Create the fill_rect (the area where the liquid or fog should be)
        fill_rect = QtCore.QRectF(zoneRect)
        fill_rect.setTop(self.top * 1.5)

        # Translate the fill_rect to be relative to the zone
        fill_rect.translate(-zoneRect.topLeft())

        if fill_rect.isEmpty():
            # the actor is below the zone; don't draw anything
            return

        rise_img: QtGui.QPixmap | None = None

        # Determine where to put the rise image
        if drawRise:
            rise_rect = fill_rect.translated(0, -24 * self.risingHeight)

            # Determine what image to draw for the rise indicator
            rise_img = self.rise
            if not drawCrest or rise_rect.top() <= 0:
                # close enough to the top zone border
                rise_rect.setTop(0)
                rise_img = self.riseCrestless

            # Set the correct height
            rise_rect.setHeight(rise_img.height() if rise_img is not None else 0)

        # If all that fits in the zone is some of the crest, determine how much
        if drawCrest:
            crest_rect = QtCore.QRectF(fill_rect)
            crest_rect.setHeight(self.crest.height() if self.crest is not None else 0)

            # Adjust the fill rect
            fill_rect.setTop(crest_rect.bottom())

        # Draw everything
        if drawCrest:
            painter.drawTiledPixmap(crest_rect, self.crest)

        painter.drawTiledPixmap(fill_rect, self.mid)

        if drawRise:
            painter.drawTiledPixmap(rise_rect, rise_img)

    def realViewLocation(self, painter: QtGui.QPainter, location_rect: QtCore.QRectF):
        """
        Real view location painter for liquids/fog
        """
        if (
            self.paintZone()
            or globals_.Area.areanum == -1
            or self.mid is None
        ):
            return

        for zone in globals_.Area.zones:
            if zone.id == self.zoneId:
                break
        else:
            return

        # Only draw in the intersection of the location and the zone. The
        # intersection needs to be translated, because draw offsets are relative
        # to the location.
        draw_rect = location_rect & zone.mapRectToScene(zone.DrawRect)
        draw_rect.translate(QtCore.QPointF(1, 1) - location_rect.topLeft())

        if draw_rect.isEmpty():
            return

        x, y, width, height = draw_rect.getRect()
        if (x is None or y is None or width is None or height is None):
            return

        drawCrest = False
        crestHeight = 0

        if self.drawCrest and self.crest:
            crestHeight = self.crest.height()
            drawCrest = y < crestHeight

        if drawCrest and self.crest is not None:
            if (crestHeight - y) >= height:
                painter.drawTiledPixmap(draw_rect, self.crest, draw_rect.topLeft())
            else:
                draw_rect.setBottom(crestHeight)
                painter.drawTiledPixmap(draw_rect, self.crest, draw_rect.topLeft())
                draw_rect.setTop(crestHeight)
                draw_rect.setHeight(height - crestHeight + y)
                painter.drawTiledPixmap(draw_rect, self.mid)
        else:
            painter.drawTiledPixmap(draw_rect, self.mid, QtCore.QPointF(0, -location_rect.top() - crestHeight))


class ActorImage_UnusedBlockPlatform(actorlib.ActorImage):  # 97, 107, 132, 160
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

        self.size = (48, 48)
        self.isDark = False
        self.drawPlatformImage = True

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('UnusedPlatform', 'unused_platform.png')
        actorlib.loadIfNotInImageCache('UnusedPlatformDark', 'unused_platform_dark.png')

    def paint(self, painter):
        if not self.drawPlatformImage:
            return

        pixmap = ImageCache['UnusedPlatformDark'] if self.isDark else ImageCache['UnusedPlatform']
        pixmap = pixmap.scaled(
            int(self.width * 1.5), int(self.height * 1.5),
            Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(0, 0, pixmap)


class ActorImage_Amp(actorlib.ActorImage_Static):  # 104, 108
    def __init__(self, parent, scale=1.5):
        super().__init__(
            parent,
            scale
        )

        self.dimensions = (-5 / 1.5, -5 / 1.5, 34 / 1.5, 34 / 1.5)

        ampAux = actorlib.AuxiliaryImage(parent, 59, 50)
        ampAux.image = ImageCache['Amp']
        ampAux.setPos(-13, -13)
        self.aux.append(ampAux)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Amp', 'amp.png')

    def dataChanged(self):
        pass


class ActorImage_Skewer(actorlib.ActorImage):  # 137, 140, 141, 142
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

        self.HorzSpikeLength = ((36 * 16) + 41) / 1.5
        self.VertSpikeLength = ((36 * 16) + 39) / 1.5
        # (16 mid sections + an end section), accounting for image/actor size difference
        self.dir = 'down'

    @staticmethod
    def loadImages():
        if 'SkewerM0up' not in ImageCache:
            for dir in ['up', 'down', 'left', 'right']:
                ImageCache['SkewerM0' + dir] = actorlib.GetPixmap(f'skewer_{dir}_m_0.png')
                ImageCache['SkewerM1' + dir] = actorlib.GetPixmap(f'skewer_{dir}_m_1.png')
                ImageCache['SkewerE0' + dir] = actorlib.GetPixmap(f'skewer_{dir}_e_0.png')
                ImageCache['SkewerE1' + dir] = actorlib.GetPixmap(f'skewer_{dir}_e_1.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        rawdistance = self.parent.actordata[3] >> 4
        distance = (
            (16, 7, 14, 10, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16)
        )[rawdistance]
        distance += 1  # In order to hide one side of the track behind the image.
        speed = (self.parent.actordata[2] >> 4) & 3

        L = 615
        W = 617  # 16 mid sections + an end section

        if speed == 3:
            self.aux[0].setSize(0, 0)
        else:
            if self.dir == 'up':
                self.aux[0].setPos(36, 24 - (distance * 24))
                self.aux[0].setSize(16, distance * 16)
            elif self.dir == 'down':
                self.aux[0].setPos(36, L - 24)
                self.aux[0].setSize(16, distance * 16)
            elif self.dir == 'left':
                self.aux[0].setPos(24 - (distance * 24), 36)
                self.aux[0].setSize(distance * 16, 16)
            else:
                self.aux[0].setPos(W - 24, 36)
                self.aux[0].setSize(distance * 16, 16)

    def paint(self, painter):
        color = self.parent.actordata[3] & 15
        if color == 2 or color == 3 or color == 7:
            mid = ImageCache['SkewerM1' + self.dir]
            end = ImageCache['SkewerE1' + self.dir]
        else:
            mid = ImageCache['SkewerM0' + self.dir]
            end = ImageCache['SkewerE0' + self.dir]

        tiles = 16
        tilesize = 36
        endsizeV = 39
        endsizeH = 41
        widthV = 98
        widthH = 99

        if self.dir == 'up':
            painter.drawPixmap(0, 0, end)
            painter.drawTiledPixmap(0, endsizeV, widthV, tilesize * tiles, mid)
        elif self.dir == 'down':
            painter.drawTiledPixmap(0, 0, widthV, tilesize * tiles, mid)
            painter.drawPixmap(0, int((self.height * 1.5) - endsizeV), end)
        elif self.dir == 'left':
            painter.drawPixmap(0, 0, end)
            painter.drawTiledPixmap(endsizeH, 0, tilesize * tiles, widthH, mid)
        elif self.dir == 'right':
            painter.drawTiledPixmap(0, 0, tilesize * tiles, widthH, mid)
            painter.drawPixmap(int((self.width * 1.5) - endsizeH), 0, end)


class ActorImage_ScrewMushroom(actorlib.ActorImage):  # 172, 382
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

        self.hasBolt = False
        self.size = (124, 180)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Bolt', 'bolt.png')
        if 'ScrewShroomT' not in ImageCache:
            ImageCache['ScrewShroomT'] = actorlib.GetPixmap('screw_shroom_top.png')
            ImageCache['ScrewShroomM'] = actorlib.GetPixmap('screw_shroom_middle.png')
            ImageCache['ScrewShroomB'] = actorlib.GetPixmap('screw_shroom_bottom.png')

    def dataChanged(self):
        mushroomId = self.parent.actordata[2] >> 4 & 0xf
        posOffset = self.parent.actordata[3]

        if posOffset == 0:
            posOffset = 8
        elif mushroomId == 0:
            posOffset += 1
        elif mushroomId > 0 and posOffset > 1:
            posOffset = 1

        self.height = 196 if self.hasBolt else 180
        self.xOffset = 2
        self.yOffset = posOffset * -16 + 16

    def paint(self, painter):
        y = 0
        if self.hasBolt:
            painter.drawPixmap(71, 0, ImageCache['Bolt'])
            y += 24
        painter.drawPixmap(0, y, ImageCache['ScrewShroomT'])
        painter.drawTiledPixmap(78, y + 96, 30, 144, ImageCache['ScrewShroomM'])
        painter.drawPixmap(78, y + 240, ImageCache['ScrewShroomB'])


class ActorImage_Door(actorlib.ActorImage):  # 182, 259, 276, 277, 278
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

        self.doorName = 'Door'
        self.doorDimensions = (0, 0, 32, 48)
        self.entranceOffset = (0, 48)

        entranceOutlineRect = actorlib.AuxiliaryRectOutline(parent, 24, 24)
        entranceOutlineRect.setIsBehindActor(False)
        self.aux.append(entranceOutlineRect)

    @staticmethod
    def loadImages():
        if 'DoorU' in ImageCache:
            return
        doors = {'Door': 'door', 'GhostDoor': 'ghost_door', 'TowerDoor': 'tower_door', 'CastleDoor': 'castle_door'}
        transform90 = QtGui.QTransform()
        transform180 = QtGui.QTransform()
        transform270 = QtGui.QTransform()
        transform90.rotate(90)
        transform180.rotate(180)
        transform270.rotate(270)

        for door, filename in doors.items():
            image = actorlib.GetImage(f'{filename}.png')
            if image is None:
                continue
            ImageCache[door + 'U'] = QtGui.QPixmap.fromImage(image)
            ImageCache[door + 'R'] = QtGui.QPixmap.fromImage(image.transformed(transform90))
            ImageCache[door + 'D'] = QtGui.QPixmap.fromImage(image.transformed(transform180))
            ImageCache[door + 'L'] = QtGui.QPixmap.fromImage(image.transformed(transform270))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryRectOutline):
            return

        rotstatus = self.parent.actordata[4]
        if rotstatus & 1 == 0:
            direction = 0
        else:
            direction = (rotstatus & 0x30) >> 4

        if direction > 3:
            direction = 0
        doorName = self.doorName
        doorSize = self.doorDimensions
        paintEntrancePos = False
        if direction == 0:
            self.image = ImageCache[doorName + 'U']
            self.dimensions = doorSize
            paintEntrancePos = True
        elif direction == 1:
            self.image = ImageCache[doorName + 'L']
            self.dimensions = (
                (doorSize[2] / 2) + doorSize[0] - doorSize[3],
                doorSize[1] + (doorSize[3] - (doorSize[2] / 2)),
                doorSize[3],
                doorSize[2],
            )
            paintEntrancePos = False
        elif direction == 2:
            self.image = ImageCache[doorName + 'D']
            self.dimensions = (
                doorSize[0],
                doorSize[1] + doorSize[3],
                doorSize[2],
                doorSize[3],
            )
            paintEntrancePos = False
        elif direction == 3:
            self.image = ImageCache[doorName + 'R']
            self.dimensions = (
                doorSize[0] + (doorSize[2] / 2),
                doorSize[1] + (doorSize[3] - (doorSize[2] / 2)),
                doorSize[3],
                doorSize[2],
            )
            paintEntrancePos = False

        self.aux[0].setSize(
            *(
                (0, 0, 0, 0),
                (24, 24) + self.entranceOffset,
            )[1 if paintEntrancePos else 0]
        )

    def paint(self, painter):
        if self.image is None:
            return

        painter.setOpacity(self.alpha)
        painter.drawPixmap(0, 0, self.image)
        painter.setOpacity(1)


class ActorImage_GiantBubble(actorlib.ActorImage):  # 205, 226
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False
        self.parent.setZValue(24999)
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal))

    @staticmethod
    def loadImages():
        if 'GiantBubble0' in ImageCache:
            return
        for shape in range(3):
            ImageCache[f'GiantBubble{shape}'] = actorlib.GetPixmap(f'giant_bubble_{shape}.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        self.shape = self.parent.actordata[4] >> 4
        direction = self.parent.actordata[5] & 15
        distance = (self.parent.actordata[5] & 0xF0) >> 4

        if self.shape > 3:
            self.shape = 0

        self.size = (
            (122, 137),
            (76, 170),
            (160, 81)
        )[self.shape]

        self.xOffset = -(self.width / 2) + 8
        self.yOffset = -(self.height / 2) + 8

        if distance == 0:
            self.aux[0].setSize(0, 0)
        elif direction == 1:  # horizontal
            self.aux[0].direction = 1
            self.aux[0].setSize((distance * 32) + self.width, 16)
            self.aux[0].setPos((-distance * 24), (self.height * 0.75) - 12)
        else:  # vertical
            self.aux[0].direction = 2
            self.aux[0].setSize(16, (distance * 32) + self.height)
            self.aux[0].setPos((self.width * 0.75) - 12, (-distance * 24))

    def paint(self, painter):
        painter.drawPixmap(0, 0, ImageCache[f'GiantBubble{self.shape}'])


class ActorImage_Block(actorlib.ActorImage):  # 207, 208, 209, 221, 255, 256, 402, 403, 422, 423
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

        rot_block_aux_image = actorlib.AuxiliaryImage(parent, 24, 24)
        rot_block_aux_image.setPos(0, 0)
        self.aux.append(rot_block_aux_image)

        rot_item_aux_image = actorlib.AuxiliaryImage(parent, 24, 24)
        rot_item_aux_image.setPos(0, 0)
        self.aux.append(rot_item_aux_image)

        self.tilenum = 1315
        self.contentsNybble = 5
        self.contentsOverride = None
        self.eightIsMushroom = False
        self.twelveIsMushroom = False
        self.rotates = False
        self.flipOverride = False
        self.transparent = False
        self.is_water_block = False

    def dataChanged(self):
        # SET CONTENTS
        # In the block_contents.png file:
        # 0 = Empty, 1 = Coin, 2 = Mushroom, 3 = Fire Flower, 4 = Propeller, 5 = Penguin Suit,
        # 6 = Mini Shroom, 7 = Star, 8 = Continuous Star, 9 = Yoshi Egg, 10 = 10 Coins,
        # 11 = 1-up, 12 = Vine, 13 = Spring, 14 = Shroom/Coin, 15 = Ice Flower, 16 = Toad, 17 = Hammer
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage) or not isinstance(self.aux[1], actorlib.AuxiliaryImage):
            return

        if self.contentsOverride is not None:
            contents = self.contentsOverride
        else:
            contents = self.parent.actordata[self.contentsNybble] & 0xF

        if contents == 2:  # 1 and 2 are always fire flowers
            contents = 3

        if contents == 12 and self.twelveIsMushroom:
            contents = 2  # 12 is a mushroom on some types
        if contents == 8 and self.eightIsMushroom:
            contents = 2  # same as above, but for type 8

        self.image = ImageCache[f'BlockContents{contents}']

        # SET UP ROTATION
        if self.rotates:
            transform = QtGui.QTransform()
            transform.translate(12, 12)

            angle = (self.parent.actordata[4] & 0xF0) >> 4
            leftTilt = self.parent.actordata[3] & 1

            angle *= 45 / 16

            if leftTilt == 0:
                transform.rotate(angle)
            else:
                transform.rotate(360 - angle)

            transform.translate(-12, -12)
            self.transform = transform

            self.aux[0].image = actorlib.GetTile(self.tilenum).transformed(transform, QtCore.Qt.TransformationMode.SmoothTransformation)
            self.aux[0].setSize(self.aux[0].image.width(), self.aux[0].image.height())

            self.aux[1].image = ImageCache[f'BlockContents{contents}'].transformed(transform, QtCore.Qt.TransformationMode.SmoothTransformation)
            self.aux[1].setSize(self.aux[1].image.width(), self.aux[1].image.height())

            self.setSize((self.aux[0].image.width() / 1.5, self.aux[0].image.height() / 1.5))

        # Flip a switch override
        if self.flipOverride:
            flip = self.image.toImage().mirrored(True, True)
            self.image = self.image.fromImage(flip)

        # Actor 433 scales the block by 1.5x
        if self.is_water_block:
            self.setOffset((-4, -4))
            self.setSize((36 / 1.5, 36 / 1.5))

    def paint(self, painter):
        if self.image is None or not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        if self.transparent:
            painter.setOpacity(0.5)
        else:
            painter.setOpacity(1.0)

        img_offs = 6 if self.is_water_block else 0
        scale = 36 if self.is_water_block else 24

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        if self.rotates:
            self.aux[0].image = actorlib.GetTile(self.tilenum).transformed(self.transform, QtCore.Qt.TransformationMode.SmoothTransformation)
            self.aux[0].setSize(self.aux[0].image.width(), self.aux[0].image.height())
        else:
            if self.tilenum < len(actorlib.Tiles):
                painter.drawPixmap(0, 0, actorlib.GetTile(self.tilenum).scaled(scale, scale))
            painter.drawPixmap(img_offs, img_offs, self.image)


class ActorImage_SpecialCoin(actorlib.ActorImage_Static):  # 253, 371, 390
    def __init__(self, parent, scale=1.5):
        super().__init__(
            parent,
            scale,
            ImageCache['SpecialCoin'],
        )


class ActorImage_Pipe(actorlib.ActorImage):  # 254, 339, 353, 377, 378, 379, 380, 450
    Top = 0
    Bottom = 1

    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

        self.parent.setZValue(24999)

        self.direction = 'U'
        self.color = 'Green'
        self.length1 = 4
        self.length2 = 4

    @staticmethod
    def loadImages():
        if 'PipeTopGreen' not in ImageCache:
            for color in ('Green', 'Red', 'Yellow', 'Blue'):
                color_l = color.lower()
                ImageCache[f'PipeTop{color}'] = actorlib.GetPixmap(f'pipe_{color_l}_top.png')
                ImageCache[f'PipeMiddleV{color}'] = actorlib.GetPixmap(f'pipe_{color_l}_middle.png')
                ImageCache[f'PipeBottom{color}'] = actorlib.GetPixmap(f'pipe_{color_l}_bottom.png')
                ImageCache[f'PipeLeft{color}'] = actorlib.GetPixmap(f'pipe_{color_l}_left.png')
                ImageCache[f'PipeMiddleH{color}'] = actorlib.GetPixmap(f'pipe_{color_l}_center.png')
                ImageCache[f'PipeRight{color}'] = actorlib.GetPixmap(f'pipe_{color_l}_right.png')

    def dataChanged(self):
        # actor types:
        # 339 = Moving Pipe Facing Up
        # 353 = Moving Pipe Facing Down
        # 377 = Pipe Up
        # 378 = Pipe Down
        # 379 = Pipe Right
        # 380 = Pipe Left
        # 450 = Enterable Pipe Up

        size = max(self.length1, self.length2) * 16

        if self.direction in 'LR':  # horizontal
            self.width = size
            self.height = 32
            if self.direction == 'R':  # faces right
                self.xOffset = 0
            else:  # faces left
                self.xOffset = 16 - size
            self.yOffset = 0

        else:  # vertical
            self.width = 32
            self.height = size
            if self.direction == 'D':  # faces down
                self.yOffset = 0
            else:  # faces up
                self.yOffset = 16 - size
            self.xOffset = 0

        if self.direction == 'U':  # facing up
            self.yOffset = 16 - size
        else:  # facing down
            self.yOffset = 0

    def paint(self, painter):
        color = self.color
        ysize = self.height * 1.5

        # Assume moving pipes
        length1 = self.length1 * 24
        length2 = self.length2 * 24
        low = min(length1, length2)
        high = max(length1, length2)

        if self.direction == 'U':
            y1 = ysize - low
            y2 = ysize - high

            if length1 != length2:
                # draw semi-transparent pipe
                painter.save()
                painter.setOpacity(0.5)
                painter.drawPixmap(0, int(y2), ImageCache[f'PipeTop{color}'])
                painter.drawTiledPixmap(0, int(y2 + 24), 48, int(high - 24), ImageCache[f'PipeMiddleV{color}'])
                painter.restore()

            # draw opaque pipe
            painter.drawPixmap(0, int(y1), ImageCache[f'PipeTop{color}'])
            painter.drawTiledPixmap(0, int(y1 + 24), 48, int(low - 24), ImageCache[f'PipeMiddleV{color}'])

        elif self.direction == 'D':

            if length1 != length2:
                # draw semi-transparent pipe
                painter.save()
                painter.setOpacity(0.5)
                painter.drawTiledPixmap(0, 0, 48, int(high - 24), ImageCache[f'PipeMiddleV{color}'])
                painter.drawPixmap(0, int(high - 24), ImageCache[f'PipeBottom{color}'])
                painter.restore()

            # draw opaque pipe
            painter.drawTiledPixmap(0, 0, 48, int(low - 24), ImageCache[f'PipeMiddleV{color}'])
            painter.drawPixmap(0, int(low - 24), ImageCache[f'PipeBottom{color}'])

        elif self.direction == 'R':

            if length1 != length2:
                # draw semi-transparent pipe
                painter.save()
                painter.setOpacity(0.5)
                painter.drawPixmap(int(high), 0, ImageCache[f'PipeRight{color}'])
                painter.drawTiledPixmap(0, 0, int(high - 24), 48, ImageCache[f'PipeMiddleH{color}'])
                painter.restore()

            # draw opaque pipe
            painter.drawPixmap(int(low - 24), 0, ImageCache[f'PipeRight{color}'])
            painter.drawTiledPixmap(0, 0, int(low - 24), 48, ImageCache[f'PipeMiddleH{color}'])

        else:  # left

            if length1 != length2:
                # draw semi-transparent pipe
                painter.save()
                painter.setOpacity(0.5)
                painter.drawTiledPixmap(0, 0, int(high - 24), 48, ImageCache[f'PipeMiddleH{color}'])
                painter.drawPixmap(int(high - 24), 0, ImageCache[f'PipeLeft{color}'])
                painter.restore()

            # draw opaque pipe
            painter.drawTiledPixmap(24, 0, int(low - 24), 48, ImageCache[f'PipeMiddleH{color}'])
            painter.drawPixmap(0, 0, ImageCache[f'PipeLeft{color}'])


class ActorImage_PipeStationary(ActorImage_Pipe):  # 377, 378, 379, 380, 450
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.length = 4

    def dataChanged(self):
        self.color = (
            'Green', 'Red', 'Yellow', 'Blue',
        )[(self.parent.actordata[5] >> 4) & 3]

        self.length1 = self.length
        self.length2 = self.length

        super().dataChanged()


class ActorImage_UnusedGiantDoor(actorlib.ActorImage_Static):  # 319, 320
    def __init__(self, parent, scale=1.5):
        super().__init__(
            parent,
            scale,
            ImageCache['UnusedGiantDoor'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('UnusedGiantDoor', 'unused_giant_door.png')


class ActorImage_BrownTowerBlock(actorlib.ActorImage):  # 354, 356
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        for vert in 'TMB':
            for horz in 'LMR':
                actorlib.loadIfNotInImageCache(
                    f'BrownBlock{vert}{horz}',
                    f'brown_block_{vert}{horz}.png'
                )

    def dataChanged(self):
        size = self.parent.actordata[5]
        height = size >> 4
        width = size & 0xF
        height = 1 if height == 0 else height
        width = 1 if width == 0 else width
        self.width = width * 16 + 16
        self.height = height * 16 + 16

    def paint(self, painter):
        width = int(self.width * 1.5)
        height = int(self.height * 1.5)

        column2x = 24
        column3x = width - 24
        row2y = 24
        row3y = height - 24
        mid_offset_x = 48
        mid_offset_y = 24

        if height % 48 == 24:
            mid_offset_y -= 12
        if width % 72 == 0:
            mid_offset_x -= 12
        elif width % 72 == 24:
            mid_offset_x -= 24

        painter.drawPixmap(0, 0, ImageCache['BrownBlockTL'])
        painter.drawTiledPixmap(column2x, 0, width - 48, 24, ImageCache['BrownBlockTM'])
        painter.drawPixmap(column3x, 0, ImageCache['BrownBlockTR'])

        painter.drawTiledPixmap(0, row2y, 24, height - 48, ImageCache['BrownBlockML'])
        painter.drawTiledPixmap(column3x, row2y, 24, height - 48, ImageCache['BrownBlockMR'])

        painter.drawPixmap(0, row3y, ImageCache['BrownBlockBL'])
        painter.drawTiledPixmap(column2x, row3y, width - 48, 24, ImageCache['BrownBlockBM'])
        painter.drawPixmap(column3x, row3y, ImageCache['BrownBlockBR'])

        # Needs to be drawn last because it covers parts the other tiles
        painter.drawTiledPixmap(12, 12, width - 24, height - 24, ImageCache['BrownBlockMM'], mid_offset_x, mid_offset_y)


class ActorImage_RollingHillWithPipe(actorlib.ActorImage):  # 355, 360
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.aux.append(actorlib.AuxiliaryCircleOutline(parent, 800))


class ActorImage_LongSkewer(actorlib.ActorImage):  # 398, 400
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.parent.setZValue(24999) # to see actor behind it easily
        self.actorbox.shown = False

        # 55 mid sections + an end section = 2021
        self.dir = 'left'

    @staticmethod
    def loadImages():
        if 'LongSkewerM0left' in ImageCache:
            return
        for dir in ['left', 'right']:
            ImageCache[f'LongSkewerM0{dir}'] = actorlib.GetPixmap(f'skewer_{dir}_m_0.png')
            ImageCache[f'LongSkewerM1{dir}'] = actorlib.GetPixmap(f'skewer_{dir}_m_1.png')
            ImageCache[f'LongSkewerE0{dir}'] = actorlib.GetPixmap(f'skewer_{dir}_e_0.png')
            ImageCache[f'LongSkewerE1{dir}'] = actorlib.GetPixmap(f'skewer_{dir}_e_1.png')

    def dataChanged(self):
        if (
            not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject)
            or not isinstance(self.aux[1], actorlib.AuxiliaryImage)
        ):
            return

        color = self.parent.actordata[3] & 15
        tiles = 55
        tilesize = 36
        endsize = 41
        width = 99

        pix = QtGui.QPixmap(2021, 99)
        pix.fill(Qt.GlobalColor.transparent)
        paint = QtGui.QPainter(pix)

        if color == 2 or color == 3 or color == 6 or color == 7:
            mid = ImageCache['LongSkewerM1' + self.dir]
            end = ImageCache['LongSkewerE1' + self.dir]
        else:
            mid = ImageCache['LongSkewerM0' + self.dir]
            end = ImageCache['LongSkewerE0' + self.dir]

        if self.dir == 'left':
            self.aux[0].setPos(-1896, 36)
            paint.drawPixmap(0, 0, end)
            paint.drawTiledPixmap(endsize, 0, tilesize * tiles, width, mid)
        elif self.dir == 'right':
            self.aux[0].setPos(171, 36)
            self.aux[1].setPos(-1829, 0)
            paint.drawTiledPixmap(0, 0, tilesize * tiles, width, mid)
            paint.drawPixmap(1980, 0, end)

        self.aux[1].image = pix
        self.aux[1].alpha = 0.9


class ActorImage_MassiveSkewer(actorlib.ActorImage):  # 401, 404
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.parent.setZValue(24999) # to see actor behind it easily

        self.SpikeLength = ((72 * 40) + 136) / 1.5
        # (40 mid sections + an end section), accounting for image/actor size difference
        self.dir = 'down'

    @staticmethod
    def loadImages():
        if 'MassiveSkewerM0up' in ImageCache:
            return
        for dir in ['up', 'down']:
            ImageCache['MassiveSkewerM0'] = actorlib.GetPixmap('massive_skewer_m_0.png')
            ImageCache['MassiveSkewerM1'] = actorlib.GetPixmap('massive_skewer_m_1.png')
            ImageCache[f'MassiveSkewerE0{dir}'] = actorlib.GetPixmap(f'massive_skewer_{dir}_e_0.png')
            ImageCache[f'MassiveSkewerE1{dir}'] = actorlib.GetPixmap(f'massive_skewer_{dir}_e_1.png')

    def dataChanged(self):
        if (
            not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject)
            or not isinstance(self.aux[1], actorlib.AuxiliaryRectOutline)
            or not isinstance(self.aux[2], actorlib.AuxiliaryImage)
        ):
            return

        color = self.parent.actordata[3] & 15
        tiles = 40
        tilesize = 72
        endsize = 136
        width = 248

        pix = QtGui.QPixmap(248, 3016)
        pix.fill(Qt.GlobalColor.transparent)
        paint = QtGui.QPainter(pix)

        if color == 2 or color == 3 or color == 6 or color == 7:
            mid = ImageCache['MassiveSkewerM1']
            end = ImageCache['MassiveSkewerE1' + self.dir]
        else:
            mid = ImageCache['MassiveSkewerM0']
            end = ImageCache['MassiveSkewerE0' + self.dir]

        offsX = 91
        offsY = -183 # Only used for down skewer

        if self.dir == 'up':
            self.aux[0].setPos(102 - offsX, -96)
            self.aux[1].setPos(-7  - offsX, -2592)
            self.aux[2].setPos(-10 - offsX, 0)
            paint.drawPixmap(0, 0, end)
            paint.drawTiledPixmap(0, endsize, width, tilesize * tiles, mid)
        elif self.dir == 'down':
            self.aux[0].setPos(102 - offsX, 184   + offsY)
            self.aux[1].setPos(-7  - offsX, 137   + offsY)
            self.aux[2].setPos(-10 - offsX, -2808 + offsY)
            paint.drawTiledPixmap(0, 0, width, tilesize * tiles, mid)
            paint.drawPixmap(0, 2880, end)

        paint = None
        self.aux[2].image = pix
        self.aux[2].alpha = 0.5


class ActorImage_ToadHouseBalloon(actorlib.ActorImage_StaticMultiple):  # 411, 412
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.hasHandle = False
        self.livesNum = 0
        # self.livesnum: 0 = 1 life, 1 = 2 lives, etc (1 + value)

    @staticmethod
    def loadImages():
        if 'ToadHouseBalloon0' in ImageCache:
            return
        for handleCacheStr, handleFileStr in (('', ''), ('Handle', 'handle_')):
            for num in range(4):
                ImageCache['ToadHouseBalloon' + handleCacheStr + str(num)] = \
                    actorlib.GetPixmap(f'mg_house_balloon_{handleFileStr}{num}.png')

    def dataChanged(self):
        self.image = ImageCache['ToadHouseBalloon' + ('Handle' if self.hasHandle else '') + str(self.livesNum)]
        self.xOffset = -13

        super().dataChanged()


# ---- High-Level Classes ----

class ActorImage_MeasureJump(actorlib.ActorImage):
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        jumpAuxImage = actorlib.AuxiliaryImage(parent, 312, 191)
        jumpAuxImage.image = ImageCache["JumpRun1"]
        jumpAuxImage.setPos(0, 0)
        self.aux.append(jumpAuxImage)

    @staticmethod
    def loadImages():
        if "JumpRun1" in ImageCache:
            return

        for i in range(1, 4):
            ImageCache[f'JumpRun{i}'] = actorlib.GetPixmap(f'jump_run_{i}.png')
            ImageCache[f'JumpRunSpin{i}'] = actorlib.GetPixmap(f'jump_run_spin_{i}.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        jumptype = self.parent.actordata[2] & 3
        flags = (self.parent.actordata[3] & 0xF0) >> 4
        direction = flags >> 3
        spin = (flags & 4) >> 2

        if jumptype > 2:
            jumptype = 0

        if spin:
            img = ImageCache[f'JumpRunSpin{jumptype + 1}']
        else:
            img = ImageCache[f'JumpRun{jumptype + 1}']

        if direction == 1:
            img = img.transformed(QtGui.QTransform().scale(-1, 1))

        self.aux[0].image = img
        width, height = img.width(), img.height()
        self.aux[0].setSize(width, height)

        if direction == 1:
            self.aux[0].setPos(-width, 0)
        else:
            self.aux[0].setPos(0, 0)


class ActorImage_CharacterSpawner(actorlib.ActorImage_StaticMultiple):  # 9
    def dataChanged(self):
        direction = self.parent.actordata[2] & 1
        character = self.parent.actordata[5] & 3

        directionstr = 'L' if direction else 'R'

        self.image = ImageCache['Character' + str(character + 1) + directionstr]

        self.offset = (
            -(self.image.width() / 3),
            -(self.image.height() / 1.5),
        )

        super().dataChanged()


class ActorImage_Goomba(actorlib.ActorImage_Static):  # 20
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Goomba'],
            (-1, -4),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Goomba', 'goomba.png')


class ActorImage_ParaGoomba(actorlib.ActorImage_Static):  # 21
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ParaGoomba'],
            (1, -10),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ParaGoomba', 'para_goomba.png')


class ActorImage_HorzMovingPlatform(ActorImage_WoodenPlatform):  # 23
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        self.width = (((self.parent.actordata[5] & 0xF) + 1) << 4) + (4 / 1.5)
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, self.width, 16, actorlib.AuxiliaryTrackObject.Horizontal))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        # get width and distance
        self.width = (((self.parent.actordata[5] & 0xF) + 1) << 4) + (4 / 1.5)
        if self.width < 20:
            self.width = 32 + (4 / 1.5)

        distance = ((self.parent.actordata[4] & 0xF) << 4) - 1

        # update the track
        self.aux[0].setSize(self.width + distance, 16)

        if (self.parent.actordata[3] & 1) == 0:
            # platform goes right
            self.aux[0].setPos(0, 0)
        else:
            # platform goes left
            self.aux[0].setPos(-distance * 1.5, 0)

        # set color, silver is only used for a value of 1
        self.color = (self.parent.actordata[3] >> 4) == 1

        self.aux[0].update()


class ActorImage_BuzzyBeetle(actorlib.ActorImage_StaticMultiple):  # 24
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BuzzyBeetle', 'buzzy_beetle.png')
        actorlib.loadIfNotInImageCache('BuzzyBeetleU', 'buzzy_beetle_u.png')
        actorlib.loadIfNotInImageCache('BuzzyBeetleShell', 'buzzy_beetle_shell.png')
        actorlib.loadIfNotInImageCache('BuzzyBeetleShellU', 'buzzy_beetle_shell_u.png')

    def dataChanged(self):

        orient = self.parent.actordata[5] & 15
        if orient == 1:
            self.image = ImageCache['BuzzyBeetleU']
            self.yOffset = 0
        elif orient == 2:
            self.image = ImageCache['BuzzyBeetleShell']
            self.yOffset = 2
        elif orient == 3:
            self.image = ImageCache['BuzzyBeetleShellU']
            self.yOffset = 2
        else:
            self.image = ImageCache['BuzzyBeetle']
            self.yOffset = 0

        super().dataChanged()


class ActorImage_Spiny(actorlib.ActorImage_StaticMultiple):  # 25
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Spiny', 'spiny.png')
        actorlib.loadIfNotInImageCache('SpinyShell', 'spiny_shell.png')
        actorlib.loadIfNotInImageCache('SpinyShellU', 'spiny_shell_u.png')
        actorlib.loadIfNotInImageCache('SpinyBall', 'spiny_ball.png')

    def dataChanged(self):

        orient = self.parent.actordata[5] & 15
        if orient == 1:
            self.image = ImageCache['SpinyBall']
            self.yOffset = 8
        elif orient == 2:
            self.image = ImageCache['SpinyShell']
            self.yOffset = 1
        elif orient == 3:
            self.image = ImageCache['SpinyShellU']
            self.yOffset = 2
        else:
            self.image = ImageCache['Spiny']
            self.yOffset = 0

        super().dataChanged()


class ActorImage_UpsideDownSpiny(actorlib.ActorImage_Static):  # 26
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SpinyU'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpinyU', 'spiny_u.png')


class ActorImage_DSStoneBlock_Vert(ActorImage_DSStoneBlock):  # 27
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 32, 16, actorlib.AuxiliaryTrackObject.Vertical))
        self.size = (32, 16)

    def dataChanged(self):
        super().dataChanged()
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        # get height and distance
        byte5 = self.parent.actordata[4]
        distance = (byte5 & 0xF) << 4

        # update the track
        self.aux[0].setSize(self.width, distance + self.height)

        if (self.parent.actordata[3] & 1) == 0:
            # block goes up
            self.aux[0].setPos(0, -distance * 1.5)
        else:
            # block goes down
            self.aux[0].setPos(0, 0)

        self.aux[0].update()


class ActorImage_DSStoneBlock_Horz(ActorImage_DSStoneBlock):  # 28
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 32, 16, actorlib.AuxiliaryTrackObject.Horizontal))
        self.size = (32, 16)

    def dataChanged(self):
        super().dataChanged()
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        # get height and distance
        byte5 = self.parent.actordata[4]
        distance = (byte5 & 0xF) << 4

        # update the track
        self.aux[0].setSize(distance + self.width, self.height)

        if (self.parent.actordata[3] & 1) == 0:
            # block goes right
            self.aux[0].setPos(0, 0)
        else:
            # block goes left
            self.aux[0].setPos(-distance * 1.5, 0)

        self.aux[0].update()


class ActorImage_OldStoneBlock_NoSpikes(ActorImage_OldStoneBlock):  # 30
    pass


class ActorImage_VertMovingPlatform(ActorImage_WoodenPlatform):  # 31
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        self.width = (((self.parent.actordata[5] & 0xF) + 1) << 4) + (4 / 1.5)
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, self.width, 16, actorlib.AuxiliaryTrackObject.Vertical))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        # get width and distance
        self.width = (((self.parent.actordata[5] & 0xF) + 1) << 4) + (4 / 1.5)
        if self.width < 20:
            self.width = 32 + (4 / 1.5)

        distance = (self.parent.actordata[4] & 0xF) << 4

        # update the track
        self.aux[0].setSize(self.width, distance + 16)

        if (self.parent.actordata[3] & 1) == 0:
            # platform goes up
            self.aux[0].setPos(0, -distance * 1.5)
        else:
            # platform goes down
            self.aux[0].setPos(0, 0)

        # set color, silver is only used for a value of 1
        self.color = (self.parent.actordata[3] >> 4) == 1

        self.aux[0].update()


class ActorImage_StarCoinRegular(ActorImage_StarCoin):  # 32
    pass


class ActorImage_QSwitch(common.ActorImage_Switch):  # 40
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.switchType = 'Q'

    def dataChanged(self):
        self.offset = (0, 0)
        super().dataChanged()


class ActorImage_PSwitch(common.ActorImage_Switch):  # 41
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.switchType = 'P'

    def dataChanged(self):
        self.offset = (0, 0)
        super().dataChanged()


class ActorImage_ExcSwitch(common.ActorImage_Switch):  # 42
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.switchType = 'E'

    def dataChanged(self):
        self.offset = (0, 0)
        super().dataChanged()


class ActorImage_QSwitchBlock(ActorImage_Block):  # 43
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48
        self.contentsOverride = 17

    def dataChanged(self):
        upsideDown = self.parent.actordata[5] & 1
        midway = (self.parent.actordata[2] >> 6) & 1
        self.flipOverride = upsideDown
        self.transparent = midway
        super().dataChanged()


class ActorImage_PSwitchBlock(ActorImage_Block):  # 44
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48
        self.contentsOverride = 18

    def dataChanged(self):
        upsideDown = self.parent.actordata[5] & 1
        self.flipOverride = upsideDown
        self.transparent = (self.parent.actordata[2] >> 6) & 1
        super().dataChanged()


class ActorImage_ExcSwitchBlock(ActorImage_Block):  # 45
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48
        self.contentsOverride = 19

    def dataChanged(self):
        upsideDown = self.parent.actordata[5] & 1
        self.flipOverride = upsideDown
        self.transparent = (self.parent.actordata[2] >> 6) & 1
        super().dataChanged()


class ActorImage_Podoboo(actorlib.ActorImage):  # 46
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        podobooAuxImage = actorlib.AuxiliaryImage(parent, 48, 48)
        podobooAuxImage.image = ImageCache['Podoboo0']
        podobooAuxImage.setPos(-6, -6)
        podobooAuxImage.hover = False
        self.aux.append(podobooAuxImage)

        self.dimensions = (-3, 5, 24, 24)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Podoboo0', 'podoboo.png')


class ActorImage_Thwomp(actorlib.ActorImage_Static):  # 47
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Thwomp'],
            (-6, -6),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Thwomp', 'thwomp.png')


class ActorImage_GiantThwomp(actorlib.ActorImage_Static):  # 48
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantThwomp'],
            (-8, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantThwomp', 'giant_thwomp.png')


class ActorImage_UnusedSeesaw(actorlib.ActorImage):  # 49
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        rotationAreaAux = actorlib.AuxiliaryRotationAreaOutline(parent, 48)
        rotationAreaAux.setPos(128, -36)
        self.aux.append(rotationAreaAux)

        self.image = ImageCache['UnusedPlatformDark']
        self.dimensions = (0, -8, 256, 16)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('UnusedPlatformDark', 'unused_platform_dark.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryRotationAreaOutline):
            return

        w = self.parent.actordata[5] & 15
        if w == 0:
            self.width = 16 * 16  # 16 blocks wide
        else:
            self.width = w * 32
        self.image = ImageCache['UnusedPlatformDark'].scaled(
            int(self.width * 1.5), int(self.height * 1.5),
            Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation,
        )
        self.xOffset = (8 * 16) - (self.width / 2)

        swingArc = self.parent.actordata[5] >> 4
        swingArcs = (
            45,
            4.5,
            9,
            18,
            65,
            80,
        )
        if swingArc <= 5:
            realSwingArc = swingArcs[swingArc]
        elif swingArc in (11, 15):
            realSwingArc = 0
        else:
            realSwingArc = 100  # infinite

        # angle starts at the right position (3 o'clock)
        # negative = clockwise, positive = counter-clockwise
        startAngle = 90 - realSwingArc
        spanAngle = realSwingArc * 2

        self.aux[0].SetAngle(startAngle, spanAngle)
        self.aux[0].setPos((self.width / 1.5) - 36, -36)
        self.aux[0].update()

    def paint(self, painter):
        if self.image is None:
            return

        painter.drawPixmap(0, 0, self.image)


class ActorImage_FallingPlatform(ActorImage_WoodenPlatform):  # 50
    def __init__(self, parent):
        super().__init__(parent, 1.5)

    def dataChanged(self):
        # get width
        raw_width = self.parent.actordata[5] & 0xF
        slow = (self.parent.actordata[5] >> 4) & 1

        self.width = ((raw_width + 1) << 4) + (4 / 1.5)
        if raw_width == 0:
            # override this for the "glitchy" effect caused by length=0
            self.width = 24
            self.xOffset = -4
        else:
            if slow:
                self.xOffset = 0
            else:
                self.xOffset = -16 * (raw_width >> 1) - 2 / 1.5

        # set color
        color = (self.parent.actordata[3] >> 4) & 3
        self.height = 16 # reset so the image isn't too big after using the bone platform
        if color == 1:
            self.color = 1
        elif color == 3:
            self.color = 2
            self.height = 20
        else:
            self.color = 0


class ActorImage_TiltingGirder(actorlib.ActorImage_Static):  # 51
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['TiltingGirder'],
            (-1 / 1.5, -28 / 1.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('TiltingGirder', 'tilting_girder.png')


class ActorImage_UnusedRotPlatforms(actorlib.ActorImage):  # 52
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        posList = [(-60, -144), (-60, 144), (-204, 0), (84, 0)]
        for index in range(4):
            img = actorlib.AuxiliaryImage(parent, 144, 24)
            img.setPos(posList[index][0], posList[index][1])
            img.image = ImageCache["UnusedRotPlatform"]
            self.aux.append(img)

    @staticmethod
    def loadImages():
        if 'UnusedRotPlatform' in ImageCache:
            return

        actorlib.loadIfNotInImageCache('UnusedPlatformDark', 'unused_platform_dark.png')

        platform = ImageCache['UnusedPlatformDark'].scaled(
            144, 24,
            Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation,
        )
        img = QtGui.QPixmap(144, 24)
        img.fill(Qt.GlobalColor.transparent)
        paint = QtGui.QPainter(img)
        paint.setOpacity(0.8)
        paint.drawPixmap(0, 0, platform)
        ImageCache['UnusedRotPlatform'] = img


class ActorImage_Quicksand(ActorImage_LiquidOrFog):  # 53
    def __init__(self, parent):
        super().__init__(parent)

        self.crest = ImageCache['LiquidSandCrest']
        self.mid = ImageCache['LiquidSand']

        self.top = self.parent.objy + 8

    @staticmethod
    def loadImages():
        if 'LiquidSand' in ImageCache:
            return
        ImageCache['LiquidSand'] = actorlib.GetPixmap('liquid_sand.png')
        ImageCache['LiquidSandCrest'] = actorlib.GetPixmap('liquid_sand_crest.png')

    def dataChanged(self):
        self.locId = self.parent.actordata[5] & 0x7F
        self.drawCrest = self.parent.actordata[4] & 8 == 0

        if self.drawCrest:
            self.top = self.parent.objy + 8
        else:
            self.top = self.parent.objy

        super().dataChanged()

    def positionChanged(self):
        if self.drawCrest:
            self.top = self.parent.objy + 8
        else:
            self.top = self.parent.objy

        super().positionChanged()


class ActorImage_Lakitu(actorlib.ActorImage_Static):  # 54
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Lakitu'],
            (-16, -24),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Lakitu', 'lakitu.png')


class ActorImage_UnusedRisingSeesaw(actorlib.ActorImage_StaticMultiple):  # 55
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['UnusedPlatformDark'].scaled(
                168, 24,
                Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation,
            ),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('UnusedPlatformDark', 'unused_platform_dark.png')

    def dataChanged(self):
        midway = (self.parent.actordata[3] >> 4) & 1
        if midway:
            self.alpha = 0.5
        else:
            self.alpha = 1.0


class ActorImage_RisingTiltGirder(actorlib.ActorImage_StaticMultiple):  # 56
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['RisingTiltGirder'],
            (-32, -10),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RisingTiltGirder', 'rising_girder.png')

    def dataChanged(self):
        midway = self.parent.actordata[5] & 1
        if midway:
            self.alpha = 0.5
        else:
            self.alpha = 1.0


class ActorImage_KoopaTroopa(actorlib.ActorImage_StaticMultiple):  # 57
    @staticmethod
    def loadImages():
        if 'KoopaG' in ImageCache:
            return
        ImageCache['KoopaG'] = actorlib.GetPixmap('koopa_green.png')
        ImageCache['KoopaR'] = actorlib.GetPixmap('koopa_red.png')
        ImageCache['KoopaShellG'] = actorlib.GetPixmap('koopa_green_shell.png')
        ImageCache['KoopaShellR'] = actorlib.GetPixmap('koopa_red_shell.png')

    def dataChanged(self):
        # get properties
        props = self.parent.actordata[5]
        shell = (props >> 4) & 1 or (self.parent.actordata[2] >> 4) != 0
        red = props & 1

        if not shell:
            self.offset = (-7, -15)
            self.image = ImageCache['KoopaG'] if not red else ImageCache['KoopaR']
        else:
            del self.offset
            self.image = ImageCache['KoopaShellG'] if not red else ImageCache['KoopaShellR']

        super().dataChanged()


class ActorImage_KoopaParatroopa(actorlib.ActorImage_StaticMultiple):  # 58
    def __init__(self, parent):
        super().__init__(parent, 1.5, None, (-7, -12))
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 0, 0, 0))

    @staticmethod
    def loadImages():
        if 'ParakoopaG' not in ImageCache:
            ImageCache['ParakoopaG'] = actorlib.GetPixmap('parakoopa_green.png')
            ImageCache['ParakoopaR'] = actorlib.GetPixmap('parakoopa_red.png')
        if 'KoopaShellG' not in ImageCache:
            ImageCache['KoopaShellG'] = actorlib.GetPixmap('koopa_green_shell.png')
            ImageCache['KoopaShellR'] = actorlib.GetPixmap('koopa_red_shell.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        # get properties
        color = self.parent.actordata[5] & 1
        mode = (self.parent.actordata[5] >> 4) & 3

        # 0: jumping
        # 3: shell
        if color == 0:
            if mode == 3:
                del self.offset
                self.image = ImageCache['KoopaShellG']
            else:
                self.offset = (-7, -12)
                self.image = ImageCache['ParakoopaG']
        else:
            if mode == 3:
                del self.offset
                self.image = ImageCache['KoopaShellR']
            else:
                self.offset = (-7, -12)
                self.image = ImageCache['ParakoopaR']

        if mode == 1 or mode == 2:
            track = self.aux[0]
            turnImmediately = self.parent.actordata[4] & 1 == 1

            if mode == 1:
                track.direction = actorlib.AuxiliaryTrackObject.Horizontal
                track.setSize(9 * 16, 16)
                if turnImmediately:
                    track.setPos(self.width / 2, self.height / 2)
                else:
                    track.setPos(-4 * 24 + self.width / 2, self.height / 2)
            else:
                track.direction = actorlib.AuxiliaryTrackObject.Vertical
                track.setSize(16, 9 * 16)
                if turnImmediately:
                    track.setPos(self.width / 2, self.height / 2)
                else:
                    track.setPos(self.width / 2, -4 * 24 + self.height / 2)

        else:
            # hide the track
            self.aux[0].setSize(0, 0)

        super().dataChanged()


class ActorImage_LineTiltGirder(actorlib.ActorImage_StaticMultiple):  # 59
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['LineGirder'],
            (-13 / 1.5, -14),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LineGirder', 'line_tilt_girder.png')

    def dataChanged(self):
        midway = (self.parent.actordata[3] >> 4) & 1
        self.alpha = 0.5 if midway else 1.0


class ActorImage_SpikeTop(actorlib.ActorImage_StaticMultiple):  # 60
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SpikeTop00'],
            (0, -4),
        )

    @staticmethod
    def loadImages():
        if 'SpikeTop00' in ImageCache:
            return
        SpikeTop = actorlib.GetImage('spiketop.png')
        if SpikeTop is None:
            return

        Transform = QtGui.QTransform()
        ImageCache['SpikeTop00'] = QtGui.QPixmap.fromImage(SpikeTop.mirrored(True, False))
        Transform.rotate(-90)
        ImageCache['SpikeTop10'] = ImageCache['SpikeTop00'].transformed(Transform)
        Transform.rotate(-90)
        ImageCache['SpikeTop20'] = ImageCache['SpikeTop00'].transformed(Transform)
        Transform.rotate(-90)
        ImageCache['SpikeTop30'] = ImageCache['SpikeTop00'].transformed(Transform)

        Transform = QtGui.QTransform()
        ImageCache['SpikeTop01'] = QtGui.QPixmap.fromImage(SpikeTop)
        Transform.rotate(-90)
        ImageCache['SpikeTop11'] = ImageCache['SpikeTop01'].transformed(Transform)
        Transform.rotate(-90)
        ImageCache['SpikeTop21'] = ImageCache['SpikeTop01'].transformed(Transform)
        Transform.rotate(-90)
        ImageCache['SpikeTop31'] = ImageCache['SpikeTop01'].transformed(Transform)

    def dataChanged(self):
        orientation = (self.parent.actordata[5] >> 4) & 3
        direction = self.parent.actordata[5] & 1

        self.image = ImageCache[f'SpikeTop{orientation}{direction}']

        self.offset = (
            (0, -4),
            (-4, 0),
            (0, 0),
            (0, 0),
        )[orientation]

        super().dataChanged()


class ActorImage_BigBoo(actorlib.ActorImage):  # 61
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        bigBooAuxImage = actorlib.AuxiliaryImage(parent, 243, 248)
        bigBooAuxImage.image = ImageCache['BigBoo']
        bigBooAuxImage.setPos(-48, -48)
        bigBooAuxImage.hover = False
        self.aux.append(bigBooAuxImage)

        self.dimensions = (-38, -80, 98, 102)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BigBoo', 'bigboo.png')


class ActorImage_SpinningFirebar(actorlib.ActorImage):  # 62
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False
        self.aux.append(actorlib.AuxiliaryCircleOutline(parent, 12, Qt.AlignmentFlag.AlignCenter))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FirebarBase', 'firebar_base_0.png')
        actorlib.loadIfNotInImageCache('FirebarBaseWide', 'firebar_base_1.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryCircleOutline):
            return

        size = self.parent.actordata[5] & 0xF
        wideBase = (self.parent.actordata[3] >> 4) & 1

        width = ((size * 2) + 1) * 12
        self.aux[0].setSize(width)

        currentAuxX = self.aux[0].x()
        currentAuxY = self.aux[0].y()
        if wideBase:
            self.aux[0].setPos(currentAuxX + 12, currentAuxY)

        self.image = ImageCache['FirebarBase'] if not wideBase else ImageCache['FirebarBaseWide']
        self.xOffset = 0 if not wideBase else -8
        self.width = 16 if not wideBase else 32

    def paint(self, painter):
        if self.image is None:
            return

        painter.drawPixmap(0, 0, self.image)


class ActorImage_SpikeBall(actorlib.ActorImage_Static):  # 63
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SpikeBall'],
            (0, 16)
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpikeBall', 'spike_ball.png')


class ActorImage_OutdoorsFog(ActorImage_LiquidOrFog):  # 64
    def __init__(self, parent):
        super().__init__(parent)
        self.mid = ImageCache['OutdoorsFog']
        self.top = self.parent.objy

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('OutdoorsFog', 'fog_outdoors.png')

    def dataChanged(self):
        self.locId = self.parent.actordata[5] & 0x7F
        super().dataChanged()

    def positionChanged(self):
        self.top = self.parent.objy
        super().positionChanged()


class ActorImage_PipePiranhaUp(actorlib.ActorImage_Static):  # 65
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PipePlantUp'],
            (4 / 1.5, -30),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PipePlantUp', 'piranha_pipe_up.png')


class ActorImage_PipePiranhaDown(actorlib.ActorImage_Static):  # 66
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PipePlantDown'],
            (4 / 1.5, 32),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PipePlantDown', 'piranha_pipe_down.png')


class ActorImage_PipePiranhaRight(actorlib.ActorImage_Static):  # 67
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PipePlantRight'],
            (32, 4 / 1.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PipePlantRight', 'piranha_pipe_right.png')


class ActorImage_PipePiranhaLeft(actorlib.ActorImage_Static):  # 68
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PipePlantLeft'],
            (-30, 4 / 1.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PipePlantLeft', 'piranha_pipe_left.png')


class ActorImage_PipeFiretrapUp(actorlib.ActorImage_Static):  # 69
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PipeFiretrapUp'],
            (-8 / 1.5, -26),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PipeFiretrapUp', 'firetrap_pipe_up.png')


class ActorImage_PipeFiretrapDown(actorlib.ActorImage_Static):  # 70
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PipeFiretrapDown'],
            (-8 / 1.5, 32),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PipeFiretrapDown', 'firetrap_pipe_down.png')


class ActorImage_PipeFiretrapRight(actorlib.ActorImage_Static):  # 71
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PipeFiretrapRight'],
            (32, 10 / 1.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PipeFiretrapRight', 'firetrap_pipe_right.png')


class ActorImage_PipeFiretrapLeft(actorlib.ActorImage_Static):  # 72
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PipeFiretrapLeft'],
            (-26, 10 / 1.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PipeFiretrapLeft', 'firetrap_pipe_left.png')


class ActorImage_GroundPiranha(actorlib.ActorImage_StaticMultiple):  # 73
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.xOffset = -20

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GroundPiranha', 'ground_piranha.png')
        actorlib.loadIfNotInImageCache('GroundPiranhaU', 'ground_piranha_ceiling.png')

    def dataChanged(self):

        upsideDown = self.parent.actordata[5] & 1
        if not upsideDown:
            self.yOffset = 14 / 1.5
            self.image = ImageCache['GroundPiranha']
        else:
            self.yOffset = -2 / 1.5
            self.image = ImageCache['GroundPiranhaU']

        super().dataChanged()


class ActorImage_BigGroundPiranha(actorlib.ActorImage_StaticMultiple):  # 74
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.xOffset = -64

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BigGroundPiranha', 'big_ground_piranha.png')
        actorlib.loadIfNotInImageCache('BigGroundPiranhaU', 'big_ground_piranha_ceiling.png')

    def dataChanged(self):

        upsideDown = self.parent.actordata[5] & 1
        if not upsideDown:
            self.yOffset = -46 / 1.5
            self.image = ImageCache['BigGroundPiranha']
        else:
            self.yOffset = -4 / 1.5
            self.image = ImageCache['BigGroundPiranhaU']

        super().dataChanged()


class ActorImage_GroundFiretrap(actorlib.ActorImage_StaticMultiple):  # 75
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.xOffset = 5

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GroundFiretrap', 'ground_firetrap.png')
        actorlib.loadIfNotInImageCache('GroundFiretrapU', 'ground_firetrap_ceiling.png')

    def dataChanged(self):

        upsideDown = self.parent.actordata[5] & 1
        if not upsideDown:
            self.yOffset = -13 / 1.5
            self.image = ImageCache['GroundFiretrap']
        else:
            self.yOffset = -2 / 1.5
            self.image = ImageCache['GroundFiretrapU']

        super().dataChanged()


class ActorImage_BigGroundFiretrap(actorlib.ActorImage_StaticMultiple):  # 76
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.xOffset = -12

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BigGroundFiretrap', 'big_ground_firetrap.png')
        actorlib.loadIfNotInImageCache('BigGroundFiretrapU', 'big_ground_firetrap_ceiling.png')

    def dataChanged(self):

        upsideDown = self.parent.actordata[5] & 1
        if not upsideDown:
            self.yOffset = -100 / 1.5
            self.image = ImageCache['BigGroundFiretrap']
        else:
            self.yOffset = -4 / 1.5
            self.image = ImageCache['BigGroundFiretrapU']

        super().dataChanged()


class ActorImage_ShipKey(actorlib.ActorImage_Static):  # 77
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ShipKey'],
            (0, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ShipKey', 'ship_key.png')


class ActorImage_CloudTrampoline(actorlib.ActorImage_StaticMultiple):  # 78
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CloudTrSmall'],
            (-2, -2),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CloudTrBig', 'cloud_trampoline_big.png')
        actorlib.loadIfNotInImageCache('CloudTrSmall', 'cloud_trampoline_small.png')

    def dataChanged(self):

        size = (self.parent.actordata[4] >> 4) & 1
        if size == 0:
            self.image = ImageCache['CloudTrSmall']
        else:
            self.image = ImageCache['CloudTrBig']

        super().dataChanged()


class ActorImage_FireBro(actorlib.ActorImage_Static):  # 80
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FireBro'],
            (-8, -22),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FireBro', 'firebro.png')


class ActorImage_OldStoneBlock_SpikesLeft(ActorImage_OldStoneBlock):  # 81
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.spikesL = True


class ActorImage_OldStoneBlock_SpikesRight(ActorImage_OldStoneBlock):  # 82
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.spikesR = True


class ActorImage_OldStoneBlock_SpikesLeftRight(ActorImage_OldStoneBlock):  # 83
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.spikesL = True
        self.spikesR = True


class ActorImage_OldStoneBlock_SpikesTop(ActorImage_OldStoneBlock):  # 84
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.spikesT = True


class ActorImage_OldStoneBlock_SpikesBottom(ActorImage_OldStoneBlock):  # 85
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.spikesB = True


class ActorImage_OldStoneBlock_SpikesTopBottom(ActorImage_OldStoneBlock):  # 86
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.spikesT = True
        self.spikesB = True


class ActorImage_TrampolineWall(actorlib.ActorImage_StaticMultiple):  # 87
    def __init__(self, parent):
        super().__init__(parent, 1.5)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('UnusedPlatformDark', 'unused_platform_dark.png')

    def dataChanged(self):
        height = (self.parent.actordata[5] & 15) + 1

        self.image = ImageCache['UnusedPlatformDark'].scaled(
            24, height * 24,
            Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation,
        )
        self.height = height * 16

        super().dataChanged()


class ActorImage_BulletBillLauncher(actorlib.ActorImage):  # 92
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BBLauncherT', 'bullet_launcher_top.png')
        actorlib.loadIfNotInImageCache('BBLauncherM', 'bullet_launcher_middle.png')

    def dataChanged(self):
        height = (self.parent.actordata[5] & 0xF0) >> 4

        self.height = (height + 2) * 16
        self.yOffset = (height + 1) * -16

    def paint(self, painter):
        painter.drawPixmap(0, 0, ImageCache['BBLauncherT'])
        painter.drawTiledPixmap(0, 48, 24, int(self.height * 1.5 - 48), ImageCache['BBLauncherM'])


class ActorImage_BanzaiBillLauncher(actorlib.ActorImage_Static):  # 93
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['BanzaiLauncher'],
            (-32, -67),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BanzaiLauncher', 'banzai_launcher.png')


class ActorImage_BoomerangBro(actorlib.ActorImage_Static):  # 94
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['BoomerangBro'],
            (-8, -22),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BoomerangBro', 'boomerangbro.png')


class ActorImage_HammerBroNormal(actorlib.ActorImage_Static):  # 95
    def __init__(self, parent, scale=1.5):
        super().__init__(
            parent,
            scale,
            ImageCache['HammerBro'],
            (-4, -21)
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('HammerBro', 'hammerbro.png')


class ActorImage_RotationControllerSwaying(actorlib.ActorImage):  # 96
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.parent.setZValue(100000)
        self.aux.append(actorlib.AuxiliaryRotationAreaOutline(parent, 48))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryRotationAreaOutline):
            return

        # get the swing arc: 4 == 90 degrees (45 left from the origin, 45 right)
        swingArc = self.parent.actordata[2] >> 4
        realSwingArc = swingArc * 11.25

        # angle starts at the right position (3 o'clock)
        # negative = clockwise, positive = counter-clockwise
        startAngle = 90 - realSwingArc
        spanAngle = realSwingArc * 2

        self.aux[0].SetAngle(startAngle, spanAngle)
        self.aux[0].update()


class ActorImage_RotationControlledSolidBetaPlatform(ActorImage_UnusedBlockPlatform):  # 97
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.isDark = True

    def dataChanged(self):
        width = (self.parent.actordata[3] & 1) << 4 | (self.parent.actordata[4] >> 4)
        height = self.parent.actordata[4] & 0xF

        if width == 0 or height == 0:
            self.actorbox.shown = True
            self.drawPlatformImage = False
            del self.size
        else:
            self.actorbox.shown = False
            self.drawPlatformImage = True
            self.size = (width * 16, height * 16)


class ActorImage_GiantSpikeBall(actorlib.ActorImage_Static):  # 98
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantSpikeBall'],
            (-24, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantSpikeBall', 'giant_spike_ball.png')


class ActorImage_PipeEnemyGenerator(actorlib.ActorImage):  # 99
    def __init__(self, parent):
        super().__init__(parent, 1.5)

    def dataChanged(self):
        self.actorbox.size = (16, 16)
        direction = (self.parent.actordata[5] & 0xF) & 3
        if direction in (0, 1):  # vertical pipe
            self.actorbox.size = (32, 16)
        elif direction in (2, 3):  # horizontal pipe
            self.actorbox.size = (16, 32)

        self.yOffset = 0
        if direction in (2, 3):
            self.yOffset = -16


class ActorImage_Swooper(actorlib.ActorImage_Static):  # 100
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Swooper'],
            (2, 0),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Swooper', 'swooper.png')


class ActorImage_Bobomb(actorlib.ActorImage_Static):  # 101
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Bobomb'],
            (-8, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Bobomb', 'bobomb.png')


class ActorImage_Broozer(actorlib.ActorImage_Static):  # 102
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Broozer'],
            (-9, -17),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Broozer', 'broozer.png')


class ActorImage_PlatformGenerator(ActorImage_WoodenPlatform):  # 103
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.yOffset = 16
        self.aux.append(actorlib.AuxiliaryImage(parent, 24, 24))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        self.width = self.parent.actordata[5] & 0xF0
        direction = self.parent.actordata[3] & 0xF

        # adjust offset since each direction is slightly different
        if direction == 0: # up
            self.yOffset = 22 / 1.5
        elif direction == 1: # down
            self.yOffset = -22 / 1.5
        else: # right, left
            self.yOffset = 0

        # setup direction preview arrow
        self.showArrow = True
        self.arrowDir = direction

        # length 0 results in the same width as length 4
        if self.width == 0:
            self.width = 64

        # override the x offset for the "glitchy" effect caused by length 0
        if self.width in {16, 24}:
            self.width = 24
            self.xOffset = -4
        else:
            self.width += 4 / 1.5
            self.xOffset = -2 / 1.5

        self.color = 0

        # Draw a direction arrow
        dirStr = ('Up', 'Down', 'Right', 'Left')[self.arrowDir % 4]
        self.aux[0].image = ImageCache[f'DirectionArrow{dirStr}']
        self.aux[0].setPos(int(((self.width - 16) / 2) * 1.5), 0)

        self.aux[0].setIsBehindActor(False)
        self.aux[0].alpha = 0.25
        self.aux[0].hover = False


class ActorImage_AmpNormal(ActorImage_Amp):  # 104
    pass


class ActorImage_Pokey(actorlib.ActorImage):  # 105
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        self.dimensions = (-4, 0, 24, 32)

    @staticmethod
    def loadImages():
        if 'PokeyTop' in ImageCache:
            return
        ImageCache['PokeyTop'] = actorlib.GetPixmap('pokey_top.png')
        ImageCache['PokeyMiddle'] = actorlib.GetPixmap('pokey_middle.png')
        ImageCache['PokeyBottom'] = actorlib.GetPixmap('pokey_bottom.png')

    def dataChanged(self):
        # get the height
        height = self.parent.actordata[5] & 7
        self.height = (height * 16) + 16 + 25
        self.yOffset = 16 - self.height

    def paint(self, painter):
        painter.drawPixmap(0, 0, ImageCache['PokeyTop'])
        painter.drawTiledPixmap(0, 37, 36, int(self.height * 1.5 - 61), ImageCache['PokeyMiddle'])
        painter.drawPixmap(0, int(self.height * 1.5 - 24), ImageCache['PokeyBottom'])


class ActorImage_LinePlatform(ActorImage_WoodenPlatform):  # 106
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.yOffset = 8

    def dataChanged(self):
        # get width
        self.width = (self.parent.actordata[5] & 0xF) << 4

        # length=0 becomes length=4
        if self.width == 0:
            self.width = 64
        # override this for the "glitchy" effect caused by length=0
        if self.width == 16:
            self.width = 24

        # reposition platform
        self.xOffset = 32 - (self.width / 2) - (2 / 1.5)

        if self.width == 0 or self.width > 24:
            self.width += 4 / 1.5
        else:
            self.xOffset += 2 / 1.5

        color = (self.parent.actordata[4] & 0xF0) >> 4
        if color > 1:
            color = 0
        self.color = color


class ActorImage_RotationControlledPassBetaPlatform(ActorImage_UnusedBlockPlatform):  # 107
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.isDark = True
        self.width = 16

    def dataChanged(self):
        size = self.parent.actordata[4]
        height = (size & 0xF) + 1

        self.yOffset = -(height - 1) * 8
        self.height = height * 16


class ActorImage_AmpLine(ActorImage_Amp):  # 108
    pass


class ActorImage_ChainBall(actorlib.ActorImage_StaticMultiple):  # 109
    def __init__(self, parent):
        super().__init__(parent, 1.5)

    @staticmethod
    def loadImages():
        if 'ChainBallU' in ImageCache:
            return
        ImageCache['ChainBallU'] = actorlib.GetPixmap('chainball_up.png')
        ImageCache['ChainBallR'] = actorlib.GetPixmap('chainball_right.png')
        ImageCache['ChainBallD'] = actorlib.GetPixmap('chainball_down.png')
        ImageCache['ChainBallL'] = actorlib.GetPixmap('chainball_left.png')

    def dataChanged(self):
        direction = self.parent.actordata[5] & 3
        if direction > 3:
            direction = 0

        if direction & 1 == 0:  # horizontal
            self.size = (96, 38)
        else:  # vertical
            self.size = (37, 96)

        if direction == 0:  # right
            self.image = ImageCache['ChainBallR']
            self.offset = (3, -8.5)
        elif direction == 1:  # up
            self.image = ImageCache['ChainBallU']
            self.offset = (-8.5, -81.5)
        elif direction == 2:  # left
            self.image = ImageCache['ChainBallL']
            self.offset = (-83, -11)
        elif direction == 3:  # down
            self.image = ImageCache['ChainBallD']
            self.offset = (-11, 3.5)

        super().dataChanged()


class ActorImage_Sunlight(actorlib.ActorImage):  # 110
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        i = ImageCache['Sunlight']
        sunlightAux = actorlib.AuxiliaryImage_FollowsRect(parent, i.width(), i.height())
        sunlightAux.realimage = i
        sunlightAux.alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        sunlightAux.hover = False
        self.aux.append(sunlightAux)

        # Moving the sunlight when a repaint occured is overkill and causes an
        # infinite loop. Alternative idea: Only move the sunlight when
        # - scrolling or
        # - zooming
        # This causes small visual bugs while moving the actor, but moving this
        # actor makes little sense, so I guess it's fine.

        slot = self.moveSunlight

        # scrolling
        scene = self.parent.scene()
        if scene is None:
            return
        view = scene.views()[0]
        horizontalScrollBar = view.horizontalScrollBar()
        verticalScrollBar = view.verticalScrollBar()
        if horizontalScrollBar is None or verticalScrollBar is None:
            return
        horizontalScrollBar.valueChanged.connect(slot)
        verticalScrollBar.valueChanged.connect(slot)

        # zooming
        mainWindow = scene.getMainWindow()
        if mainWindow is None:
            return
        mainWindow.ZoomWidget.slider.valueChanged.connect(slot)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Sunlight', 'sunlight.png')

    def paint(self, painter):
        self.moveSunlight()
        actorlib.ActorImage.paint(self, painter)

    def moveSunlight(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage_FollowsRect):
            return

        try:
            actorlib.loadIfNotInImageCache('Sunlight', 'sunlight.png')

            if not actorlib.RealViewEnabled:
                self.aux[0].realimage = None
                return

            zone = self.parent.nearestZone(True)
            if zone is None:
                self.aux[0].realimage = None
                return

            if not isinstance(zone, ZoneItem):
                return

            zoneRect = QtCore.QRectF(zone.objx * 1.5, zone.objy * 1.5, zone.width * 1.5, zone.height * 1.5)
            scene = self.parent.scene()
            if scene is None:
                return
            view = scene.views()[0]
            viewport = view.viewport()
            if viewport is None:
                return
            viewRect = view.mapToScene(viewport.rect()).boundingRect()
            bothRect = zoneRect & viewRect

            if bothRect.getRect() == (0, 0, 0, 0):
                # The zone is out of view -> hide the image
                self.aux[0].realimage = None
                return

            self.aux[0].realimage = ImageCache['Sunlight']
            self.aux[0].move(*bothRect.getRect())
        except RuntimeError:
            # happens if the parent was deleted
            pass


class ActorImage_Blooper(actorlib.ActorImage_Static):  # 111
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Blooper'],
            (-3, -10),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Blooper', 'blooper.png')


class ActorImage_BlooperBabies(actorlib.ActorImage_Static):  # 112
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['BlooperBabies'],
            (-5, -10),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BlooperBabies', 'blooper_babies.png')


class ActorImage_Flagpole(actorlib.ActorImage):  # 113
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        self.image = ImageCache['Flagpole']

        self.aux.append(actorlib.AuxiliaryImage(parent, 144, 149))
        self.offset = (-34, -144)
        self.size = (73 / 1.5, 160)

    @staticmethod
    def loadImages():
        if 'Flagpole' in ImageCache:
            return
        ImageCache['Flagpole'] = actorlib.GetPixmap('flagpole.png')
        ImageCache['FlagpoleSecret'] = actorlib.GetPixmap('flagpole_secret.png')
        ImageCache['Castle'] = actorlib.GetPixmap('castle.png')
        ImageCache['CastleSecret'] = actorlib.GetPixmap('castle_secret.png')
        ImageCache['SnowCastle'] = actorlib.GetPixmap('snow_castle.png')
        ImageCache['SnowCastleSecret'] = actorlib.GetPixmap('snow_castle_secret.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        # get the info (mimic the way the game does it)
        exit_type = self.parent.actordata[2] >> 4
        snow_type = self.parent.actordata[5] & 0xF
        value = exit_type + snow_type * 2

        if value == 0:
            show_snow = show_secret = False
        elif value == 1:
            show_snow = False
            show_secret = True
        elif value == 2:
            show_snow = True
            show_secret = False
        else:
            show_snow = show_secret = True

        if show_secret:
            suffix = "Secret"
        else:
            suffix = ""

        self.image = ImageCache['Flagpole' + suffix]

        if show_snow:
            self.aux[0].image = ImageCache['SnowCastle' + suffix]
            self.aux[0].setPos(362, 94)
        else:
            self.aux[0].image = ImageCache['Castle' + suffix]
            self.aux[0].setPos(362, 101)

    def paint(self, painter):
        if self.image is None:
            return

        painter.drawPixmap(0, 0, self.image)


class ActorImage_FlameCannon(actorlib.ActorImage_StaticMultiple):  # 114
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        self.height = 64

    @staticmethod
    def loadImages():
        if 'FlameCannonR' in ImageCache:
            return
        transform90 = QtGui.QTransform()
        transform270 = QtGui.QTransform()
        transform90.rotate(90)
        transform270.rotate(270)

        image = actorlib.GetImage('continuous_flame_cannon.png')
        if image is None:
            return

        ImageCache['FlameCannonR'] = QtGui.QPixmap.fromImage(image)
        ImageCache['FlameCannonD'] = QtGui.QPixmap.fromImage(image.transformed(transform90))
        ImageCache['FlameCannonL'] = QtGui.QPixmap.fromImage(image.mirrored(True, False))
        ImageCache['FlameCannonU'] = QtGui.QPixmap.fromImage(image.transformed(transform270).mirrored(True, False))

    def dataChanged(self):
        direction = self.parent.actordata[5] & 15
        if direction > 3:
            direction = 0

        if direction == 0:  # right
            del self.offset
        elif direction == 1:  # left
            self.offset = (-48, 0)
        elif direction == 2:  # up
            self.offset = (0, -48)
        elif direction == 3:  # down
            del self.offset

        directionstr = 'RLUD'[direction]
        self.image = ImageCache[f'FlameCannon{directionstr}']

        super().dataChanged()


class ActorImage_Cheep(actorlib.ActorImage):  # 115
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        self.aux.append(actorlib.AuxiliaryTrackObject(self.parent, 24, 24, actorlib.AuxiliaryTrackObject.Horizontal))

    @staticmethod
    def loadImages():
        if 'CheepGreen' in ImageCache:
            return
        ImageCache['CheepRedLeft'] = actorlib.GetPixmap('cheep_red.png')
        ImageCache['CheepRedRight'] = QtGui.QPixmap.fromImage(actorlib.GetImage('cheep_red.png').mirrored(True, False))
        ImageCache['CheepRedAtYou'] = actorlib.GetPixmap('cheep_red_atyou.png')
        ImageCache['CheepGreen'] = actorlib.GetPixmap('cheep_green.png')
        ImageCache['CheepYellow'] = actorlib.GetPixmap('cheep_yellow.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        type = self.parent.actordata[5] & 0xF
        if type in (1, 7):
            self.image = ImageCache['CheepGreen']
        elif type == 8:
            self.image = ImageCache['CheepYellow']
        elif type == 5:
            self.image = ImageCache['CheepRedAtYou']
        else:
            self.image = ImageCache['CheepRedLeft']
        self.size = (self.image.width() / 1.5, self.image.height() / 1.5)

        if type == 3:
            distance = ((self.parent.actordata[3] & 0xF) + 1) * 16
            self.aux[0].setSize((distance * 2) + 16, 16)
            self.aux[0].setPos(-distance * 1.5, 0)
        else:
            self.aux[0].setSize(0, 24)

    def paint(self, painter):
        if self.image is None:
            return

        painter.drawPixmap(0, 0, self.image)


class ActorImage_CoinCheep(actorlib.ActorImage):  # 116
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'CheepRedLeft' in ImageCache:
            return
        ImageCache['CheepRedLeft'] = actorlib.GetPixmap('cheep_red.png')
        ImageCache['CheepRedRight'] = QtGui.QPixmap.fromImage(actorlib.GetImage('cheep_red.png').mirrored(True, False))
        ImageCache['CheepRedAtYou'] = actorlib.GetPixmap('cheep_red_atyou.png')
        ImageCache['CheepGreen'] = actorlib.GetPixmap('cheep_green.png')
        ImageCache['CheepYellow'] = actorlib.GetPixmap('cheep_yellow.png')

    def dataChanged(self):

        waitFlag = self.parent.actordata[5] & 1
        if waitFlag:
            self.actorbox.shown = False
            self.image = ImageCache['CheepRedAtYou']
        else:
            type = self.parent.actordata[2] >> 4
            if type & 3 == 3:
                self.actorbox.shown = True
                self.image = None
            elif type < 7:
                self.actorbox.shown = False
                self.image = self.image = ImageCache['CheepRedRight']
            else:
                self.actorbox.shown = False
                self.image = self.image = ImageCache['CheepRedLeft']

        if self.image is not None:
            self.size = (self.image.width() / 1.5, self.image.height() / 1.5)

    def paint(self, painter):
        if self.image is None:
            return
        painter.drawPixmap(0, 0, self.image)


class ActorImage_PulseFlameCannon(actorlib.ActorImage_StaticMultiple):  # 117
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.height = 112

    @staticmethod
    def loadImages():
        if 'PulseFlameCannonR' in ImageCache:
            return
        transform90 = QtGui.QTransform()
        transform270 = QtGui.QTransform()
        transform90.rotate(90)
        transform270.rotate(270)

        onImage = actorlib.GetImage('synchro_flame_jet.png')
        if onImage is None:
            return

        ImageCache['PulseFlameCannonR'] = QtGui.QPixmap.fromImage(onImage)
        ImageCache['PulseFlameCannonD'] = QtGui.QPixmap.fromImage(onImage.transformed(transform90))
        ImageCache['PulseFlameCannonL'] = QtGui.QPixmap.fromImage(onImage.mirrored(True, False))
        ImageCache['PulseFlameCannonU'] = QtGui.QPixmap.fromImage(
            onImage.transformed(transform270).mirrored(True, False))

    def dataChanged(self):

        direction = self.parent.actordata[5] & 15
        if direction > 3:
            direction = 0

        if direction == 0:
            del self.offset
        elif direction == 1:
            self.offset = (-96, 0)
        elif direction == 2:
            self.offset = (0, -96)
        elif direction == 3:
            del self.offset

        directionstr = 'RLUD'[direction]
        self.image = ImageCache[f'PulseFlameCannon{directionstr}']

        super().dataChanged()


class ActorImage_DryBones(actorlib.ActorImage_Static):  # 118
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['DryBones'],
            (-7, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('DryBones', 'drybones.png')


class ActorImage_GiantDryBones(actorlib.ActorImage_Static):  # 119
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantDryBones'],
            (-13, -24),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantDryBones', 'giant_drybones.png')


class ActorImage_SledgeBro(actorlib.ActorImage_Static):  # 120
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SledgeBro'],
            (-8, -28.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SledgeBro', 'sledgebro.png')


# TODO: Properly implement 'down & right' track
class ActorImage_OneWayPlatform(ActorImage_WoodenPlatform):  # 122
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        width = self.parent.actordata[5] & 0xF
        if width < 2:
            width = 1
        self.width = width * 32 + 32

        self.aux.append(actorlib.AuxiliaryTrackObject(parent, self.width, 16, actorlib.AuxiliaryTrackObject.Horizontal))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        width = self.parent.actordata[5] & 0xF
        if width < 2:
            width = 1
        self.width = width * 32 + (52 / 1.5)

        self.xOffset = self.width * -0.5

        self.color = ((self.parent.actordata[4] & 0xF0) >> 4) & 1

        distance = (self.parent.actordata[3] & 0xF0) >> 4
        direction = self.parent.actordata[3] & 0xF

        if distance != 0 or direction != 4:
            if distance == 1:
                increment = 14
            else:
                increment = 16

            self.aux[0].setRotation(0)

            if direction <= 1:  # horizontal
                self.aux[0].direction = 2
                self.aux[0].setSize(self.width, self.height + (distance * 16 * increment))
            elif direction <= 3:  # vertical
                self.aux[0].direction = 1
                self.aux[0].setSize(self.width + (distance * 16 * increment), self.height)
            else:  # down & right
                self.aux[0].direction = 1
                self.aux[0].setSize((self.width - (16 * width)) + (distance * 16 * increment), self.height)
                self.aux[0].setRotation(45)

            if direction == 1 or direction == 2:  # right, down
                self.aux[0].setPos(0, 0)
            elif direction == 3:  # left
                self.aux[0].setPos(-(distance * increment) * 24, 0)
            elif direction == 0:  # up
                self.aux[0].setPos(0, -(distance * increment) * 24)
            else: # down & right
                self.aux[0].setPos(self.width + (16 * width), -8)
        else:
            self.aux[0].setSize(0, 0)


class ActorImage_UnusedCastlePlatform(actorlib.ActorImage):  # 123
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.parent.setZValue(24999)

        self.aux.append(actorlib.AuxiliaryImage(parent, 384, 410))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('UnusedCastlePlatform', 'unused_castle_platform.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        rawSize = self.parent.actordata[4] >> 4

        if rawSize != 0:
            widthInBlocks = rawSize * 4
        else:
            widthInBlocks = 8

        topRadiusInBlocks = widthInBlocks / 10
        heightInBlocks = widthInBlocks + topRadiusInBlocks

        self.aux[0].image = ImageCache['UnusedCastlePlatform'].scaled(widthInBlocks * 24, int(heightInBlocks * 24))
        self.aux[0].setPos(-(self.aux[0].image.width() / 2), (-topRadiusInBlocks * 16) * 1.5)


class ActorImage_FenceKoopaHorz(actorlib.ActorImage_StaticMultiple):  # 125
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-3, -12)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FenceKoopaHG', 'fencekoopa_horz.png')
        actorlib.loadIfNotInImageCache('FenceKoopaHR', 'fencekoopa_horz_red.png')

    def dataChanged(self):
        color = self.parent.actordata[5] & 1
        if color == 1:
            self.image = ImageCache['FenceKoopaHR']
        else:
            self.image = ImageCache['FenceKoopaHG']

        super().dataChanged()


class ActorImage_FenceKoopaVert(actorlib.ActorImage_StaticMultiple):  # 126
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        self.offset = (-2, -12)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FenceKoopaVG', 'fencekoopa_vert.png')
        actorlib.loadIfNotInImageCache('FenceKoopaVR', 'fencekoopa_vert_red.png')

    def dataChanged(self):

        color = self.parent.actordata[5] & 1
        if color == 1:
            self.image = ImageCache['FenceKoopaVR']
        else:
            self.image = ImageCache['FenceKoopaVG']

        super().dataChanged()


class ActorImage_FlipFence(actorlib.ActorImage_Static):  # 127
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FlipFence'],
            (-4, -8),
        )
        parent.setZValue(24999)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FlipFence', 'flipfence.png')


class ActorImage_FlipFenceLong(actorlib.ActorImage_Static):  # 128
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FlipFenceLong'],
            (4, 0),
        )
        parent.setZValue(24999)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FlipFenceLong', 'flipfence_long.png')


class ActorImage_4Spinner(actorlib.ActorImage_Static):  # 129
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['4Spinner'],
            (-97 / 1.5, -48),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('4Spinner', '4spinner.png')

    def dataChanged(self):
        super().dataChanged()
        self.alpha = 0.6 if (self.parent.actordata[2] >> 4) & 1 else 1


class ActorImage_Wiggler(actorlib.ActorImage_Static):  # 130
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Wiggler'],
            (0, -12),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Wiggler', 'wiggler.png')


class ActorImage_Boo(actorlib.ActorImage):  # 131
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        booAuxImage = actorlib.AuxiliaryImage(parent, 50, 51)
        booAuxImage.image = ImageCache['Boo1']
        booAuxImage.setPos(-6, -6)

        self.aux.append(booAuxImage)

        self.dimensions = (-1, -4, 22, 22)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Boo1', 'boo1.png')


class ActorImage_UnusedBlockPlatform1(ActorImage_UnusedBlockPlatform):  # 132
    def dataChanged(self):
        self.width = ((self.parent.actordata[5] & 0xF) + 1) * 16
        self.height = ((self.parent.actordata[5] >> 4) + 1) * 16


class ActorImage_StalagmitePlatform(actorlib.ActorImage):  # 133
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        stalagmiteAuxImage = actorlib.AuxiliaryImage(parent, 48, 156)
        stalagmiteAuxImage.image = ImageCache['StalagmitePlatformBottom']
        stalagmiteAuxImage.setPos(24, 60)

        self.aux.append(stalagmiteAuxImage)

        self.image = ImageCache['StalagmitePlatformTop']
        self.dimensions = (0, -8, 64, 40)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('StalagmitePlatformTop', 'stalagmite_platform_top.png')
        actorlib.loadIfNotInImageCache('StalagmitePlatformBottom', 'stalagmite_platform_bottom.png')

    def paint(self, painter):
        if self.image is None:
            return

        painter.drawPixmap(0, 0, self.image)


class ActorImage_Crow(actorlib.ActorImage_Static):  # 134
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Crow'],
            (-3, -2),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Crow', 'crow.png')


class ActorImage_HangingPlatform(actorlib.ActorImage_Static):  # 135
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        hangingPlatformAuxImage = actorlib.AuxiliaryImage(parent, 11, 378)
        hangingPlatformAuxImage.image = ImageCache['HangingPlatformTop']
        hangingPlatformAuxImage.setPos(138, -378)
        self.aux.append(hangingPlatformAuxImage)

        self.image = ImageCache['HangingPlatformBottom']
        self.size = (192, 32)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('HangingPlatformTop', 'hanging_platform_top.png')
        actorlib.loadIfNotInImageCache('HangingPlatformBottom', 'hanging_platform_bottom.png')


class ActorImage_RotBulletLauncher(actorlib.ActorImage):  # 136
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        self.dimensions = (-8 / 1.5, 0, 40 / 1.5, 16)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RotLauncherCannonL', 'bullet_cannon_rot_L.png')
        actorlib.loadIfNotInImageCache('RotLauncherCannonR', 'bullet_cannon_rot_R.png')
        actorlib.loadIfNotInImageCache('RotLauncherPivot', 'bullet_cannon_rot_P.png')

    def dataChanged(self):
        pieces = self.parent.actordata[3] & 15
        pieces = min(pieces, 7)
        self.yOffset = -pieces * 16
        self.height = (pieces + 1) * 16

    def paint(self, painter):
        pieces = (self.parent.actordata[3] & 15) + 1
        pieces = min(pieces, 8)
        pivot1_4 = self.parent.actordata[4] & 15
        pivot5_8 = self.parent.actordata[4] >> 4
        startleft1_4 = self.parent.actordata[5] & 15
        startleft5_8 = self.parent.actordata[5] >> 4

        pivots = [pivot1_4, pivot5_8]
        startleft = [startleft1_4, startleft5_8]

        ysize = self.height * 1.5

        for piece in range(pieces):
            bitpos = 1 << (piece & 3)
            if pivots[piece // 4] & bitpos:
                painter.drawPixmap(7, int(ysize - (piece + 1) * 24), ImageCache['RotLauncherPivot'])
            else:
                xo = 8
                image = ImageCache['RotLauncherCannonR']
                if startleft[piece // 4] & bitpos:
                    transform = QtGui.QTransform()
                    transform.rotate(180)
                    image = ImageCache['RotLauncherCannonL']
                    xo = 0
                painter.drawPixmap(xo, int(ysize - (piece + 1) * 24 - 1), image)


class ActorImage_SkewerDown(ActorImage_Skewer):  # 137
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.dir = 'down'
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 64, actorlib.AuxiliaryTrackObject.Vertical))

        self.dimensions = (0, 16 - self.VertSpikeLength, 66, self.VertSpikeLength)


class ActorImage_Water(ActorImage_LiquidOrFog):  # 138
    def __init__(self, parent):
        super().__init__(parent)

        self.crest = ImageCache['LiquidWaterCrest']
        self.mid = ImageCache['LiquidWater']
        self.rise = ImageCache['LiquidWaterRiseCrest']
        self.riseCrestless = ImageCache['LiquidWaterRise']

        self.top = self.parent.objy

    @staticmethod
    def loadImages():
        if 'LiquidWater' in ImageCache:
            return
        ImageCache['LiquidWater'] = actorlib.GetPixmap('liquid_water.png')
        ImageCache['LiquidWaterCrest'] = actorlib.GetPixmap('liquid_water_crest.png')
        ImageCache['LiquidWaterRise'] = actorlib.GetPixmap('liquid_water_rise.png')
        ImageCache['LiquidWaterRiseCrest'] = actorlib.GetPixmap('liquid_water_rise_crest.png')
        ImageCache['LiquidWaterFull'] = actorlib.GetPixmap('liquid_water_full.png')

    def dataChanged(self):
        self.locId = self.parent.actordata[5] & 0x7F
        self.drawCrest = self.parent.actordata[4] & 8 == 0

        self.risingHeight = (self.parent.actordata[3] & 0xF) << 4
        self.risingHeight |= self.parent.actordata[4] >> 4
        if self.parent.actordata[2] & 15 > 7:  # falling
            self.risingHeight = -self.risingHeight

        if not self.drawCrest and self.locId == 0:
            self.mid = ImageCache['LiquidWaterFull']
        else:
            self.mid = ImageCache['LiquidWater']

        super().dataChanged()

    def positionChanged(self):
        self.top = self.parent.objy
        super().positionChanged()


class ActorImage_Lava(ActorImage_LiquidOrFog):  # 139
    def __init__(self, parent):
        super().__init__(parent)

        self.crest = ImageCache['LiquidLavaCrest']
        self.mid = ImageCache['LiquidLava']
        self.rise = ImageCache['LiquidLavaRiseCrest']
        self.riseCrestless = ImageCache['LiquidLavaRise']

        self.top = self.parent.objy

    @staticmethod
    def loadImages():
        if 'LiquidLava' in ImageCache:
            return
        ImageCache['LiquidLava'] = actorlib.GetPixmap('liquid_lava.png')
        ImageCache['LiquidLavaCrest'] = actorlib.GetPixmap('liquid_lava_crest.png')
        ImageCache['LiquidLavaRise'] = actorlib.GetPixmap('liquid_lava_rise.png')
        ImageCache['LiquidLavaRiseCrest'] = actorlib.GetPixmap('liquid_lava_rise_crest.png')

    def dataChanged(self):
        self.locId = self.parent.actordata[5] & 0x7F
        self.drawCrest = self.parent.actordata[4] & 8 == 0

        self.risingHeight = (self.parent.actordata[3] & 0xF) << 4
        self.risingHeight |= self.parent.actordata[4] >> 4
        if self.parent.actordata[2] & 15 > 7:  # falling
            self.risingHeight = -self.risingHeight

        super().dataChanged()

    def positionChanged(self):
        self.top = self.parent.objy
        super().positionChanged()


class ActorImage_SkewerUp(ActorImage_Skewer):  # 140
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.dir = 'up'
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 64, actorlib.AuxiliaryTrackObject.Vertical))

        self.dimensions = (0, 0, 66, self.VertSpikeLength)


class ActorImage_SkewerRight(ActorImage_Skewer):  # 141
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.dir = 'right'
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 64, 16, actorlib.AuxiliaryTrackObject.Horizontal))

        self.dimensions = (16 - self.HorzSpikeLength, 0, self.HorzSpikeLength, 66)


class ActorImage_SkewerLeft(ActorImage_Skewer):  # 142
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.dir = 'left'
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 64, 16, actorlib.AuxiliaryTrackObject.Horizontal))

        self.dimensions = (0, 0, self.HorzSpikeLength, 66)


class ActorImage_Arrow(actorlib.ActorImage_StaticMultiple):  # 143
    def __init__(self, parent):
        super().__init__(parent, 1.5)

    @staticmethod
    def loadImages():
        if 'Arrow0' in ImageCache:
            return
        for i in range(8):
            ImageCache[f'Arrow{i}'] = actorlib.GetPixmap(f'arrow_{i}.png')

    def dataChanged(self):
        ArrowOffsets = [(4, 1), (7, 7), (1, 4), (7, -2), (4, 0), (-2, -2), (0, 4), (-2, 7)]

        direction = self.parent.actordata[5] & 7
        self.image = ImageCache[f'Arrow{direction}']

        self.width = self.image.width() / 1.5
        self.height = self.image.height() / 1.5
        # dividing here so the tuple looks more readable and the images can use pixels instead of units for their offsets
        self.offset = (ArrowOffsets[direction][0] / 1.5, ArrowOffsets[direction][1] / 1.5)

        super().dataChanged()


class ActorImage_RedCoin(actorlib.ActorImage_Static):  # 144
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['RedCoin'],
        )


class ActorImage_FloatingBarrel(actorlib.ActorImage_Static):  # 145
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            offset = (-16, -9)
        )

        img = ImageCache['FloatingBarrel']
        self.width = (img.width() / self.scale) + 1
        self.height = (img.height() / self.scale) + 2

        floatingBarrelAuxImage = actorlib.AuxiliaryImage(parent, img.width(), img.height())
        floatingBarrelAuxImage.image = img
        self.aux.append(floatingBarrelAuxImage)

        path = QtGui.QPainterPath()
        path.lineTo(QtCore.QPointF(self.width * 1.5, 0))

        self.aux.append(actorlib.AuxiliaryPainterPath(parent, path, img.width(),
            actorlib.OutlinePen.width() if actorlib.OutlinePen else 1, 0, 36))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FloatingBarrel', 'barrel_floating.png')

    def dataChanged(self):
        # Don't let actorlib.ActorImage_Static reset size
        actorlib.ActorImage.dataChanged(self)


class ActorImage_ChainChomp(actorlib.ActorImage_Static):  # 146
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ChainChomp'],
            (-90, -32),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ChainChomp', 'chain_chomp.png')


class ActorImage_Coin(actorlib.ActorImage_StaticMultiple):  # 147
    @staticmethod
    def loadImages():
        if 'CoinF' in ImageCache:
            return

        iceblock = actorlib.GetPixmap('iceblock00.png')
        if iceblock is None:
            return

        pix = QtGui.QPixmap(24, 24)
        pix.fill(Qt.GlobalColor.transparent)
        paint = QtGui.QPainter(pix)
        paint.setOpacity(0.9)
        paint.drawPixmap(0, 0, iceblock)
        paint.setOpacity(0.6)
        paint.drawPixmap(0, 0, ImageCache['Coin'])
        del paint
        ImageCache['CoinF'] = pix

        ImageCache['CoinBubble'] = actorlib.GetPixmap('coin_bubble.png')

    def dataChanged(self):
        type = self.parent.actordata[5] & 0xF

        if type == 0:
            self.image = ImageCache['Coin']
            self.offset = (0, 0)
        elif type == 0xF:
            self.image = ImageCache['CoinF']
            self.offset = (0, 0)
        elif type in (1, 2, 4):
            self.image = ImageCache['CoinBubble']
            self.offset = (-4, -4)
        else:
            self.image = ImageCache['SpecialCoin']
            self.offset = (0, 0)

        super().dataChanged()


class ActorImage_Spring(actorlib.ActorImage_Static):  # 148
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Spring'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Spring', 'spring.png')

    def dataChanged(self):
        offset = (self.parent.actordata[5] >> 4) & 1
        self.xOffset = 8 if offset else 0

        super().dataChanged()


class ActorImage_RotationControllerSpinning(actorlib.ActorImage):  # 149
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.parent.setZValue(100000)


class ActorImage_Porcupuffer(actorlib.ActorImage_Static):  # 151
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Porcupuffer'],
            (-16, -18),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Porcupuffer', 'porcu_puffer.png')


class ActorImage_QSwitchUnused(common.ActorImage_Switch):  # 153
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.switchType = 'Q'

    def dataChanged(self):
        self.offset = (0, 0)
        super().dataChanged()


class ActorImage_StarCoinLineControlled(ActorImage_StarCoin):  # 155
    pass


class ActorImage_RedCoinRing(actorlib.ActorImage):  # 156
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        redCoinRingAuxImage = actorlib.AuxiliaryImage(parent, 76, 95)
        redCoinRingAuxImage.image = ImageCache['RedCoinRing']
        redCoinRingAuxImage.setPos(-10, -15)
        redCoinRingAuxImage.hover = False
        self.aux.append(redCoinRingAuxImage)

        self.dimensions = (-10, -8, 37, 48)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RedCoinRing', 'redcoinring.png')

        overlays = (
            ('Fire', ImageCache['BlockContents3']),
            ('Prop', ImageCache['BlockContents4']),
            ('Peng', ImageCache['BlockContents5']),
            ('IceF', ImageCache['BlockContents15']),
        )
        for name, image in overlays:
            newPix = QtGui.QPixmap(ImageCache['RedCoinRing'])
            painter = QtGui.QPainter(newPix)
            painter.setOpacity(0.8)
            painter.drawPixmap(26, 36, image)
            del painter
            ImageCache['RedCoinRing' + name] = newPix

    def dataChanged(self):
        item = (self.parent.actordata[5] >> 4) & 0x3
        shifted = self.parent.actordata[5] & 1
        self.xOffset = -2 if shifted else -10

        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        itemStrs = ('Fire', 'Prop', 'Peng', 'IceF')
        self.aux[0].image = ImageCache['RedCoinRing' + itemStrs[item]]


class ActorImage_BigBrick(actorlib.ActorImage_StaticMultiple):  # 157
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BigBrick', 'big_brick.png')
        actorlib.loadIfNotInImageCache('ShipKey', 'ship_key.png')
        actorlib.loadIfNotInImageCache('5Coin', '5_coin.png')

        if 'YoshiFire' not in ImageCache:
            pix = QtGui.QPixmap(48, 24)
            pix.fill(Qt.GlobalColor.transparent)
            paint = QtGui.QPainter(pix)
            paint.drawPixmap(0, 0, ImageCache['BlockContents9'])
            paint.drawPixmap(24, 0, ImageCache['BlockContents3'])
            del paint
            ImageCache['YoshiFire'] = pix

        for power in range(16):
            if power in (0, 8, 12, 13):
                ImageCache[f'BigBrick{power}'] = ImageCache['BigBrick']
                continue

            x = y = 24
            overlay = ImageCache[f'BlockContents{power}']
            if power == 9:
                overlay = ImageCache['YoshiFire']
                x = 12
            elif power == 10:
                overlay = ImageCache['5Coin']
            elif power == 14:
                overlay = ImageCache['ShipKey']
                x, y = 22, 18

            new = QtGui.QPixmap(ImageCache['BigBrick'])
            paint = QtGui.QPainter(new)
            paint.drawPixmap(x, y, overlay)
            del paint
            ImageCache[f'BigBrick{power}'] = new

    def dataChanged(self):

        power = self.parent.actordata[5] & 0xF
        self.image = ImageCache[f'BigBrick{power}']
        super().dataChanged()


class ActorImage_FireSnake(actorlib.ActorImage_StaticMultiple):  # 158
    def __init__(self, parent):
        super().__init__(parent, 1.5)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FireSnakeWait', 'fire_snake_0.png')
        actorlib.loadIfNotInImageCache('FireSnake', 'fire_snake_1.png')

    def dataChanged(self):

        move = self.parent.actordata[5] & 15
        if move == 1:
            del self.size
            self.yOffset = 0
            self.image = ImageCache['FireSnakeWait']
        else:
            self.size = (20, 32)
            self.yOffset = -16
            self.image = ImageCache['FireSnake']

        super().dataChanged()


class ActorImage_UnusedBlockPlatform2(ActorImage_UnusedBlockPlatform):  # 160
    def dataChanged(self):
        self.width = ((self.parent.actordata[4] & 0xF) + 1) * 16
        self.height = ((self.parent.actordata[4] >> 4) + 1) * 16
        self.xOffset = (self.parent.actordata[3] & 0xF)
        self.yOffset = ((self.parent.actordata[3] >> 4) & 0xF)


class ActorImage_PipeBubbles(actorlib.ActorImage_StaticMultiple):  # 161
    @staticmethod
    def loadImages():
        if 'PipeBubblesU' in ImageCache:
            return
        transform90 = QtGui.QTransform()
        transform180 = QtGui.QTransform()
        transform270 = QtGui.QTransform()
        transform90.rotate(90)
        transform180.rotate(180)
        transform270.rotate(270)

        image = actorlib.GetImage('pipe_bubbles.png')
        if image is None:
            return

        ImageCache['PipeBubblesU'] = QtGui.QPixmap.fromImage(image)
        ImageCache['PipeBubblesR'] = QtGui.QPixmap.fromImage(image.transformed(transform90))
        ImageCache['PipeBubblesD'] = QtGui.QPixmap.fromImage(image.transformed(transform180))
        ImageCache['PipeBubblesL'] = QtGui.QPixmap.fromImage(image.transformed(transform270))

    def dataChanged(self):

        direction = self.parent.actordata[5] & 15
        if direction == 0 or direction > 3:
            self.dimensions = (0, -52, 32, 53)
            direction = 'U'
        elif direction == 1:
            self.dimensions = (0, 16, 32, 53)
            direction = 'D'
        elif direction == 2:
            self.dimensions = (16, -16, 53, 32)
            direction = 'R'
        elif direction == 3:
            self.dimensions = (-52, -16, 53, 32)
            direction = 'L'

        self.image = ImageCache[f'PipeBubbles{direction}']

        super().dataChanged()


class ActorImage_SnakeBlock(actorlib.ActorImage):  # 166
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SnakeBlock', 'snake_block.png')

    def dataChanged(self):
        length = self.parent.actordata[5] & 15
        self.width = (length + 3) * 16

    def paint(self, painter):
        endpiece = ImageCache['SnakeBlock']
        painter.drawPixmap(0, 0, endpiece)
        painter.drawTiledPixmap(24, 0, int((self.width * 1.5) - 48), 24, ImageCache['SnakeBlock'])
        painter.drawPixmap(int((self.width * 1.5) - 24), 0, endpiece)


class ActorImage_ChestnutGoomba(actorlib.ActorImage_Static):  # 170
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ChestnutGoomba'],
            (-6, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ChestnutGoomba', 'chestnut_goomba.png')


class ActorImage_PowerupBubble(actorlib.ActorImage_Static):  # 171
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MushroomBubble'],
            (-8, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MushroomBubble', 'powerup_bubble.png')


class ActorImage_ScrewMushroomWithBolt(ActorImage_ScrewMushroom):  # 172
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.hasBolt = True


class ActorImage_GiantFloatingLog(actorlib.ActorImage_Static):  # 173
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantFloatingLog'],
            (-152, -32),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantFloatingLog', 'giant_floating_log.png')


class ActorImage_OneWayGate(actorlib.ActorImage_StaticMultiple):  # 174
    @staticmethod
    def loadImages():
        if '1WayGate00' in ImageCache:
            return

        # This loop generates all one-way gate images from a single image
        gate = actorlib.GetImage('one_way_gate.png')
        if gate is None:
            return

        for flip in (0, 1):
            for direction in range(4):
                if flip:
                    newgate = QtGui.QPixmap.fromImage(gate.mirrored(True, False))
                else:
                    newgate = QtGui.QPixmap.fromImage(gate)

                width = 24
                height = 60  # constants, from the PNG
                xsize = width if direction in (0, 1) else height
                ysize = width if direction in (2, 3) else height
                rotValue = 0
                xpos = 0
                ypos = 0
                if direction == 1:
                    rotValue = 180
                    xpos = -width
                    ypos = -height
                elif direction == 2:
                    rotValue = 270
                    xpos = -width
                    ypos = 0
                elif direction == 3:
                    rotValue = 90
                    xpos = 0
                    ypos = -height

                dest = QtGui.QPixmap(xsize, ysize)
                dest.fill(Qt.GlobalColor.transparent)
                p = QtGui.QPainter(dest)
                p.rotate(rotValue)
                p.drawPixmap(xpos, ypos, newgate)
                del p

                ImageCache[f'1WayGate{flip}{direction}'] = dest

    def dataChanged(self):

        flag = (self.parent.actordata[5] >> 4) & 1
        direction = self.parent.actordata[5] & 3
        self.image = ImageCache[f'1WayGate{flag}{direction}']

        direction = min(direction, 3)
        self.offset = (
            (0, -22),
            (0, -2),
            (-22, 0),
            (-2, 0),
        )[direction]

        super().dataChanged()


class ActorImage_FlyingQBlock(actorlib.ActorImage):  # 175
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        self.dimensions = (-12, -16, 42, 32)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FlyingQBlock', 'flying_qblock.png')

    def paint(self, painter):
        theme = self.parent.actordata[4] >> 4
        content = self.parent.actordata[5] & 0xF

        if theme > 3:
            theme = 0

        if content == 2:
            content = 17
        elif content in (8, 9, 10, 12, 13, 14):
            content = 0

        painter.drawPixmap(0, 0, ImageCache['FlyingQBlock'])
        painter.drawPixmap(18, 23, ImageCache[f'Blocks{theme}'])
        painter.drawPixmap(18, 23, ImageCache[f'BlockContents{content}'])


class ActorImage_RouletteBlock(actorlib.ActorImage_StaticMultiple):  # 176
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['RouletteBlock'],
            (-4, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RouletteBlock', 'roulette.png')

        overlays = (
            ('Fire', ImageCache['BlockContents3']),
            ('Prop', ImageCache['BlockContents4']),
            ('IceF', ImageCache['BlockContents15']),
            ('Peng', ImageCache['BlockContents5']),
        )
        for name, image in overlays:
            newPix = QtGui.QPixmap(ImageCache['RouletteBlock'])
            painter = QtGui.QPainter(newPix)
            painter.drawPixmap(6, 6, image)
            del painter
            ImageCache['RouletteBlock' + name] = newPix

    def dataChanged(self):
        item = self.parent.actordata[5] & 0x3

        itemStrs = ('Fire', 'Prop', 'IceF', 'Peng')
        self.image = ImageCache['RouletteBlock' + itemStrs[item]]

        super().dataChanged()


class ActorImage_FireChomp(actorlib.ActorImage_Static):  # 177
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FireChomp'],
            (-2, -20),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FireChomp', 'fire_chomp.png')


class ActorImage_ScalePlatform(actorlib.ActorImage):  # 178
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (0, -16 / 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'WoodenPlatformL' not in ImageCache:
            ImageCache['WoodenPlatformL'] = actorlib.GetPixmap('wood_platform_left.png')
            ImageCache['WoodenPlatformM'] = actorlib.GetPixmap('wood_platform_middle.png')
            ImageCache['WoodenPlatformR'] = actorlib.GetPixmap('wood_platform_right.png')
        if 'ScaleRopeH' not in ImageCache:
            ImageCache['ScaleRopeH'] = actorlib.GetPixmap('scale_rope_horz.png')
            ImageCache['ScaleRopeV'] = actorlib.GetPixmap('scale_rope_vert.png')
            ImageCache['ScalePulley'] = actorlib.GetPixmap('scale_pulley.png')

    def dataChanged(self):
        info1 = self.parent.actordata[4]
        info2 = self.parent.actordata[5]
        self.platformWidth = (info1 & 0xF0) >> 4
        if self.platformWidth > 12:
            self.platformWidth = -1

        self.ropeLengthLeft = info1 & 0xF
        self.ropeLengthRight = (info2 & 0xF0) >> 4
        self.ropeWidth = info2 & 0xF

        ropeWidth = self.ropeWidth * 16
        platformWidth = (self.platformWidth + 3) * 16
        self.width = ropeWidth + platformWidth + (8 / 1.5)

        maxRopeHeight = max(self.ropeLengthLeft, self.ropeLengthRight)
        self.height = maxRopeHeight * 16 + 19
        if maxRopeHeight == 0:
            self.height += 8

        self.xOffset = -(self.platformWidth + 3) * 8 - (2 / 1.5)

    def paint(self, painter):
        ropeThickness = 6

        # this is FUN!! (not)
        ropeLeft = int(self.ropeLengthLeft * 24 + 4)
        if self.ropeLengthLeft == 0:
            ropeLeft += 12

        ropeRight = int(self.ropeLengthRight * 24 + 4)
        if self.ropeLengthRight == 0:
            ropeRight += 12

        ropeWidth = int(self.ropeWidth * 24 + 12)
        platformWidth = int((self.platformWidth + 3) * 24)

        ropeX = int(platformWidth / 2 - 1)

        painter.drawTiledPixmap(ropeX + 10, 0, ropeWidth - 26, ropeThickness, ImageCache['ScaleRopeH'])

        ropeVertImage = ImageCache['ScaleRopeV']
        painter.drawTiledPixmap(ropeX, 10, ropeThickness, ropeLeft - ropeThickness, ropeVertImage)
        painter.drawTiledPixmap(ropeX + ropeWidth - 12, 10, ropeThickness, ropeRight - ropeThickness, ropeVertImage)

        pulleyImage = ImageCache['ScalePulley']
        painter.drawPixmap(ropeX, 0, pulleyImage)
        painter.drawPixmap(ropeX + ropeWidth - 26, 0, pulleyImage)

        platforms = [(0, ropeLeft), (ropeX + ropeWidth - int(platformWidth / 2) - 7, ropeRight)]
        for x, y in platforms:
            painter.drawPixmap(x, y, ImageCache['WoodenPlatformL'])
            painter.drawTiledPixmap(x + 26, y, (platformWidth - 48), 24, ImageCache['WoodenPlatformM'])
            painter.drawPixmap(x + platformWidth - 22, y, ImageCache['WoodenPlatformR'])


class ActorImage_SpecialExit(actorlib.ActorImage):  # 179
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 0, 0))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryRectOutline):
            return

        w = (self.parent.actordata[4] & 15) + 1
        h = (self.parent.actordata[5] >> 4) + 1
        if w == 1 and h == 1:  # no point drawing a 1x1 outline behind the self.parent
            self.aux[0].setSize(0, 0)
            return
        self.aux[0].setSize(w * 24, h * 24)


class ActorImage_CheepChomp(actorlib.ActorImage_Static):  # 180
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CheepChomp'],
            (-32, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CheepChomp', 'cheep_chomp.png')


class ActorImage_EventDoor(ActorImage_Door):  # 182
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.alpha = 0.5


class ActorImage_ToadBalloon(actorlib.ActorImage_Static):  # 185
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ToadBalloon'],
            (-4, -4),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ToadBalloon', 'toad_balloon.png')


class ActorImage_PlayerBlock(actorlib.ActorImage_Static):  # 187
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PlayerBlock'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PlayerBlock', 'player_block.png')


class ActorImage_MidwayFlag(actorlib.ActorImage_Static):  # 188
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MidwayFlag'],
            (1 / 1.5, -55 / 1.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MidwayFlag', 'midway_flag.png')


class ActorImage_LarryKoopa(actorlib.ActorImage_Static):  # 189
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['LarryKoopa'],
            (-17, -33),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LarryKoopa', 'Larry_Koopa.png')


class ActorImage_TiltingGirderUnused(actorlib.ActorImage_Static):  # 190
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['TiltingGirder'],
            (0, -18),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('TiltingGirder', 'tilting_girder.png')


class ActorImage_TileEvent(common.ActorImage_TileEvent):  # 191
    def __init__(self, parent):
        super().__init__(parent)
        self.notAllowedTypes = [2, 5, 7]

    def getTileFromType(self, type):
        if type == 0:
            return actorlib.GetTile(55)

        if type == 1:
            return actorlib.GetTile(48)

        if type == 3:
            return actorlib.GetTile(52)

        if type == 4:
            return actorlib.GetTile(51)

        if type == 6:
            return actorlib.GetTile(45)

        if type == 12:
            return actorlib.GetTile(256 * 3 + 67)

        if type == 14:
            return actorlib.GetTile(256)

        return None


class ActorImage_LarryKoopaCastleBoss(actorlib.ActorImage):  # 192
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        larryKoopaAuxImage = actorlib.AuxiliaryImage(parent, 528, 240)
        larryKoopaAuxImage.image = ImageCache['LarryKoopaCastleBoss']
        larryKoopaAuxImage.setPos(48, 192)
        self.aux.append(larryKoopaAuxImage)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, 0, 288))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LarryKoopaCastleBoss', 'larry_castle_boss.png')


class ActorImage_Urchin(actorlib.ActorImage_Static):  # 193
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Urchin'],
            (-12, -14),
        )

        track = actorlib.AuxiliaryTrackObject(
            parent, 16, 16, actorlib.AuxiliaryTrackObject.Vertical
        )
        track.setPos(self.width * 0.75 - 12, self.height * 0.75 - 12)
        track.setIsBehindActor(False)
        self.aux.append(track)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Urchin', 'urchin.png')

    def dataChanged(self):
        super().dataChanged()
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        distance = ((self.parent.actordata[5] & 0xF0) << 1) | 8
        horizontal = (self.parent.actordata[5] & 1) == 1

        if horizontal:
            self.aux[0].direction = actorlib.AuxiliaryTrackObject.Horizontal
            self.aux[0].setSize(distance + 8, 16)
            self.aux[0].setPos((self.width - distance) * 0.75 - 8, self.height * 0.75 - 12)
        else:
            self.aux[0].direction = actorlib.AuxiliaryTrackObject.Vertical
            self.aux[0].setSize(16, distance + 8)
            self.aux[0].setPos(self.width * 0.75 - 12, (self.height - distance) * 0.75 - 8)

class ActorImage_MegaUrchin(actorlib.ActorImage_Static):  # 194
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MegaUrchin'],
            (-48, -46),
        )

        track = actorlib.AuxiliaryTrackObject(
            parent, 16, 16, actorlib.AuxiliaryTrackObject.Vertical
        )
        track.setPos(self.width * 0.75 - 12, self.height * 0.75 - 12)
        track.setIsBehindActor(False)
        self.aux.append(track)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MegaUrchin', 'mega_urchin.png')

    def dataChanged(self):
        super().dataChanged()
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        distance = ((self.parent.actordata[5] & 0xF0) << 1) | 8
        horizontal = (self.parent.actordata[5] & 1) == 1

        if horizontal:
            self.aux[0].direction = actorlib.AuxiliaryTrackObject.Horizontal
            self.aux[0].setSize(distance + 8, 16)
            self.aux[0].setPos((self.width - distance) * 0.75 - 8, self.height * 0.75 - 12)
        else:
            self.aux[0].direction = actorlib.AuxiliaryTrackObject.Vertical
            self.aux[0].setSize(16, distance + 8)
            self.aux[0].setPos(self.width * 0.75 - 12, (self.height - distance) * 0.75 - 8)


class ActorImage_HuckitCrab(actorlib.ActorImage_StaticMultiple):  # 195
    @staticmethod
    def loadImages():
        if 'HuckitCrabR' in ImageCache:
            return

        huckit_crab = actorlib.GetImage('huckit_crab.png')
        if huckit_crab is None:
            return

        ImageCache['HuckitCrabL'] = QtGui.QPixmap.fromImage(huckit_crab)
        ImageCache['HuckitCrabR'] = QtGui.QPixmap.fromImage(huckit_crab.mirrored(True, False))

    def dataChanged(self):
        direction = self.parent.actordata[5]

        if direction == 1: # Right
            self.image = ImageCache['HuckitCrabR']
            self.xOffset = 0
        else: # Left
            self.image = ImageCache['HuckitCrabL']
            self.xOffset = -16

        super().dataChanged()


class ActorImage_Fishbones(actorlib.ActorImage_StaticMultiple):  # 196
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FishbonesL'],
            (0, -2)
        )
        self.aux.append(actorlib.AuxiliaryTrackObject(
            parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal
        ))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        direction = self.parent.actordata[5] >> 4
        distance = self.parent.actordata[5] & 0xF

        # distance values > 1 result in a distance of 9
        if distance == 0:
            distance = 5
        elif distance == 1:
            distance = 7
        else:
            distance = 9

        self.aux[0].setSize(distance * 16, 16)
        self.aux[0].setPos(distance * -12 + 12, 2)

        if direction == 1:
            self.image = ImageCache['FishbonesR']
        else:
            self.image = ImageCache['FishbonesL']

        super().dataChanged()

    @staticmethod
    def loadImages():
        if 'FishbonesL' in ImageCache:
            return
        Fishbones = actorlib.GetImage('fishbones.png')
        if Fishbones is None:
            return

        ImageCache['FishbonesL'] = QtGui.QPixmap.fromImage(Fishbones)
        ImageCache['FishbonesR'] = QtGui.QPixmap.fromImage(Fishbones.mirrored(True, False))


class ActorImage_Clam(actorlib.ActorImage_StaticMultiple):  # 197
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-29, -54)

    @staticmethod
    def loadImages():
        if 'ClamEmpty' in ImageCache:
            return

        if 'PSwitch' not in ImageCache:
            pSwitch = actorlib.GetImage('p_switch.png')
            if pSwitch is None:
                return

            ImageCache['PSwitch'] = QtGui.QPixmap.fromImage(pSwitch)
            ImageCache['PSwitchU'] = QtGui.QPixmap.fromImage(pSwitch.mirrored(True, True))

        actorlib.loadIfNotInImageCache('ClamEmpty', 'clam.png')

        overlays = (
            (26, 22, 'Star', ImageCache['StarCoin']),
            (40, 42, '1Up', ImageCache['BlockContents11']),
            (42, 42, 'PSwitch', ImageCache['PSwitch']),
            (42, 42, 'PSwitchU', ImageCache['PSwitchU']),
        )
        for x, y, clamName, overlayImage in overlays:
            newPix = QtGui.QPixmap(ImageCache['ClamEmpty'])
            painter = QtGui.QPainter(newPix)
            painter.setOpacity(0.6)
            painter.drawPixmap(x, y, overlayImage)
            del painter
            ImageCache['Clam' + clamName] = newPix

        # 2 coins special case
        newPix = QtGui.QPixmap(ImageCache['ClamEmpty'])
        painter = QtGui.QPainter(newPix)
        painter.setOpacity(0.6)
        painter.drawPixmap(28, 42, ImageCache['Coin'])
        painter.drawPixmap(52, 42, ImageCache['Coin'])
        del painter
        ImageCache['Clam2Coin'] = newPix

    def dataChanged(self):

        holds = self.parent.actordata[5] & 0xF
        switchdir = self.parent.actordata[4] & 0xF

        holdsStr = 'Empty'
        if holds == 1:
            holdsStr = 'Star'
        elif holds == 2:
            holdsStr = '2Coin'
        elif holds == 3:
            holdsStr = '1Up'
        elif holds == 4:
            if switchdir == 1:
                holdsStr = 'PSwitchU'
            else:
                holdsStr = 'PSwitch'

        self.image = ImageCache['Clam' + holdsStr]

        super().dataChanged()


class ActorImage_GiantGoomba(actorlib.ActorImage_Static):  # 198
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantGoomba'],
            (-6, -19),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantGoomba', 'giant_goomba.png')


class ActorImage_MegaGoomba(actorlib.ActorImage_Static):  # 199
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MegaGoomba'],
            (-11, -37),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MegaGoomba', 'mega_goomba.png')


class ActorImage_Microgoomba(actorlib.ActorImage_Static):  # 200
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Microgoomba'],
            (4, 8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Microgoomba', 'microgoomba.png')


class ActorImage_Icicle(actorlib.ActorImage_StaticMultiple):  # 201
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('IcicleSmallS', 'icicle_small_static.png')
        actorlib.loadIfNotInImageCache('IcicleLargeS', 'icicle_large_static.png')

    def dataChanged(self):

        size = self.parent.actordata[5] & 1
        if size == 0:
            self.image = ImageCache['IcicleSmallS']
        else:
            self.image = ImageCache['IcicleLargeS']

        super().dataChanged()


class ActorImage_MGCannon(actorlib.ActorImage_Static):  # 202
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MGCannon'],
            (-19 / 1.5, -40),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MGCannon', 'mg_cannon.png')


class ActorImage_Chest(actorlib.ActorImage_StaticMultiple):  # 203
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Chest'],
            (-12, -10),
        )

        itemAuxImage = actorlib.AuxiliaryImage(parent, 24, 24)
        itemAuxImage.setIsBehindActor(False)
        itemAuxImage.setPos(18, 8)
        self.aux.append(itemAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Chest', 'chest.png')

    def dataChanged(self):
        pipeAlign = (self.parent.actordata[2] >> 4) & 1
        if pipeAlign:
            self.yOffset = -13 / 1.5
        else:
            self.yOffset = -10

        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        # Render item
        chestType = self.parent.actordata[4] & 0xF
        if chestType == 0:
            item = self.parent.actordata[5] & 0xF
            # Hide for 'Nothing' values (or Random)
            if item < 2 or item > 8:
                self.aux[0].alpha = 0.0
                return
            else:
                self.aux[0].alpha = 1.0

            itemsIdx = [2, 3, 4, 5, 6, 7, 15]
            self.aux[0].image = ImageCache[f'BlockContents{itemsIdx[item-2]}']
        else: # Mushroom
            self.aux[0].image = ImageCache['BlockContents2']

        super().dataChanged()


class ActorImage_RollObjSpawner(actorlib.ActorImage_StaticMultiple):  # 204
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.yOffset = -16

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpikeBall', 'spike_ball.png')
        actorlib.loadIfNotInImageCache('RollingBarrel', 'barrel_rolling.png')

    def dataChanged(self):
        barrel = (self.parent.actordata[2] >> 4) & 1
        if barrel:
            self.image = ImageCache['RollingBarrel']
        else:
            self.image = ImageCache['SpikeBall']

        super().dataChanged()


class ActorImage_GiantBubbleNormal(ActorImage_GiantBubble):  # 205
    pass


class ActorImage_Zoom(actorlib.ActorImage):  # 206
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 0, 0))

    def dataChanged(self):
        super().dataChanged()
        if not isinstance(self.aux[0], actorlib.AuxiliaryRectOutline):
            return

        w = self.parent.actordata[5]
        h = self.parent.actordata[4]
        if w == 0 and h == 0:  # no point drawing a 1x1 outline behind the self.parent
            self.aux[0].setSize(0, 0, 0, 0)
            return
        self.aux[0].setSize(w * 24, h * 24, 0, 24 - (h * 24))


class ActorImage_QBlock(ActorImage_Block):  # 207
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49


class ActorImage_QBlockUnused(ActorImage_Block):  # 208
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49
        self.eightIsMushroom = True
        self.twelveIsMushroom = True


class ActorImage_BrickBlock(ActorImage_Block):  # 209
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48


class ActorImage_BowserJr1stController(actorlib.ActorImage):  # 211
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        bowserJr1stAuxImage = actorlib.AuxiliaryImage(parent, 672, 80)
        bowserJr1stAuxImage.image = ImageCache['BowserJr1stController']
        bowserJr1stAuxImage.setPos(-504, -55)
        self.aux.append(bowserJr1stAuxImage)

        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, -504, -312))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BowserJr1stController', 'boss_controller_bowserjr_1.png')


class ActorImage_RollingHill(actorlib.ActorImage):  # 212

    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.RollingHillSizes = [0, 18 * 16, 32 * 16, 50 * 16, 64 * 16, 10 * 16, 14 * 16, 20 * 16, 0, 0, 0, 0, 0, 0, 0, 0]

        size = (self.parent.actordata[3] >> 4) & 0xF
        realSize = self.RollingHillSizes[size]

        self.aux.append(actorlib.AuxiliaryCircleOutline(parent, realSize))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryCircleOutline):
            return

        size = (self.parent.actordata[3] >> 4) & 0xF
        if size != 0:
            realSize = self.RollingHillSizes[size]
        else:
            adjust = self.parent.actordata[4]
            realSize = 32 * (adjust + 1)

        self.aux[0].setSize(realSize)
        self.aux[0].update()


class ActorImage_FreefallPlatform(actorlib.ActorImage_Static):  # 214
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FreefallGH'],
        )
        self.parent.setZValue(24999)

        pathNodeAuxRect = actorlib.AuxiliaryRectOutline(parent, 24, 24, 0, 0)
        pathNodeAuxRect.setIsBehindActor(False)
        self.aux.append(pathNodeAuxRect)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FreefallGH', 'freefall_gh_platform.png')


class ActorImage_Poison(ActorImage_LiquidOrFog):  # 216
    def __init__(self, parent):
        super().__init__(parent)

        self.crest = ImageCache['LiquidPoisonCrest']
        self.mid = ImageCache['LiquidPoison']
        self.rise = ImageCache['LiquidPoisonRiseCrest']
        self.riseCrestless = ImageCache['LiquidPoisonRise']

        self.top = self.parent.objy

    @staticmethod
    def loadImages():
        if 'LiquidPoison' in ImageCache:
            return
        ImageCache['LiquidPoison'] = actorlib.GetPixmap('liquid_poison.png')
        ImageCache['LiquidPoisonCrest'] = actorlib.GetPixmap('liquid_poison_crest.png')
        ImageCache['LiquidPoisonRise'] = actorlib.GetPixmap('liquid_poison_rise.png')
        ImageCache['LiquidPoisonRiseCrest'] = actorlib.GetPixmap('liquid_poison_rise_crest.png')

    def dataChanged(self):
        self.locId = self.parent.actordata[5] & 0x7F
        self.drawCrest = self.parent.actordata[4] & 8 == 0

        self.risingHeight = (self.parent.actordata[3] & 0xF) << 4
        self.risingHeight |= self.parent.actordata[4] >> 4
        if self.parent.actordata[2] & 15 > 7:  # falling
            self.risingHeight = -self.risingHeight

        super().dataChanged()

    def positionChanged(self):
        self.top = self.parent.objy
        super().positionChanged()


class ActorImage_LineBlock(common.ActorImage_LineBlock):  # 219

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LineBlock', 'lineblock.png')

    def dataChanged(self):
        self.setLineBlockImage(ImageCache['LineBlock'])

        super().dataChanged()


class ActorImage_InvisibleBlock(ActorImage_Block):  # 221
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.eightIsMushroom = True
        self.tilenum = 0x200 * 4


class ActorImage_ConveyorSpike(actorlib.ActorImage_Static):  # 222
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SpikeU'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpikeU', 'spike_up.png')


class ActorImage_SpringBlock(actorlib.ActorImage_StaticMultiple):  # 223
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpringBlock1', 'spring_block.png')
        actorlib.loadIfNotInImageCache('SpringBlock2', 'spring_block_alt.png')

    def dataChanged(self):
        type = self.parent.actordata[5] & 1
        self.image = ImageCache['SpringBlock2'] if type else ImageCache['SpringBlock1']

        super().dataChanged()


class ActorImage_JumboRay(actorlib.ActorImage_StaticMultiple):  # 224
    @staticmethod
    def loadImages():
        if 'JumboRayL' in ImageCache:
            return
        Ray = actorlib.GetImage('jumbo_ray.png')
        if Ray is None:
            return

        ImageCache['JumboRayL'] = QtGui.QPixmap.fromImage(Ray)
        ImageCache['JumboRayR'] = QtGui.QPixmap.fromImage(Ray.mirrored(True, False))

    def dataChanged(self):

        flyleft = self.parent.actordata[4] & 15
        if flyleft:
            self.xOffset = 0
            self.image = ImageCache['JumboRayL']
        else:
            self.xOffset = -152
            self.image = ImageCache['JumboRayR']

        super().dataChanged()


class ActorImage_FloatingCoin(ActorImage_SpecialCoin):  # 225
    pass


class ActorImage_GiantBubbleUnused(ActorImage_GiantBubble):  # 226
    pass


class ActorImage_PipeCannon(actorlib.ActorImage):  # 227
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        # self.aux[0] is the pipe image
        pipeAuxImage = actorlib.AuxiliaryImage(parent, 24, 24)
        pipeAuxImage.hover = False
        self.aux.append(pipeAuxImage)

        # self.aux[1] is the trajectory indicator
        trajectoryIndicatorAuxImage = actorlib.AuxiliaryPainterPath(parent, QtGui.QPainterPath(), 24, 24)
        trajectoryIndicatorAuxImage.fillFlag = False
        self.aux.append(trajectoryIndicatorAuxImage)
        pipeAuxImage.setZValue(trajectoryIndicatorAuxImage.zValue() + 1)

        self.size = (32, 64)

    @staticmethod
    def loadImages():
        if 'PipeCannon0' in ImageCache:
            return
        for i in range(7):
            pipeCannon = actorlib.GetImage(f'pipe_cannon_{i}.png')
            if pipeCannon is None:
                continue

            ImageCache[f'PipeCannon{i}'] = QtGui.QPixmap.fromImage(pipeCannon)

    def dataChanged(self):
        if (
            not isinstance(self.aux[0], actorlib.AuxiliaryImage)
            or not isinstance(self.aux[1], actorlib.AuxiliaryPainterPath)
        ):
            return

        fireDirection = (self.parent.actordata[5] & 0xF) % 7

        self.aux[0].image = ImageCache[f'PipeCannon{fireDirection}']

        path = None
        if fireDirection == 0:
            # 30 deg to the right
            self.aux[0].setSize(84, 101, 0, -5)
            path = QtGui.QPainterPath(QtCore.QPointF(0, 184))
            path.cubicTo(QtCore.QPointF(152, -24), QtCore.QPointF(168, -24), QtCore.QPointF(264, 48))
            path.lineTo(QtCore.QPointF(480, 216))
            self.aux[1].setSize(480, 216, 24, -120)
        elif fireDirection == 1:
            # 30 deg to the left
            self.aux[0].setSize(85, 101, -36, -5)
            path = QtGui.QPainterPath(QtCore.QPointF(480 - 0, 184))
            path.cubicTo(QtCore.QPointF(480 - 152, -24), QtCore.QPointF(480 - 168, -24), QtCore.QPointF(480 - 264, 48))
            path.lineTo(QtCore.QPointF(480 - 480, 216))
            self.aux[1].setSize(480, 216, -480 + 24, -120)
        elif fireDirection == 2:
            # 15 deg to the right
            self.aux[0].setSize(60, 102, 0, -6)
            path = QtGui.QPainterPath(QtCore.QPointF(0, 188))
            path.cubicTo(QtCore.QPointF(36, -36), QtCore.QPointF(60, -36), QtCore.QPointF(96, 84))
            path.lineTo(QtCore.QPointF(144, 252))
            self.aux[1].setSize(144, 252, 30, -156)
        elif fireDirection == 3:
            # 15 deg to the left
            self.aux[0].setSize(61, 102, -12, -6)
            path = QtGui.QPainterPath(QtCore.QPointF(144 - 0, 188))
            path.cubicTo(QtCore.QPointF(144 - 36, -36), QtCore.QPointF(144 - 60, -36), QtCore.QPointF(144 - 96, 84))
            path.lineTo(QtCore.QPointF(144 - 144, 252))
            self.aux[1].setSize(144, 252, -144 + 18, -156)
        elif fireDirection == 4:
            # Straight up
            self.aux[0].setSize(135, 132, -43, -35)
            path = QtGui.QPainterPath(QtCore.QPointF(26, 0))
            path.lineTo(QtCore.QPointF(26, 656))
            self.aux[1].setSize(48, 656, 0, -632)
        elif fireDirection == 5:
            # 45 deg to the right
            self.aux[0].setSize(90, 98, 0, -1)
            path = QtGui.QPainterPath(QtCore.QPointF(0, 320))
            path.lineTo(QtCore.QPointF(264, 64))
            path.cubicTo(QtCore.QPointF(348, -14), QtCore.QPointF(420, -14), QtCore.QPointF(528, 54))
            path.lineTo(QtCore.QPointF(1036, 348))
            self.aux[1].setSize(1036, 348, 24, -252)
        elif fireDirection == 6:
            # 45 deg to the left
            self.aux[0].setSize(91, 98, -42, -1)
            path = QtGui.QPainterPath(QtCore.QPointF(1036 - 0, 320))
            path.lineTo(QtCore.QPointF(1036 - 264, 64))
            path.cubicTo(QtCore.QPointF(1036 - 348, -14), QtCore.QPointF(1036 - 420, -14), QtCore.QPointF(1036 - 528, 54))
            path.lineTo(QtCore.QPointF(1036 - 1036, 348))
            self.aux[1].setSize(1036, 348, -1036 + 24, -252)

        if path is not None:
            self.aux[1].setPath(path)


class ActorImage_ExtendShroom(actorlib.ActorImage):  # 228
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False
        self.parent.setZValue(24999)

    @staticmethod
    def loadImages():
        if 'ExtendShroomB' in ImageCache:
            return
        ImageCache['ExtendShroomB'] = actorlib.GetPixmap('extend_shroom_big.png')
        ImageCache['ExtendShroomS'] = actorlib.GetPixmap('extend_shroom_small.png')
        ImageCache['ExtendShroomC'] = actorlib.GetPixmap('extend_shroom_cont.png')
        ImageCache['ExtendShroomStem'] = actorlib.GetPixmap('extend_shroom_stem.png')

    def dataChanged(self):

        props = self.parent.actordata[5]
        size = self.parent.actordata[4] & 1
        self.start = (props & 0x10) >> 4
        stemlength = props & 0xF

        if size == 0:  # big
            self.image = ImageCache['ExtendShroomB']
            self.width = 160
        else:  # small
            self.image = ImageCache['ExtendShroomS']
            self.width = 96

        if self.start == 0:  # contracted
            self.indicator, self.image = self.image, ImageCache['ExtendShroomC']

        self.xOffset = 8 - (self.width / 2)
        self.height = (stemlength * 16) + 48

    def paint(self, painter):
        if self.image is None:
            return

        if self.start == 0: # contracted, so paint indicator
            painter.save()
            painter.setOpacity(0.5)
            painter.drawPixmap(0, 0, self.indicator)
            painter.restore()

            painter.drawPixmap(int(self.width * 1.5 / 2 - 24), 0, self.image)
        else:
            painter.drawPixmap(0, 0, self.image)

        painter.drawTiledPixmap(
            int((self.width * 1.5) / 2 - 14),
            48,
            28,
            int((self.height * 1.5) - 48),
            ImageCache['ExtendShroomStem'],
        )


class ActorImage_SandPillar(actorlib.ActorImage_Static):  # 229
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SandPillar'],
            (-33, -150),
        )
        self.alpha = 0.65

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SandPillar', 'sand_pillar.png')


class ActorImage_Bramball(actorlib.ActorImage_Static):  # 230
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Bramball'],
            (-50 / 1.5, -71 / 1.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Bramball', 'bramball.png')


class ActorImage_WiggleShroom(actorlib.ActorImage):  # 231
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False
        self.parent.setZValue(24999)
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Vertical))

    @staticmethod
    def loadImages():
        if 'WiggleShroomL' in ImageCache:
            return
        ImageCache['WiggleShroomL'] = actorlib.GetPixmap('wiggle_shroom_left.png')
        ImageCache['WiggleShroomM'] = actorlib.GetPixmap('wiggle_shroom_middle.png')
        ImageCache['WiggleShroomR'] = actorlib.GetPixmap('wiggle_shroom_right.png')
        ImageCache['WiggleShroomS'] = actorlib.GetPixmap('wiggle_shroom_stem.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        width = (self.parent.actordata[4] & 0xF0) >> 4
        long = (self.parent.actordata[3] >> 2) & 1
        extends = (self.parent.actordata[3] >> 5) & 1
        distance = self.parent.actordata[3] & 3 # this is also the stem length

        self.xOffset = -(width * 8) - 20
        self.width = (width * 16) + 56
        self.wiggleleft = ImageCache['WiggleShroomL']
        self.wigglemiddle = ImageCache['WiggleShroomM']
        self.wiggleright = ImageCache['WiggleShroomR']
        self.wigglestem = ImageCache['WiggleShroomS']

        if extends:
            self.aux[0].setPos((self.width * 0.75) - 12, (-distance * 24))
            self.aux[0].setSize(16, (distance * 32))
            if long:
                self.height = 96
            else:
                self.height = 64
        else:
            self.aux[0].setSize(0, 0)
            self.height = (distance * 16) + 64

    def paint(self, painter):
        xsize = self.width * 1.5
        painter.drawPixmap(0, 0, self.wiggleleft)
        painter.drawTiledPixmap(18, 0, int(xsize - 36), 24, self.wigglemiddle)
        painter.drawPixmap(int(xsize - 18), 0, self.wiggleright)
        painter.drawTiledPixmap(int((xsize / 2) - 12), 24, 24, int((self.height * 1.5) - 24), self.wigglestem)


class ActorImage_MechaKoopa(actorlib.ActorImage_Static):  # 232
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MechaKoopa'],
            (-8, -14),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MechaKoopa', 'mechakoopa.png')


class ActorImage_Bulber(actorlib.ActorImage):  # 233
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        self.dimensions = (-35 / 1.5, -26 / 1.5, 59, 50)

        self.aux.append(actorlib.AuxiliaryTrackObject(self.parent, 244, 244, actorlib.AuxiliaryTrackObject.Horizontal))

        bulberAuxImage = actorlib.AuxiliaryImage(parent, 243, 248)
        bulberAuxImage.image = ImageCache['BulberL']
        self.aux.append(bulberAuxImage)

    @staticmethod
    def loadImages():
        if 'BulberL' in ImageCache:
            return
        Bulber = actorlib.GetImage('bulber.png')
        if Bulber is None:
            return

        ImageCache['BulberL'] = QtGui.QPixmap.fromImage(Bulber)
        ImageCache['BulberR'] = QtGui.QPixmap.fromImage(Bulber.mirrored(True, False))

    def dataChanged(self):
        if (
            not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject)
            or not isinstance(self.aux[1], actorlib.AuxiliaryImage)
        ):
            return

        type = self.parent.actordata[5] & 0xF
        if type == 1:
            distance = ((self.parent.actordata[4] & 0xF) + 1) * 16
            isLeft = (self.parent.actordata[4] >> 4) & 1
            self.aux[0].setSize((distance * 2) + 48, 16)
            self.aux[0].setPos((-distance * 1.5) + self.width - 48, self.height)
            if isLeft:
                self.aux[1].image = ImageCache['BulberL']
                self.aux[1].setPos(-8, 0)
                self.offset = (-35 / 1.5, -26 / 1.5)
            else:
                self.aux[1].image = ImageCache['BulberR']
                self.aux[1].setPos(0, 0)
                self.offset = (-27 / 1.5, -26 / 1.5)
        else:
            self.aux[0].setSize(0, 24)
            self.aux[1].image = ImageCache['BulberL']
            self.aux[1].setPos(-8, 0)


class ActorImage_PCoin(actorlib.ActorImage_Static):  # 237
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PCoin'],
        )


class ActorImage_Foo(actorlib.ActorImage_Static):  # 238
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Foo'],
            (-8, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Foo', 'foo.png')


class ActorImage_GiantWiggler(actorlib.ActorImage_Static):  # 240
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GiantWiggler'],
            (-24, -64),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantWiggler', 'giant_wiggler.png')


class ActorImage_FallingLedgeBar(actorlib.ActorImage_Static):  # 242
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FallingLedgeBar'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FallingLedgeBar', 'falling_ledge_bar.png')


# TODO: Make 'Filled Arrow' preview; Consider if it would be worth it to preview the formation repeats
class ActorImage_CheepFormation(actorlib.ActorImage_Static):  # 247
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = True

        # Create auxes
        for _ in range(16):
            cheepRedLeftAuxImage = actorlib.AuxiliaryImage(parent, 26, 24)
            cheepRedLeftAuxImage.image = ImageCache['CheepRedLeft']
            cheepRedLeftAuxImage.setIsBehindActor(False)
            cheepRedLeftAuxImage.hover = False
            self.aux.append(cheepRedLeftAuxImage)

    @staticmethod
    def loadImages():
        if 'CheepRedLeft' in ImageCache:
            return
        ImageCache['CheepRedLeft'] = actorlib.GetPixmap('cheep_red.png')
        ImageCache['CheepRedRight'] = QtGui.QPixmap.fromImage(actorlib.GetImage('cheep_red.png').mirrored(True, False))

    def dataChanged(self):
        isLeft = (self.parent.actordata[4] >> 4) & 0x1
        cheepNum = self.parent.actordata[4] & 0xF
        doStretch = self.parent.actordata[3] & 0x1
        formation = self.parent.actordata[5] & 0xF
        if formation > 4:
            formation = 0

        # Setup stuff
        for i, aux in enumerate(self.aux):
            if not isinstance(aux, actorlib.AuxiliaryImage):
                continue

            dirs = ['CheepRedRight', 'CheepRedLeft']
            aux.image = ImageCache[dirs[isLeft]]
            aux.alpha = 1.0 if i <= cheepNum else 0.0

        if formation == 0: # Arrow
            positions = [
                0,
                32, -32,
                64, -64,
                96, -96,
                128, -128,
                160, -160,
                192, -192,
                224, -224,
                256, -256
            ]

            for i, aux in enumerate(self.aux):
                if not isinstance(aux, actorlib.AuxiliaryImage):
                    continue

                yAdj = 0.75 if doStretch else 0.5
                xAdj = 1 if isLeft else -1
                aux.setPos(abs(positions[i])*1.5 * xAdj, -positions[i]*1.5 * yAdj)
        elif formation == 1: # Filled Arrow
            for aux in self.aux:
                if not isinstance(aux, actorlib.AuxiliaryImage):
                    continue
                aux.alpha = 0.0
        else: # Vertical, Diagonals
            for i, aux in enumerate(self.aux):
                if not isinstance(aux, actorlib.AuxiliaryImage):
                    continue

                xAdj = 1 if isLeft else -1
                yAdj = 0.75 if doStretch else 1
                yVal = (i * 32) * 1.5
                xVal = 0 if formation == 2 else yVal

                if formation == 3: # Upwards Diagonal
                    yAdj *= -1
                aux.setPos(xVal*xAdj, yVal*yAdj)

        super().dataChanged()


class ActorImage_EventDeactivBlock(ActorImage_Block):  # 252
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49 # ? block


class ActorImage_RotControlledCoin(ActorImage_SpecialCoin):  # 253
    pass


class ActorImage_RotControlledPipe(ActorImage_Pipe):  # 254
    def dataChanged(self):
        self.length1 = self.length2 = (self.parent.actordata[4] >> 4) + 2
        dir = self.parent.actordata[4] & 3
        self.direction = 'URDL'[dir]
        super().dataChanged()


class ActorImage_RotatingQBlock(ActorImage_Block):  # 255
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49
        self.contentsNybble = 4
        self.twelveIsMushroom = True
        self.rotates = True


class ActorImage_RotatingBrickBlock(ActorImage_Block):  # 256
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48
        self.contentsNybble = 4
        self.twelveIsMushroom = True
        self.rotates = True


class ActorImage_MoveWhenOnMetalLavaBlock(actorlib.ActorImage_StaticMultiple):  # 257
    @staticmethod
    def loadImages():
        if 'MetalLavaBlock0' in ImageCache:
            return
        ImageCache['MetalLavaBlock0'] = actorlib.GetPixmap('lava_iron_block_0.png')
        ImageCache['MetalLavaBlock1'] = actorlib.GetPixmap('lava_iron_block_1.png')
        ImageCache['MetalLavaBlock2'] = actorlib.GetPixmap('lava_iron_block_2.png')

    def dataChanged(self):
        size = (self.parent.actordata[5] & 0xF) % 3
        self.image = ImageCache[f'MetalLavaBlock{size}']

        super().dataChanged()


class ActorImage_RegularDoor(ActorImage_Door):  # 259
    pass


class ActorImage_MovementController_TwoWayLine(actorlib.ActorImage):  # 260
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal))

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        direction = self.parent.actordata[3] & 3
        distance = (self.parent.actordata[5] >> 4) + 1

        if direction <= 1:  # horizontal
            self.aux[0].direction = 1
            self.aux[0].setSize(distance * 16, 16)
        else:  # vertical
            self.aux[0].direction = 2
            self.aux[0].setSize(16, distance * 16)

        if direction == 0 or direction == 3:  # right, down
            self.aux[0].setPos(0, 0)
        elif direction == 1:  # left
            self.aux[0].setPos((-distance * 24) + 24, 0)
        elif direction == 2:  # up
            self.aux[0].setPos(0, (-distance * 24) + 24)


class ActorImage_OldStoneBlock_MovementControlled(ActorImage_OldStoneBlock):  # 261
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.hasMovementAux = False


class ActorImage_PoltergeistItem(actorlib.ActorImage):  # 262
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        poltergeistBlockAuxImage = actorlib.AuxiliaryImage(parent, 60, 60)
        poltergeistBlockAuxImage.image = ImageCache['PoltergeistBlock']
        poltergeistBlockAuxImage.setPos(-28, -28) # (image_width_of_glow - tile-width) / 2; Same for every value that is a multiple of 14 here
        poltergeistBlockAuxImage.hover = False
        self.aux.append(poltergeistBlockAuxImage)

    @staticmethod
    def loadImages():
        if 'PoltergeistBlock' in ImageCache:
            return

        actorlib.loadIfNotInImageCache('GhostHouseStand', 'ghost_house_stand.png')
        actorlib.loadIfNotInImageCache('PoltergeistBlock', 'poltergeist_block.png')

        polterstand = actorlib.GetPixmap('poltergeist_light.png')
        polterblock = actorlib.GetPixmap('poltergeist_light.png')

        standpainter = QtGui.QPainter(polterstand)
        blockpainter = QtGui.QPainter(polterblock)

        standpainter.drawPixmap(28, 14, ImageCache['GhostHouseStand'])
        blockpainter.drawPixmap(28, 28, ImageCache['PoltergeistBlock'])

        del standpainter
        del blockpainter

        ImageCache['PoltergeistStand'] = polterstand
        ImageCache['PoltergeistBlock'] = polterblock

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        style = self.parent.actordata[5] & 15
        if style == 0:
            self.offset = (0, 0)
            self.height = 16
            self.aux[0].setSize(80, 80)
            self.aux[0].image = ImageCache['PoltergeistBlock']
            self.aux[0].setPos(-28, -28)
        else:
            self.offset = (8, -16)
            self.height = 32
            self.aux[0].setSize(80, 80)
            self.aux[0].image = ImageCache['PoltergeistStand']
            self.aux[0].setPos(-28, -14)


class ActorImage_WaterPiranha(actorlib.ActorImage_Static):  # 263
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['WaterPiranhaBody'],
            (-4 / 1.5, -30),
        )

        # Highest point
        ballAuxImage = actorlib.AuxiliaryImage(parent, 38, 30)
        ballAuxImage.image = ImageCache['WaterPiranhaBall']
        ballAuxImage.setPos(2, -170)
        ballAuxImage.hover = True
        self.aux.append(ballAuxImage)

        # Lowest point
        lowestAuxImage = actorlib.AuxiliaryImage(parent, 38, 30)
        lowestAuxImage.image = ImageCache['WaterPiranhaBall']
        lowestAuxImage.setPos(2, -24)
        lowestAuxImage.alpha = 0.5
        lowestAuxImage.hover = True
        self.aux.append(lowestAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('WaterPiranhaBody', 'water_piranha_body.png')
        actorlib.loadIfNotInImageCache('WaterPiranhaBall', 'water_piranha_ball.png')


class ActorImage_WalkingPiranha(actorlib.ActorImage_Static):  # 264
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['WalkPiranha'],
            (-4 / 1.5, -50),
        )
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, self.width, 16, actorlib.AuxiliaryTrackObject.Horizontal))
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, self.width, 16, actorlib.AuxiliaryTrackObject.Horizontal))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('WalkPiranha', 'walk_piranha.png')

    def dataChanged(self):
        if (
            not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject)
            or not isinstance(self.aux[1], actorlib.AuxiliaryTrackObject)
        ):
            return

        distance = self.parent.actordata[5] & 0xF
        sideLen = (distance + 2) * 16

        self.aux[0].setPos(6 / 1.5, 112 / 1.5)
        self.aux[0].setSize(sideLen, 16)

        self.aux[1].setPos(-(sideLen * 1.5) + (42 / 1.5), 112 / 1.5)
        self.aux[1].setSize(sideLen, 16)

        self.aux[0].update()
        self.aux[1].update()
        super().dataChanged()


class ActorImage_FallingIcicle(actorlib.ActorImage_StaticMultiple):  # 265
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('IcicleSmall', 'icicle_small.png')
        actorlib.loadIfNotInImageCache('IcicleLarge', 'icicle_large.png')

    def dataChanged(self):
        super().dataChanged()

        size = self.parent.actordata[5] & 1
        if size == 0:
            self.image = ImageCache['IcicleSmall']
            self.height = 19
        else:
            self.image = ImageCache['IcicleLarge']
            self.height = 36


class ActorImage_RotatingFence(actorlib.ActorImage):  # 266
    def __init__(self, parent):
        w, h = ImageCache['RotatingFence'].width(), ImageCache['RotatingFence'].height()
        super().__init__(parent)
        self.parent.setZValue(24999)

        rotatingFenceAuxImage = actorlib.AuxiliaryImage(parent, w, h)
        rotatingFenceAuxImage.image = ImageCache['RotatingFence']
        rotatingFenceAuxImage.setPos(-((w / 2) + 90) / 1.5, -((h / 2) + 90) / 1.5)
        self.aux.append(rotatingFenceAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RotatingFence', 'rotating_chainlink.png')


class ActorImage_TiltGrate(actorlib.ActorImage_StaticMultiple):  # 267
    @staticmethod
    def loadImages():
        if 'TiltGrateU' in ImageCache:
            return

        ImageCache['TiltGrateU'] = actorlib.GetPixmap('tilt_grate_up.png')
        ImageCache['TiltGrateD'] = actorlib.GetPixmap('tilt_grate_down.png')
        ImageCache['TiltGrateL'] = actorlib.GetPixmap('tilt_grate_left.png')
        ImageCache['TiltGrateR'] = actorlib.GetPixmap('tilt_grate_right.png')

    def dataChanged(self):
        direction = self.parent.actordata[5] & 3
        direction = min(direction, 3)

        if direction < 2:
            self.size = (69, 166)
        else:
            self.size = (166, 69)

        if direction == 0:
            self.offset = (-50 / 1.5, -170 / 1.5)
            self.image = ImageCache['TiltGrateU']
        elif direction == 1:
            self.offset = (-50 / 1.5, 20 / 1.5)
            self.image = ImageCache['TiltGrateD']
        elif direction == 2:
            self.offset = (-218 / 1.5, -2 / 1.5)
            self.image = ImageCache['TiltGrateL']
        elif direction == 3:
            self.offset = (-28 / 1.5, -2 / 1.5)
            self.image = ImageCache['TiltGrateR']

        super().dataChanged()


class ActorImage_LavaGeyser(actorlib.ActorImage_StaticMultiple):  # 268
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        self.parent.setZValue(24999)
        self.dimensions = (-37, -186, 69, 200)

    @staticmethod
    def loadImages():
        if 'LavaGeyser0' in ImageCache:
            return
        for i in range(7):
            lavaGeyser = actorlib.GetImage(f'lava_geyser_{i}.png')
            if lavaGeyser is None:
                continue

            ImageCache[f'LavaGeyser{i}'] = QtGui.QPixmap.fromImage(lavaGeyser)

    def dataChanged(self):

        height = self.parent.actordata[4] >> 4
        startsOn = self.parent.actordata[5] & 1

        if height > 6:
            height = 0
        self.offset = (
            (-30, -170),
            (-28, -155),
            (-30, -155),
            (-43, -138),
            (-32, -105),
            (-26, -89),
            (-32, -34),
        )[height]

        self.alpha = 0.75 if startsOn else 0.5

        self.image = ImageCache[f'LavaGeyser{height}']

        super().dataChanged()


class ActorImage_Parabomb(actorlib.ActorImage_Static):  # 269
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Parabomb'],
            (-2, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Parabomb', 'parabomb.png')


class ActorImage_ScaredyRat(actorlib.ActorImage):  # 271
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ScaredyRat', 'scaredy_rat.png')

    def dataChanged(self):
        number = (self.parent.actordata[5] >> 4) & 3
        direction = self.parent.actordata[5] & 0xF

        self.width = (number + 1) * (ImageCache['ScaredyRat'].width() / 1.5)

        if direction == 0:  # Facing right
            self.xOffset = -self.width + 16
        else:
            self.xOffset = 0

    def paint(self, painter):
        direction = self.parent.actordata[5] & 0xF

        rat = ImageCache['ScaredyRat']
        if direction == 1:
            rat = QtGui.QImage(rat)
            rat = QtGui.QPixmap.fromImage(rat.mirrored(True, False))

        painter.drawTiledPixmap(0, 0, int(self.width * 1.5), 24, rat)


class ActorImage_IceBro(actorlib.ActorImage_Static):  # 272
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['IceBro'],
            (-5, -23),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('IceBro', 'icebro.png')


class ActorImage_CastleGear(actorlib.ActorImage):  # 274
    def __init__(self, parent):
        super().__init__(parent)
        self.aux.append(actorlib.AuxiliaryImage(parent, 456, 456))
        self.parent.setZValue(24999)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CastleGearL', 'castle_gear_large.png')
        actorlib.loadIfNotInImageCache('CastleGearS', 'castle_gear_small.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        big = (self.parent.actordata[4] & 0xF) & 1

        if big:
            self.aux[0].image = ImageCache['CastleGearL']
            self.aux[0].setPos(-216, -216)
        else:
            self.aux[0].image = ImageCache['CastleGearS']
            self.aux[0].setPos(-145, -145)

class ActorImage_FiveEnemyRaft(actorlib.ActorImage_Static):  # 275
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['FiveEnemyRaft'],
            (0, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FiveEnemyRaft', '5_enemy_max_raft.png')


class ActorImage_GhostDoor(ActorImage_Door):  # 276
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.doorName = 'GhostDoor'
        self.doorDimensions = (0, 0, 34, 48)


class ActorImage_TowerDoor(ActorImage_Door):  # 277
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.doorName = 'TowerDoor'
        self.doorDimensions = (-2, -12, 53, 61)
        self.entranceOffset = (15, 66)


class ActorImage_CastleDoor(ActorImage_Door):  # 278
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.doorName = 'CastleDoor'
        self.doorDimensions = (-2, -12, 53, 61)
        self.entranceOffset = (15, 66)


class ActorImage_GiantIceBlock(actorlib.ActorImage_StaticMultiple):  # 280
    @staticmethod
    def loadImages():
        if 'BigIceBlockEmpty' in ImageCache:
            return
        ImageCache['BigIceBlockEmpty'] = actorlib.GetPixmap('big_ice_block_empty.png')
        ImageCache['BigIceBlockBobomb'] = actorlib.GetPixmap('big_ice_block_bobomb.png')
        ImageCache['BigIceBlockSpikeBall'] = actorlib.GetPixmap('big_ice_block_spikeball.png')

    def dataChanged(self):

        item = self.parent.actordata[5] & 3
        if item > 2:
            item = 0

        if item == 0:
            self.image = ImageCache['BigIceBlockEmpty']
        elif item == 1:
            self.image = ImageCache['BigIceBlockBobomb']
        elif item == 2:
            self.image = ImageCache['BigIceBlockSpikeBall']

        super().dataChanged()


class ActorImage_RiseFallWater(ActorImage_LiquidOrFog):  # 285
    def __init__(self, parent):
        super().__init__(parent)

        self.crest = ImageCache['LiquidWaterCrest']
        self.mid = ImageCache['LiquidWater']
        self.rise = ImageCache['LiquidWaterRiseCrest']
        self.riseCrestless = ImageCache['LiquidWaterRise']

        self.top = self.parent.objy
        self.depth = 48

    @staticmethod
    def loadImages():
        if 'LiquidWater' in ImageCache:
            return
        ImageCache['LiquidWater'] = actorlib.GetPixmap('liquid_water.png')
        ImageCache['LiquidWaterCrest'] = actorlib.GetPixmap('liquid_water_crest.png')
        ImageCache['LiquidWaterRise'] = actorlib.GetPixmap('liquid_water_rise.png')
        ImageCache['LiquidWaterRiseCrest'] = actorlib.GetPixmap('liquid_water_rise_crest.png')

    def dataChanged(self):

        self.risingHeight = ((self.parent.actordata[5] >> 4) & 0xF)* 2 + 2 # distance
        self.depth = (self.parent.actordata[5] & 0xF) * 2 + 2

        if self.parent.actordata[3] & 8:  # it Fall
            self.risingHeight = -self.risingHeight

        super().dataChanged()

    def realViewZone(self, painter, zoneRect):
        if self.rise is None or self.crest is None:
            return

        crest_rect = QtCore.QRectF()
        rise_rect = QtCore.QRectF()

        # Create the fill_rect (the area where the liquid or fog should be)
        fill_rect = QtCore.QRectF(zoneRect)
        fill_rect.setTop(self.top * 1.5)

        # Translate the fill_rect to be relative to the zone
        fill_rect.translate(-zoneRect.topLeft())

        # Determine where to put the rise image
        rise_rect = fill_rect.translated(0, -24 * self.risingHeight)

        # Determine what image to draw for the rise indicator
        rise_img = self.rise

        # Set the correct height
        rise_rect.setHeight(rise_img.height())

        # Determine crest & fill's dimensions
        crest_rect = QtCore.QRectF(fill_rect)

        # Limit the crest to not draw past its maximum dimensions
        if (self.depth*24 < self.crest.height()):
            crest_rect.setHeight(self.depth*24)
        else:
            crest_rect.setHeight(self.crest.height())
        fill_rect.setTop(crest_rect.bottom())
        fill_rect.setHeight(self.depth*24 - self.crest.height())

        # Draw everything
        painter.drawTiledPixmap(crest_rect, self.crest)
        painter.drawTiledPixmap(rise_rect, rise_img)
        painter.drawTiledPixmap(fill_rect, self.mid)


    def positionChanged(self):
        self.top = self.parent.objy
        super().positionChanged()


class ActorImage_WoodCircle(actorlib.ActorImage_StaticMultiple):  # 286
    @staticmethod
    def loadImages():
        if 'WoodCircle0' in ImageCache:
            return
        ImageCache['WoodCircle0'] = actorlib.GetPixmap('wood_circle_0.png')
        ImageCache['WoodCircle1'] = actorlib.GetPixmap('wood_circle_1.png')
        ImageCache['WoodCircle2'] = actorlib.GetPixmap('wood_circle_2.png')

    def dataChanged(self):
        super().dataChanged()
        size = (self.parent.actordata[5] & 0xF) % 3

        self.image = ImageCache[f'WoodCircle{size}']

        if size > 2:
            size = 0
        self.dimensions = (
            (-24, -24, 64, 64),
            (-40, -40, 96, 96),
            (-56, -56, 128, 128),
        )[size]


class ActorImage_PathIceBlock(actorlib.ActorImage_StaticMultiple):  # 287
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False
        self.alpha = 0.8

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PathIceBlock', 'unused_path_ice_block.png')

    def dataChanged(self):
        width = (self.parent.actordata[5] & 0xF) + 1
        height = (self.parent.actordata[5] >> 4) + 1

        self.image = ImageCache['PathIceBlock'].scaled(width * 24, height * 24)

        super().dataChanged()


class ActorImage_RollingBarrel(actorlib.ActorImage_Static):  # 288
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['RollingBarrel'],
            (2 / 1.5, -14 / 1.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RollingBarrel', 'barrel_rolling.png')


class ActorImage_Box(actorlib.ActorImage_StaticMultiple):  # 289
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ShipKey', 'ship_key.png')
        actorlib.loadIfNotInImageCache('5Coin', '5_coin.png')

        if 'YoshiFire' not in ImageCache:
            pix = QtGui.QPixmap(48, 24)
            pix.fill(Qt.GlobalColor.transparent)
            paint = QtGui.QPainter(pix)
            paint.drawPixmap(0, 0, ImageCache['BlockContents9'])
            paint.drawPixmap(24, 0, ImageCache['BlockContents3'])
            del paint
            ImageCache['YoshiFire'] = pix

        if 'Box00' in ImageCache:
            return
        for style, stylestr in ((0, 'wood'), (1, 'metal')):
            for size, sizestr in zip(range(4), ('small', 'wide', 'tall', 'big')):
                box = actorlib.GetImage(f'box_{stylestr}_{sizestr}.png')
                if box is None:
                    continue

                ImageCache[f'Box{style}{size}'] = QtGui.QPixmap.fromImage(box)

                items = (
                    (12, 12, 'Coin',  ImageCache['BlockContents1']),
                    (12, 12, 'Mush',  ImageCache['BlockContents2']),
                    (12, 12, 'Fire',  ImageCache['BlockContents3']),
                    (12, 12, 'Prop',  ImageCache['BlockContents4']),
                    (12, 12, 'Peng',  ImageCache['BlockContents5']),
                    (12, 12, 'Mini',  ImageCache['BlockContents6']),
                    (12, 12, 'Star',  ImageCache['BlockContents7']),
                    (0,  12, 'EggF',  ImageCache['YoshiFire']),
                    (12, 12, '5Coin', ImageCache['5Coin']),
                    (12, 12, '1Up',   ImageCache['BlockContents11']),
                    (8,  6,  'Key',   ImageCache['ShipKey']),
                    (12, 12, 'Ice',   ImageCache['BlockContents15']),
                )
                for x, y, itemName, overlayImage in items:
                    newPix = QtGui.QPixmap(ImageCache[f'Box{style}{size}'])
                    painter = QtGui.QPainter(newPix)

                    sizeOffs = (
                        (0,  0),
                        (24, 0),
                        (0,  24),
                        (24, 24),
                    )
                    painter.drawPixmap(x + sizeOffs[size][0], y + sizeOffs[size][1], overlayImage)
                    del painter
                    ImageCache[f'Box{style}{size}{itemName}'] = newPix

    def dataChanged(self):

        style = self.parent.actordata[4] & 1
        size = (self.parent.actordata[5] >> 4) & 3
        item = self.parent.actordata[5] & 0xF

        itemStr = ''
        if style != 1:
            itemNames = ('', 'Coin', 'Mush', 'Fire', 'Prop', 'Peng', 'Mini', 'Star',
                        'Mush', 'EggF', '5Coin', '1Up', 'Mush', 'Mush', 'Key', 'Ice')
            itemStr = itemNames[item]

        self.image = ImageCache[f'Box{style}{size}{itemStr}']

        super().dataChanged()


class ActorImage_Parabeetle(actorlib.ActorImage_StaticMultiple):  # 291
    @staticmethod
    def loadImages():
        if 'ParabeetleRight' in ImageCache:
            return
        ImageCache['ParabeetleRight'] = actorlib.GetPixmap('parabeetle_right.png')
        ImageCache['ParabeetleLeft'] = actorlib.GetPixmap('parabeetle_left.png')
        ImageCache['ParabeetleMoreRight'] = actorlib.GetPixmap('parabeetle_moreright.png')
        ImageCache['ParabeetleAtYou'] = actorlib.GetPixmap('parabeetle_atyou.png')

    def dataChanged(self):
        direction = self.parent.actordata[5] & 0xf
        self.yOffset = -8 / 1.5

        if direction == 0:  # right
            self.xOffset = -19 / 1.5
            self.image = ImageCache['ParabeetleRight']
        elif direction in [1, 14]:  # left
            self.xOffset = -14 / 1.5
            self.image = ImageCache['ParabeetleLeft']
        elif direction in [2, 4, 6, 8, 10]:  # more right
            self.xOffset = -14
            self.image = ImageCache['ParabeetleMoreRight']
        elif direction in [3, 5, 7, 9, 11, 12, 13, 15]:  # at you
            self.xOffset = -22
            self.image = ImageCache['ParabeetleAtYou']

        super().dataChanged()


class ActorImage_HeavyParabeetle(actorlib.ActorImage_StaticMultiple):  # 292
    @staticmethod
    def loadImages():
        if 'HeavyParabeetleRight' in ImageCache:
            return
        ImageCache['HeavyParabeetleRight'] = actorlib.GetPixmap('heavy_parabeetle_right.png')
        ImageCache['HeavyParabeetleLeft'] = actorlib.GetPixmap('heavy_parabeetle_left.png')
        ImageCache['HeavyParabeetleMoreRight'] = actorlib.GetPixmap('heavy_parabeetle_moreright.png')
        ImageCache['HeavyParabeetleAtYou'] = actorlib.GetPixmap('heavy_parabeetle_atyou.png')

    def dataChanged(self):

        direction = self.parent.actordata[5] & 0xf
        self.yOffset = -85 / 1.5

        if direction == 0:  # right
            self.xOffset = -58 / 1.5
            self.image = ImageCache['HeavyParabeetleRight']
        elif direction in [1, 14]:  # left
            self.xOffset = -58 / 1.5
            self.image = ImageCache['HeavyParabeetleLeft']
        elif direction in [2, 4, 6, 8, 10]:  # more right
            self.xOffset = -58 / 1.5
            self.image = ImageCache['HeavyParabeetleMoreRight']
        elif direction in [3, 5, 7, 9, 11, 12, 13, 15]:  # at you
            self.xOffset = -58
            self.image = ImageCache['HeavyParabeetleAtYou']

        super().dataChanged()


class ActorImage_IceCube(actorlib.ActorImage_Static):  # 294
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['IceCube'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('IceCube', 'ice_cube.png')


class ActorImage_NutPlatform(actorlib.ActorImage_StaticMultiple):  # 295
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('NutPlatform', 'nut_platform.png')

    def dataChanged(self):
        offsetUp = self.parent.actordata[5] >> 4
        offsetRight = self.parent.actordata[5] & 7

        if offsetUp == 0:
            self.yOffset = -8
        else:
            self.yOffset = 0

        self.xOffset = (
            -16,
            -8,
            0,
            8,
            16,
            24,
            32,
            40,
        )[offsetRight]

        self.image = ImageCache['NutPlatform']

        super().dataChanged()


class ActorImage_MegaBuzzy(actorlib.ActorImage_StaticMultiple):  # 296
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-43, -74)

    @staticmethod
    def loadImages():
        if 'MegaBuzzyR' in ImageCache:
            return
        ImageCache['MegaBuzzyR'] = actorlib.GetPixmap('megabuzzy_right.png')
        ImageCache['MegaBuzzyL'] = actorlib.GetPixmap('megabuzzy_left.png')
        actorlib.loadIfNotInImageCache('MegaBuzzyF', 'megabuzzy_front.png')

    def dataChanged(self):

        direction = self.parent.actordata[5] & 3
        if direction == 0 or direction > 2:
            self.image = ImageCache['MegaBuzzyR']
        elif direction == 1:
            self.image = ImageCache['MegaBuzzyL']
        elif direction == 2:
            self.image = ImageCache['MegaBuzzyF']

        super().dataChanged()


class ActorImage_DragonCoaster(actorlib.ActorImage):  # 297
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False
        self.height = 22

    @staticmethod
    def loadImages():
        if 'DragonHead' in ImageCache:
            return
        ImageCache['DragonHead'] = actorlib.GetPixmap('dragon_coaster_head.png')
        ImageCache['DragonBody'] = actorlib.GetPixmap('dragon_coaster_body.png')
        ImageCache['DragonTail'] = actorlib.GetPixmap('dragon_coaster_tail.png')

    def dataChanged(self):
        raw_size = self.parent.actordata[5] & 7

        if raw_size == 0:
            self.width = 32
            self.xOffset = 0
        else:
            self.width = (raw_size * 32) + 32
            self.xOffset = 32 - self.width

    def paint(self, painter):
        raw_size = self.parent.actordata[5] & 15

        if raw_size == 0 or raw_size == 8:
            # just the head
            painter.drawPixmap(0, 0, ImageCache['DragonHead'])
        elif raw_size == 1:
            # head and tail only
            painter.drawPixmap(48, 0, ImageCache['DragonHead'])
            painter.drawPixmap(0, 0, ImageCache['DragonTail'])
        else:
            painter.drawPixmap(int((self.width * 1.5) - 48), 0, ImageCache['DragonHead'])
            if raw_size > 1:
                painter.drawTiledPixmap(48, 0, int((self.width * 1.5) - 96), 24, ImageCache['DragonBody'])
            painter.drawPixmap(0, 0, ImageCache['DragonTail'])


class ActorImage_LongCannon(actorlib.ActorImage_StaticMultiple):  # 298
    def __init__(self, parent):
        super().__init__(parent, 1.5)

    @staticmethod
    def loadImages():
        # TODO: make LongCannonER and BLongCannonER
        if 'LongCannonFL' in ImageCache:
            return
        ImageCache['LongCannonFL'] = actorlib.GetPixmap('cannon_front_left.png')
        ImageCache['LongCannonFR'] = actorlib.GetPixmap('cannon_front_right.png')
        ImageCache['LongCannonM'] = actorlib.GetPixmap('cannon_middle.png')
        ImageCache['LongCannonEL'] = actorlib.GetPixmap('cannon_end_left.png')

        ImageCache['BLongCannonFL'] = actorlib.GetPixmap('cannonbig_front_left.png')
        ImageCache['BLongCannonFR'] = actorlib.GetPixmap('cannonbig_front_right.png')
        ImageCache['BLongCannonM'] = actorlib.GetPixmap('cannonbig_middle.png')
        ImageCache['BLongCannonEL'] = actorlib.GetPixmap('cannonbig_end_left.png')

        ImageCache['LongCannonFU'] = actorlib.GetPixmap('cannon_front_up.png')
        ImageCache['BLongCannonFU'] = actorlib.GetPixmap('cannonbig_front_up.png')

        ImageCache['LongCannonER'] = ImageCache['LongCannonEL']
        ImageCache['BLongCannonER'] = ImageCache['BLongCannonEL']
        #ImageCache['LongCannonER'] = actorlib.GetPixmap('cannon_end_right.png')
        #ImageCache['BLongCannonER'] = actorlib.GetPixmap('cannonbig_end_right.png')

    def dataChanged(self):
        super().dataChanged()

        raw_length = self.parent.actordata[4] & 0xF
        self.dir = self.parent.actordata[5] & 1
        self.big = self.parent.actordata[5] & 0x10 != 0

        self.bugged = (self.parent.actordata[5] & 2 == 2) and self.dir == 0

        if self.bugged:
            self.dir = 1

        if self.big:
            self.height = 32
            self.tilesize = 48
            self.width = 16 * (raw_length + 3)
            if self.dir == 0:
                self.numMiddle = raw_length - 2
                self.xOffset = 16 - self.width
            else:
                self.xOffset = 0
                self.numMiddle = raw_length - 1

            if self.bugged:
                self.xOffset = -8
                self.width += 8
        else:
            self.height = 16
            self.tilesize = 24
            self.numMiddle = raw_length
            self.width = 16 * (raw_length + 2)
            if self.dir == 0:
                self.xOffset = 12 - self.width
            else:
                self.xOffset = 4

            if self.bugged:
                self.xOffset = 0
                self.height += 8
                self.width -= 4

    def paint(self, painter):
        super().paint(painter)

        big_s = 'B' if self.big else ''

        middle = ImageCache[big_s + 'LongCannonM']
        solid = actorlib.GetTile(1)
        if self.dir == 0: # right
            front = ImageCache[big_s + 'LongCannonFR']
            end = ImageCache[big_s + 'LongCannonEL']
        else:
            front = ImageCache[big_s + 'LongCannonFL']
            end = ImageCache[big_s + 'LongCannonER']

        # the front
        if self.bugged and self.big:
            front = ImageCache['BLongCannonFU']
            painter.drawPixmap(0, 0, front)
        elif self.bugged:
            front = ImageCache['LongCannonFU']
            painter.drawPixmap(0, 12, front)
        elif self.big and self.dir == 0:
            painter.drawPixmap(24 + 24 * self.numMiddle + self.tilesize, 0, front)
        elif self.dir == 0:
            painter.drawPixmap(24 * self.numMiddle + self.tilesize, 0, front)
        else:
            painter.drawPixmap(0, 0, front)

        # the middle
        if self.bugged and self.big:
            painter.drawTiledPixmap(self.tilesize, 0, self.numMiddle * 24 + 8, self.tilesize, middle)
        elif self.bugged:
            painter.drawTiledPixmap(self.tilesize, 12, self.numMiddle * 24 - 8, self.tilesize, middle)
        elif self.dir == 0 and self.big:
            painter.drawTiledPixmap(self.tilesize + 24, 0, self.numMiddle * 24, self.tilesize, middle)
        else:
            painter.drawTiledPixmap(self.tilesize, 0, self.numMiddle * 24, self.tilesize, middle)

        # the end
        if self.bugged and self.big:
            painter.drawPixmap(24 * self.numMiddle + self.tilesize + 8, 0, end)
        elif self.bugged:
            painter.drawPixmap(24 * self.numMiddle + self.tilesize - 8, 12, end)
        elif self.dir == 0 and self.big:
            painter.drawTiledPixmap(0, 0, 24, 48, solid)
            painter.drawPixmap(24, 0, end)
        elif self.dir == 0:
            painter.drawPixmap(0, 0, end)
        else:
            painter.drawPixmap(24 * self.numMiddle + self.tilesize, 0, end)


class ActorImage_CannonMulti(actorlib.ActorImage_StaticMultiple):  # 299
    def __init__(self, parent):
        super().__init__(parent, 1.5)

    @staticmethod
    def loadImages():
        if 'CannonMultiU0' in ImageCache:
            return
        CannonUR = actorlib.GetImage('cannon_multi_0.png')
        CannonUL = actorlib.GetImage('cannon_multi_1.png')
        if CannonUR is None or CannonUL is None:
            return

        ImageCache['CannonMultiU0'] = QtGui.QPixmap.fromImage(CannonUR)
        ImageCache['CannonMultiU1'] = QtGui.QPixmap.fromImage(CannonUL)
        ImageCache['CannonMultiD0'] = QtGui.QPixmap.fromImage(CannonUR.mirrored(False, True))
        ImageCache['CannonMultiD1'] = QtGui.QPixmap.fromImage(CannonUL.mirrored(False, True))

    def dataChanged(self):
        left = self.parent.actordata[5] & 1
        upsideDown = (self.parent.actordata[5] >> 4) & 1

        if upsideDown:
            self.image = ImageCache[f'CannonMultiD{left}']
            self.offset = (-8, -1)
        else:
            self.image = ImageCache[f'CannonMultiU{left}']
            self.offset = (-8, -11)

        super().dataChanged()


class ActorImage_RotCannon(actorlib.ActorImage_StaticMultiple):  # 300
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RotCannon', 'rot_cannon.png')
        actorlib.loadIfNotInImageCache('RotCannonU', 'rot_cannon_u.png')

    def dataChanged(self):

        upsideDown = (self.parent.actordata[5] >> 4) & 1
        if not upsideDown:
            self.image = ImageCache['RotCannon']
            self.offset = (-12, -29)
        else:
            self.image = ImageCache['RotCannonU']
            self.offset = (-12, 0)

        super().dataChanged()


class ActorImage_RotCannonPipe(actorlib.ActorImage_StaticMultiple):  # 301
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RotCannonPipe', 'rot_cannon_pipe.png')
        actorlib.loadIfNotInImageCache('RotCannonPipeU', 'rot_cannon_pipe_u.png')

    def dataChanged(self):

        upsideDown = (self.parent.actordata[5] >> 4) & 1
        if not upsideDown:
            self.image = ImageCache['RotCannonPipe']
            self.offset = (-40, -74)
        else:
            self.image = ImageCache['RotCannonPipeU']
            self.offset = (-40, 0)

        super().dataChanged()


class ActorImage_MontyMole(actorlib.ActorImage_StaticMultiple):  # 303
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Mole', 'monty_mole.png')
        actorlib.loadIfNotInImageCache('MoleCave', 'monty_mole_hole.png')

    def dataChanged(self):

        notInCave = self.parent.actordata[5] & 1
        if not notInCave:  # wow, that looks weird
            self.image = ImageCache['MoleCave']
            self.offset = (-6, -8 / 1.5)
        else:
            self.image = ImageCache['Mole']
            self.offset = (-2, -4)

        super().dataChanged()


class ActorImage_RotFlameCannon(actorlib.ActorImage_StaticMultiple):  # 304
    @staticmethod
    def loadImages():
        if 'RotFlameCannon0' in ImageCache:
            return
        for i in range(5):
            originalImg = actorlib.GetImage(f'rotating_flame_cannon_{i}.png')
            if originalImg is None:
                continue

            mirroredImg = QtGui.QPixmap.fromImage(originalImg.mirrored(False, True))
            ImageCache[f'RotFlameCannon{i}'] = QtGui.QPixmap.fromImage(originalImg)
            ImageCache[f'RotFlameCannonFlipped{i}'] = mirroredImg

    def dataChanged(self):

        orientation = self.parent.actordata[5] >> 4
        length = self.parent.actordata[5] & 15
        orientation = '' if orientation == 0 else 'Flipped'

        if length > 4:
            length = 0
        if not orientation:
            self.yOffset = -2
        else:
            self.yOffset = 0

        self.image = ImageCache[f'RotFlameCannon{orientation}{length}']

        super().dataChanged()


class ActorImage_LightCircle(actorlib.ActorImage):  # 305
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        lightCircleAuxImage = actorlib.AuxiliaryImage(parent, 128, 128)
        lightCircleAuxImage.image = ImageCache['LightCircle']
        lightCircleAuxImage.setPos(-60, -60)
        lightCircleAuxImage.hover = False
        lightCircleAuxImage.setIsBehindActor(False)
        self.aux.append(lightCircleAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LightCircle', 'light_circle.png')


class ActorImage_RotSpotlight(actorlib.ActorImage_StaticMultiple):  # 306
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-22, -64)

    @staticmethod
    def loadImages():
        if 'RotSpotlight0' in ImageCache:
            return
        for i in range(16):
            ImageCache[f'RotSpotlight{i}'] = actorlib.GetPixmap(f'rotational_spotlight_{i}.png')

    def dataChanged(self):

        angle = self.parent.actordata[3] & 15
        self.image = ImageCache[f'RotSpotlight{angle}']

        super().dataChanged()


class ActorImage_HammerBroPlatform(ActorImage_HammerBroNormal):  # 308
    pass


class ActorImage_SynchroFlameJet(actorlib.ActorImage_StaticMultiple):  # 309
    @staticmethod
    def loadImages():
        if 'SynchroFlameJetOnR' in ImageCache:
            return
        transform90 = QtGui.QTransform()
        transform270 = QtGui.QTransform()
        transform90.rotate(90)
        transform270.rotate(270)

        onImage = actorlib.GetImage('synchro_flame_jet.png')
        offImage = actorlib.GetImage('synchro_flame_jet_off.png')
        if onImage is None or offImage is None:
            return

        ImageCache['SynchroFlameJetOnR'] = QtGui.QPixmap.fromImage(onImage)
        ImageCache['SynchroFlameJetOnD'] = QtGui.QPixmap.fromImage(onImage.transformed(transform90))
        ImageCache['SynchroFlameJetOnL'] = QtGui.QPixmap.fromImage(onImage.mirrored(True, False))
        ImageCache['SynchroFlameJetOnU'] = QtGui.QPixmap.fromImage(
            onImage.transformed(transform270).mirrored(True, False))
        ImageCache['SynchroFlameJetOffR'] = QtGui.QPixmap.fromImage(offImage)
        ImageCache['SynchroFlameJetOffD'] = QtGui.QPixmap.fromImage(offImage.transformed(transform90))
        ImageCache['SynchroFlameJetOffL'] = QtGui.QPixmap.fromImage(offImage.mirrored(True, False))
        ImageCache['SynchroFlameJetOffU'] = QtGui.QPixmap.fromImage(
            offImage.transformed(transform270).mirrored(True, False))

    def dataChanged(self):
        mode = self.parent.actordata[4] & 1
        direction = self.parent.actordata[5] & 3

        mode = 'Off' if mode else 'On'
        self.offset = (
            (0, 0),
            (-96, 0),
            (0, -96),
            (0, 0),
        )[direction]
        directionstr = 'RLUD'[direction]

        self.image = ImageCache[f'SynchroFlameJet{mode}{directionstr}']

        super().dataChanged()


class ActorImage_ArrowSign(actorlib.ActorImage_StaticMultiple):  # 310
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-8, -16)

    @staticmethod
    def loadImages():
        if 'ArrowSign0' in ImageCache:
            return
        for i in range(8):
            ImageCache[f'ArrowSign{i}'] = actorlib.GetPixmap(f'arrow_sign_{i}.png')

    def dataChanged(self):
        direction = self.parent.actordata[5] & 0xF
        if direction > 7:
            direction = 0

        self.image = ImageCache[f'ArrowSign{direction}']
        super().dataChanged()


class ActorImage_MegaIcicle(actorlib.ActorImage_Static):  # 311
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MegaIcicle'],
            (-24, -3),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MegaIcicle', 'mega_icicle.png')


class ActorImage_BubbleGen(actorlib.ActorImage):  # 314

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BubbleGenEffect', 'bubble_gen.png')

    def dataChanged(self):
        scene = self.parent.scene()
        if scene is not None:
            scene.update()

    def positionChanged(self):
        scene = self.parent.scene()
        if scene is not None:
            scene.update()

    def realViewZone(self, painter, zoneRect):

        # Constants (change these if you want)
        bubbleFrequency = .01
        bubbleEccentricityX = 16
        bubbleEccentricityY = 48

        size = self.parent.actordata[5] & 0xF
        if size > 3:
            return

        Image = ImageCache['BubbleGenEffect']

        if size == 0:
            pct = 50.0
        elif size == 1:
            pct = 60.0
        elif size == 2:
            pct = 80.0
        else:
            pct = 70.0
        Image = Image.scaledToWidth(int(Image.width() * pct / 100))

        distanceFromTop = (self.parent.objy * 1.5) - zoneRect.topLeft().y()
        rndGen = random.Random()
        rndGen.seed(distanceFromTop + self.parent.objx)  # looks ridiculous without this

        numOfBubbles = int(distanceFromTop * bubbleFrequency)
        for num in range(numOfBubbles):
            xmod = (rndGen.random() * 2 * bubbleEccentricityX) - bubbleEccentricityX
            ymod = (rndGen.random() * 2 * bubbleEccentricityY) - bubbleEccentricityY
            x = ((self.parent.objx * 1.5) - zoneRect.topLeft().x()) + xmod + 12 - (Image.width() / 2.0)
            y = ((num * 1.0 / numOfBubbles) * distanceFromTop) + ymod
            if not (0 < y < self.parent.objy * 1.5):
                continue
            painter.drawPixmap(int(x), int(y), Image)


class ActorImage_Bolt(actorlib.ActorImage_Static):  # 315
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Bolt'],
            (2 / 1.5, 0),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Bolt', 'bolt.png')


class ActorImage_BoltBox(actorlib.ActorImage):  # 316
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'BoltBoxTL' in ImageCache:
            return
        ImageCache['BoltBoxTL'] = actorlib.GetPixmap('boltbox_tl.png')
        ImageCache['BoltBoxT'] = actorlib.GetPixmap('boltbox_t.png')
        ImageCache['BoltBoxTR'] = actorlib.GetPixmap('boltbox_tr.png')
        ImageCache['BoltBoxL'] = actorlib.GetPixmap('boltbox_l.png')
        ImageCache['BoltBoxM'] = actorlib.GetPixmap('boltbox_m.png')
        ImageCache['BoltBoxR'] = actorlib.GetPixmap('boltbox_r.png')
        ImageCache['BoltBoxBL'] = actorlib.GetPixmap('boltbox_bl.png')
        ImageCache['BoltBoxB'] = actorlib.GetPixmap('boltbox_b.png')
        ImageCache['BoltBoxBR'] = actorlib.GetPixmap('boltbox_br.png')

    def dataChanged(self):
        size = self.parent.actordata[5]
        self.width = (size & 0xF) * 16 + 32
        self.height = ((size & 0xF0) >> 4) * 16 + 32

    def paint(self, painter):
        xsize = int(self.width * 1.5)
        ysize = int(self.height * 1.5)

        painter.drawPixmap(0, 0, ImageCache['BoltBoxTL'])
        painter.drawTiledPixmap(24, 0, xsize - 48, 24, ImageCache['BoltBoxT'])
        painter.drawPixmap(xsize - 24, 0, ImageCache['BoltBoxTR'])

        painter.drawTiledPixmap(0, 24, 24, ysize - 48, ImageCache['BoltBoxL'])
        painter.drawTiledPixmap(24, 24, xsize - 48, ysize - 48, ImageCache['BoltBoxM'])
        painter.drawTiledPixmap(xsize - 24, 24, 24, ysize - 48, ImageCache['BoltBoxR'])

        painter.drawPixmap(0, ysize - 24, ImageCache['BoltBoxBL'])
        painter.drawTiledPixmap(24, ysize - 24, xsize - 48, 24, ImageCache['BoltBoxB'])
        painter.drawPixmap(xsize - 24, ysize - 24, ImageCache['BoltBoxBR'])


class ActorImage_BoxGenerator(actorlib.ActorImage_StaticMultiple):  # 318
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.yOffset = -64

        boxAuxImage = actorlib.AuxiliaryImage(parent, 96, 48)
        boxAuxImage.setPos(0, 64)
        boxAuxImage.alpha = 0.5
        boxAuxImage.hover = True
        self.aux.append(boxAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BoxGenerator', 'box_generator.png')

        actorlib.loadIfNotInImageCache('Box01', 'box_wood_wide.png')
        actorlib.loadIfNotInImageCache('Box11', 'box_metal_wide.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        boxType = self.parent.actordata[4] & 1

        if boxType == 0:
            typeStr = 'Box01'
        else:
            typeStr = 'Box11'

        self.aux[0].image = ImageCache[typeStr]

        self.image = ImageCache['BoxGenerator']

        super().dataChanged()


class ActorImage_UnusedWiimoteDoor(ActorImage_UnusedGiantDoor):  # 319
    pass


class ActorImage_UnusedSlidingWiimoteDoor(ActorImage_UnusedGiantDoor):  # 320
    pass


class ActorImage_ArrowBlock(actorlib.ActorImage_StaticMultiple):  # 321
    @staticmethod
    def loadImages():
        if 'ArrowBlock0' in ImageCache:
            return
        ImageCache['ArrowBlock0'] = actorlib.GetPixmap('arrow_block_up.png')
        ImageCache['ArrowBlock1'] = actorlib.GetPixmap('arrow_block_down.png')
        ImageCache['ArrowBlock2'] = actorlib.GetPixmap('arrow_block_left.png')
        ImageCache['ArrowBlock3'] = actorlib.GetPixmap('arrow_block_right.png')

    def dataChanged(self):
        direction = self.parent.actordata[5] & 3
        self.image = ImageCache[f'ArrowBlock{direction}']

        super().dataChanged()


class ActorImage_BooCircle(actorlib.ActorImage):  # 323
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        self.BooAuxImage = QtGui.QPixmap(1024, 1024)
        self.BooAuxImage.fill(Qt.GlobalColor.transparent)
        booAuxImage = actorlib.AuxiliaryImage(parent, 1024, 1024)
        booAuxImage.image = self.BooAuxImage
        offsetX = ImageCache['Boo1'].width() / 4
        offsetY = ImageCache['Boo1'].height() / 4
        booAuxImage.setPos(-512 + offsetX, -512 + offsetY)
        booAuxImage.hover = False
        self.aux.append(booAuxImage)

    @staticmethod
    def loadImages():
        if 'Boo2' in ImageCache:
            return
        ImageCache['Boo1'] = actorlib.GetPixmap('boo1.png')
        ImageCache['Boo2'] = actorlib.GetPixmap('boo2.png')
        ImageCache['Boo3'] = actorlib.GetPixmap('boo3.png')
        ImageCache['Boo4'] = actorlib.GetPixmap('boo4.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        # Constants (change these to fine-tune the boo positions)
        radiusMultiplier = 24  # pixels between boos per distance value
        radiusConstant = 24  # add to all radius values
        opacity = 0.5

        # Read the data
        outrad = self.parent.actordata[2] & 15
        inrad = self.parent.actordata[3] >> 4
        ghostnum = 1 + (self.parent.actordata[3] & 15)
        differentRads = inrad != outrad

        # Give up if the data is invalid
        if inrad > outrad:
            null = QtGui.QPixmap(2, 2)
            null.fill(Qt.GlobalColor.transparent)
            self.aux[0].image = null
            return

        # Create a pixmap
        pix = QtGui.QPixmap(1024, 1024)
        pix.fill(Qt.GlobalColor.transparent)
        paint = QtGui.QPainter(pix)
        paint.setOpacity(opacity)

        # Paint each boo
        for i in range(ghostnum):
            # Find the angle at which to place the ghost from the center
            MissingGhostWeight = 0.75 - (1 / ghostnum)  # approximate
            angle = math.radians(-360 * i / (ghostnum + MissingGhostWeight)) + 89.6

            # Since the origin of the boo img is in the top left, account for that
            offsetX = ImageCache['Boo1'].width() / 2
            offsetY = (ImageCache['Boo1'].height() / 2) + 16  # the circle is not centered

            # Pick a pixmap
            boo = ImageCache[f'Boo{1 if i == 0 else ((i - 1) % 3) + 2}']  # 1  2 3 4  2 3 4  2 3 4 ...

            # Find the abs pos, and paint the ghost at its inner position
            x = math.sin(angle) * ((inrad * radiusMultiplier) + radiusConstant) - offsetX
            y = -(math.cos(angle) * ((inrad * radiusMultiplier) + radiusConstant)) - offsetY
            paint.drawPixmap(int(x + 512), int(y + 512), boo)

            # Paint it at its outer position if it has one
            if differentRads:
                x = math.sin(angle) * ((outrad * radiusMultiplier) + radiusConstant) - offsetX
                y = -(math.cos(angle) * ((outrad * radiusMultiplier) + radiusConstant)) - offsetY
                paint.drawPixmap(int(x + 512), int(y + 512), boo)

        # Finish it
        paint = None
        self.aux[0].image = pix


class ActorImage_GhostHouseStand(actorlib.ActorImage_Static):  # 325
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GhostHouseStand'],
            (8, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GhostHouseStand', 'ghost_house_stand.png')


class ActorImage_KingBill(actorlib.ActorImage):  # 326
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        kingBillAuxPath = actorlib.AuxiliaryPainterPath(parent, QtGui.QPainterPath(), 24, 24)
        kingBillAuxPath.setSize(24 * 17, 24 * 17)
        self.aux.append(kingBillAuxPath)

        self.paths = []
        for direction in range(4):

            # This has to be within the loop because the
            # following commands transpose them
            PointsRects = (  # These form a LEFT-FACING bullet
                QtCore.QPointF(192, -180 + 180),
                QtCore.QRectF(0, -180 + 180, 384, 384),
                QtCore.QPointF(192 + 72, 204 + 180),
                QtCore.QPointF(192 + 72 + 6, 204 - 24 + 180),
                QtCore.QPointF(192 + 72 + 42, 204 - 24 + 180),
                QtCore.QPointF(192 + 72 + 48, 204 + 180),
                QtCore.QPointF(192 + 72 + 96, 204 + 180),
                QtCore.QPointF(192 + 72 + 96 + 6, 204 - 6 + 180),
                QtCore.QPointF(192 + 72 + 96 + 6, -180 + 6 + 180),
                QtCore.QPointF(192 + 72 + 96, -180 + 180),
                QtCore.QPointF(192 + 72 + 48, -180 + 180),
                QtCore.QPointF(192 + 72 + 42, -180 + 24 + 180),
                QtCore.QPointF(192 + 72 + 6, -180 + 24 + 180),
                QtCore.QPointF(192 + 72, -180 + 180),
            )

            arc = 'LR'
            for thing in PointsRects:  # translate each point to flip the image
                if direction == 0:  # faces left
                    arc = 'LR'
                elif direction == 1:  # faces right
                    arc = 'LR'
                    if isinstance(thing, QtCore.QPointF):
                        thing.setX(408 - thing.x())
                    else:
                        thing.setRect(408 - thing.x(), thing.y(), -thing.width(), thing.height())
                elif direction == 2:  # faces down
                    arc = 'UD'
                    if isinstance(thing, QtCore.QPointF):
                        x = thing.y()
                        y = 408 - thing.x()
                        thing.setX(x)
                        thing.setY(y)
                    else:
                        x = thing.y()
                        y = 408 - thing.x()
                        thing.setRect(x, y, thing.height(), -thing.width())
                else:  # faces up
                    arc = 'UD'
                    if isinstance(thing, QtCore.QPointF):
                        x = thing.y()
                        y = thing.x()
                        thing.setX(x)
                        thing.setY(y)
                    else:
                        x = thing.y()
                        y = thing.x()
                        thing.setRect(x, y, thing.height(), thing.width())

            PainterPath = QtGui.QPainterPath()
            PainterPath.moveTo(PointsRects[0])
            if arc == 'LR':
                PainterPath.arcTo(PointsRects[1], 90, 180)
            else:
                PainterPath.arcTo(PointsRects[1], 180, -180)
            for point in PointsRects[2:]:
                PainterPath.lineTo(point)
            PainterPath.closeSubpath()
            self.paths.append(PainterPath)

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryPainterPath):
            return

        direction = self.parent.actordata[5] & 3

        self.aux[0].setPath(self.paths[direction])

        newx, newy = (
            (0, (-8 * 24) + 12),
            ((-24 * 16), (-8 * 24) + 12),
            ((-24 * 10), (-24 * 16)),
            ((-24 * 5), 0),
        )[direction]
        self.aux[0].setPos(newx, newy)

        super().dataChanged()


class ActorImage_LinePlatformBolt(actorlib.ActorImage_Static):  # 327
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
        )

        self.dimensions = (0, -16, 112, 32)

    @staticmethod
    def loadImages():
        if 'LinePlatformBoltLeft' in ImageCache:
            return

        ImageCache['LinePlatformBoltLeft'] = actorlib.GetPixmap('line_platform_with_bolt_left.png')
        ImageCache['LinePlatformBoltCenter'] = actorlib.GetPixmap('line_platform_with_bolt_center.png')
        ImageCache['LinePlatformBoltRight'] = actorlib.GetPixmap('line_platform_with_bolt_right.png')
        actorlib.loadIfNotInImageCache('Bolt', 'bolt.png')

    def dataChanged(self):
        pass

    def paint(self, painter):
        super().paint(painter)

        painter.drawPixmap(62, 0, ImageCache['Bolt'])
        painter.drawPixmap(0, 24, ImageCache['LinePlatformBoltLeft'])
        painter.drawTiledPixmap(24, 24, 120, 24, ImageCache['LinePlatformBoltCenter'])
        painter.drawPixmap(144, 24, ImageCache['LinePlatformBoltRight'])


class ActorImage_BubbleCannon(actorlib.ActorImage_StaticMultiple):  # 328
    @staticmethod
    def loadImages():
        if 'BubbleCannon0' in ImageCache:
            return
        ImageCache['BubbleCannon0'] = actorlib.GetPixmap('bubble_cannon_small.png')
        ImageCache['BubbleCannon1'] = actorlib.GetPixmap('bubble_cannon_big.png')

    def dataChanged(self):
        size = self.parent.actordata[5] & 1
        self.image = ImageCache[f'BubbleCannon{size}']
        self.offset = (
            (-17, -15),
            (-36, -31),
        )[size]

        super().dataChanged()


class ActorImage_RopeLadder(actorlib.ActorImage_StaticMultiple):  # 330
    @staticmethod
    def loadImages():
        if 'RopeLadder0' in ImageCache:
            return
        ImageCache['RopeLadder0'] = actorlib.GetPixmap('ropeladder_0.png')
        ImageCache['RopeLadder1'] = actorlib.GetPixmap('ropeladder_1.png')
        ImageCache['RopeLadder2'] = actorlib.GetPixmap('ropeladder_2.png')

    def dataChanged(self):

        size = self.parent.actordata[5]
        if size > 2:
            size = 0

        self.image = ImageCache[f'RopeLadder{size}']
        self.offset = (-3, -2)

        super().dataChanged()


class ActorImage_DishPlatform(actorlib.ActorImage_StaticMultiple):  # 331
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)
        self.actorbox.shown = True

        self.aux.append(actorlib.AuxiliaryImage(parent, 304, 195))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('DishPlatform0', 'dish_platform_short.png')
        actorlib.loadIfNotInImageCache('DishPlatform1', 'dish_platform_long.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        posY = -12

        size = self.parent.actordata[4] & 15
        if size == 0:
            posX = -215
            width = 454
        else:
            size = 1
            posX = -311
            width = 646

        self.aux[0].image = ImageCache[f'DishPlatform{size}']
        self.aux[0].setSize(width, 195, posX, posY)

        super().dataChanged()


class ActorImage_PlayerBlockPlatform(actorlib.ActorImage_Static):  # 333
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PlayerBlockPlatform'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PlayerBlockPlatform', 'player_block_platform.png')


class ActorImage_CheepGiant(actorlib.ActorImage):  # 334
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        self.aux.append(actorlib.AuxiliaryTrackObject(self.parent, 24, 24, actorlib.AuxiliaryTrackObject.Horizontal))

    @staticmethod
    def loadImages():
        if 'CheepGiantRedLeft' in ImageCache:
            return
        ImageCache['CheepGiantRedLeft'] = actorlib.GetPixmap('cheep_giant_red.png')
        ImageCache['CheepGiantRedAtYou'] = actorlib.GetPixmap('cheep_giant_red_atyou.png')
        ImageCache['CheepGiantGreen'] = actorlib.GetPixmap('cheep_giant_green.png')
        ImageCache['CheepGiantYellow'] = actorlib.GetPixmap('cheep_giant_yellow.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        type = self.parent.actordata[5] & 0xF
        if type in (1, 7):
            self.image = ImageCache['CheepGiantGreen']
        elif type == 8:
            self.image = ImageCache['CheepGiantYellow']
        elif type == 5:
            self.image = ImageCache['CheepGiantRedAtYou']
        else:
            self.image = ImageCache['CheepGiantRedLeft']
        self.size = (self.image.width() / 1.5, self.image.height() / 1.5)
        self.xOffset = 0 if type != 5 else -8

        if type == 3:
            distance = ((self.parent.actordata[3] & 0xF) + 1) * 16
            self.aux[0].setSize((distance * 2) + 16, 16)
            self.aux[0].setPos(-distance * 1.5, 8)
        else:
            self.aux[0].setSize(0, 24)

    def paint(self, painter):
        if self.image is None:
            return

        painter.drawPixmap(0, 0, self.image)


class ActorImage_CheepSchool(actorlib.ActorImage_Static):  # 335
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = True

        # Make 4 auxiliaries for our formation Cheeps
        self.aux.append(actorlib.AuxiliaryImage(parent, 26, 24))
        self.aux.append(actorlib.AuxiliaryImage(parent, 26, 24))
        self.aux.append(actorlib.AuxiliaryImage(parent, 26, 24))
        self.aux.append(actorlib.AuxiliaryImage(parent, 26, 24))

    @staticmethod
    def loadImages():
        if 'CheepRedLeft' in ImageCache:
            return
        ImageCache['CheepRedLeft'] = actorlib.GetPixmap('cheep_red.png')

    def dataChanged(self):
        formation = self.parent.actordata[4] & 0xF
        shape = self.parent.actordata[5] & 0xF
        noPreview = formation == 0 or formation > 3

        for aux in self.aux:
            if not isinstance(aux, actorlib.AuxiliaryImage):
                continue

            aux.image = ImageCache['CheepRedLeft']
            aux.setIsBehindActor(False)
            aux.hover = False
            # Hide them if its random or an invalid ID
            aux.alpha = 0.0 if noPreview else 1.0
        if noPreview:
            return

        shape = min(shape, 2)

        positions = [
        ( # Shape 0
            # Aux 0   # Aux 1   # Aux 2   # Aux 3
            (), # Dummy space for random option
            ((16, 36), (32, 8), (28, 64), (48, 32)),
            ((16, 8), (32, 36), (48, 4), (64, 39)),
            ((16, 36), (32, 8), (48, 40), (64, 12)),
        ), ( # Shape 1
            (),
            ((8, 20), (36, 8), (64, 18), (92, 3)),
            ((8, 18), (36, 4), (64, 8), (92, 20)),
            ((8, 5), (36, 20), (64, 18), (92, 8)),
        ), ( # Shape 2
            (),
            ((8, 8), (24, 36), (5, 64), (20, 92)),
            ((20, 8), (13, 36), (8, 64), (24, 92)),
            ((8, 8), (28, 36), (24, 64), (4, 92)),
        )]

        for idx, aux in enumerate(self.aux):
            if not isinstance(aux, actorlib.AuxiliaryImage):
                continue

            aux.setPos((positions[shape][formation][idx][0]-8) * 1.5, (positions[shape][formation][idx][1]-8) * 1.5)
        super().dataChanged()


class ActorImage_WendyKoopa(actorlib.ActorImage_Static):  # 336
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['WendyKoopa'],
            (-23, -23),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('WendyKoopa', 'Wendy_Koopa.png')


class ActorImage_IggyKoopa(actorlib.ActorImage_Static):  # 337
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['IggyKoopa'],
            (-17, -46),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('IggyKoopa', 'Iggy_Koopa.png')


# Copied and edited from Miyamoto, credit to mrbengtsson for original code
class ActorImage_MovingBulletBillLauncher(actorlib.ActorImage):  # 338
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BBLauncherT', 'bullet_launcher_top.png')
        actorlib.loadIfNotInImageCache('BBLauncherM', 'bullet_launcher_middle.png')


    def dataChanged(self):
        self.image = None
        self.xOffset = 0
        self.width = 16

        self.cannonHeight = (self.parent.actordata[5] & 0xF0) >> 4
        self.cannonHeightTwo = self.parent.actordata[5] & 0xF

        if self.cannonHeight >= self.cannonHeightTwo:
            self.height = (self.cannonHeight + 2) * 16
            self.yOffset = -(self.cannonHeight + 1) * 16
        else:
            self.height = (self.cannonHeightTwo + 2) * 16
            self.yOffset = -(self.cannonHeightTwo + 1) * 16

    def paint(self, painter):
        if self.cannonHeightTwo > self.cannonHeight:
            painter.drawPixmap(0, 0, 24, 48, ImageCache['BBLauncherT'])
            painter.drawTiledPixmap(0, 48, 24, 24 * self.cannonHeightTwo, ImageCache['BBLauncherM'])

            painter.setOpacity(0.5)
            painter.drawPixmap(0, 24 * (self.cannonHeightTwo - self.cannonHeight), 24, 48, ImageCache['BBLauncherT'])
            painter.drawTiledPixmap(0, 24 * (self.cannonHeightTwo - self.cannonHeight + 2), 24, 48 * self.cannonHeight, ImageCache['BBLauncherM'])
            painter.setOpacity(1)
        else:
            if self.cannonHeightTwo < self.cannonHeight: # No need to draw both if they're at the same height
                painter.setOpacity(0.5)
                painter.drawPixmap(0, 0, 24, 48, ImageCache['BBLauncherT'])
                painter.drawTiledPixmap(0, 48, 24, 24 * self.cannonHeight, ImageCache['BBLauncherM'])
                painter.setOpacity(1)

            painter.drawPixmap(0, 24 * (self.cannonHeight - self.cannonHeightTwo), 24, 48, ImageCache['BBLauncherT'])
            painter.drawTiledPixmap(0, 24 * (self.cannonHeight - self.cannonHeightTwo + 2), 24, 48 * self.cannonHeight, ImageCache['BBLauncherM'])


class ActorImage_Pipe_MovingUp(ActorImage_Pipe):  # 339
    def dataChanged(self):
        self.length1 = (self.parent.actordata[5] >> 4) + 2
        self.length2 = (self.parent.actordata[5] & 0xF) + 2
        self.color = (
            'Green', 'Red', 'Yellow', 'Blue',
        )[self.parent.actordata[3] & 3]

        super().dataChanged()


class ActorImage_LemmyKoopa(actorlib.ActorImage_Static):  # 340
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['LemmyKoopa'],
            (-16, -53),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LemmyKoopa', 'Lemmy_Koopa.png')


class ActorImage_BigShell(actorlib.ActorImage_StaticMultiple):  # 341
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (-149 / 1.5, -217 / 1.5)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BigShell', 'bigshell_green.png')
        actorlib.loadIfNotInImageCache('BigShellGrass', 'bigshell_green_grass.png')
        actorlib.loadIfNotInImageCache('BigShellInside', 'bigshell_inside.png')

    def dataChanged(self):
        style = self.parent.actordata[5] & 1

        if style == 0:
            self.image = ImageCache['BigShellGrass']
        else:
            self.image = ImageCache['BigShell']

        super().dataChanged()

    def paint(self, painter):
        if globals_.Layer0Shown and self.image is not None:
            painter.drawPixmap(0, 0, self.image.width(), self.image.height(), self.image)
        else:
            painter.drawPixmap(0, 0, 322, 248, ImageCache['BigShellInside'])


class ActorImage_Muncher(actorlib.ActorImage_StaticMultiple):  # 342
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Muncher', 'muncher.png')
        actorlib.loadIfNotInImageCache('MuncherF', 'muncher_frozen.png')

    def dataChanged(self):

        frozen = self.parent.actordata[5] & 1
        if frozen == 1:
            self.image = ImageCache['MuncherF']
            self.offset = (0, 0)
        else:
            self.image = ImageCache['Muncher']
            self.offset = (0, -1)

        super().dataChanged()


class ActorImage_Fuzzy(actorlib.ActorImage_StaticMultiple):  # 343
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Fuzzy', 'fuzzy.png')
        actorlib.loadIfNotInImageCache('FuzzyGiant', 'fuzzy_giant.png')

    def dataChanged(self):
        giant = self.parent.actordata[4] & 1

        self.image = ImageCache['FuzzyGiant'] if giant else ImageCache['Fuzzy']
        self.offset = (-18, -18) if giant else (-7, -7)

        super().dataChanged()


class ActorImage_MortonKoopa(actorlib.ActorImage_Static):  # 344
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MortonKoopa'],
            (-17, -34),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MortonKoopa', 'Morton_Koopa.png')


class ActorImage_ChainHolder(actorlib.ActorImage_Static):  # 345
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ChainHolder'],
            (0, -12)
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ChainHolder', 'chain_holder.png')


class ActorImage_HangingChainPlatform(actorlib.ActorImage_StaticMultiple):  # 346
    @staticmethod
    def loadImages():
        if 'HangingChainPlatform0' in ImageCache:
            return
        ImageCache['HangingChainPlatform0'] = actorlib.GetPixmap('hanging_chain_platform_small.png')
        ImageCache['HangingChainPlatform1'] = actorlib.GetPixmap('hanging_chain_platform_medium.png')
        ImageCache['HangingChainPlatform2'] = actorlib.GetPixmap('hanging_chain_platform_large.png')

    def dataChanged(self):
        size = (self.parent.actordata[4] & 3) % 3
        self.offset = (
            (-26, -12),
            (-42, -12),
            (-58, -12),
        )[size]
        self.image = ImageCache[f'HangingChainPlatform{size}']

        super().dataChanged()


class ActorImage_RoyKoopa(actorlib.ActorImage_Static):  # 347
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['RoyKoopa'],
            (-27, -24)
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RoyKoopa', 'Roy_Koopa.png')


class ActorImage_LudwigVonKoopa(actorlib.ActorImage_Static):  # 348
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['LudwigVonKoopa'],
            (-20, -30),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LudwigVonKoopa', 'Ludwig_Von_Koopa.png')


class ActorImage_MortonKoopaCastleBoss(actorlib.ActorImage):  # 349
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        mortonKoopaAuxImage = actorlib.AuxiliaryImage(parent, 552, 408)
        mortonKoopaAuxImage.image = ImageCache['MortonKoopaCastleBoss']
        mortonKoopaAuxImage.setPos(48, 0)
        self.aux.append(mortonKoopaAuxImage)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, 0, 288))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MortonKoopaCastleBoss', 'morton_castle_boss.png')


class ActorImage_RockyWrench(actorlib.ActorImage_Static):  # 352
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['RockyWrench'],
            (-2, -41),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RockyWrench', 'rocky_wrench.png')


class ActorImage_Pipe_MovingDown(ActorImage_Pipe):  # 353
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.direction = 'D'

    def dataChanged(self):
        self.length1 = (self.parent.actordata[5] >> 4) + 2
        self.length2 = (self.parent.actordata[5] & 0xF) + 2
        self.color = (
            'Green', 'Red', 'Yellow', 'Blue',
        )[self.parent.actordata[3] & 3]

        super().dataChanged()


class ActorImage_BrownTowerBlockTwoWayLine(ActorImage_BrownTowerBlock):  # 354
    pass



class ActorImage_RollingHillWith1Pipe(ActorImage_RollingHillWithPipe):  # 355
    pass


class ActorImage_BrownTowerBlockNormal(ActorImage_BrownTowerBlock):  # 356
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal))

    def dataChanged(self):
        super().dataChanged()
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        # now set up the track
        direction = self.parent.actordata[2] & 3
        distance = (self.parent.actordata[4] & 0xF0) >> 4

        if direction <= 1:  # horizontal
            self.aux[0].direction = 1
            self.aux[0].setSize(self.width + (distance * 16), self.height)
        else:  # vertical
            self.aux[0].direction = 2
            self.aux[0].setSize(self.width, self.height + (distance * 16))

        if (direction in (0, 3)) or (direction not in (1, 2)):  # right, down
            self.aux[0].setPos(0, 0)
        elif direction == 1:  # left
            self.aux[0].setPos(-distance * 24, 0)
        elif direction == 2:  # up
            self.aux[0].setPos(0, -distance * 24)


class ActorImage_Fruit(actorlib.ActorImage_StaticMultiple):  # 357
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Fruit', 'fruit.png')
        actorlib.loadIfNotInImageCache('FruitCookie', 'fruit_cookie.png')

    def dataChanged(self):

        style = self.parent.actordata[5] & 1
        if style == 0:
            self.image = ImageCache['Fruit']
        else:
            self.image = ImageCache['FruitCookie']

        super().dataChanged()


class ActorImage_LavaParticles(ActorImage_LiquidOrFog):  # 358
    @staticmethod
    def loadImages():
        if 'LavaParticlesA' in ImageCache:
            return
        ImageCache['LavaParticlesA'] = actorlib.GetPixmap('lava_particles_a.png')
        ImageCache['LavaParticlesB'] = actorlib.GetPixmap('lava_particles_b.png')
        ImageCache['LavaParticlesC'] = actorlib.GetPixmap('lava_particles_c.png')

    def dataChanged(self):
        type = (self.parent.actordata[5] & 0xF) % 3
        self.mid = (
            ImageCache['LavaParticlesA'],
            ImageCache['LavaParticlesB'],
            ImageCache['LavaParticlesC'],
        )[type]

        super().dataChanged()


class ActorImage_WallLantern(actorlib.ActorImage):  # 359
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        wallLanternAuxImage = actorlib.AuxiliaryImage(parent, 128, 128)
        wallLanternAuxImage.image = ImageCache['WallLanternAux']
        wallLanternAuxImage.setPos(-48, -48)
        wallLanternAuxImage.hover = False
        self.aux.append(wallLanternAuxImage)

        self.image = ImageCache['WallLantern']
        self.yOffset = 8

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('WallLantern', 'wall_lantern.png')
        actorlib.loadIfNotInImageCache('WallLanternAux', 'wall_lantern_aux.png')

    def paint(self, painter):
        if self.image is None:
            return

        painter.drawPixmap(0, 0, self.image)


class ActorImage_RollingHillWith8Pipes(ActorImage_RollingHillWithPipe):  # 360
    pass


class ActorImage_CrystalBlock(actorlib.ActorImage_StaticMultiple):  # 361
    @staticmethod
    def loadImages():
        if 'CrystalBlock0' in ImageCache:
            return
        for size in range(3):
            ImageCache[f'CrystalBlock{size}'] = actorlib.GetPixmap(f'crystal_block_{size}.png')

    def dataChanged(self):
        size = self.parent.actordata[4] & 3

        if size == 0:
            self.offset = (-7 / 1.5, -10 / 1.5)
        elif size == 1:
            self.offset = (-8, -8 / 1.5)
        else:
            self.offset = (-10 / 1.5, -11 / 1.5)
            size = 2

        self.image = ImageCache[f'CrystalBlock{size}']

        super().dataChanged()


class ActorImage_ColoredBox(actorlib.ActorImage):  # 362
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'CBox0TL' in ImageCache:
            return
        for color in range(4):
            for direction in ('TL', 'T', 'TR', 'L', 'M', 'R', 'BL', 'B', 'BR'):
                ImageCache[f'CBox{color}{direction}'] = actorlib.GetPixmap(f'cbox_{direction}_{color}.png')

    def dataChanged(self):
        self.color = (self.parent.actordata[3] >> 4) & 3

        size = self.parent.actordata[4]
        width = size >> 4
        height = size & 0xF

        self.width = (width + 3) * 16
        self.height = (height + 3) * 16

    def paint(self, painter):
        prefix = f'CBox{self.color}'
        xsize = int(self.width * 1.5)
        ysize = int(self.height * 1.5)

        painter.drawPixmap(0, 0, ImageCache[prefix + 'TL'])
        painter.drawPixmap(xsize - 25, 0, ImageCache[prefix + 'TR'])
        painter.drawPixmap(0, ysize - 25, ImageCache[prefix + 'BL'])
        painter.drawPixmap(xsize - 25, ysize - 25, ImageCache[prefix + 'BR'])

        painter.drawTiledPixmap(25, 0, xsize - 50, 25, ImageCache[prefix + 'T'])
        painter.drawTiledPixmap(25, ysize - 25, xsize - 50, 25, ImageCache[prefix + 'B'])
        painter.drawTiledPixmap(0, 25, 25, ysize - 50, ImageCache[prefix + 'L'])
        painter.drawTiledPixmap(xsize - 25, 25, 25, ysize - 50, ImageCache[prefix + 'R'])

        painter.drawTiledPixmap(25, 25, xsize - 50, ysize - 50, ImageCache[prefix + 'M'])


class ActorImage_RoyKoopaCastleBoss(actorlib.ActorImage):  # 364
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        royKoopaAuxImage = actorlib.AuxiliaryImage(parent, 528, 384)
        royKoopaAuxImage.image = ImageCache['RoyKoopaCastleBoss']
        royKoopaAuxImage.setPos(72, -96)
        self.aux.append(royKoopaAuxImage)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, 24, 312))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('RoyKoopaCastleBoss', 'roy_castle_boss.png')


class ActorImage_LudwigVonKoopaCastleBoss(actorlib.ActorImage):  # 365
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        ludwigVonKoopaAuxImage = actorlib.AuxiliaryImage(parent, 720, 840)
        ludwigVonKoopaAuxImage.image = ImageCache['LudwigVonKoopaCastleBoss']
        ludwigVonKoopaAuxImage.setPos(-24, -360)
        self.aux.append(ludwigVonKoopaAuxImage)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, 24, 288))
        rect2AuxImage = actorlib.AuxiliaryRectOutline(parent, 528, 24, 72, 264)
        rect2AuxImage.fillFlag = False
        self.aux.append(rect2AuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LudwigVonKoopaCastleBoss', 'ludwig_castle_boss.png')


class ActorImage_CubeKinokoRot(actorlib.ActorImage_StaticMultiple):  # 366
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CubeKinokoG', 'cube_kinoko_g.png')
        actorlib.loadIfNotInImageCache('CubeKinokoR', 'cube_kinoko_r.png')

    def dataChanged(self):

        style = self.parent.actordata[4] & 1
        if style == 0:
            self.image = ImageCache['CubeKinokoR']
        else:
            self.image = ImageCache['CubeKinokoG']

        super().dataChanged()


class ActorImage_CubeKinokoLine(actorlib.ActorImage_Static):  # 367
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CubeKinokoP'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CubeKinokoP', 'cube_kinoko_p.png')


class ActorImage_FlashRaft(actorlib.ActorImage_StaticMultiple):  # 368
    def __init__(self, parent):
        super().__init__( parent, 1.5, )

        self.dimensions = (-5 / 1.5, 0, 322 / 1.5, 36)

        flashRaftAuxImage = actorlib.AuxiliaryImage(parent, 344, 87)
        flashRaftAuxImage.image = ImageCache['FlashlightRaft']
        flashRaftAuxImage.setPos(-11, -28)
        self.aux.append(flashRaftAuxImage)
        flashRaftLampAuxImage = actorlib.AuxiliaryImage(parent, 132, 120)
        flashRaftLampAuxImage.image = ImageCache['FlashlightLamp']
        flashRaftLampAuxImage.setPos(-33, -120)
        self.aux.append(flashRaftLampAuxImage)

        pathNodeAuxRect = actorlib.AuxiliaryRectOutline(parent, 24, 24, 144, 30)
        pathNodeAuxRect.setIsBehindActor(False)
        self.aux.append(pathNodeAuxRect)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('FlashlightRaft', 'flashraft.png')
        actorlib.loadIfNotInImageCache('FlashlightLamp', 'flashraft_light.png')

    def dataChanged(self):
        if (
            not isinstance(self.aux[0], actorlib.AuxiliaryImage)
            or not isinstance(self.aux[1], actorlib.AuxiliaryImage)
            or not isinstance(self.aux[2], actorlib.AuxiliaryRectOutline)
        ):
            return

        pathcontrolled = self.parent.actordata[5] & 1
        midway = (self.parent.actordata[5] >> 4) & 1

        self.aux[2].setSize(24, 24, 161, 24) if pathcontrolled else self.aux[2].setSize(0, 0)

        if midway:
            self.aux[0].alpha = 0.5
            self.aux[1].alpha = 0.5
        else:
            self.aux[0].alpha = 1
            self.aux[1].alpha = 1


class ActorImage_SlidingPenguin(actorlib.ActorImage_StaticMultiple):  # 369
    @staticmethod
    def loadImages():
        if 'PenguinL' in ImageCache:
            return
        penguin = actorlib.GetImage('sliding_penguin.png')
        if penguin is None:
            return

        ImageCache['PenguinL'] = QtGui.QPixmap.fromImage(penguin)
        ImageCache['PenguinR'] = QtGui.QPixmap.fromImage(penguin.mirrored(True, False))

    def dataChanged(self):

        direction = self.parent.actordata[5] & 1
        if direction == 0:
            self.image = ImageCache['PenguinL']
        else:
            self.image = ImageCache['PenguinR']

        super().dataChanged()


class ActorImage_CloudBlock(actorlib.ActorImage_Static):  # 370
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CloudBlock'],
            (-4, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CloudBlock', 'cloud_block.png')


class ActorImage_RollingHillCoin(ActorImage_SpecialCoin):  # 371
    pass


class ActorImage_IggyKoopaCastleBoss(actorlib.ActorImage):  # 372
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)
        iggyKoopaAuxImage = actorlib.AuxiliaryImage(parent, 240, 288)
        iggyKoopaAuxImage.image = ImageCache['IggyKoopaCastleBoss']
        iggyKoopaAuxImage.setSize(240, 288, 360, 48)
        self.aux.append(iggyKoopaAuxImage)

        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, 24, 312))

        arenaOutline = actorlib.AuxiliaryRectOutline(parent, 528, 264, 72, 24)
        arenaOutline.fillFlag = False
        self.aux.append(arenaOutline)

        w = actorlib.OutlinePen.widthF() if actorlib.OutlinePen else 1
        centerPlatformOutline = actorlib.AuxiliaryRectOutline(parent, 336 + w, 24 + w, int(168 - w / 2), int(144 - w / 2))
        centerPlatformOutline.fillFlag = False
        self.aux.append(centerPlatformOutline)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('IggyKoopaCastleBoss', 'iggy_castle_boss.png')


class ActorImage_RaftWater(ActorImage_LiquidOrFog):  # 373
    def __init__(self, parent):
        super().__init__(parent)

        self.crest = ImageCache['RaftWaterCrest']
        self.mid = ImageCache['RaftWater']

        self.top = self.parent.objy
        self.drawCrest = True

    @staticmethod
    def loadImages():
        if 'RaftWaterCrest' in ImageCache:
            return
        ImageCache['RaftWater'] = actorlib.GetPixmap('liquid_water.png')
        ImageCache['RaftWaterCrest'] = actorlib.GetPixmap('liquid_water_crest.png')

    def positionChanged(self):
        self.top = self.parent.objy
        super().positionChanged()


class ActorImage_SnowWind(ActorImage_LiquidOrFog):  # 374
    def __init__(self, parent):
        super().__init__(parent)
        self.mid = ImageCache['SnowEffect']

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SnowEffect', 'snow.png')

    def paintZone(self):
        # For now, we only paint snow
        return self.parent.actordata[5] == 0 and self.zoneId != -1


class ActorImage_WendyKoopaCastleBoss(actorlib.ActorImage):  # 375
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        wendyKoopaAuxImage = actorlib.AuxiliaryImage(parent, 648, 528)
        wendyKoopaAuxImage.image = ImageCache['WendyKoopaCastleBoss']
        wendyKoopaAuxImage.setPos(0, -120)
        self.aux.append(wendyKoopaAuxImage)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, 0, 288))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('WendyKoopaCastleBoss', 'wendy_castle_boss.png')


class ActorImage_MovingFence(actorlib.ActorImage):  # 376
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.actorbox.shown = False
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal))

    @staticmethod
    def loadImages():
        if 'MovingFence0' in ImageCache:
            return
        for shape in range(4):
            ImageCache[f'MovingFence{shape}'] = actorlib.GetPixmap(f'moving_fence_{shape}.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        self.shape = (self.parent.actordata[4] >> 4) & 3
        direction = self.parent.actordata[5] & 1
        distance = (self.parent.actordata[5] & 0xF0) >> 4

        self.size = (
            (64, 64),
            (64, 128),
            (64, 224),
            (192, 64)
        )[self.shape]

        self.xOffset = -self.size[0] / 2
        self.yOffset = -self.size[1] / 2

        if distance == 0:
            self.aux[0].setSize(0, 0)
        elif direction == 1: # horizontal
            self.aux[0].direction = 1
            self.aux[0].setSize((distance * 32) + self.width, 16)
            self.aux[0].setPos(-distance * 24, (self.height * 0.75) - 12)
        else: # vertical
            self.aux[0].direction = 2
            self.aux[0].setSize(16, (distance * 32) + self.height)
            self.aux[0].setPos((self.width * 0.75) - 12, -distance * 24)

    def paint(self, painter):
        painter.drawPixmap(0, 0, ImageCache[f'MovingFence{self.shape}'])


class ActorImage_Pipe_Up(ActorImage_PipeStationary):  # 377
    def dataChanged(self):
        self.length = (self.parent.actordata[5] & 0xF) + 2
        super().dataChanged()


class ActorImage_Pipe_Down(ActorImage_PipeStationary):  # 378
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.direction = 'D'

    def dataChanged(self):
        self.length = (self.parent.actordata[5] & 0xF) + 2
        super().dataChanged()


class ActorImage_Pipe_Right(ActorImage_PipeStationary):  # 379
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.direction = 'R'

    def dataChanged(self):
        self.length = (self.parent.actordata[5] & 0xF) + 2
        super().dataChanged()


class ActorImage_Pipe_Left(ActorImage_PipeStationary):  # 380
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.direction = 'L'

    def dataChanged(self):
        self.length = (self.parent.actordata[5] & 0xF) + 2
        super().dataChanged()


class ActorImage_LemmyKoopaCastleBoss(actorlib.ActorImage):  # 381
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        lemmyKoopaAuxImage = actorlib.AuxiliaryImage(parent, 552, 216)
        lemmyKoopaAuxImage.image = ImageCache['LemmyKoopaCastleBoss']
        lemmyKoopaAuxImage.setPos(48, 168)
        self.aux.append(lemmyKoopaAuxImage)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, 0, 312))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LemmyKoopaCastleBoss', 'lemmy_castle_boss.png')


class ActorImage_ScrewMushroomNoBolt(ActorImage_ScrewMushroom):  # 382
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.hasBolt = False


class ActorImage_KamekController(actorlib.ActorImage):  # 383
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)
        kamekAuxImage = actorlib.AuxiliaryImage(parent, 1272, 360)
        kamekAuxImage.image = ImageCache['KamekController']
        kamekAuxImage.setPos(-144, 48)
        self.aux.append(kamekAuxImage)
        arenaOutline = actorlib.AuxiliaryRectOutline(parent, 1154, 360, 0, 48)
        arenaOutline.fillFlag = False
        self.aux.append(arenaOutline)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('KamekController', 'boss_controller_kamek.png')


class ActorImage_PipeCooliganGenerator(actorlib.ActorImage):  # 384
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.size = (16, 32)
        self.actorbox.yOffset = -16


class ActorImage_IceBlock(actorlib.ActorImage_StaticMultiple):  # 385
    @staticmethod
    def loadImages():
        if 'IceBlock00' in ImageCache:
            return
        for i in range(4):
            for j in range(4):
                ImageCache[f'IceBlock{i}{j}'] = actorlib.GetPixmap(f'iceblock{i}{j}.png')

    def dataChanged(self):

        size = self.parent.actordata[5]
        height = (size & 0x30) >> 4
        width = size & 3

        self.image = ImageCache[f'IceBlock{width}{height}']
        self.xOffset = width * -4
        self.yOffset = height * -8

        super().dataChanged()


class ActorImage_PowBlock(actorlib.ActorImage_Static):  # 386
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['POW']
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('POW', 'pow.png')


class ActorImage_Bush(actorlib.ActorImage_StaticMultiple):  # 387
    def __init__(self, parent):
        # this actor image should actually show behind layer 1...
        super().__init__(parent, 1.5)
        self.parent.setZValue(24999)

    @staticmethod
    def loadImages():
        if 'Bush00' in ImageCache:
            return
        for typenum, typestr in enumerate(('green', 'yellowish')):
            for sizenum, sizestr in enumerate(('small', 'med', 'large', 'xlarge')):
                ImageCache[f'Bush{typenum}{sizenum}'] = actorlib.GetPixmap(f'bush_{typestr}_{sizestr}.png')

    def dataChanged(self):

        props = self.parent.actordata[5]
        style = (props >> 4) & 1
        size = props & 3

        self.offset = (
            (-22, -25),
            (-30, -44),
            (-40, -60),
            (-53, -78),
        )[size]

        self.image = ImageCache[f'Bush{style}{size}']

        super().dataChanged()


class ActorImage_Barrel(actorlib.ActorImage_Static):  # 388
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Barrel'],
            (-4, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Barrel', 'barrel.png')


class ActorImage_StarCoinBoltControlled(ActorImage_StarCoin):  # 389
    pass


class ActorImage_BoltControlledCoin(ActorImage_SpecialCoin):  # 390
    pass


class ActorImage_GlowBlock(actorlib.ActorImage):  # 391
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        glowBlockAuxImage = actorlib.AuxiliaryImage(parent, 46, 46)
        glowBlockAuxImage.image = ImageCache['GlowBlock']
        glowBlockAuxImage.setPos(-11, -11)
        self.aux.append(glowBlockAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GlowBlock', 'glow_block.png')


class ActorImage_PropellerBlock(actorlib.ActorImage_Static):  # 393
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PropellerBlock'],
            (-3, -6),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PropellerBlock', 'propeller_block.png')


class ActorImage_LemmyBall(actorlib.ActorImage_Static):  # 394
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['LemmyBall'],
            (-6, 0),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LemmyBall', 'lemmyball.png')


class ActorImage_SpinyCheep(actorlib.ActorImage_StaticMultiple):  # 395
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.yOffset = -8 / 1.5

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpinyCheep', 'cheep_spiny.png')
        actorlib.loadIfNotInImageCache('SpinyCheepRight', 'cheep_spiny_right.png')

    def dataChanged(self):
        super().dataChanged()
        # It can face right if set to chase players, but not when forced to face left
        chasePly = self.parent.actordata[5] & 0xF
        forceLeft = (self.parent.actordata[2] >> 4) & 8

        if chasePly and not forceLeft:
            self.image = ImageCache['SpinyCheepRight']
            self.xOffset = -2
        else:
            self.image = ImageCache['SpinyCheep']
            self.xOffset = -2 / 1.5


class ActorImage_MoveWhenOn(actorlib.ActorImage):  # 396
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'MoveWhenOnL' in ImageCache:
            return
        ImageCache['MoveWhenOnL'] = actorlib.GetPixmap('mwo_left.png')
        ImageCache['MoveWhenOnM'] = actorlib.GetPixmap('mwo_middle.png')
        ImageCache['MoveWhenOnR'] = actorlib.GetPixmap('mwo_right.png')
        ImageCache['MoveWhenOnC'] = actorlib.GetPixmap('mwo_circle.png')
        ImageCache['MoveWhenOnCEmpty'] = actorlib.GetPixmap('mwo_circle_empty.png')

    def dataChanged(self):
        # get width
        self.raw_size = self.parent.actordata[5] & 0xF
        if self.raw_size == 0:
            self.xOffset = -16
            self.width = 32
        elif self.raw_size == 1:
            self.width = 16
        else:
            self.xOffset = -2 / 1.5
            self.width = self.raw_size * 16 + 4

        self.height = 28 / 1.5
        self.yOffset = -2 / 1.5

    def paint(self, painter):
        if self.raw_size == 0:
            # hack for the glitchy version
            painter.drawPixmap(0, 2, ImageCache['MoveWhenOnR'])
            painter.drawPixmap(24, 2, ImageCache['MoveWhenOnL'])
        elif self.raw_size == 1:
            painter.drawPixmap(0, 2, ImageCache['MoveWhenOnM'])
        else:
            painter.drawPixmap(0, 2, ImageCache['MoveWhenOnL'])
            if self.raw_size > 2:
                painter.drawTiledPixmap(26, 2, (self.raw_size - 2) * 24, 24, ImageCache['MoveWhenOnM'])
            painter.drawPixmap(int((self.width * 1.5) - 28), 2, ImageCache['MoveWhenOnR'])

        center = int((self.width / 2) * 1.5)
        painter.drawPixmap(center - 15, 0, ImageCache['MoveWhenOnCEmpty'])


class ActorImage_GhostHouseBox(actorlib.ActorImage):  # 397
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'GHBoxTL' in ImageCache:
            return
        for direction in ('TL', 'T', 'TR', 'L', 'M', 'R', 'BL', 'B', 'BR'):
            ImageCache[f'GHBox{direction}'] = actorlib.GetPixmap(f'ghbox_{direction}.png')

    def dataChanged(self):
        height = self.parent.actordata[4] >> 4
        width = self.parent.actordata[5] & 15

        self.width = (width + 2) * 16
        self.height = (height + 2) * 16

    def paint(self, painter):
        prefix = 'GHBox'
        xsize = int(self.width * 1.5)
        ysize = int(self.height * 1.5)

        # Corners
        painter.drawPixmap(0, 0, ImageCache[prefix + 'TL'])
        painter.drawPixmap(xsize - 24, 0, ImageCache[prefix + 'TR'])
        painter.drawPixmap(0, ysize - 24, ImageCache[prefix + 'BL'])
        painter.drawPixmap(xsize - 24, ysize - 24, ImageCache[prefix + 'BR'])

        # Edges
        painter.drawTiledPixmap(24, 0, xsize - 48, 24, ImageCache[prefix + 'T'])
        painter.drawTiledPixmap(24, ysize - 24, xsize - 48, 24, ImageCache[prefix + 'B'])
        painter.drawTiledPixmap(0, 24, 24, ysize - 48, ImageCache[prefix + 'L'])
        painter.drawTiledPixmap(xsize - 24, 24, 24, ysize - 48, ImageCache[prefix + 'R'])

        # Middle
        painter.drawTiledPixmap(24, 24, xsize - 48, ysize - 48, ImageCache[prefix + 'M'])


class ActorImage_LongSkewerRight(ActorImage_LongSkewer):  # 398
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.dir = 'right'
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 1296, 16, actorlib.AuxiliaryTrackObject.Horizontal))
        self.aux.append(actorlib.AuxiliaryImage(parent, 2021, 99))

        self.dimensions = (-112, 0, 128, 66) # 6 mid sections + end section


class ActorImage_LongSkewerLeft(ActorImage_LongSkewer):  # 400
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.dir = 'left'
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 1296, 16, actorlib.AuxiliaryTrackObject.Horizontal))
        self.aux.append(actorlib.AuxiliaryImage(parent, 2021, 99))

        self.dimensions = (0, 0, 128, 66)


class ActorImage_MassiveSkewerDown(ActorImage_MassiveSkewer):  # 401
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.dir = 'down'
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 80, actorlib.AuxiliaryTrackObject.Vertical))
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 240, 2664, 4, 2944))
        self.aux.append(actorlib.AuxiliaryImage(parent, 248, 3016))

class ActorImage_LineQBlock(ActorImage_Block):  # 402
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49
        self.twelveIsMushroom = True


class ActorImage_LineBrickBlock(ActorImage_Block):  # 403
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48


class ActorImage_MassiveSkewerUp(ActorImage_MassiveSkewer):  # 404
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.dir = 'up'
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 80, actorlib.AuxiliaryTrackObject.Vertical))
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 240, 2664, 4, -2592))
        self.aux.append(actorlib.AuxiliaryImage(parent, 248, 3016))


class ActorImage_BowserJr2ndController(actorlib.ActorImage):  # 405
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        bowserJr2ndAuxImage = actorlib.AuxiliaryImage(parent, 672, 384)
        bowserJr2ndAuxImage.image = ImageCache['BowserJr2ndController']
        bowserJr2ndAuxImage.setPos(-504, -336)
        self.aux.append(bowserJr2ndAuxImage)

        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, -504, -312))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BowserJr2ndController', 'boss_controller_bowserjr_2.png')


class ActorImage_BowserJr3rdController(actorlib.ActorImage):  # 406
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        bowserJr3rdAuxImage = actorlib.AuxiliaryImage(parent, 672, 372)
        bowserJr3rdAuxImage.image = ImageCache['BowserJr3rdController']
        bowserJr3rdAuxImage.setPos(-324, -192)
        self.aux.append(bowserJr3rdAuxImage)

        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24, -324, -192))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BowserJr3rdController', 'boss_controller_bowserjr_3.png')


class ActorImage_BossControllerCastleBoss(actorlib.ActorImage):  # 407
    def __init__(self, parent):
        super().__init__(parent)

        self.parent.setZValue(24999)

        shutterDoor1AuxImage = actorlib.AuxiliaryImage(parent, 48, 96)
        shutterDoor1AuxImage.image = ImageCache['ShutterDoor']
        shutterDoor2AuxImage = actorlib.AuxiliaryImage(parent, 48, 96)
        shutterDoor2AuxImage.image = ImageCache['ShutterDoor']
        shutterDoor2AuxImage.alpha = 0.375
        shutterDoor3AuxImage = actorlib.AuxiliaryImage(parent, 48, 96)
        shutterDoor3AuxImage.image = ImageCache['ShutterDoor']
        shutterDoor4AuxImage = actorlib.AuxiliaryImage(parent, 48, 96)
        shutterDoor4AuxImage.image = ImageCache['ShutterDoor']
        shutterDoor4AuxImage.alpha = 0.375

        self.aux.append(shutterDoor1AuxImage)
        self.aux.append(shutterDoor2AuxImage)
        self.aux.append(shutterDoor3AuxImage)
        self.aux.append(shutterDoor4AuxImage)

    def dataChanged(self):
        if (
            not isinstance(self.aux[0], actorlib.AuxiliaryImage)
            or not isinstance(self.aux[1], actorlib.AuxiliaryImage)
            or not isinstance(self.aux[2], actorlib.AuxiliaryImage)
            or not isinstance(self.aux[3], actorlib.AuxiliaryImage)
        ):
            return
        boss = (self.parent.actordata[5] & 0xF) % 7

        self.aux[0].setPos(*(
                (0, -216),
                (0, -216),
                (0, -216),
                (0, -216),
                (0, -216),
                (0, -240),
                (0, -216)
        )[boss])
        self.aux[1].setPos(self.aux[0].x(), self.aux[0].y() + 96)
        self.aux[2].setPos(*(
                (576, -120),
                (576, -120),
                (600, -120),
                (576, -120),
                (576, -120),
                (600, -120),
                (576, -487)
            )[boss])
        self.aux[3].setPos(self.aux[2].x(), self.aux[2].y() - 96)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ShutterDoor', 'shutter_door.png')


class ActorImage_ToadHouseBalloonUnused(ActorImage_ToadHouseBalloon):  # 411
    def dataChanged(self):
        super().dataChanged()
        if self.image is None:
            return

        self.livesNum = (self.parent.actordata[4] >> 4) & 3

        self.yOffset = 8 - (self.image.height() / 3)


class ActorImage_ToadHouseBalloonUsed(ActorImage_ToadHouseBalloon):  # 412
    def dataChanged(self):
        self.livesNum = (self.parent.actordata[4] >> 4) & 3
        self.hasHandle = not ((self.parent.actordata[5] >> 4) & 1)
        shiftPos = self.parent.actordata[3] & 1
        posAdj = 8 if shiftPos else 0

        super().dataChanged()

        self.xOffset = -13 + posAdj
        if self.hasHandle:
            self.yOffset = 12 - posAdj
        elif self.image is not None:
            self.yOffset = 16 - (self.image.height() / 3) - posAdj


class ActorImage_WendyRing(actorlib.ActorImage_Static):  # 413
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['WendyRing'],
            (-4, 4),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('WendyRing', 'wendy_ring.png')


class ActorImage_Gabon(actorlib.ActorImage_StaticMultiple):  # 414
    @staticmethod
    def loadImages():
        if 'GabonLeft' in ImageCache:
            return
        gabon = actorlib.GetImage('gabon.png')
        if gabon is None:
            return

        ImageCache['GabonLeft'] = QtGui.QPixmap.fromImage(gabon)
        ImageCache['GabonRight'] = QtGui.QPixmap.fromImage(gabon.mirrored(True, False))
        actorlib.loadIfNotInImageCache('GabonSpike', 'gabon_spike.png')

    def dataChanged(self):
        throwdir = self.parent.actordata[5] & 1
        facing = self.parent.actordata[4] & 1

        if throwdir == 0:
            self.image = ImageCache['GabonSpike']
            self.offset = (-7, -31) #-11, -47
        else:
            self.image = (
                ImageCache['GabonLeft'],
                ImageCache['GabonRight'],
            )[facing]
            self.offset = (-8, -33) #-12, -50

        super().dataChanged()


class ActorImage_BetaLarryKoopa(actorlib.ActorImage_Static):  # 415
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['LarryKoopaBeta'],
            (-13, -22.5),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LarryKoopaBeta', 'Larry_Koopa_Unused.png')


class ActorImage_InvisibleOneUp(actorlib.ActorImage_Static):  # 416
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['InvisibleOneUp'],
            (3, 5),
        )
        self.alpha = 0.65

    @staticmethod
    def loadImages():
        if 'InvisibleOneUp' in ImageCache:
            return
        ImageCache['InvisibleOneUp'] = ImageCache['BlockContents11'].scaled(16, 16)


class ActorImage_SpinjumpCoin(actorlib.ActorImage_Static):  # 417
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SpecialCoin'],
        )
        self.alpha = 0.55


class ActorImage_BanzaiGen(actorlib.ActorImage_Static):  # 418
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['BanzaiGen'],
            (-56 / 1.5, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BanzaiGen', 'banzai_bill_gen.png')


class ActorImage_Bowser(actorlib.ActorImage_Static):  # 419
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Bowser'],
            (-35, -70),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Bowser', 'bowser.png')


class ActorImage_GiantGlowBlock(actorlib.ActorImage):  # 420
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        self.aux.append(actorlib.AuxiliaryImage(parent, 100, 100))
        self.size = (32, 32)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GiantGlowBlockOn', 'giant_glow_block.png')
        actorlib.loadIfNotInImageCache('GiantGlowBlockOff', 'giant_glow_block_off.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        type = self.parent.actordata[4] >> 4
        if type == 0:
            self.aux[0].image = ImageCache['GiantGlowBlockOn']
            self.aux[0].setSize(100, 100, -23, -23)
        else:
            self.aux[0].image = ImageCache['GiantGlowBlockOff']
            self.aux[0].setSize(48, 48)


class ActorImage_UnusedGhostDoor(actorlib.ActorImage_Static):  # 421
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['GhostDoorU'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GhostDoorU', 'ghost_door.png')


class ActorImage_ToadQBlock(ActorImage_Block):  # 422
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49
        self.contentsOverride = 16


class ActorImage_ToadBrickBlock(ActorImage_Block):  # 423
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 48
        self.contentsOverride = 16


class ActorImage_PalmTree(actorlib.ActorImage_StaticMultiple):  # 424
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.xOffset = -24

    @staticmethod
    def loadImages():
        if 'PalmTree0' in ImageCache:
            return
        for i in range(8):
            ImageCache[f'PalmTree{i}'] = actorlib.GetPixmap(f'palmtree_{i}.png')

    def dataChanged(self):

        size = self.parent.actordata[5] & 7
        self.image = ImageCache[f'PalmTree{size}']
        self.yOffset = 16 - (self.image.height() / 1.5)

        super().dataChanged()


class ActorImage_Jellybeam(actorlib.ActorImage_Static):  # 425
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Jellybeam'],
            (-13 / 1.5, -11 / 1.5),
        )

        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Vertical))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Jellybeam', 'jellybeam.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        distance = self.parent.actordata[5] & 3
        self.aux[0].setSize(16, (distance * 32) + 118)
        self.aux[0].setPos(self.width * 0.75 - 12, self.height * 0.75 - 16)

        super().dataChanged()


class ActorImage_Kamek(actorlib.ActorImage_Static):  # 427
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Kamek'],
            (-19, -15),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Kamek', 'kamek.png')


class ActorImage_MGPanel(actorlib.ActorImage_Static):  # 428
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MGPanel'],
            (-4, -8),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MGPanel', 'minigame_flip_panel.png')


class ActorImage_BowserController(actorlib.ActorImage):  # 431
    def __init__(self, parent):
        super().__init__(parent)

        bowserShutterDoor1AuxImage = actorlib.AuxiliaryImage(parent, 48, 144)
        bowserShutterDoor1AuxImage.image = ImageCache['BowserShutterDoor']
        bowserShutterDoor1AuxImage.setPos(1250, -288)
        self.aux.append(bowserShutterDoor1AuxImage)

        bowserShutterDoor2AuxImage = actorlib.AuxiliaryImage(parent, 48, 144)
        bowserShutterDoor2AuxImage.image = ImageCache['BowserShutterDoor']
        bowserShutterDoor2AuxImage.setPos(1250, -144)
        bowserShutterDoor2AuxImage.alpha = 0.5
        self.aux.append(bowserShutterDoor2AuxImage)


        arenaOutline = actorlib.AuxiliaryRectOutline(parent, 768, 408, 1248, -336)
        arenaOutline.fillFlag = False
        self.aux.append(arenaOutline)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BowserShutterDoor', 'bowser_shutter_door.png')


class ActorImage_Toad(actorlib.ActorImage_Static):  # 432
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Toad'],
            (8, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Toad', 'toad.png')


class ActorImage_FloatingQBlock(ActorImage_Block):  # 433
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.tilenum = 49
        self.is_water_block = True

        self.contentsNybble = 5
        self.twelveIsMushroom = True


class ActorImage_WarpCannon(actorlib.ActorImage_StaticMultiple):  # 434
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.offset = (5, -25)

    @staticmethod
    def loadImages():
        if 'Warp0' in ImageCache:
            return
        ImageCache['Warp0'] = actorlib.GetPixmap('warp_w5.png')
        ImageCache['Warp1'] = actorlib.GetPixmap('warp_w6.png')
        ImageCache['Warp2'] = actorlib.GetPixmap('warp_w8.png')

    def dataChanged(self):

        dest = self.parent.actordata[5] & 3
        if dest == 3:
            dest = 0
        self.image = ImageCache[f'Warp{dest}']

        super().dataChanged()


class ActorImage_GhostFog(ActorImage_LiquidOrFog):  # 435
    def __init__(self, parent):
        super().__init__(parent)
        self.mid = ImageCache['GhostFog']
        self.top = self.parent.objy

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('GhostFog', 'fog_ghost.png')

    def dataChanged(self):
        self.locId = self.parent.actordata[5] & 0x7F
        super().dataChanged()

    def positionChanged(self):
        # This actor's cutoff works a bit differently. The effect is always
        # fixed to the top of the zone, but only the part below the actor image
        # is rendered.
        # BUG: This is not recreated.
        self.top = self.parent.objy
        super().positionChanged()


class ActorImage_PurplePole(actorlib.ActorImage):  # 437
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'VertPole' in ImageCache:
            return
        ImageCache['VertPoleTop'] = actorlib.GetPixmap('purple_pole_top.png')
        ImageCache['VertPole'] = actorlib.GetPixmap('purple_pole_middle.png')
        ImageCache['VertPoleBottom'] = actorlib.GetPixmap('purple_pole_bottom.png')

    def dataChanged(self):
        length = self.parent.actordata[5]
        self.height = (length + 3) * 16

    def paint(self, painter):
        painter.drawPixmap(0, 0, ImageCache['VertPoleTop'])
        painter.drawTiledPixmap(0, 24, 24, int(self.height * 1.5 - 48), ImageCache['VertPole'])
        painter.drawPixmap(0, int(self.height * 1.5 - 24), ImageCache['VertPoleBottom'])


class ActorImage_ShapeBlocks(actorlib.ActorImage_StaticMultiple):  # 438
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)
        self.actorbox.shown = True

        self.aux.append(actorlib.AuxiliaryImage(parent, 360, 360))

    @staticmethod
    def loadImages():
        if 'ShapeBlock0' in ImageCache:
            return

        for i in range(5):
            ImageCache[f'ShapeBlock{i}'] = actorlib.GetPixmap(f'shape_block_{i}.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        type = (self.parent.actordata[4] & 15) % 5

        offsets = (
            (-112, -112),
            (-112, -112),
            (-97, -81),
            (-80, -96),
            (-112, -112),
        )
        sizes = (
            (360, 360),
            (360, 360),
            (312, 264),
            (264, 312),
            (360, 360),
        )

        self.aux[0].image = ImageCache[f'ShapeBlock{type}']
        self.aux[0].setSize(sizes[type][0], sizes[type][1], offsets[type][0] * 1.5, offsets[type][1] * 1.5)

        super().dataChanged()


class ActorImage_CagePeachFake(actorlib.ActorImage_Static):  # 439
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CagePeachFake'],
            (-18, -106),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CagePeachFake', 'cage_peach_fake.png')


class ActorImage_HorizontalRope(actorlib.ActorImage):  # 440
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('HorzRope', 'horizontal_rope_middle.png')
        actorlib.loadIfNotInImageCache('HorzRopeEnd', 'horizontal_rope_end.png')

    def dataChanged(self):
        length = self.parent.actordata[5]
        self.width = (length + 3) * 16

    def paint(self, painter):
        endpiece = ImageCache['HorzRopeEnd']
        painter.drawPixmap(0, 0, endpiece)
        painter.drawTiledPixmap(24, 0, int(self.width * 1.5 - 48), 24, ImageCache['HorzRope'])
        painter.drawPixmap(int(self.width * 1.5 - 24), 0, endpiece)


class ActorImage_MushroomPlatform(actorlib.ActorImage):  # 441
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'RedShroomL' in ImageCache:
            return
        ImageCache['RedShroomL'] = actorlib.GetPixmap('red_mushroom_left.png')
        ImageCache['RedShroomM'] = actorlib.GetPixmap('red_mushroom_middle.png')
        ImageCache['RedShroomR'] = actorlib.GetPixmap('red_mushroom_right.png')
        ImageCache['GreenShroomL'] = actorlib.GetPixmap('green_mushroom_left.png')
        ImageCache['GreenShroomM'] = actorlib.GetPixmap('green_mushroom_middle.png')
        ImageCache['GreenShroomR'] = actorlib.GetPixmap('green_mushroom_right.png')
        ImageCache['BlueShroomL'] = actorlib.GetPixmap('blue_mushroom_left.png')
        ImageCache['BlueShroomM'] = actorlib.GetPixmap('blue_mushroom_middle.png')
        ImageCache['BlueShroomR'] = actorlib.GetPixmap('blue_mushroom_right.png')
        ImageCache['OrangeShroomL'] = actorlib.GetPixmap('orange_mushroom_left.png')
        ImageCache['OrangeShroomM'] = actorlib.GetPixmap('orange_mushroom_middle.png')
        ImageCache['OrangeShroomR'] = actorlib.GetPixmap('orange_mushroom_right.png')

    def dataChanged(self):
        # get size/color
        self.color = self.parent.actordata[4] & 1
        self.shroomsize = (self.parent.actordata[5] >> 4) & 1
        self.height = 16 * (self.shroomsize + 1)

        # get width
        width = self.parent.actordata[5] & 0xF
        if self.shroomsize == 0:
            self.width = (width << 4) + 32
            self.offset = (
                0 - (((width + 1) // 2) << 4),
                0,
            )
        else:
            self.width = (width << 5) + 64
            self.offset = (
                16 - (self.width / 2),
                -16,
            )

    def paint(self, painter):
        tilesize = 24 + (self.shroomsize * 24)
        if self.shroomsize == 0:
            if self.color == 0:
                color = 'Orange'
            else:
                color = 'Blue'
        else:
            if self.color == 0:
                color = 'Red'
            else:
                color = 'Green'

        painter.drawPixmap(0, 0, ImageCache[color + 'ShroomL'])
        painter.drawTiledPixmap(tilesize, 0, int((self.width * 1.5) - (tilesize * 2)), tilesize,
                                ImageCache[color + 'ShroomM'])
        painter.drawPixmap(int(self.width * 1.5) - tilesize, 0, ImageCache[color + 'ShroomR'])


class ActorImage_ReplayBlock(actorlib.ActorImage_Static):  # 443
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ReplayBlock'],
            (-8, -16),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ReplayBlock', 'replay_block.png')


class ActorImage_PreSwingingVine(actorlib.ActorImage_Static):  # 444
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PreSwingVine'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PreSwingVine', 'swing_vine.png')


class ActorImage_CagePeachReal(actorlib.ActorImage_Static):  # 445
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['CagePeachReal'],
            (-18, -106),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('CagePeachReal', 'cage_peach_real.png')


class ActorImage_UnderwaterLamp(actorlib.ActorImage):  # 447
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

        underwaterLampAuxImage = actorlib.AuxiliaryImage(parent, 105, 105)
        underwaterLampAuxImage.image = ImageCache['UnderwaterLamp']
        underwaterLampAuxImage.setPos(-34, -34)
        self.aux.append(underwaterLampAuxImage)

        self.dimensions = (-4, -4, 24, 26)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('UnderwaterLamp', 'underwater_lamp.png')


class ActorImage_MetalBar(actorlib.ActorImage_Static):  # 448
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MetalBar'],
            (0, -32),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MetalBar', 'metal_bar.png')


class ActorImage_Pipe_EnterableUp(ActorImage_PipeStationary):  # 450
    def dataChanged(self):
        self.length = (self.parent.actordata[5] & 0xF) + 2
        super().dataChanged()


class ActorImage_ScaredyRatDespawner(actorlib.ActorImage_Static):  # 451
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['ScaredyRatDespawner'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('ScaredyRatDespawner', 'scaredy_rat_despawner.png')


class ActorImage_BowserDoor(actorlib.ActorImage_Static):  # 452
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['BowserDoor'],
            (-53, -130),
        )
        arenaOutline = actorlib.AuxiliaryRectOutline(parent, 24, 24)
        arenaOutline.setIsBehindActor(False)
        arenaOutline.setPos(91, 243)
        self.aux.append(arenaOutline)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BowserDoor', 'bowser_door.png')


class ActorImage_Seaweed(actorlib.ActorImage_StaticMultiple):  # 453
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.parent.setZValue(24998)

    @staticmethod
    def loadImages():
        if 'Seaweed0' in ImageCache:
            return
        for i in range(4):
            ImageCache[f'Seaweed{i}'] = actorlib.GetPixmap(f'seaweed_{i}.png')

    def dataChanged(self):
        SeaweedSizes = [0, 1, 2, 2, 3, 3]
        SeaweedXOffsets = [-15, -25, -29, -38]

        style = (self.parent.actordata[5] & 0xF) % 6
        size = SeaweedSizes[style]

        self.image = ImageCache[f'Seaweed{size}']
        self.offset = (
            SeaweedXOffsets[size],
            16 - (self.image.height() / 1.5),
        )

        super().dataChanged()


class ActorImage_HammerPlatform(actorlib.ActorImage):  # 455
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        w, h = ImageCache['HammerPlatform'].width(), ImageCache['HammerPlatform'].height()
        hammerPlatformAuxImage = actorlib.AuxiliaryImage(parent, w, h)
        hammerPlatformAuxImage.image = ImageCache['HammerPlatform']
        hammerPlatformAuxImage.setPos(-24 * 1.5, -8 * 1.5)
        self.aux.append(hammerPlatformAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('HammerPlatform', 'hammer_platform.png')


class ActorImage_BossBridge(actorlib.ActorImage_StaticMultiple):  # 456
    @staticmethod
    def loadImages():
        if 'BossBridgeL' in ImageCache:
            return
        ImageCache['BossBridgeL'] = actorlib.GetPixmap('boss_bridge_left.png')
        ImageCache['BossBridgeM'] = actorlib.GetPixmap('boss_bridge_middle.png')
        ImageCache['BossBridgeR'] = actorlib.GetPixmap('boss_bridge_right.png')

    def dataChanged(self):
        style = (self.parent.actordata[5] & 3) % 3
        self.image = (
            ImageCache['BossBridgeM'],
            ImageCache['BossBridgeR'],
            ImageCache['BossBridgeL'],
        )[style]

        super().dataChanged()


class ActorImage_SpinningThinBars(actorlib.ActorImage):  # 457
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.setZValue(24999)

        w, h = ImageCache['SpinningThinBars'].width(), ImageCache['SpinningThinBars'].height()
        spinningThinBarsAuxImage = actorlib.AuxiliaryImage(parent, w, h)
        spinningThinBarsAuxImage.image = ImageCache['SpinningThinBars']
        spinningThinBarsAuxImage.setPos(-115.4 * 1.5, -115.4 * 1.5)
        self.aux.append(spinningThinBarsAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SpinningThinBars', 'spinning_thin_bars.png')


class ActorImage_LongMetalBar(actorlib.ActorImage):  # 458
    def __init__(self, parent):
        super().__init__(parent)
        i = ImageCache['LongMetalBar']
        longMetalBarAuxImage = actorlib.AuxiliaryImage(parent, i.width(), i.height())
        longMetalBarAuxImage.image = i
        longMetalBarAuxImage.setSize(i.width(), i.height(), -252, -24)
        self.aux.append(longMetalBarAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LongMetalBar', 'long_metal_bar.png')


class ActorImage_SilverGearBlock(actorlib.ActorImage_StaticMultiple):  # 460
    @staticmethod
    def loadImages():
        if 'SilverGearBlockDown3' in ImageCache:
            return
        for gear in range(4):
            image = actorlib.GetImage(f'silver_gear_block_{gear}.png')
            if image is None:
                continue

            ImageCache[f'SilverGearBlockUp{gear}'] = QtGui.QPixmap.fromImage(image)
            ImageCache[f'SilverGearBlockDown{gear}'] = QtGui.QPixmap.fromImage(image.mirrored(True, True))

    def dataChanged(self):
        style = self.parent.actordata[5] & 3
        flipped = (self.parent.actordata[5] >> 4) & 1

        if flipped:
            self.image = ImageCache[f'SilverGearBlockDown{style}']
        else:
            self.image = ImageCache[f'SilverGearBlockUp{style}']

        super().dataChanged()


class ActorImage_EnormousBlock(actorlib.ActorImage):  # 462
    def __init__(self, parent):
        super().__init__(parent, 1.5)

        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 24, 24))
        self.aux.append(
            actorlib.AuxiliaryPainterPath(parent, QtGui.QPainterPath(), 24, 24)
        )
        self.aux.append(
            actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal)
        )

        self.spikes = []
        for height in (28, 16, 41, 47, 31):
            spikes = []
            for direction in range(2):
                # This has to be within the loop because the
                # following commands transpose them
                if direction == 0:
                    points = ((0, 0), (24, 12))
                else:
                    # faces right
                    points = ((24, 0), (0, 12))

                painterPath = QtGui.QPainterPath()
                painterPath.moveTo(direction * 24, 0)
                for i in range(height):
                    for point in points:
                        painterPath.lineTo(QtCore.QPointF(point[0], point[1] + i * 24))
                painterPath.lineTo(QtCore.QPointF(direction * 24, height * 24))
                painterPath.closeSubpath()
                spikes.append(painterPath)
            self.spikes.append(spikes)

    def dataChanged(self):
        if (
            not isinstance(self.aux[0], actorlib.AuxiliaryRectOutline)
            or not isinstance(self.aux[1], actorlib.AuxiliaryPainterPath)
            or not isinstance(self.aux[2], actorlib.AuxiliaryTrackObject)
        ):
            return

        size = (self.parent.actordata[5] >> 1) & 7
        direction = self.parent.actordata[2] & 1
        distance = (self.parent.actordata[4] >> 4) + 1
        side = self.parent.actordata[5] & 1

        # update the platform
        realsize = ((18, 28), (18, 16), (18, 41), (18, 47), (24, 31))[size]
        self.aux[0].setSize(realsize[0] * 24 - 24, realsize[1] * 24)
        if side == 0:
            self.aux[0].setPos(0, 0)
        else:
            self.aux[0].setPos(24, 0)

        # update the spikes
        self.aux[1].setSize(48, realsize[1] * 24 + 24)
        if side == 0:
            self.aux[1].setPos(realsize[0] * 24 - 24, 0)
        else:
            self.aux[1].setPos(0, 0)
        self.aux[1].setPath(self.spikes[size][side])

        # update the track
        self.aux[2].setSize(distance * 16, 16)
        halfheight = realsize[1] * 12 - 12
        halfwidth = realsize[0] * 12
        if direction == 0:
            self.aux[2].setPos(halfwidth, halfheight)
        else:
            self.aux[2].setPos(halfwidth - distance * 24, halfheight)


class ActorImage_Glare(actorlib.ActorImage):  # 463
    def __init__(self, parent):
        super().__init__(parent)
        sunGlareAuxImage = actorlib.AuxiliaryImage(parent, 1000, 1000)
        sunGlareAuxImage.image = ImageCache['SunGlare']
        sunGlareAuxImage.setSize(9 * 24, 9 * 24, -4 * 24 - 5, -4 * 24 - 20)
        self.aux.append(sunGlareAuxImage)

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SunGlare', 'glare.png')


class ActorImage_SwingingVine(actorlib.ActorImage_StaticMultiple):  # 464
    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SwingVine', 'swing_vine.png')
        actorlib.loadIfNotInImageCache('SwingChain', 'swing_chain.png')

    def dataChanged(self):
        style = self.parent.actordata[5] & 1
        self.image = ImageCache['SwingVine'] if not style else ImageCache['SwingChain']

        super().dataChanged()


class ActorImage_LavaIronBlock(actorlib.ActorImage_Static):  # 466
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['LavaIronBlock'],
            (-1, -1),
        )

        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Horizontal))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('LavaIronBlock', 'lava_iron_block.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        direction = self.parent.actordata[2] & 3
        distance = (self.parent.actordata[4] & 0xF0) >> 4

        if direction <= 1: # horizontal
            self.aux[0].direction = 1
            self.aux[0].setSize((distance * 16) + 16, 16)
        else: # vertical
            self.aux[0].direction = 2
            self.aux[0].setSize(16, (distance * 16) + 16)

        if direction == 0: # right
            self.aux[0].setPos(self.width + 48, self.height / 2)
        elif direction == 1: # left
            self.aux[0].setPos((-distance * 24) + 2, self.height / 2)
        elif direction == 2: # up
            self.aux[0].setPos((self.width * 0.75) - 12, (-distance * 24))
        else: # down
            self.aux[0].setPos((self.width * 0.75) - 12, self.height)

        super().dataChanged()


class ActorImage_MovingGemBlock(actorlib.ActorImage_Static):  # 467
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['MovingGemBlock'],
        )

        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 16, 16, actorlib.AuxiliaryTrackObject.Vertical))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MovingGemBlock', 'moving_gem_block.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        direction = self.parent.actordata[2] & 1
        distance = (self.parent.actordata[4] & 0xF0) >> 4

        self.aux[0].setSize(16, (distance * 16) + 16)
        if direction == 0: # up
            self.aux[0].setPos(self.width / 2, -distance * 24)
        else: # down
            self.aux[0].setPos(self.width / 2, self.height - 8)

        super().dataChanged()


class ActorImage_BoltPlatform(actorlib.ActorImage):  # 469
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.actorbox.shown = False

    @staticmethod
    def loadImages():
        if 'BoltPlatformL' in ImageCache:
            return
        ImageCache['BoltPlatformL'] = actorlib.GetPixmap('bolt_platform_left.png')
        ImageCache['BoltPlatformM'] = actorlib.GetPixmap('bolt_platform_middle.png')
        ImageCache['BoltPlatformR'] = actorlib.GetPixmap('bolt_platform_right.png')

    def dataChanged(self):
        self.offset = (0, -2)
        super().dataChanged()

        length = self.parent.actordata[5] & 0xF
        self.width = (length + 2) * 16

    def paint(self, painter):
        super().paint(painter)

        painter.drawPixmap(0, 0, ImageCache['BoltPlatformL'])
        painter.drawTiledPixmap(24, 3, int(self.width * 1.5) - 48, 24, ImageCache['BoltPlatformM'])
        painter.drawPixmap(int(self.width * 1.5) - 24, 0, ImageCache['BoltPlatformR'])


class ActorImage_BoltPlatformWire(actorlib.ActorImage_Static):  # 470
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['BoltPlatformWire'],
            (5, -240),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('BoltPlatformWire', 'bolt_platform_wire.png')


class ActorImage_PotPlatform(actorlib.ActorImage_Static):  # 471
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['PotPlatform'],
            (-9, -3),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('PotPlatform', 'pot_platform.png')


class ActorImage_IceFloeGenerator(actorlib.ActorImage):  # 472
    def __init__(self, parent):
        super().__init__(parent)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 96, 120, 0, -96))


class ActorImage_FloatingIceFloeGenerator(actorlib.ActorImage):  # 473
    def __init__(self, parent):
        super().__init__(parent)
        self.aux.append(actorlib.AuxiliaryRectOutline(parent, 96, 96, 0, 24))


class ActorImage_IceFloe(actorlib.ActorImage_StaticMultiple):  # 475
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.alpha = 0.65

    @staticmethod
    def loadImages():
        if 'IceFloe0' in ImageCache:
            return

        for size in range(13):
            image = actorlib.GetImage(f'ice_floe_{size}.png')
            if image is None:
                continue

            ImageCache[f'IceFloe{size}'] = QtGui.QPixmap.fromImage(image)

    def dataChanged(self):

        size = self.parent.actordata[5] & 15

        if size > 12:
            size = 0

        self.offset = (
            (-1, -32),  # 0: 3x3
            (-2, -48),  # 1: 4x4
            (-2, -64),  # 2: 5x5
            (-2, -32),  # 3: 4x3
            (-2, -48),  # 4: 5x4
            (-3, -80),  # 5: 7x6
            (-3, -160),  # 6: 16x11
            (-3, -112),  # 7: 11x8
            (-1, -48),  # 8: 2x4
            (-2, -48),  # 9: 3x4
            (-2.5, -96),  # 10: 6x7
            (-1, -64),  # 11: 2x5
            (-1, -64),  # 12: 3x5
        )[size]

        self.image = ImageCache[f'IceFloe{size}']

        super().dataChanged()


class ActorImage_FlyingWrench(actorlib.ActorImage_Static):  # 476
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['Wrench'],
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('Wrench', 'wrench.png')


class ActorImage_SuperGuideBlock(actorlib.ActorImage_StaticMultiple):  # 477
    def __init__(self, parent):
        super().__init__(
            parent,
            1.5,
            ImageCache['SuperGuide'],
            (-4, -4),
        )

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('SuperGuide', 'superguide_block.png')

    def dataChanged(self):
        midway = self.parent.actordata[5] & 1
        if midway:
            self.alpha = 0.5
        else:
            self.alpha = 1.0


class ActorImage_BowserSwitchSm(common.ActorImage_Switch):  # 478
    def __init__(self, parent):
        super().__init__(parent, 1.5)
        self.switchType = 'E'

    def dataChanged(self):
        self.offset = (0, 0)
        super().dataChanged()


class ActorImage_BowserSwitchLg(actorlib.ActorImage_StaticMultiple):  # 479
    @staticmethod
    def loadImages():
        if 'ELSwitch' in ImageCache:
            return
        elg = actorlib.GetImage('e_switch_lg.png')
        if elg is None:
            return

        ImageCache['ELSwitch'] = QtGui.QPixmap.fromImage(elg)
        ImageCache['ELSwitchU'] = QtGui.QPixmap.fromImage(elg.mirrored(True, True))

    def dataChanged(self):
        midway = (self.parent.actordata[2] >> 6) & 1
        upsideDown = self.parent.actordata[5] & 1
        shiftY = self.parent.actordata[3] & 0xF
        shiftX = (self.parent.actordata[5] >> 4) & 0xF

        if midway:
            self.alpha = 0.5
        else:
            self.alpha = 1.0

        if shiftX != 0:
            self.xOffset = -7
        else:
            self.xOffset = -15

        if not upsideDown:
            self.image = ImageCache['ELSwitch']

            if shiftY != 0:
                self.yOffset = -40
            else:
                self.yOffset = -24
        else:
            self.image = ImageCache['ELSwitchU']

            if shiftY != 0:
                self.yOffset = 16
            else:
                self.yOffset = 0

        super().dataChanged()


class ActorImage_MortonSkewer(actorlib.ActorImage):  # 480
    def __init__(self, parent):
        super().__init__(parent)
        self.actorbox.shown = False
        self.dimensions = (0, -368, 64, 410)
        self.aux.append(actorlib.AuxiliaryTrackObject(parent, 36, 591, actorlib.AuxiliaryTrackObject.Vertical))

    @staticmethod
    def loadImages():
        actorlib.loadIfNotInImageCache('MortonSkewerM', 'skewer_down_m_0.png')
        actorlib.loadIfNotInImageCache('MortonSkewerE', 'skewer_down_e_0.png')

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryTrackObject):
            return

        self.aux[0].setPos(36, 591)
        self.aux[0].setSize(16, 160)

    def paint(self, painter):
        painter.drawTiledPixmap(0, 0, 98, 576, ImageCache['MortonSkewerM'])
        painter.drawPixmap(0, 576, ImageCache['MortonSkewerE'])


class ActorImage_FinalBossRubble(actorlib.ActorImage_StaticMultiple):  # 481
    def __init__(self, parent):
        super().__init__(parent)

    @staticmethod
    def loadImages():
        if 'FinalBossRubble0' in ImageCache:
            return
        for size in range(2):
            image = actorlib.GetImage(f'final_boss_rubble_{size}.png')
            if image is None:
                continue

            ImageCache[f'FinalBossRubble{size}'] = QtGui.QPixmap.fromImage(image)

    def dataChanged(self):
        size = self.parent.actordata[5] & 1

        self.image = ImageCache[f'FinalBossRubble{size}']

        super().dataChanged()


class ActorImage_FinalBossEffects(actorlib.ActorImage):  # 482
    def __init__(self, parent):
        super().__init__(parent)
        finalBossEffectsAuxImage = actorlib.AuxiliaryImage(parent, 3612, 672)
        finalBossEffectsAuxImage.image = ImageCache['FinalBossEffects0']
        finalBossEffectsAuxImage.setPos(-228, -555)
        self.aux.append(finalBossEffectsAuxImage)
        self.parent.setZValue(24999)

    @staticmethod
    def loadImages():
        if 'FinalBossEffects0' in ImageCache:
            return

        for i in range(3):
            image = actorlib.GetImage(f'final_boss_effects_{i}.png')
            if image is None:
                continue

            ImageCache[f'FinalBossEffects{i}'] = QtGui.QPixmap.fromImage(image)

    def dataChanged(self):
        if not isinstance(self.aux[0], actorlib.AuxiliaryImage):
            return

        style = self.parent.actordata[5] & 15

        # Styles greater than 2 load nothing
        if style > 2:
            self.aux[0].image = None

        else:
            self.aux[0].image = ImageCache[f'FinalBossEffects{style}']

            if style == 0:
                self.aux[0].setPos(-228, -555)
            elif style == 1:
                self.aux[0].setPos(-228, -408)
            else:
                self.aux[0].setPos(-24, -192)


################################################################
################################################################
################################################################
################################################################


ImageClasses = {
    0: ActorImage_MeasureJump,
    9: ActorImage_CharacterSpawner,
    20: ActorImage_Goomba,
    21: ActorImage_ParaGoomba,
    23: ActorImage_HorzMovingPlatform,
    24: ActorImage_BuzzyBeetle,
    25: ActorImage_Spiny,
    26: ActorImage_UpsideDownSpiny,
    27: ActorImage_DSStoneBlock_Vert,
    28: ActorImage_DSStoneBlock_Horz,
    30: ActorImage_OldStoneBlock_NoSpikes,
    31: ActorImage_VertMovingPlatform,
    32: ActorImage_StarCoinRegular,
    40: ActorImage_QSwitch,
    41: ActorImage_PSwitch,
    42: ActorImage_ExcSwitch,
    43: ActorImage_QSwitchBlock,
    44: ActorImage_PSwitchBlock,
    45: ActorImage_ExcSwitchBlock,
    46: ActorImage_Podoboo,
    47: ActorImage_Thwomp,
    48: ActorImage_GiantThwomp,
    49: ActorImage_UnusedSeesaw,
    50: ActorImage_FallingPlatform,
    51: ActorImage_TiltingGirder,
    52: ActorImage_UnusedRotPlatforms,
    53: ActorImage_Quicksand,
    54: ActorImage_Lakitu,
    55: ActorImage_UnusedRisingSeesaw,
    56: ActorImage_RisingTiltGirder,
    57: ActorImage_KoopaTroopa,
    58: ActorImage_KoopaParatroopa,
    59: ActorImage_LineTiltGirder,
    60: ActorImage_SpikeTop,
    61: ActorImage_BigBoo,
    62: ActorImage_SpinningFirebar,
    63: ActorImage_SpikeBall,
    64: ActorImage_OutdoorsFog,
    65: ActorImage_PipePiranhaUp,
    66: ActorImage_PipePiranhaDown,
    67: ActorImage_PipePiranhaRight,
    68: ActorImage_PipePiranhaLeft,
    69: ActorImage_PipeFiretrapUp,
    70: ActorImage_PipeFiretrapDown,
    71: ActorImage_PipeFiretrapRight,
    72: ActorImage_PipeFiretrapLeft,
    73: ActorImage_GroundPiranha,
    74: ActorImage_BigGroundPiranha,
    75: ActorImage_GroundFiretrap,
    76: ActorImage_BigGroundFiretrap,
    77: ActorImage_ShipKey,
    78: ActorImage_CloudTrampoline,
    80: ActorImage_FireBro,
    81: ActorImage_OldStoneBlock_SpikesLeft,
    82: ActorImage_OldStoneBlock_SpikesRight,
    83: ActorImage_OldStoneBlock_SpikesLeftRight,
    84: ActorImage_OldStoneBlock_SpikesTop,
    85: ActorImage_OldStoneBlock_SpikesBottom,
    86: ActorImage_OldStoneBlock_SpikesTopBottom,
    87: ActorImage_TrampolineWall,
    92: ActorImage_BulletBillLauncher,
    93: ActorImage_BanzaiBillLauncher,
    94: ActorImage_BoomerangBro,
    95: ActorImage_HammerBroNormal,
    96: ActorImage_RotationControllerSwaying,
    97: ActorImage_RotationControlledSolidBetaPlatform,
    98: ActorImage_GiantSpikeBall,
    99: ActorImage_PipeEnemyGenerator,
    100: ActorImage_Swooper,
    101: ActorImage_Bobomb,
    102: ActorImage_Broozer,
    103: ActorImage_PlatformGenerator,
    104: ActorImage_AmpNormal,
    105: ActorImage_Pokey,
    106: ActorImage_LinePlatform,
    107: ActorImage_RotationControlledPassBetaPlatform,
    108: ActorImage_AmpLine,
    109: ActorImage_ChainBall,
    110: ActorImage_Sunlight,
    111: ActorImage_Blooper,
    112: ActorImage_BlooperBabies,
    113: ActorImage_Flagpole,
    114: ActorImage_FlameCannon,
    115: ActorImage_Cheep,
    116: ActorImage_CoinCheep,
    117: ActorImage_PulseFlameCannon,
    118: ActorImage_DryBones,
    119: ActorImage_GiantDryBones,
    120: ActorImage_SledgeBro,
    122: ActorImage_OneWayPlatform,
    123: ActorImage_UnusedCastlePlatform,
    125: ActorImage_FenceKoopaHorz,
    126: ActorImage_FenceKoopaVert,
    127: ActorImage_FlipFence,
    128: ActorImage_FlipFenceLong,
    129: ActorImage_4Spinner,
    130: ActorImage_Wiggler,
    131: ActorImage_Boo,
    132: ActorImage_UnusedBlockPlatform1,
    133: ActorImage_StalagmitePlatform,
    134: ActorImage_Crow,
    135: ActorImage_HangingPlatform,
    136: ActorImage_RotBulletLauncher,
    137: ActorImage_SkewerDown,
    138: ActorImage_Water,
    139: ActorImage_Lava,
    140: ActorImage_SkewerUp,
    141: ActorImage_SkewerRight,
    142: ActorImage_SkewerLeft,
    143: ActorImage_Arrow,
    144: ActorImage_RedCoin,
    145: ActorImage_FloatingBarrel,
    146: ActorImage_ChainChomp,
    147: ActorImage_Coin,
    148: ActorImage_Spring,
    149: ActorImage_RotationControllerSpinning,
    151: ActorImage_Porcupuffer,
    153: ActorImage_QSwitchUnused,
    155: ActorImage_StarCoinLineControlled,
    156: ActorImage_RedCoinRing,
    157: ActorImage_BigBrick,
    158: ActorImage_FireSnake,
    160: ActorImage_UnusedBlockPlatform2,
    161: ActorImage_PipeBubbles,
    166: ActorImage_SnakeBlock,
    170: ActorImage_ChestnutGoomba,
    171: ActorImage_PowerupBubble,
    172: ActorImage_ScrewMushroomWithBolt,
    173: ActorImage_GiantFloatingLog,
    174: ActorImage_OneWayGate,
    175: ActorImage_FlyingQBlock,
    176: ActorImage_RouletteBlock,
    177: ActorImage_FireChomp,
    178: ActorImage_ScalePlatform,
    179: ActorImage_SpecialExit,
    180: ActorImage_CheepChomp,
    182: ActorImage_EventDoor,
    185: ActorImage_ToadBalloon,
    187: ActorImage_PlayerBlock,
    188: ActorImage_MidwayFlag,
    189: ActorImage_LarryKoopa,
    190: ActorImage_TiltingGirderUnused,
    191: ActorImage_TileEvent,
    192: ActorImage_LarryKoopaCastleBoss,
    193: ActorImage_Urchin,
    194: ActorImage_MegaUrchin,
    195: ActorImage_HuckitCrab,
    196: ActorImage_Fishbones,
    197: ActorImage_Clam,
    198: ActorImage_GiantGoomba,
    199: ActorImage_MegaGoomba,
    200: ActorImage_Microgoomba,
    201: ActorImage_Icicle,
    202: ActorImage_MGCannon,
    203: ActorImage_Chest,
    204: ActorImage_RollObjSpawner,
    205: ActorImage_GiantBubbleNormal,
    206: ActorImage_Zoom,
    207: ActorImage_QBlock,
    208: ActorImage_QBlockUnused,
    209: ActorImage_BrickBlock,
    211: ActorImage_BowserJr1stController,
    212: ActorImage_RollingHill,
    214: ActorImage_FreefallPlatform,
    216: ActorImage_Poison,
    219: ActorImage_LineBlock,
    221: ActorImage_InvisibleBlock,
    222: ActorImage_ConveyorSpike,
    223: ActorImage_SpringBlock,
    224: ActorImage_JumboRay,
    225: ActorImage_FloatingCoin,
    226: ActorImage_GiantBubbleUnused,
    227: ActorImage_PipeCannon,
    228: ActorImage_ExtendShroom,
    229: ActorImage_SandPillar,
    230: ActorImage_Bramball,
    231: ActorImage_WiggleShroom,
    232: ActorImage_MechaKoopa,
    233: ActorImage_Bulber,
    237: ActorImage_PCoin,
    238: ActorImage_Foo,
    240: ActorImage_GiantWiggler,
    242: ActorImage_FallingLedgeBar,
    247: ActorImage_CheepFormation,
    252: ActorImage_EventDeactivBlock,
    253: ActorImage_RotControlledCoin,
    254: ActorImage_RotControlledPipe,
    255: ActorImage_RotatingQBlock,
    257: ActorImage_MoveWhenOnMetalLavaBlock,
    256: ActorImage_RotatingBrickBlock,
    259: ActorImage_RegularDoor,
    260: ActorImage_MovementController_TwoWayLine,
    261: ActorImage_OldStoneBlock_MovementControlled,
    262: ActorImage_PoltergeistItem,
    263: ActorImage_WaterPiranha,
    264: ActorImage_WalkingPiranha,
    265: ActorImage_FallingIcicle,
    266: ActorImage_RotatingFence,
    267: ActorImage_TiltGrate,
    268: ActorImage_LavaGeyser,
    269: ActorImage_Parabomb,
    271: ActorImage_ScaredyRat,
    272: ActorImage_IceBro,
    274: ActorImage_CastleGear,
    275: ActorImage_FiveEnemyRaft,
    276: ActorImage_GhostDoor,
    277: ActorImage_TowerDoor,
    278: ActorImage_CastleDoor,
    280: ActorImage_GiantIceBlock,
    285: ActorImage_RiseFallWater,
    286: ActorImage_WoodCircle,
    287: ActorImage_PathIceBlock,
    288: ActorImage_RollingBarrel,
    289: ActorImage_Box,
    291: ActorImage_Parabeetle,
    292: ActorImage_HeavyParabeetle,
    294: ActorImage_IceCube,
    295: ActorImage_NutPlatform,
    296: ActorImage_MegaBuzzy,
    297: ActorImage_DragonCoaster,
    298: ActorImage_LongCannon,
    299: ActorImage_CannonMulti,
    300: ActorImage_RotCannon,
    301: ActorImage_RotCannonPipe,
    303: ActorImage_MontyMole,
    304: ActorImage_RotFlameCannon,
    305: ActorImage_LightCircle,
    306: ActorImage_RotSpotlight,
    308: ActorImage_HammerBroPlatform,
    309: ActorImage_SynchroFlameJet,
    310: ActorImage_ArrowSign,
    311: ActorImage_MegaIcicle,
    314: ActorImage_BubbleGen,
    315: ActorImage_Bolt,
    316: ActorImage_BoltBox,
    318: ActorImage_BoxGenerator,
    319: ActorImage_UnusedWiimoteDoor,
    320: ActorImage_UnusedSlidingWiimoteDoor,
    321: ActorImage_ArrowBlock,
    323: ActorImage_BooCircle,
    325: ActorImage_GhostHouseStand,
    326: ActorImage_KingBill,
    327: ActorImage_LinePlatformBolt,
    328: ActorImage_BubbleCannon,
    330: ActorImage_RopeLadder,
    331: ActorImage_DishPlatform,
    333: ActorImage_PlayerBlockPlatform,
    334: ActorImage_CheepGiant,
    335: ActorImage_CheepSchool,
    336: ActorImage_WendyKoopa,
    337: ActorImage_IggyKoopa,
    338: ActorImage_MovingBulletBillLauncher,
    339: ActorImage_Pipe_MovingUp,
    340: ActorImage_LemmyKoopa,
    341: ActorImage_BigShell,
    342: ActorImage_Muncher,
    343: ActorImage_Fuzzy,
    344: ActorImage_MortonKoopa,
    345: ActorImage_ChainHolder,
    346: ActorImage_HangingChainPlatform,
    347: ActorImage_RoyKoopa,
    348: ActorImage_LudwigVonKoopa,
    349: ActorImage_MortonKoopaCastleBoss,
    352: ActorImage_RockyWrench,
    353: ActorImage_Pipe_MovingDown,
    354: ActorImage_BrownTowerBlockTwoWayLine,
    355: ActorImage_RollingHillWith1Pipe,
    356: ActorImage_BrownTowerBlockNormal,
    357: ActorImage_Fruit,
    358: ActorImage_LavaParticles,
    359: ActorImage_WallLantern,
    360: ActorImage_RollingHillWith8Pipes,
    361: ActorImage_CrystalBlock,
    362: ActorImage_ColoredBox,
    364: ActorImage_RoyKoopaCastleBoss,
    365: ActorImage_LudwigVonKoopaCastleBoss,
    366: ActorImage_CubeKinokoRot,
    367: ActorImage_CubeKinokoLine,
    368: ActorImage_FlashRaft,
    369: ActorImage_SlidingPenguin,
    370: ActorImage_CloudBlock,
    371: ActorImage_RollingHillCoin,
    372: ActorImage_IggyKoopaCastleBoss,
    373: ActorImage_RaftWater,
    374: ActorImage_SnowWind,
    375: ActorImage_WendyKoopaCastleBoss,
    376: ActorImage_MovingFence,
    377: ActorImage_Pipe_Up,
    378: ActorImage_Pipe_Down,
    379: ActorImage_Pipe_Right,
    380: ActorImage_Pipe_Left,
    381: ActorImage_LemmyKoopaCastleBoss,
    382: ActorImage_ScrewMushroomNoBolt,
    383: ActorImage_KamekController,
    384: ActorImage_PipeCooliganGenerator,
    385: ActorImage_IceBlock,
    386: ActorImage_PowBlock,
    387: ActorImage_Bush,
    388: ActorImage_Barrel,
    389: ActorImage_StarCoinBoltControlled,
    390: ActorImage_BoltControlledCoin,
    391: ActorImage_GlowBlock,
    393: ActorImage_PropellerBlock,
    394: ActorImage_LemmyBall,
    395: ActorImage_SpinyCheep,
    396: ActorImage_MoveWhenOn,
    397: ActorImage_GhostHouseBox,
    398: ActorImage_LongSkewerRight,
    400: ActorImage_LongSkewerLeft,
    401: ActorImage_MassiveSkewerDown,
    402: ActorImage_LineQBlock,
    403: ActorImage_LineBrickBlock,
    404: ActorImage_MassiveSkewerUp,
    405: ActorImage_BowserJr2ndController,
    406: ActorImage_BowserJr3rdController,
    407: ActorImage_BossControllerCastleBoss,
    411: ActorImage_ToadHouseBalloonUnused,
    412: ActorImage_ToadHouseBalloonUsed,
    413: ActorImage_WendyRing,
    414: ActorImage_Gabon,
    415: ActorImage_BetaLarryKoopa,
    416: ActorImage_InvisibleOneUp,
    417: ActorImage_SpinjumpCoin,
    418: ActorImage_BanzaiGen,
    419: ActorImage_Bowser,
    420: ActorImage_GiantGlowBlock,
    421: ActorImage_UnusedGhostDoor,
    422: ActorImage_ToadQBlock,
    423: ActorImage_ToadBrickBlock,
    424: ActorImage_PalmTree,
    425: ActorImage_Jellybeam,
    427: ActorImage_Kamek,
    428: ActorImage_MGPanel,
    431: ActorImage_BowserController,
    432: ActorImage_Toad,
    433: ActorImage_FloatingQBlock,
    434: ActorImage_WarpCannon,
    435: ActorImage_GhostFog,
    437: ActorImage_PurplePole,
    438: ActorImage_ShapeBlocks,
    439: ActorImage_CagePeachFake,
    440: ActorImage_HorizontalRope,
    441: ActorImage_MushroomPlatform,
    443: ActorImage_ReplayBlock,
    444: ActorImage_PreSwingingVine,
    445: ActorImage_CagePeachReal,
    447: ActorImage_UnderwaterLamp,
    448: ActorImage_MetalBar,
    450: ActorImage_Pipe_EnterableUp,
    451: ActorImage_ScaredyRatDespawner,
    452: ActorImage_BowserDoor,
    453: ActorImage_Seaweed,
    455: ActorImage_HammerPlatform,
    456: ActorImage_BossBridge,
    457: ActorImage_SpinningThinBars,
    458: ActorImage_LongMetalBar,
    460: ActorImage_SilverGearBlock,
    462: ActorImage_EnormousBlock,
    463: ActorImage_Glare,
    464: ActorImage_SwingingVine,
    466: ActorImage_LavaIronBlock,
    467: ActorImage_MovingGemBlock,
    469: ActorImage_BoltPlatform,
    470: ActorImage_BoltPlatformWire,
    471: ActorImage_PotPlatform,
    472: ActorImage_IceFloeGenerator,
    473: ActorImage_FloatingIceFloeGenerator,
    475: ActorImage_IceFloe,
    476: ActorImage_FlyingWrench,
    477: ActorImage_SuperGuideBlock,
    478: ActorImage_BowserSwitchSm,
    479: ActorImage_BowserSwitchLg,
    480: ActorImage_MortonSkewer,
    481: ActorImage_FinalBossRubble,
    482: ActorImage_FinalBossEffects,
}
