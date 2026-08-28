import os
from typing import cast

from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
import spritelib as SLib
from src.data.level.items.basic import InstanceDefinition, LevelEditorItem
from src.ui.theme.reggie_theme import setOverrideCursor


class InstanceDefinition_EntranceItem(InstanceDefinition):
    """
    Definition of an instance of EntranceItem
    """
    fieldNames = (
        'entid',
        'destarea',
        'destentrance',
        'enttype',
        'entzone',
        'entlayer',
        'entpath',
        'cpdirection',
        'entsettings',
    )

    @staticmethod
    def itemList():
        return globals_.Area.entrances

    def createNew(self):
        return EntranceItem(self.objx, self.objy, *(field for field in self.fields))


class EntranceItem(LevelEditorItem):
    """
    Level editor item that represents an entrance
    """
    instanceDef = InstanceDefinition_EntranceItem
    BoundingRect = QtCore.QRectF(0, 0, 24, 24)
    RoundedRect = QtCore.QRectF(1, 1, 22, 22)
    EntranceImages = None

    class AuxEntranceItem(QtWidgets.QGraphicsItem):
        """
        Auxiliary item for drawing entrance things
        """
        BoundingRect = QtCore.QRectF(0, 0, 24, 24)

        def __init__(self, parent):
            """
            Initializes the auxiliary entrance thing
            """
            super().__init__(parent)
            self.parent = cast(EntranceItem, parent)
            self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, True)
            self.setParentItem(parent)
            self.hover = False

        def TypeChange(self):
            """
            Handles type changes to the entrance
            """
            if self.parent.enttype == 20:
                # Jumping facing right
                self.setPos(0, -276)
                self.BoundingRect = QtCore.QRectF(0, 0, 98, 300)
            elif self.parent.enttype == 21:
                # Vine
                self.setPos(-12, -240)
                self.BoundingRect = QtCore.QRectF(0, 0, 48, 696)
            elif self.parent.enttype == 24:
                # Jumping facing left
                self.setPos(-74, -276)
                self.BoundingRect = QtCore.QRectF(0, 0, 98, 300)
            elif self.parent.enttype in (3, 4, 5, 6) and ((self.parent.entsettings & 4) != 0):
                # Forward pipe
                idx = self.parent.enttype - 3
                exit_pos = [
                    (0, 144), # Up
                    (0, -144), # Down
                    (120, 24), # Left
                    (-144, 24), # Right
                ]
                self.setPos(exit_pos[idx][0], exit_pos[idx][1])
                self.BoundingRect = QtCore.QRectF(0, 0, 48, 48)
            else:
                self.setPos(0, 0)
                self.BoundingRect = QtCore.QRectF(0, 0, 24, 24)

        def paint(self, painter, option, widget = ...):
            """
            Paints the entrance aux
            """
            if not painter or not option or not SLib.OutlinePen or not globals_.theme:
                return

            painter.setClipRect(option.exposedRect)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

            if self.parent.enttype == 20:
                # Jumping facing right

                path = QtGui.QPainterPath(QtCore.QPointF(12, 276))
                path.cubicTo(QtCore.QPointF(40, -24), QtCore.QPointF(50, -24), QtCore.QPointF(60, 36))
                path.lineTo(QtCore.QPointF(96, 300))

                painter.setPen(SLib.OutlinePen)
                painter.drawPath(path)

            elif self.parent.enttype == 21:
                # Vine

                # Draw the top half
                painter.setOpacity(1)
                painter.drawPixmap(0, 0, SLib.ImageCache['VineTop'])
                painter.drawTiledPixmap(12, 48, 24, 168, SLib.ImageCache['VineMid'])
                # Draw the bottom half
                # This is semi-transparent because you can't interact with it.
                painter.setOpacity(0.5)
                painter.drawTiledPixmap(12, 216, 24, 456, SLib.ImageCache['VineMid'])
                painter.drawPixmap(12, 672, SLib.ImageCache['VineBtm'])

            elif self.parent.enttype == 24:
                # Jumping facing left

                path = QtGui.QPainterPath(QtCore.QPointF(86, 276))
                path.cubicTo(QtCore.QPointF(58, -24), QtCore.QPointF(48, -24), QtCore.QPointF(38, 36))
                path.lineTo(QtCore.QPointF(2, 300))

                painter.setPen(SLib.OutlinePen)
                painter.drawPath(path)

            elif self.parent.enttype in (3, 4, 5, 6) and ((self.parent.entsettings & 4) != 0):
                # Forward pipe
                painter.setBrush(QtGui.QBrush(globals_.theme.color('entrance_fill')))
                color = globals_.theme.color('entrance_lines')
                if color is not None:
                    painter.setPen(QtGui.QPen(color, 2))

                painter.drawEllipse(4, 4, 40, 40)

        def boundingRect(self):
            """
            Required by Qt
            """
            return self.BoundingRect

    def __init__(self, x, y, id, destarea, destentrance, type, zone, layer, path, settings, leave_level_val, cpd):
        """
        Creates an entrance with specific data
        """
        if EntranceItem.EntranceImages is None:
            ei = []
            src = QtGui.QPixmap(os.path.join('reggiedata', 'entrances.png'))
            for i in range(18):
                ei.append(src.copy(i * 24, 0, 24, 24))
            EntranceItem.EntranceImages = ei

        LevelEditorItem.__init__(self)
        if globals_.CursorMode != 0:
            self.setAcceptHoverEvents(True)

        self.font = globals_.NumberFont
        self.objx = x
        self.objy = y
        self.entid = id
        self.destarea = destarea
        self.destentrance = destentrance
        self.enttype = type
        self.entzone = zone
        self.entsettings = settings
        self.entlayer = layer
        self.entpath = path
        self.listitem = None
        self.leave_level = (leave_level_val != 0)
        self.cpdirection = cpd
        self.LevelRect = QtCore.QRectF(self.objx / 16, self.objy / 16, 1.5, 1.5)

        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, not globals_.EntrancesFrozen)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, not globals_.EntrancesFrozen)

        self.aux = self.AuxEntranceItem(self)

        globals_.DirtyOverride += 1
        self.setPos(int(x * 1.5), int(y * 1.5))
        globals_.DirtyOverride -= 1

        self.setZValue(27000)
        self.UpdateTooltip()
        self.UpdateRects()

    def UpdateTooltip(self):
        """
        Updates the entrance object's tooltip
        """
        if self.enttype >= len(globals_.EntranceTypeNames):
            name = globals_.trans.string('Entrances', 1)
        else:
            name = globals_.EntranceTypeNames[self.enttype]

        if (self.entsettings & 0x80) != 0:
            destination = globals_.trans.string('Entrances', 2)
        elif self.leave_level:
            destination = globals_.trans.string('Entrances', 7)
        elif self.destarea == 0:
            destination = globals_.trans.string('Entrances', 3, '[id]', self.destentrance)
        else:
            destination = globals_.trans.string('Entrances', 4, '[id]', self.destentrance, '[area]', self.destarea)

        self.name = name
        self.destination = destination
        self.setToolTip(globals_.trans.string('Entrances', 0, '[ent]', self.entid, '[type]', name, '[dest]', destination))

    def ListString(self):
        """
        Returns a string that can be used to describe the entrance in a list
        """
        if self.enttype >= len(globals_.EntranceTypeNames):
            name = globals_.trans.string('Entrances', 1)
        else:
            name = globals_.EntranceTypeNames[self.enttype]

        if (self.entsettings & 0x80) != 0:
            return globals_.trans.string('Entrances', 5, '[id]', self.entid, '[name]', name, '[x]', self.objx, '[y]', self.objy)
        else:
            return globals_.trans.string('Entrances', 6, '[id]', self.entid, '[name]', name, '[x]', self.objx, '[y]', self.objy)

    def __lt__(self, other):
        return self.entid < other.entid

    def UpdateRects(self):
        """
        Updates the rectangles associated with this entrance.
        """
        # Determine the size and position of the entrance
        x, y, w, h = 0, 0, 1, 1
        if self.enttype in (0, 1):
            # Standing entrance
            x, w = -2.25, 5.5
        elif self.enttype in (3, 4):
            # Vertical pipe
            w = 2
        elif self.enttype in (5, 6):
            # Horizontal pipe
            h = 2

        # Now make the rects
        self.RoundedRect = QtCore.QRectF((x * 24) + 1, (y * 24) + 1, (w * 24) - 2, (h * 24) - 2)
        self.BoundingRect = QtCore.QRectF(x * 24, y * 24, w * 24, h * 24)
        self.LevelRect = QtCore.QRectF(x + (self.objx / 16), y + (self.objy / 16), w, h)

        # Update the aux thing
        self.aux.TypeChange()

    def TypeChange(self):
        """
        Handles the entrance's type changing. This updates the associated
        rectangles and redraws the scene and level overview.
        """
        old_rect = self.getFullRect()

        self.UpdateRects()

        # Update the scene and level overview
        if globals_.mainWindow is not None:
            globals_.mainWindow.scene.update(old_rect.united(self.getFullRect()))
            globals_.mainWindow.level_overview.update()

    def paint(self, painter, option, widget = ...):
        """
        Paints the entrance
        """
        if not painter or not option or not globals_.theme or not self.font:
            return

        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(globals_.theme.color('entrance_fill_s')))
            painter.setPen(QtGui.QPen(globals_.theme.color('entrance_lines_s')))
        else:
            painter.setBrush(QtGui.QBrush(globals_.theme.color('entrance_fill')))
            painter.setPen(QtGui.QPen(globals_.theme.color('entrance_lines')))

        if globals_.UseRoundedRectangles:
            painter.drawRoundedRect(self.RoundedRect, 4, 4)
        else:
            painter.drawRect(self.RoundedRect)

        icon_type = 0
        ent_type = self.enttype

        ent_types = [
            1,  # 0: Normal
            1,  # 1: ^
            2,  # 2: Door Exit
            4,  # 3: Pipe Up
            5,  # 4: Pipe Down
            6,  # 5: Pipe Left
            7,  # 6: Pipe Right
            0,  # 7
            12, # 8: Ground Pound
            13, # 9: Sliding
            0, 0, 0, # 10, 11, 12
            0, 0, 0, # 13, 14, 15
            8,  # 16: Mini Pipe Up
            9,  # 17: Mini Pipe Down
            10, # 18: Mini Pipe Up
            11, # 19: Mini Pipe Left
            15, # 20: Mini Pipe Right
            17, # 21: Vine
            0,  # 22
            14, # 23: Boss Entrance
            16, # 24: Jump Left
            0, 0, # 25, 26
            3,  # 27: Door Entrance
            0, 0, # 28, 29
        ]
        icon_type = ent_types[ent_type]

        imgs = EntranceItem.EntranceImages
        if imgs is not None:
            painter.drawPixmap(0, 0, imgs[icon_type])

        painter.setFont(self.font)
        painter.drawText(3, 12, str(self.entid))

    def delete(self):
        """
        Delete the entrance from the level
        """
        if globals_.mainWindow is None:
            return

        elist = globals_.mainWindow.entranceList
        globals_.mainWindow.UpdateFlag = True
        elist.takeItem(elist.row(self.listitem))
        globals_.mainWindow.UpdateFlag = False

        sel_model = elist.selectionModel()
        if sel_model is not None:
            sel_model.clearSelection()

        globals_.Area.entrances.remove(self)
        scene = self.scene()
        if scene is not None:
            scene.update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())

        setOverrideCursor(None)

    def itemChange(self, change, value):
        """
        Handle movement
        """
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Make sure the bounding rect and level rects are updated, as well
            # as the scene and level overview. The TypeChange function already
            # takes care of this, so we can just call that function.
            self.TypeChange()

        return super().itemChange(change, value)

    def getFullRect(self):
        """
        Returns a rectangle that contains the entrance and any
        auxiliary objects.
        """

        br = self.BoundingRect | self.aux.BoundingRect.translated(self.aux.pos())

        return br.translated(self.pos())

    def hoverMoveEvent(self, event):
        LevelEditorItem.hoverMoveEvent(self, event)
        if (self.isSelected() or globals_.CursorMode == 2) and not globals_.EntrancesFrozen:
            setOverrideCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        LevelEditorItem.hoverLeaveEvent(self, event)
        setOverrideCursor(None)
