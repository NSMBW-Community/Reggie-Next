from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
import spritelib as SLib
from src.data.level.dirty import SetDirty
from src.data.level.items.basic import LevelEditorItem
from src.data.level.items.zone_grabber import ZoneGrabberItem


class ZoneItem(LevelEditorItem):
    """
    Level editor item that represents a zone
    """

    def __init__(self, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, boundings, bgA, bgB, id_=None):
        """
        Creates a zone with specific data
        """
        LevelEditorItem.__init__(self)

        self.font = globals_.NumberFont
        self.TitlePos = QtCore.QPointF(10, 18)

        self.objx = a
        self.objy = b
        self.width = c
        self.height = d
        self.modeldark = e
        self.terraindark = f
        self.id = g
        self.block3id = h
        self.cammode = i
        self.camzoom = j
        self.visibility = k
        self.block5id = l
        self.block6id = m
        self.camtrack = n
        self.music = o
        self.sfxmod = p

        # Create grabbers for resizing
        self.GrabberTL = ZoneGrabberItem(self, 1)
        self.GrabberTR = ZoneGrabberItem(self, 2)
        self.GrabberBL = ZoneGrabberItem(self, 3)
        self.GrabberBR = ZoneGrabberItem(self, 4)

        self.UpdateRects()
        self.aux = set()

        if id_ is not None:
            self.id = id_

        self.UpdateTitle()

        bounding = None
        for block in boundings:
            if block[4] == self.block3id:
                bounding = block
                break

        if bounding is not None:
            self.yupperbound = bounding[0]
            self.ylowerbound = bounding[1]
            self.yupperbound2 = bounding[2]
            self.ylowerbound2 = bounding[3]
            self.entryid = bounding[4]
            self.mpcamzoomadjust = bounding[5]
            self.yupperbound3 = bounding[6]
            self.ylowerbound3 = bounding[7]

        bgABlock = None
        id = self.block5id
        for block in bgA:
            if block[0] == id:
                bgABlock = block

        if bgABlock is not None:
            self.entryidA = bgABlock[0]
            self.XscrollA = bgABlock[1]
            self.YscrollA = bgABlock[2]
            self.YpositionA = bgABlock[3]
            self.XpositionA = bgABlock[4]
            self.bg1A = bgABlock[5]
            self.bg2A = bgABlock[6]
            self.bg3A = bgABlock[7]
            self.ZoomA = bgABlock[8]

        bgBBlock = None
        id = self.block6id
        for block in bgB:
            if block[0] == id:
                bgBBlock = block

        if bgBBlock is not None:
            self.entryidB = bgBBlock[0]
            self.XscrollB = bgBBlock[1]
            self.YscrollB = bgBBlock[2]
            self.YpositionB = bgBBlock[3]
            self.XpositionB = bgBBlock[4]
            self.bg1B = bgBBlock[5]
            self.bg2B = bgBBlock[6]
            self.bg3B = bgBBlock[7]
            self.ZoomB = bgBBlock[8]

        self.dragging = False
        self.dragstartx = -1
        self.dragstarty = -1
        self.ent_indicator_show = False
        self.ent_indicator_offset = 0

        globals_.DirtyOverride += 1
        self.setPos(int(a * 1.5), int(b * 1.5))
        globals_.DirtyOverride -= 1
        self.setZValue(50000)

    def UpdateTitle(self):
        """
        Updates the zone's title
        """
        self.title = globals_.trans.string('Zones', 0, '[num]', self.id + 1)

    def UpdateRects(self):
        """
        Updates the zone's bounding rectangle
        """
        if globals_.mainWindow is None:
            return

        if hasattr(globals_.mainWindow, 'ZoomLevel'):
            grabberWidth = 480 / globals_.mainWindow.ZoomLevel
            if grabberWidth < 4.8:
                grabberWidth = 4.8
        else:
            grabberWidth = 4.8

        self.prepareGeometryChange()
        self.BoundingRect = QtCore.QRectF(-3, -3, self.width * 1.5 + 6, self.height * 1.5 + 6)
        self.ZoneRect = QtCore.QRectF(self.objx, self.objy, self.width, self.height)
        self.DrawRect = QtCore.QRectF(0, 0, self.width * 1.5, self.height * 1.5)
        self.GrabberRectTL = QtCore.QRectF(-3, -3, grabberWidth, grabberWidth)
        self.GrabberRectTR = QtCore.QRectF(self.width * 1.5 - grabberWidth + 3, -3, grabberWidth, grabberWidth)
        self.GrabberRectBL = QtCore.QRectF(-3, self.height * 1.5 - grabberWidth + 3, grabberWidth, grabberWidth)
        self.GrabberRectBR = QtCore.QRectF(self.width * 1.5 - grabberWidth + 3, self.height * 1.5 - grabberWidth + 3, grabberWidth, grabberWidth)

        # Update grabber rects
        self.GrabberTL.UpdateRects(self.GrabberRectTL)
        self.GrabberTR.UpdateRects(self.GrabberRectTR)
        self.GrabberBL.UpdateRects(self.GrabberRectBL)
        self.GrabberBR.UpdateRects(self.GrabberRectBR)

    def getCameraHeight(self):
        """
        Returns the applicable camera height(s) for this zone.
        """
        if self.cammode in {0, 1, 6, 7}:
            heights = [[14, 19], [14, 19, 24], [14, 19, 28], [20, 24], [19, 24, 28], [17, 24], [17, 24, 28], [17, 20], [7, 11, 28], [17, 20.5, 24], [17, 20, 28]]
        elif self.cammode == 2:
            heights = [[14, 19], [14, 19, 24], [14, 19, 28], [19, 19, 24], [19, 24, 28], [19, 24, 28], [17, 24, 28], [17, 20.5, 24]]
        else:
            heights = [[14], [19], [24], [28], [17], [20], [16], [28], [7], [10.5]]

        return heights[self.camzoom]

    def updateEntranceIndicator(self):
        """
        Updates the member fields related to the entrance indicator.
        """
        # Only show the indicator in area 1.
        if globals_.Area.areanum != 1:
            self.ent_indicator_show = False
            return

        # Only show the indicator when this zone contains the initial entrance.
        for entrance in globals_.Area.entrances:
            if entrance.entid == globals_.Area.startEntrance:
                break
        else:
            # The initial entrance does not exist.
            self.ent_indicator_show = False
            return

        initial_id = SLib.MapPositionToZoneID(globals_.Area.zones, entrance.objx, entrance.objy, get_id=True)
        if initial_id != self.id:
            # The initial entrance is not closest to this zone.
            self.ent_indicator_show = False
            return

        # Only show the indicator when this zone does not contain an autoscroller
        # or ambush controller.
        for sprite in globals_.Area.sprites:
            if sprite.type not in {91, 454}:  # {autoscroll, ambush}
                continue

            zone_id = SLib.MapPositionToZoneID(globals_.Area.zones, sprite.objx, sprite.objy, get_id=True)

            if self.id == zone_id:
                # The zone contains either an ambush controller or an autoscroller
                self.ent_indicator_show = False
                return

        # Only show the indicator when this zone is vertical. This requirement
        # is a bit weird - maybe change this condition to something related to
        # zone direction or tracking mode?
        if self.width < self.height:
            self.ent_indicator_show = False
            return

        # Only show the indicator when this zone's size is
        height = self.getCameraHeight()[0]

        if height in {14, 17}:  # These final heights are too small
            self.ent_indicator_show = False
            return

        self.ent_indicator_show = True

        # Multiply the height by the aspect ratio to get the width, divide by 2
        # to get half of it and by 24 to convert blocks to pixels. This is all
        # combined to reduce floating point rounding errors.
        self.ent_indicator_offset = height * 24 * 16 / 18

    def paint(self, painter, option, widget = ...):
        """
        Paints the zone on screen
        """
        if not painter or not option or not globals_.theme or not self.font:
            return

        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Paint an indicator line to show the leftmost edge of where entrances
        # can be safely placed.
        if globals_.DrawEntIndicators:
            # This function could be called only when a sprite or entrance is
            # moved or created. If this starts giving trouble, do that.
            self.updateEntranceIndicator()

            # Only draw the indicator if we should
            if self.ent_indicator_show and self.ent_indicator_offset < self.DrawRect.width():
                offset = self.ent_indicator_offset

                color = globals_.theme.color('zone_entrance_helper')
                if color is not None:
                    painter.setPen(QtGui.QPen(color, 2))
                lineStart = QtCore.QPointF(self.DrawRect.x() + offset, self.DrawRect.y())
                lineEnd = QtCore.QPointF(self.DrawRect.x() + offset, self.DrawRect.y() + self.DrawRect.height())
                painter.drawLine(lineStart, lineEnd)

        # Paint liquids/fog
        if globals_.SpritesShown and globals_.SpriteImagesShown and globals_.RealViewEnabled:
            zoneRect = self.mapRectToScene(self.DrawRect)
            from sprites import SpriteImage_BubbleGen as bubbleGenType
            from sprites import SpriteImage_LiquidOrFog as liquidOrFogType

            for sprite in globals_.Area.sprites:
                if isinstance(sprite.ImageObj, liquidOrFogType) and sprite.ImageObj.paintZone() and self.id == sprite.ImageObj.zoneId:
                    sprite.ImageObj.realViewZone(painter, zoneRect)
                if isinstance(sprite.ImageObj, bubbleGenType) and hasattr(sprite, 'zoneID') and self.id == sprite.zoneID:
                    sprite.ImageObj.realViewZone(painter, zoneRect)
        else: # Fixes issues with the liquid/fog only disappearing where sprites updated the scene
            self.update(self.DrawRect)

        # Now paint the borders
        color = globals_.theme.color('zone_lines')
        if color is not None:
            painter.setPen(QtGui.QPen(color, 3))
        if self.visibility >= 32 and globals_.RealViewEnabled:
            painter.setBrush(QtGui.QBrush(globals_.theme.color('zone_dark_fill')))
        painter.drawRect(self.DrawRect)

        # And text
        color = globals_.theme.color('zone_text')
        if color is not None:
            painter.setPen(QtGui.QPen(color, 3))
        painter.setFont(self.font)
        painter.drawText(self.TitlePos, self.title)

        # Draw the bounds indicator rectangle
        if globals_.BoundsDrawn:
            painter.setBrush(QtGui.QBrush(QtGui.QColor.fromRgb(255,255,255,42)))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            r1 = QtCore.QRectF(self.DrawRect)
            r1.setHeight((self.yupperbound + 80) * 1.5)
            r1.moveTop(self.DrawRect.bottom() - (self.getCameraHeight()[0] * 24))
            painter.drawRect(r1)

            r2 = QtCore.QRectF(self.DrawRect)
            r2.setHeight((72 - self.ylowerbound) * 1.5)
            r2.moveBottom(self.DrawRect.bottom())
            painter.drawRect(r2)

    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for resizing
        """
        if not event:
            return

        if self.GrabberRectTL.contains(event.pos()):
            self.dragging = True
            self.dragcorner = 1
        elif self.GrabberRectTR.contains(event.pos()):
            self.dragging = True
            self.dragcorner = 2
        elif self.GrabberRectBL.contains(event.pos()):
            self.dragging = True
            self.dragcorner = 3
        elif self.GrabberRectBR.contains(event.pos()):
            self.dragging = True
            self.dragcorner = 4
        else:
            self.dragging = False

        if self.dragging:
            # Start dragging
            self.dragstartx = int(event.scenePos().x() / 1.5)
            self.dragstarty = int(event.scenePos().y() / 1.5)
            self.draginitialx1 = self.objx
            self.draginitialy1 = self.objy
            self.draginitialx2 = self.objx + self.width
            self.draginitialy2 = self.objy + self.height
            event.accept()
        else:
            LevelEditorItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed for resizing
        """
        if not event or not globals_.mainWindow:
            return

        if event.buttons() != QtCore.Qt.MouseButton.NoButton and self.dragging:
            # Resize it
            clickedx = int(event.scenePos().x() / 1.5)
            clickedy = int(event.scenePos().y() / 1.5)

            x1 = self.draginitialx1
            y1 = self.draginitialy1
            x2 = self.draginitialx2
            y2 = self.draginitialy2

            # If alt is not held, snap to 8x8 grid
            if QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.KeyboardModifier.AltModifier:
                clickedx = 8 * round(clickedx / 8)
                clickedy = 8 * round(clickedy / 8)
                x1 = 8 * round(x1 / 8)
                y1 = 8 * round(y1 / 8)
                x2 = 8 * round(x2 / 8)
                y2 = 8 * round(y2 / 8)

            MIN_X = 16
            MIN_Y = 16
            MIN_W = 204
            MIN_H = 112

            if self.dragcorner == 1: # TL
                # Rect from (x2, y2) to clicked
                x1 = clickedx
                y1 = clickedy
                if x1 < MIN_X: x1 = MIN_X
                if y1 < MIN_Y: y1 = MIN_Y
                if x2 - x1 < MIN_W: x1 = x2 - MIN_W
                if y2 - y1 < MIN_H: y1 = y2 - MIN_H

            elif self.dragcorner == 2: # TR
                # Rect from (x1, y2) to clicked
                x2 = clickedx
                y1 = clickedy
                if y1 < MIN_Y: y1 = MIN_Y
                if x2 - x1 < MIN_W: x2 = x1 + MIN_W
                if y2 - y1 < MIN_H: y1 = y2 - MIN_H

            elif self.dragcorner == 3: # BL
                # Rect from (x2, y1) to clicked
                x1 = clickedx
                y2 = clickedy
                if x1 < MIN_X: x1 = MIN_X
                if x2 - x1 < MIN_W: x1 = x2 - MIN_W
                if y2 - y1 < MIN_H: y2 = y1 + MIN_H

            elif self.dragcorner == 4: # BR
                # Rect from (x1, y1) to clicked
                x2 = clickedx
                y2 = clickedy
                if x2 - x1 < MIN_W: x2 = x1 + MIN_W
                if y2 - y1 < MIN_H: y2 = y1 + MIN_H

            oldx = self.x()
            oldy = self.y()
            oldw = self.width * 1.5
            oldh = self.height * 1.5

            self.objx = x1
            self.objy = y1
            self.width = x2 - x1
            self.height = y2 - y1

            oldrect = QtCore.QRectF(oldx, oldy, oldw, oldh)

            self.UpdateRects()
            self.setPos(int(self.objx * 1.5), int(self.objy * 1.5))

            newrect = QtCore.QRectF(self.x(), self.y(), self.width * 1.5, self.height * 1.5)
            updaterect = oldrect.united(newrect)
            updaterect += QtCore.QMarginsF(-3, -3, 3, 3)

            scene = self.scene()
            if scene is not None:
                scene.update(updaterect)

            globals_.mainWindow.level_overview.update()

            for spr in globals_.Area.sprites:
                spr.ImageObj.positionChanged()

            SetDirty()

            event.accept()
        else:
            LevelEditorItem.mouseMoveEvent(self, event)

    def itemChange(self, change, value):
        """
        Avoids snapping for zones
        """
        return QtWidgets.QGraphicsItem.itemChange(self, change, value)
