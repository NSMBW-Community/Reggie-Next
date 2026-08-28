from typing import cast

from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
import spritelib as SLib
from src.data.common.utils import clamp
from src.data.level.dirty import SetDirty
from src.data.level.items.basic import InstanceDefinition, LevelEditorItem
from src.data.level.items.object import ObjectItem
from src.ui.actions.undo.move_item import MoveItemUndoAction
from src.ui.theme.reggie_theme import setOverrideCursor


class InstanceDefinition_SpriteItem(InstanceDefinition):
    """
    Definition of an instance of SpriteItem
    """
    fieldNames = (
        'type',
        'spritedata',
    )

    @staticmethod
    def itemList():
        return globals_.Area.sprites

    def createNew(self):
        return SpriteItem(self.fields[0][1], self.objx, self.objy, self.fields[1][1])


class SpriteItem(LevelEditorItem):
    """
    Level editor item that represents a sprite
    """
    instanceDef = InstanceDefinition_SpriteItem
    BoundingRect = QtCore.QRectF(0, 0, 24, 24)
    SelectionRect = QtCore.QRectF(0, 0, 23, 23)

    def __init__(self, sprite_num, x, y, data):
        """
        Creates a sprite with specific data
        """
        LevelEditorItem.__init__(self)
        self.setZValue(26000)
        if globals_.CursorMode != 0:
            self.setAcceptHoverEvents(True)

        self.font = globals_.NumberFont
        self.sprite_num = sprite_num
        self.objx = x
        self.objy = y
        self.spritedata = data
        self.LevelRect = QtCore.QRectF(self.objx / 16, self.objy / 16, 1.5, 1.5)
        self.ChangingPos = False

        self.ImageObj = SLib.SpriteImage(self)

        if 0 <= sprite_num < globals_.NumSprites:
            self.name = globals_.Sprites[sprite_num].name
        else:
            self.name = globals_.trans.string('Sprites', 24)

        self.InitializeSprite()

        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, not globals_.SpritesFrozen)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, not globals_.SpritesFrozen)

        globals_.DirtyOverride += 1
        if globals_.SpriteImagesShown:
            self.setPos(
                (self.objx + self.ImageObj.xOffset) * 1.5,
                (self.objy + self.ImageObj.yOffset) * 1.5,
            )
        else:
            self.setPos(
                self.objx * 1.5,
                self.objy * 1.5,
            )
        globals_.DirtyOverride -= 1

    def SetType(self, sprite_num):
        """
        Sets the type of the sprite
        """
        if 0 <= sprite_num < globals_.NumSprites:
            self.name = globals_.Sprites[sprite_num].name
        else:
            self.name = globals_.trans.string('Sprites', 24) # 'UNKNOWN'

        self.setToolTip(globals_.trans.string('Sprites', 0, '[type]', sprite_num, '[name]', self.name))
        self.sprite_num = sprite_num

        self.InitializeSprite()
        self.UpdateListItem()

    def __lt__(self, other):
        # Sort by objx, then objy, then sprite type
        score = lambda sprite: (sprite.objx, sprite.objy, sprite.type)

        return score(self) < score(other)

    def InitializeSprite(self):
        """
        Initializes sprite and creates any auxiliary objects needed
        """
        sprite_num = self.sprite_num

        if not 0 <= sprite_num < globals_.NumSprites:
            return

        self.name = globals_.Sprites[sprite_num].name
        self.setToolTip(globals_.trans.string('Sprites', 0, '[type]', self.sprite_num, '[name]', self.name))

        imgs = globals_.gamedef.getImageClasses()
        if sprite_num in imgs:
            self.setImageObj(imgs[sprite_num])

    def setImageObj(self, obj):
        """
        Sets a new sprite image object for this SpriteItem
        """
        for aux_obj in self.ImageObj.aux:
            aux_obj = cast(SLib.AuxiliarySpriteItem, aux_obj)
            scene = aux_obj.scene()

            if scene is not None:
                scene.removeItem(aux_obj)

        self.setZValue(26000)
        self.resetTransform()

        if (self.sprite_num in globals_.gamedef.getImageClasses()) and (self.sprite_num not in SLib.SpriteImagesLoaded):
            globals_.gamedef.getImageClasses()[self.sprite_num].loadImages()
            SLib.SpriteImagesLoaded.add(self.sprite_num)

        self.ImageObj = obj(self) if obj else SLib.SpriteImage(self)

        # show auxiliary objects properly
        for aux in self.ImageObj.aux:
            aux = cast(SLib.AuxiliarySpriteItem, aux)
            aux.setVisible(globals_.SpriteImagesShown)

        self.UpdateDynamicSizing()

    def UpdateDynamicSizing(self):
        """
        Updates the sizes for dynamically sized sprites
        """
        curr_rect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        curr_aux_rects = []
        for aux_obj in self.ImageObj.aux:
            aux_obj = cast(SLib.AuxiliarySpriteItem, aux_obj)

            curr_aux_rects.append(QtCore.QRectF(
                aux_obj.x() + self.x(),
                aux_obj.y() + self.y(),
                aux_obj.boundingRect().width(),
                aux_obj.boundingRect().height(),
            ))

        self.ImageObj.dataChanged()

        if globals_.SpriteImagesShown:
            self.UpdateRects()
            self.ChangingPos = True
            self.setPos(
                (self.objx + self.ImageObj.xOffset) * 1.5,
                (self.objy + self.ImageObj.yOffset) * 1.5,
            )
            self.ChangingPos = False

        scene = self.scene()
        if scene is not None:
            scene.update(curr_rect)
            scene.update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
            for auxUpdateRect in curr_aux_rects:
                scene.update(auxUpdateRect)

    def UpdateRects(self):
        """
        Creates all the rectangles for the sprite
        """
        self.prepareGeometryChange()

        # Get rects
        imgRect = QtCore.QRectF(
            0, 0,
            self.ImageObj.width * 1.5,
            self.ImageObj.height * 1.5,
        )
        spriteboxRect = QtCore.QRectF(
            0, 0,
            self.ImageObj.spritebox.BoundingRect.width(),
            self.ImageObj.spritebox.BoundingRect.height(),
        )
        imgOffsetRect = imgRect.translated(
            (self.objx + self.ImageObj.xOffset) * 1.5,
            (self.objy + self.ImageObj.yOffset) * 1.5,
        )
        spriteboxOffsetRect = spriteboxRect.translated(
            (self.objx * 1.5) + self.ImageObj.spritebox.BoundingRect.topLeft().x(),
            (self.objy * 1.5) + self.ImageObj.spritebox.BoundingRect.topLeft().y(),
        )

        if globals_.SpriteImagesShown:
            unitedRect = imgRect.united(spriteboxRect)

            if self.ImageObj.spritebox.shown:
                unitedOffsetRect = imgOffsetRect.united(spriteboxOffsetRect)
            else:
                unitedOffsetRect = imgOffsetRect

            # SelectionRect: Used to determine the size of the
            # "this sprite is selected" translucent white box that
            # appears when a sprite with an image is selected.
            self.SelectionRect = QtCore.QRectF(
                0.5, 0.5,
                imgRect.width() - 1,
                imgRect.height() - 1,
            )

            # LevelRect: Used by the Level Overview to determine
            # the size and position of the sprite in the level.
            # Measured in blocks.
            self.LevelRect = QtCore.QRectF(
                unitedOffsetRect.topLeft() / 24,
                unitedOffsetRect.size() / 24,
            )

            # BoundingRect: The sprite can only paint within
            # this area.
            self.BoundingRect = unitedRect.translated(
                self.ImageObj.spritebox.BoundingRect.topLeft()
            )

        else:
            self.SelectionRect = QtCore.QRectF(0.5, 0.5, 23, 23)

            self.LevelRect = QtCore.QRectF(
                spriteboxOffsetRect.topLeft() / 24,
                spriteboxOffsetRect.size() / 24,
            )

            # BoundingRect: The sprite can only paint within
            # this area.
            self.BoundingRect = self.ImageObj.spritebox.BoundingRect

    def getFullRect(self):
        """
        Returns a rectangle that contains the sprite and all
        auxiliary objects.
        """
        self.UpdateRects()

        br = self.BoundingRect.translated(
            self.x(),
            self.y(),
        )
        for aux in self.ImageObj.aux:
            aux = cast(SLib.AuxiliarySpriteItem, aux)

            br = br.united(
                aux.boundingRect().translated(
                    aux.x() + self.x(),
                    aux.y() + self.y(),
                )
            )

        return br

    def itemChange(self, change, value):
        """
        Makes sure positions don't go out of bounds and updates them as necessary
        """

        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene = self.scene()
            if scene is None or globals_.mainWindow is None:
                return value

            if self.ChangingPos:
                return value

            # The sprite image offset as a point
            if globals_.SpriteImagesShown:
                offset_point = QtCore.QPointF(*self.ImageObj.getOffset())
            else:
                offset_point = QtCore.QPointF()

            # Convert the new position from 24 units per block into 16 units per
            # block
            new_pos = value / 1.5

            # Move the position to sprite origin space by subtracting the image
            # offset
            origin_pos = (new_pos - offset_point).toPoint()

            # Snap this position to the grid
            drag_offset = None
            if globals_.OverrideSnapping or QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
                # Snap the smallest amount possible -> 1/16th of a block
                snap_level = 1
            elif self.isSelected() and len(globals_.mainWindow.CurrentSelection) > 1:
                objects_selected = any(isinstance(x, ObjectItem) for x in globals_.mainWindow.CurrentSelection)

                # dragoffsetx and y are in 24 = 1 block units, so convert it to
                # 16 = 1 block units
                drag_offset = QtCore.QPointF(self.dragoffsetx, self.dragoffsety) / 1.5

                origin_pos = (QtCore.QPointF(origin_pos) + drag_offset).toPoint()

                if objects_selected:
                    # Snap to full blocks (16/16)
                    snap_level = 16
                else:
                    # Snap to half blocks, but adjust for drag offset
                    snap_level = 8

            else:
                # Snap to half-blocks (8/16)
                snap_level = 8

            # Make sure the position is in bounds
            x = clamp(origin_pos.x(), 0, 16368)
            y = clamp(origin_pos.y(), 0, 8176)

            # When snapping, round to the nearest multiple of snap_level. Round
            # up when two multiples are equally far apart.
            origin_pos.setX(int((x + (snap_level / 2)) // snap_level) * snap_level)
            origin_pos.setY(int((y + (snap_level / 2)) // snap_level) * snap_level)

            if drag_offset is not None:
                origin_pos = (QtCore.QPointF(origin_pos) - drag_offset).toPoint()

            # Move position back to sprite image space by adding the image offset
            # and calculate objx and objy based on the sprite origin position.
            new_pos = QtCore.QPointF(QtCore.QPointF(origin_pos) + offset_point) * 1.5

            x = origin_pos.x()
            y = origin_pos.y()

            if x != self.objx or y != self.objy:
                updRect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
                scene.update(updRect)

                self.LevelRect.moveTo(new_pos / 24)

                for aux_obj in self.ImageObj.aux:
                    aux_obj = cast(SLib.AuxiliarySpriteItem, aux_obj)

                    update_rect = QtCore.QRectF(
                        self.pos() + aux_obj.pos(),
                        aux_obj.boundingRect().size(),
                    )
                    scene.update(update_rect)

                scene.update(
                    self.ImageObj.spritebox.BoundingRect.translated(self.pos())
                )

                oldx = self.objx
                oldy = self.objy
                self.objx = x
                self.objy = y
                if self.positionChanged is not None:
                    self.positionChanged(self, oldx, oldy, x, y)

                # Add moving this sprite to the undo stack.
                if len(globals_.mainWindow.CurrentSelection) == 1:
                    act = MoveItemUndoAction(self, oldx, oldy, x, y)
                    globals_.mainWindow.undoStack.addOrExtendAction(act)
                elif len(globals_.mainWindow.CurrentSelection) > 1:
                    pass

                self.ImageObj.positionChanged()

                SetDirty()

            return new_pos

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def setNewObjPos(self, newobjx, newobjy):
        """
        Sets a new position, through objx and objy
        """
        self.objx, self.objy = newobjx, newobjy

        if globals_.SpriteImagesShown:
            newobjx += self.ImageObj.xOffset
            newobjy += self.ImageObj.yOffset

        self.setPos(newobjx * 1.5, newobjy * 1.5)

    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for cloning
        """
        if not event or not globals_.mainWindow:
            return

        if event.button() != QtCore.Qt.MouseButton.LeftButton or QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.KeyboardModifier.ControlModifier:
            old_pos = (self.objx, self.objy)

            LevelEditorItem.mousePressEvent(self, event)

            if not globals_.SpriteImagesShown:
                self.setNewObjPos(*old_pos)

            return

        globals_.mainWindow.CreateSprite(self.objx, self.objy, self.sprite_num, self.spritedata)
        globals_.mainWindow.scene.clearSelection()
        self.setSelected(True)

    def hoverMoveEvent(self, event):
        LevelEditorItem.hoverMoveEvent(self, event)
        if (self.isSelected() or globals_.CursorMode == 2) and not globals_.SpritesFrozen:
            setOverrideCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        LevelEditorItem.hoverLeaveEvent(self, event)
        setOverrideCursor(None)

    def nearestZone(self, obj=False):
        """
        Calls a modified MapPositionToZoneID (if obj = True, it returns the
        actual ZoneItem object). If the area is not fully loaded yet, or there
        are no zones, it returns None.
        """
        if not hasattr(globals_.Area, 'zones'):
            return None

        zone_idx = SLib.MapPositionToZoneID(globals_.Area.zones, self.objx, self.objy)

        if zone_idx == -1:
            return None

        zone_obj = globals_.Area.zones[zone_idx]

        return zone_obj if obj else zone_obj.id

    def updateScene(self):
        """
        Calls self.scene().update()
        """
        # Some of the more advanced painters need to update the whole scene
        # and this is a convenient way to do it:
        # self.parent.updateScene()
        scene = self.scene()
        if scene is not None:
            scene.update()

    def paint(self, painter: QtGui.QPainter | None, option: 'QtWidgets.QStyleOptionGraphicsItem | None'=None,
              widget: QtWidgets.QWidget | None=None, overrideGlobals=False):
        """
        Paints the sprite
        """
        if not painter or not self.font:
            return

        # Setup stuff
        if option is not None:
            painter.setClipRect(option.exposedRect)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Turn aux things on or off
        for aux in self.ImageObj.aux:
            aux = cast(SLib.AuxiliarySpriteItem, aux)
            aux.setVisible(globals_.SpriteImagesShown)

        # Default spritebox
        drawSpritebox = True
        spriteboxRect = QtCore.QRectF(1, 1, 22, 22)

        if globals_.SpriteImagesShown or overrideGlobals:
            self.ImageObj.paint(painter)

            drawSpritebox = self.ImageObj.spritebox.shown

            # Draw the selected-sprite-image overlay box
            if self.isSelected() and (not drawSpritebox or self.ImageObj.size != (16, 16)):
                color = globals_.theme.color('sprite_lines_s')
                if color is not None:
                    painter.setPen(QtGui.QPen(color, 1, QtCore.Qt.PenStyle.DashLine))
                painter.drawRect(self.SelectionRect)
                color = globals_.theme.color('sprite_fill_s')
                if color is not None:
                    painter.fillRect(self.SelectionRect, color)

            # Determine the spritebox position
            if drawSpritebox:
                spriteboxRect = self.ImageObj.spritebox.RoundedRect

        # Draw the spritebox if applicable
        if drawSpritebox:
            if self.isSelected():
                painter.setBrush(QtGui.QBrush(globals_.theme.color('spritebox_fill_s')))
                color = globals_.theme.color('spritebox_lines_s')
                if color is not None:
                    painter.setPen(QtGui.QPen(color, 1))
            else:
                painter.setBrush(QtGui.QBrush(globals_.theme.color('spritebox_fill')))
                color = globals_.theme.color('spritebox_lines')
                if color is not None:
                    painter.setPen(QtGui.QPen(color, 1))

            if globals_.UseRoundedRectangles:
                painter.drawRoundedRect(spriteboxRect, 4, 4)
            else:
                painter.drawRect(spriteboxRect)

            painter.setFont(self.font)
            painter.drawText(spriteboxRect, QtCore.Qt.AlignmentFlag.AlignCenter, str(self.sprite_num))

    def scene(self):
        """
        Solves a small bug
        """
        if globals_.mainWindow is not None:
            return globals_.mainWindow.scene

    def delete(self):
        """
        Delete the sprite from the level
        """
        if globals_.mainWindow is None:
            return

        self.ImageObj.remove()
        globals_.mainWindow.UpdateFlag = True
        globals_.mainWindow.spriteList.takeSprite(self)
        globals_.mainWindow.UpdateFlag = False

        sel_model = globals_.mainWindow.spriteList.selectionModel()
        if sel_model is not None:
            sel_model.clearSelection()
        globals_.Area.RemoveSprite(self)

        # The zone painters need for the whole thing to update
        scene = self.scene()
        if scene is not None:
            scene.update()

        setOverrideCursor(None)
