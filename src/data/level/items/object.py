import os
import random

from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
from src.data.common.utils import clamp
from src.data.level.dirty import SetDirty
from src.data.level.items.abstract_object import AbstractObjectItem
from src.data.level.items.basic import InstanceDefinition, LevelEditorItem
from src.data.tileset.object.renderers import RenderObject
from src.ui.actions.undo.move_item import MoveItemUndoAction
from src.ui.theme.reggie_theme import setOverrideCursor


class InstanceDefinition_ObjectItem(InstanceDefinition):
    """
    Definition of an instance of ObjectItem
    """

    fieldNames = (
        "tileset",
        "type",
        "layer",
        "width",
        "height",
    )

    @staticmethod
    def itemList():
        # List concatenation here
        return (
            globals_.Area.layers[0] + globals_.Area.layers[1] + globals_.Area.layers[2]
        )

    def createNew(self):
        if not self.objx or not self.objy:
            self.objx = 0
            self.objy = 0

        return ObjectItem(
            self.fields[0][1],
            self.fields[1][1],
            self.fields[2][1],
            self.objx,
            self.objy,
            self.fields[3][1],
            self.fields[4][1],
            1,
        )


class ObjectItem(LevelEditorItem, AbstractObjectItem):
    """
    Level editor item that represents an ingame object
    """
    instanceDef = InstanceDefinition_ObjectItem

    def __init__(self, tileset: int, object_num: int, layer: int, x: int, y: int, width: int, height: int, z: int):
        """
        Creates an object with specific data
        """
        LevelEditorItem.__init__(self)
        if globals_.CursorMode != 0:
            self.setAcceptHoverEvents(True)

        self.tileset = tileset
        self.object_num = object_num
        self.objx = x
        self.objy = y
        self.layer = layer
        self.width = width
        self.height = height
        self.objdata = None

        self.wasExtended = False

        self.TLGrabbed = self.TRGrabbed = self.BLGrabbed = self.BRGrabbed = False
        self.MTGrabbed = self.MLGrabbed = self.MBGrabbed = self.MRGrabbed = False

        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, not globals_.ObjectsFrozen)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, not globals_.ObjectsFrozen)

        self.UpdateRects()

        self.dragging = False
        self.dragstartx = -1
        self.dragstarty = -1
        self.objsDragging = {}

        globals_.DirtyOverride += 1
        self.setPos(x * 24, y * 24)
        globals_.DirtyOverride -= 1

        self.setZValue(z)

        if layer == 0:
            self.setVisible(globals_.Layer0Shown)
        elif layer == 1:
            self.setVisible(globals_.Layer1Shown)
        elif layer == 2:
            self.setVisible(globals_.Layer2Shown)

        self.updateObjCache()
        self.UpdateTooltip()

    def SetType(self, tileset, object_num):
        """
        Sets the type of the object
        """
        self.tileset = tileset
        self.object_num = object_num
        self.updateObjCache()
        self.update()

        self.UpdateTooltip()

    def UpdateTooltip(self):
        """
        Updates the tooltip
        """
        self.setToolTip(
            globals_.trans.string('Objects', 0, '[tileset]', self.tileset + 1, '[obj]', self.object_num, '[width]', self.width,
                         '[height]', self.height, '[layer]', self.layer))

    def updateObjCache(self):
        """
        Updates the rendered object data
        """
        self.objdata = RenderObject(self.tileset, self.object_num, self.width, self.height)
        self.randomise()

    def isBottomRowSpecial(self):
        """
        Returns whether the bottom row of self.objdata contains the special
        vdouble top tile.
        """
        if globals_.TilesetFilesLoaded[self.tileset] is None or not len(globals_.TilesetInfo):
            # No randomisation info -> false
            return False

        name = self.get_tileset_base_name()

        if name not in globals_.TilesetInfo:
            # Tileset not randomised -> false
            return False

        tileset_info = globals_.TilesetInfo[name]

        for x in range(self.width):
            # Get the special data for this tile
            if self.objdata is None:
                return

            tile = self.objdata[-1][x] & 0xFF

            tile_selection = tileset_info.get(tile)
            if tile_selection is None:
                # Tile not randomised -> continue with next position
                continue

            if tile_selection.special & 0b01:
                return True

        return False

    def randomise(self, startx=0, starty=0, width=None, height=None):
        """
        Randomises (a part of) the self.objdata according to the loaded tileset
        info
        """
        # TODO: Make the code that prevents two identical tiles next to each
        # other work even on the edges of the object. This requires a function
        # that returns the tile on the block next to the current tile on a
        # specified layer. Maybe something for the Area class?

        if not len(globals_.TilesetInfo) or globals_.TilesetFilesLoaded[self.tileset] is None:
            # no randomisation info -> exit
            return

        if self.objdata is None:
            return

        obj_def = globals_.ObjectDefinitions[self.tileset][self.object_num]
        if obj_def is None:
            return

        if globals_.ObjectDefinitions[self.tileset][self.object_num] is None or len(obj_def.rows[0][0]) == 1:
            # Slope -> exit
            return

        name = self.get_tileset_base_name()

        if name not in globals_.TilesetInfo:
            # Tileset not randomised -> exit
            return

        tileset_info = globals_.TilesetInfo.get(name)
        if tileset_info is None:
            return

        if width is None:
            width = self.width

        if height is None:
            height = self.height

        # Randomise every tile in this region
        for y in range(starty, starty + height):
            for x in range(startx, startx + width):
                # Should we randomise this tile?
                tile = self.objdata[y][x] & 0xFF

                tile_selection = tileset_info.get(tile)
                if tile_selection is None:
                    # Tile not randomised -> continue with next position
                    continue

                # If the special indicates the top, don't randomise it now, but
                # randomise it when we come across the bottom.
                if tile_selection.special & 0b01:
                    continue

                tiles_ = tile_selection.tiles[:]

                # Take direction into account - chosen tile must be different from
                # the tile to the left/top. Using try/except here so the value has
                # to be looked up only once.

                # direction is 2 bits:
                # highest := vertical direction; lowest := horizontal direction
                if tile_selection.direction & 0b01 and x > 0:
                    # only look at the left neighbour, since we will generate the
                    # right neighbour later
                    try:
                        tiles_.remove(self.objdata[y][x-1] & 0xFF)
                    except ValueError:
                        pass

                if tile_selection.direction & 0b10 and y > 0:
                    # Only look at the above neighbour, since we will generate the
                    # neighbour below later
                    try:
                        tiles_.remove(self.objdata[y-1][x] & 0xFF)
                    except ValueError:
                        pass

                # If we removed all options, just use the original tiles
                if not tiles_:
                    tiles_ = tile_selection.tiles

                choice = (self.tileset << 8) | random.choice(tiles_)
                self.objdata[y][x] = choice

                # Bottom of special, so change the tile above to the tile in the
                # previous row of the tileset image (at offset choice - 0x10).
                if tile_selection.special & 0b10:
                    if y > 0:
                        self.objdata[y - 1][x] = choice - 0x10
                    else:
                        # y is equal to 0. When this happens in-game, the game
                        # just changes the tile above (even if it's 'air') to
                        # (choice - 0x10).

                        # TODO: faking that here would mean decreasing the y position
                        # and increasing the height of this object and its boundingrect
                        # by 1, then adding a new row to self.objdata at the top,
                        # then placing the choice there, and finally updating the
                        # z position to be greater than that of the object(s) above.

                        # tl;dr: A lot of work to properly implement this.
                        pass

    def get_tileset_base_name(self):
        """
        Returns the bare file name of the tileset file this object uses. This
        file name has all extensions ('.arc' or '.arc.LH') removed.
        """
        tileset_path = globals_.TilesetFilesLoaded[self.tileset]
        if tileset_path is None:
            return None

        filename = os.path.splitext(os.path.basename(tileset_path))[0]

        if "." in filename:
            # The tileset file is probably LH-compressed.
            filename = os.path.splitext(filename)[0]

        return filename

    def updateObjCacheWH(self, width, height):
        """
        Updates the rendered object data with custom width and height
        """
        obj_def = globals_.ObjectDefinitions[self.tileset][self.object_num]
        if obj_def is None:
            return

        # If we don't have to randomise, simply rerender everything
        if globals_.TilesetFilesLoaded[self.tileset] is None \
           or not len(globals_.TilesetInfo) \
           or globals_.ObjectDefinitions is None \
           or globals_.ObjectDefinitions[self.tileset] is None \
           or obj_def is None \
           or obj_def.rows is None \
           or obj_def.rows[0] is None \
           or obj_def.rows[0][0] is None \
           or len(obj_def.rows[0][0]) == 1:
            # No randomisation info -> exit
            save = (self.width, self.height)
            self.width, self.height = width, height
            self.updateObjCache()
            self.width, self.height = save
            return

        name = self.get_tileset_base_name()
        tile = obj_def.rows[0][0][1] & 0xFF

        if name not in globals_.TilesetInfo or tile not in globals_.TilesetInfo[name]:
            # No randomisation needed -> exit
            save = (self.width, self.height)
            self.width, self.height = width, height
            self.updateObjCache()
            self.width, self.height = save
            return

        if width == self.width and height == self.height:
            # Width and height did not change, so there is nothing to do
            return

        if self.objdata is None:
            return

        if height < self.height:
            self.objdata = self.objdata[:height]
        elif height > self.height:
            # Add extra rows at the bottom
            if self.isBottomRowSpecial():
                # Re-render the bottom row as well
                self.objdata = self.objdata[:-1]
                self.height -= 1

            self.objdata += RenderObject(self.tileset, self.object_num, self.width, height - self.height)
            self.randomise(0, self.height, self.width, height - self.height)

        if width < self.width:
            for y in range(len(self.objdata)):
                self.objdata[y] = self.objdata[y][:width]
        elif width > self.width:
            new = RenderObject(self.tileset, self.object_num, width - self.width, height)
            for y in range(len(self.objdata)):
                self.objdata[y] += new[y]
            self.randomise(self.width, 0, width - self.width, height)

    def UpdateRects(self):
        """
        Recreates the bounding and selection rects
        """
        self.prepareGeometryChange()
        self.BoundingRect = QtCore.QRectF(0, 0, 24 * self.width, 24 * self.height)
        self.SelectionRect = self.BoundingRect - QtCore.QMarginsF(0.5, 0.5, 0.5, 0.5)

        # Make sure the grabbers don't overlap
        size = min(4.8 + self.width * self.height * 0.01, min(self.width, self.height) * 24 / 3 - 1)

        corner_offset_width = 24 * self.width - size
        corner_offset_height = 24 * self.height - size

        self.GrabberRectTL = QtCore.QRectF(0, 0, size, size)
        self.GrabberRectTR = QtCore.QRectF(corner_offset_width, 0, size, size)

        self.GrabberRectBL = QtCore.QRectF(0, corner_offset_height, size, size)
        self.GrabberRectBR = QtCore.QRectF(corner_offset_width, corner_offset_height, size, size)

        self.GrabberRectMT = QtCore.QRectF(corner_offset_width / 2, 0, size, size)
        self.GrabberRectML = QtCore.QRectF(0, corner_offset_height / 2, size, size)
        self.GrabberRectMB = QtCore.QRectF(corner_offset_width / 2, corner_offset_height, size, size)
        self.GrabberRectMR = QtCore.QRectF(corner_offset_width, corner_offset_height / 2, size, size)

        # Create rects for the edges
        longwidth = 24 * self.width - 2 * size
        longheight = 24 * self.height - 2 * size
        self.GrabberRectMT_ = QtCore.QRectF(size, 0, longwidth, size)
        self.GrabberRectML_ = QtCore.QRectF(0, size, size, longheight)
        self.GrabberRectMB_ = QtCore.QRectF(size, longheight + size, longwidth, size)
        self.GrabberRectMR_ = QtCore.QRectF(longwidth + size, size, size, longheight)

        self.LevelRect = QtCore.QRectF(self.objx, self.objy, self.width, self.height)

    def itemChange(self, change, value):
        """
        Makes sure positions don't go out of bounds and updates them as necessary
        """
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene = self.scene()
            if scene is None or globals_.mainWindow is None:
                return value

            # Snap to 24x24
            newpos = value
            newpos.setX(int((newpos.x() + 12) / 24) * 24)
            newpos.setY(int((newpos.y() + 12) / 24) * 24)
            x = newpos.x()
            y = newpos.y()

            # Don't let it get out of the boundaries
            newpos.setX(clamp(x, 0, 24576))
            newpos.setY(clamp(y, 0, 12288))

            # Update the data
            x = int(newpos.x() / 24)
            y = int(newpos.y() / 24)
            if x != self.objx or y != self.objy:
                self.LevelRect.moveTo(x, y)

                oldx = self.objx
                oldy = self.objy
                self.objx = x
                self.objy = y
                if self.positionChanged is not None:
                    self.positionChanged(self, oldx, oldy, x, y)

                if len(globals_.mainWindow.CurrentSelection) == 1:
                    act = MoveItemUndoAction(self, oldx, oldy, x, y)
                    globals_.mainWindow.undoStack.addOrExtendAction(act)
                elif len(globals_.mainWindow.CurrentSelection) > 1:
                    pass

                SetDirty()

                scene.invalidate(self.x(), self.y(), self.width * 24, self.height * 24,
                                 QtWidgets.QGraphicsScene.SceneLayer.BackgroundLayer)

            return newpos

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def paint(self, painter, option, widget = ...):
        """
        Paints the object
        """
        if not self.isSelected():
            return

        if not painter or not globals_.theme:
            return

        color_line_s = globals_.theme.color('object_lines_s')
        color_line_r = globals_.theme.color('object_lines_r')
        if not color_line_s or not color_line_r:
            return

        painter.setPen(QtGui.QPen(color_line_s, 1, QtCore.Qt.PenStyle.DashLine))
        painter.drawRect(self.SelectionRect)

        color = globals_.theme.color('object_fill_s')
        if color is not None:
            painter.fillRect(self.SelectionRect, color)

        is_grabbed = [
            self.TLGrabbed, self.TRGrabbed,
            self.BLGrabbed, self.BRGrabbed,
            self.MTGrabbed, self.MLGrabbed,
            self.MRGrabbed, self.MBGrabbed
        ]
        grabber_rects = [
            self.GrabberRectTL, self.GrabberRectTR,
            self.GrabberRectBL, self.GrabberRectBR,
            self.GrabberRectMT, self.GrabberRectML,
            self.GrabberRectMR, self.GrabberRectMB
        ]

        for i, rect in enumerate(grabber_rects):
            if is_grabbed[i]:
                color = color_line_r
            else:
                color = color_line_s

            painter.fillRect(rect, color)

    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for resizing
        """
        if not event or not globals_.mainWindow:
            return

        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
                new_item = globals_.mainWindow.CreateObject(
                    self.tileset, self.object_num, self.layer, self.objx,
                    self.objy, self.width, self.height
                )

                # Swap the Z values so it doesn't look like the
                # cloned item is the old one
                newZ = new_item.zValue()
                new_item.setZValue(self.zValue())
                self.setZValue(newZ)

                globals_.mainWindow.scene.clearSelection()
                self.setSelected(True)

        self.TLGrabbed = self.GrabberRectTL.contains(event.pos())
        self.TRGrabbed = self.GrabberRectTR.contains(event.pos())
        self.BLGrabbed = self.GrabberRectBL.contains(event.pos())
        self.BRGrabbed = self.GrabberRectBR.contains(event.pos())
        self.MTGrabbed = self.GrabberRectMT_.contains(event.pos())
        self.MLGrabbed = self.GrabberRectML_.contains(event.pos())
        self.MBGrabbed = self.GrabberRectMB_.contains(event.pos())
        self.MRGrabbed = self.GrabberRectMR_.contains(event.pos())

        if self.isSelected() and (
            self.TLGrabbed
            or self.TRGrabbed
            or self.BLGrabbed
            or self.BRGrabbed
            or self.MTGrabbed
            or self.MLGrabbed
            or self.MBGrabbed
            or self.MRGrabbed
        ):
            # Start dragging
            self.dragging = True
            self.dragstartx = int((event.pos().x() - 10) / 24)
            self.dragstarty = int((event.pos().y() - 10) / 24)
            self.objsDragging = {}

            for selitem in globals_.mainWindow.scene.selectedItems():
                if not isinstance(selitem, ObjectItem):
                    continue

                self.objsDragging[selitem] = [selitem.width, selitem.height]

            event.accept()

        else:
            LevelEditorItem.mousePressEvent(self, event)
            self.dragging = False
            self.objsDragging = {}

        self.UpdateTooltip()
        self.update()

    def hoverEnterEvent(self, event):
        LevelEditorItem.hoverEnterEvent(self, event)
        if (self.isSelected() or globals_.CursorMode == 2) and not globals_.ObjectsFrozen:
            setOverrideCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def hoverMoveEvent(self, event):
        LevelEditorItem.hoverMoveEvent(self, event)
        if globals_.ObjectsFrozen or not event:
            return

        TLHovered = self.GrabberRectTL.contains(event.pos())
        TRHovered = self.GrabberRectTR.contains(event.pos())
        BLHovered = self.GrabberRectBL.contains(event.pos())
        BRHovered = self.GrabberRectBR.contains(event.pos())
        MTHovered = self.GrabberRectMT_.contains(event.pos())
        MLHovered = self.GrabberRectML_.contains(event.pos())
        MBHovered = self.GrabberRectMB_.contains(event.pos())
        MRHovered = self.GrabberRectMR_.contains(event.pos())

        if self.isSelected(): # Can only resize if first selected
            if MTHovered or MBHovered:
                setOverrideCursor(QtCore.Qt.CursorShape.SizeVerCursor)
            elif MLHovered or MRHovered:
                setOverrideCursor(QtCore.Qt.CursorShape.SizeHorCursor)
            elif TLHovered or BRHovered:
                setOverrideCursor(QtCore.Qt.CursorShape.SizeFDiagCursor)
            elif TRHovered or BLHovered:
                setOverrideCursor(QtCore.Qt.CursorShape.SizeBDiagCursor)
            else:
                setOverrideCursor(QtCore.Qt.CursorShape.SizeAllCursor)
        elif globals_.CursorMode == 2:
            setOverrideCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        LevelEditorItem.hoverLeaveEvent(self, event)
        setOverrideCursor(None)

    def UpdateObj(self, oldX, oldY, newSize):
        """
        Updates the object if the width/height/position has been changed
        """
        self.updateObjCacheWH(newSize[0], newSize[1])

        oldrect = self.BoundingRect
        oldrect.translate(oldX * 24, oldY * 24)

        self.width, self.height = newSize
        self.UpdateRects()

        updaterect = oldrect.united(self.BoundingRect.translated(self.objx * 24, self.objy * 24))
        scene = self.scene()
        if scene is not None:
            scene.update(updaterect)

    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed for resizing
        """
        if event is None:
            return

        if event.buttons() != QtCore.Qt.MouseButton.NoButton and self.dragging:
            # Resize it
            dsx = self.dragstartx
            dsy = self.dragstarty

            clickedx = int((event.pos().x() - 12) / 24)
            clickedy = int((event.pos().y() - 12) / 24)

            cx = self.objx
            cy = self.objy
            obj: ObjectItem

            if self.TLGrabbed:
                if clickedx != dsx or clickedy != dsy:
                    for obj in self.objsDragging:
                        oldWidth = self.objsDragging[obj][0] + 0
                        oldHeight = self.objsDragging[obj][1] + 0

                        self.objsDragging[obj][0] -= clickedx - dsx
                        self.objsDragging[obj][1] -= clickedy - dsy

                        if self.objsDragging[obj][0] < 1 or self.objsDragging[obj][1] < 1:
                            if self.objsDragging[obj][0] < 1:
                                self.objsDragging[obj][0] = oldWidth

                            if self.objsDragging[obj][1] < 1:
                                self.objsDragging[obj][1] = oldHeight

                        else:
                            newX = obj.objx + clickedx - dsx
                            newY = obj.objy + clickedy - dsy
                            newSize = [obj.width, obj.height]

                            newWidth = self.objsDragging[obj][0]
                            newHeight = self.objsDragging[obj][1]

                            if newX >= 0 and newX + newWidth == obj.objx + obj.width:
                                obj.objx = newX
                                newSize[0] = newWidth

                            else:
                                self.objsDragging[obj][0] = oldWidth

                            if newY >= 0 and newY + newHeight == obj.objy + obj.height:
                                obj.objy = newY
                                newSize[1] = newHeight

                            else:
                                self.objsDragging[obj][1] = oldHeight

                            obj.setPos(obj.objx * 24, obj.objy * 24)
                            obj.UpdateRects()
                            obj.UpdateObj(cx, cy, newSize)

                    SetDirty()

            elif self.TRGrabbed:
                if clickedx < 0:
                    clickedx = 0

                if clickedx != dsx or clickedy != dsy:
                    self.dragstartx = clickedx

                    for obj in self.objsDragging:
                        oldHeight = self.objsDragging[obj][1] + 0

                        self.objsDragging[obj][0] += clickedx - dsx
                        self.objsDragging[obj][1] -= clickedy - dsy

                        if self.objsDragging[obj][1] < 1:
                            self.objsDragging[obj][1] = oldHeight

                        else:
                            newY = obj.objy + clickedy - dsy
                            newSize = [obj.width, obj.height]

                            newWidth = self.objsDragging[obj][0]
                            if newWidth < 1:
                                newWidth = 1

                            newHeight = self.objsDragging[obj][1]

                            if newY >= 0 and newY + newHeight == obj.objy + obj.height:
                                obj.objy = newY
                                newSize[1] = newHeight
                                obj.setPos(obj.objx * 24, newY * 24)

                            else:
                                self.objsDragging[obj][1] = oldHeight

                            newSize[0] = newWidth

                            obj.UpdateRects()
                            obj.UpdateObj(cx, cy, newSize)

                    SetDirty()

            elif self.BLGrabbed:
                if clickedy < 0:
                    clickedy = 0

                if clickedx != dsx or clickedy != dsy:
                    self.dragstarty = clickedy

                    for obj in self.objsDragging:
                        oldWidth = self.objsDragging[obj][0] + 0

                        self.objsDragging[obj][0] -= clickedx - dsx
                        self.objsDragging[obj][1] += clickedy - dsy

                        if self.objsDragging[obj][0] < 1:
                            self.objsDragging[obj][0] = oldWidth

                        else:
                            newX = obj.objx + clickedx - dsx
                            newWidth = self.objsDragging[obj][0]
                            newHeight = self.objsDragging[obj][1]
                            newSize = [obj.width, obj.height]

                            if newHeight < 1:
                                newHeight = 1

                            if newX >= 0 and newX + newWidth == obj.objx + obj.width:
                                obj.objx = newX
                                newSize[0] = newWidth
                                obj.setPos(newX * 24, obj.objy * 24)

                            else:
                                self.objsDragging[obj][0] = oldWidth

                            newSize[1] = newHeight
                            obj.UpdateObj(cx, cy, newSize)

                    SetDirty()

            elif self.BRGrabbed:
                if clickedx < 0: clickedx = 0
                if clickedy < 0: clickedy = 0

                if clickedx != dsx or clickedy != dsy:
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy

                    for obj in self.objsDragging:
                        self.objsDragging[obj][0] += clickedx - dsx
                        self.objsDragging[obj][1] += clickedy - dsy

                        newWidth = self.objsDragging[obj][0]
                        newHeight = self.objsDragging[obj][1]

                        if newWidth < 1:
                            newWidth = 1

                        if newHeight < 1:
                            newHeight = 1

                        newSize = [newWidth, newHeight]

                        obj.UpdateObj(cx, cy, newSize)

                    SetDirty()

            elif self.MTGrabbed:
                if clickedy != dsy:
                    for obj in self.objsDragging:
                        oldHeight = self.objsDragging[obj][1]

                        self.objsDragging[obj][1] -= clickedy - dsy

                        if self.objsDragging[obj][1] < 1:
                            self.objsDragging[obj][1] = oldHeight

                        else:
                            newY = obj.objy + clickedy - dsy
                            newHeight = self.objsDragging[obj][1]
                            newSize = [obj.width, obj.height]

                            if newY >= 0 and newY + newHeight == obj.objy + obj.height:
                                obj.objy = newY
                                newSize[1] = newHeight
                                obj.setPos(obj.objx * 24, newY * 24)

                            else:
                                self.objsDragging[obj][1] = oldHeight

                            obj.UpdateObj(cx, cy, newSize)

                    SetDirty()

            elif self.MLGrabbed:
                if clickedx != dsx:
                    for obj in self.objsDragging:
                        oldWidth = self.objsDragging[obj][0]

                        self.objsDragging[obj][0] -= clickedx - dsx

                        if self.objsDragging[obj][0] < 1:
                            self.objsDragging[obj][0] = oldWidth

                        else:
                            newX = obj.objx + clickedx - dsx

                            newWidth = self.objsDragging[obj][0]
                            newSize = [obj.width, obj.height]

                            if newX >= 0 and newX + newWidth == obj.objx + obj.width:
                                obj.objx = newX
                                newSize[0] = newWidth
                                obj.setPos(newX * 24, obj.objy * 24)

                            else:
                                self.objsDragging[obj][0] = oldWidth

                            obj.UpdateObj(cx, cy, newSize)

                    SetDirty()

            elif self.MBGrabbed:
                if clickedy < 0:
                    clickedy = 0

                if clickedy != dsy:
                    self.dragstarty = clickedy

                    for obj in self.objsDragging:
                        self.objsDragging[obj][1] += clickedy - dsy

                        newHeight = self.objsDragging[obj][1]
                        if newHeight < 1:
                            newHeight = 1

                        newSize = [obj.width, newHeight]
                        obj.UpdateObj(cx, cy, newSize)

                    SetDirty()

            elif self.MRGrabbed:
                if clickedx < 0:
                    clickedx = 0

                if clickedx != dsx:
                    self.dragstartx = clickedx

                    for obj in self.objsDragging:
                        self.objsDragging[obj][0] += clickedx - dsx

                        newWidth = self.objsDragging[obj][0]
                        if newWidth < 1:
                            newWidth = 1

                        newSize = (newWidth, obj.height)
                        obj.UpdateObj(cx, cy, newSize)

                    SetDirty()

            event.accept()

        else:
            LevelEditorItem.mouseMoveEvent(self, event)

        self.UpdateTooltip()

    def delete(self):
        """
        Delete the object from the level
        """
        globals_.Area.RemoveFromLayer(self)
        scene = self.scene()
        if scene is not None:
            scene.update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        setOverrideCursor(None)

    def mouseReleaseEvent(self, event):
        """
        Overrides releasing the mouse after a move
        """
        LevelEditorItem.mouseReleaseEvent(self, event)

        self.TLGrabbed = self.TRGrabbed = self.BLGrabbed = self.BRGrabbed = False
        self.MTGrabbed = self.MLGrabbed = self.MBGrabbed = self.MRGrabbed = False
        self.update()
