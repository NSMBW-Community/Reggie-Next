from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
from src.data.common.utils import clamp
from src.data.level.dirty import SetDirty
from src.data.level.items.basic import InstanceDefinition, LevelEditorItem
from src.ui.theme.reggie_theme import setOverrideCursor


class InstanceDefinition_LocationItem(InstanceDefinition):
    """
    Definition of an instance of LocationItem
    """
    fieldNames = (
        'width',
        'height',
        'id',
    )

    @staticmethod
    def itemList():
        return globals_.Area.locations

    def createNew(self):
        return LocationItem(self.objx, self.objy, *(field for field in self.fields))


class LocationItem(LevelEditorItem):
    """
    Level editor item that represents a sprite location
    """
    instanceDef = InstanceDefinition_LocationItem
    sizeChanged = None  # Callback: sizeChanged(SpriteItem obj, int width, int height)
    dragstartx, dragstarty = None, None

    def __init__(self, x, y, width, height, id):
        """
        Creates a location with specific data
        """
        LevelEditorItem.__init__(self)
        if globals_.CursorMode != 0:
            self.setAcceptHoverEvents(True)

        self.font = globals_.NumberFont
        self.objx = x
        self.objy = y
        self.width = width
        self.height = height
        self.id = id
        self.listitem = None
        self.LevelRect = QtCore.QRectF(self.objx / 16, self.objy / 16, 1.5, 1.5)

        self.UpdateTitle()
        self.UpdateRects()

        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, not globals_.LocationsFrozen)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, not globals_.LocationsFrozen)

        globals_.DirtyOverride += 1
        self.setPos(int(x * 1.5), int(y * 1.5))
        globals_.DirtyOverride -= 1

        self.dragging = False
        self.setZValue(24000)

    def ListString(self):
        """
        Returns a string that can be used to describe the location in a list
        """
        return globals_.trans.string('Locations', 2, '[id]', self.id, '[width]', int(self.width), '[height]', int(self.height),
                            '[x]', int(self.objx), '[y]', int(self.objy))

    def UpdateTitle(self):
        """
        Updates the location's title
        """
        self.title = globals_.trans.string('Locations', 0, '[id]', self.id)

        # Since font never changes, we can just define TitleRect here
        if self.font is not None:
            metrics = QtGui.QFontMetrics(self.font)
            self.TitleRect = QtCore.QRectF(metrics.boundingRect(self.title))
            self.TitleRect.setWidth(self.TitleRect.width() + 4.0)
            self.TitleRect.moveTo(4, 4)

        self.UpdateRects()

    def __lt__(self, other):
        return self.id < other.id

    def UpdateRects(self):
        """
        Updates the location's bounding rectangle
        """
        self.prepareGeometryChange()

        self.BoundingRectWithoutTitleRect = QtCore.QRectF(0, 0, self.width * 1.5, self.height * 1.5)

        self.SelectionRect = QtCore.QRectF(self.objx * 1.5, self.objy * 1.5, self.width * 1.5, self.height * 1.5)
        self.ZoneRect = QtCore.QRectF(self.objx, self.objy, self.width, self.height)
        self.DrawRect = QtCore.QRectF(1, 1, (self.width * 1.5) - 2, (self.height * 1.5) - 2)
        self.GrabberRect = QtCore.QRectF((1.5 * self.width) - 4.8, (1.5 * self.height) - 4.8, 4.8, 4.8)
        self.BoundingRect = self.BoundingRectWithoutTitleRect.united(self.TitleRect).united(self.GrabberRect)
        self.UpdateListItem()

    def shape(self):
        """
        self.BoundingRect is big enough to include self.TitleRect (so
        the ID text can be painted), but that makes the hit-detection
        region too large if the rect is small.
        """
        # We basically make a vertically-flipped "L" shape if the location
        # is small, so that you can click on the ID number to select the location
        qpp = QtGui.QPainterPath()
        qpp.setFillRule(QtCore.Qt.FillRule.WindingFill)
        qpp.addRect(self.BoundingRectWithoutTitleRect)
        qpp.addRect(self.TitleRect)
        return qpp

    def paint(self, painter, option, widget = ...):
        """
        Paints the location on screen
        """
        if not painter or not globals_.theme or not self.font:
            return

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Paint liquids/fog
        if globals_.SpritesShown and globals_.SpriteImagesShown and globals_.RealViewEnabled:
            location_rect = self.sceneTransform().mapRect(self.DrawRect)
            from sprites import SpriteImage_LiquidOrFog as liquidOrFogType

            for sprite in globals_.Area.sprites:
                if isinstance(sprite.ImageObj, liquidOrFogType) and self.id == sprite.ImageObj.locId:
                    sprite.ImageObj.realViewLocation(painter, location_rect)

        # Draw the purple rectangle
        if not self.isSelected():
            painter.setBrush(QtGui.QBrush(globals_.theme.color('location_fill')))
            painter.setPen(QtGui.QPen(globals_.theme.color('location_lines')))
        else:
            painter.setBrush(QtGui.QBrush(globals_.theme.color('location_fill_s')))
            color = globals_.theme.color('location_lines_s')
            if color is not None:
                painter.setPen(QtGui.QPen(color, 1, QtCore.Qt.PenStyle.DashLine))
        painter.drawRect(self.DrawRect)

        # Draw the ID
        painter.setPen(QtGui.QPen(globals_.theme.color('location_text')))
        painter.setFont(self.font)
        painter.drawText(self.TitleRect, self.title)

        # Draw the resizer rectangle, if selected
        if self.isSelected():
            color = globals_.theme.color('location_lines_s')
            if color is not None:
                painter.fillRect(self.GrabberRect, color)

    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for resizing
        """
        if not event or not globals_.mainWindow:
            return

        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
                new_item = globals_.mainWindow.CreateLocation(
                    self.objx, self.objy, self.width, self.height, self.id
                )

                if new_item is not None:
                    # Swap the Z values so it doesn't look like the
                    # cloned item is the old one
                    new_z = new_item.zValue()
                    new_item.setZValue(self.zValue())
                    self.setZValue(new_z)

                    globals_.mainWindow.scene.clearSelection()
                    self.setSelected(True)

        if self.isSelected() and self.GrabberRect.contains(event.pos()):
            # start dragging
            self.dragging = True
            self.dragstartx = self.objx
            self.dragstarty = self.objy
            event.accept()
        else:
            LevelEditorItem.mousePressEvent(self, event)
            self.dragging = False

    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed for resizing
        """
        if not event or not globals_.mainWindow:
            return

        if event.buttons() != QtCore.Qt.MouseButton.NoButton and self.dragging:
            # Resize the location.
            change = self.dragResize(event.scenePos(), self.dragstartx, self.dragstarty)

            if change:
                SetDirty()
                globals_.mainWindow.level_overview.update()

                if self.sizeChanged is not None:
                    self.sizeChanged(self, self.width, self.height)

                # This code causes an error or something.
                # if RealViewEnabled:
                #     for sprite in globals_.Area.sprites:
                #         if self.id in sprite.ImageObj.locationIDs and sprite.ImageObj.updateSceneAfterLocationMoved:
                #             self.scene().update()

            event.accept()
        else:
            LevelEditorItem.mouseMoveEvent(self, event)

    def dragResize(self, clicked, dsx, dsy):
        """
        Handles resizing the location and returns whether the location was
        changed.
        """
        clickx = clamp(int(clicked.x() / 1.5), 0, 65535)
        clicky = clamp(int(clicked.y() / 1.5), 0, 65535)

        # if alt is not held, snap to 8x8 grid
        if QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.KeyboardModifier.AltModifier:
            dsx = 8 * round(dsx / 8)
            dsy = 8 * round(dsy / 8)
            clickx = 8 * round(clickx / 8)
            clicky = 8 * round(clicky / 8)

        # Calculate the dimensions of the rectangle from ds(x, y) to
        # click(x, y)
        x = min(dsx, clickx)
        y = min(dsy, clicky)
        width = max(1, abs(clickx - dsx))
        height = max(1, abs(clicky - dsy))

        change = False

        # if the position changed, set the new one
        if self.objx != x or self.objy != y:
            self.objx = x
            self.objy = y

            globals_.OverrideSnapping = True
            self.setPos(x * 1.5, y * 1.5)
            globals_.OverrideSnapping = False
            self.UpdateListItem()
            change = True

        # if the size changed, recache it and update the area
        if self.width != width or self.height != height:
            self.width = width
            self.height = height

            oldrect = self.BoundingRect
            oldrect.translate(dsx * 1.5, dsy * 1.5)
            newrect = QtCore.QRectF(self.x(), self.y(), self.width * 1.5, self.height * 1.5)
            updaterect = oldrect.united(newrect)

            self.UpdateRects()
            scene = self.scene()
            if scene is not None:
                scene.update(updaterect)

            change = True

        return change

    def delete(self):
        """
        Delete the location from the level
        """
        if globals_.mainWindow is None:
            return

        loclist = globals_.mainWindow.locationList
        globals_.mainWindow.UpdateFlag = True
        loclist.takeItem(loclist.row(self.listitem))
        globals_.mainWindow.UpdateFlag = False

        sel_model = loclist.selectionModel()
        if sel_model is not None:
            sel_model.clearSelection()

        globals_.Area.locations.remove(self)
        scene = self.scene()
        if scene is not None:
            scene.update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        setOverrideCursor(None)

    def mouseReleaseEvent(self, event):
        """
        Overrides releasing the mouse after a move
        """
        LevelEditorItem.mouseReleaseEvent(self, event)

        self.dragging = False
        self.update()

    def hoverMoveEvent(self, event):
        if event is None:
            return

        LevelEditorItem.hoverMoveEvent(self, event)
        if globals_.LocationsFrozen:
            return

        if self.isSelected() and self.GrabberRect.contains(event.pos()):
            setOverrideCursor(QtCore.Qt.CursorShape.SizeFDiagCursor)
        elif self.isSelected() or globals_.CursorMode == 2:
            setOverrideCursor(QtCore.Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        LevelEditorItem.hoverLeaveEvent(self, event)
        setOverrideCursor(None)
