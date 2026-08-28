from typing import cast

from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
from src.data.common.utils import clamp
from src.data.level.abstract_path import AbstractPath
from src.data.level.dirty import SetDirty
from src.data.level.items.abstract_object import AbstractObjectItem
from src.data.level.items.path_editor_line import PathEditorLineItem
from src.ui.actions.undo.move_item import MoveItemUndoAction
from src.ui.actions.undo.simultaneous import SimultaneousUndoAction
from src.ui.widgets.item_sorts_by_other import ListWidgetItem_SortsByOther


class InstanceDefinition:
    """
    ABC for a definition of an instance of a LevelEditorItem class, used for persistence and comparisons
    """
    fieldNames = []

    def __init__(self, other=None):
        """
        Initializes it
        """
        self.fields = [[name, None] for name in self.fieldNames]
        if other:
            self.setFrom(other)
        else:
            self.clear()

    @staticmethod
    def itemList():
        """
        Returns a list of all instances of this item currently in the level
        """
        return []

    def clear(self):
        """
        Clears all data and position data
        """
        self.objx = None
        self.objy = None
        self.clearData()

    def clearData(self):
        """
        Clears all data
        """
        for field in self.fields:
            field = None

    def setFrom(self, other):
        """
        Sets data and position from an item
        """
        self.objx = other.objx
        self.objy = other.objy
        self.setDataFrom(other)

    def setDataFrom(self, other):
        """
        Sets data from an item
        """
        for field in self.fields:
            field[1] = getattr(other, field[0])

    def matches(self, other):
        """
        Returns True if this instance definition matches the specified item
        """
        return self.objx == other.objx and self.objy == other.objy and self.matchesData(other)

    def matchesData(self, other):
        """
        Returns True if this instance definition's data matches the specified item's data
        """
        matches = True
        for field in self.fields:
            matches = matches and (field[1] == getattr(other, field[0]))
        return matches

    def defMatches(self, other):
        """
        Returns True if this instance definition matches the specified instance definition
        """
        matches = True
        matches = matches and (self.objx == other.objx)
        matches = matches and (self.objy == other.objy)
        return matches and self.defMatchesData(other)

    def defMatchesData(self, other):
        """
        Returns True if this instance definition's data matches the specified instance definition's data
        """
        matches = True
        for myField, otherField in zip(self.fields, other.fields):
            matches = matches and (myField == otherField)
        return matches

    def createNew(self):
        """
        Creates a new instance of the target class, with the data specified here
        """
        # This will need to be implemented separately in each subclass
        return LevelEditorItem()

    def findInstance(self):
        """
        Returns a matching instance of this thing in the level
        """
        for item in self.itemList():
            if isinstance(item, AbstractPath):
                # Path does not have objx/y, but the nodes do
                for node in item._nodes:
                    if self.matches(node):
                        return node
            else:
                if self.matches(item):
                    return item


class LevelEditorItem(QtWidgets.QGraphicsItem):
    """
    Class for any type of item that can show up in the level editor control
    """
    instanceDef = InstanceDefinition
    positionChanged = None  # Callback: positionChanged(LevelEditorItem obj, int oldx, int oldy, int x, int y)
    autoPosChange = False
    dragoffsetx = 0
    dragoffsety = 0
    objx, objy = 0, 0
    BoundingRect = QtCore.QRectF(0, 0, 24, 24)

    def __init__(self):
        """
        Generic constructor for level editor items
        """
        QtWidgets.QGraphicsItem.__init__(self)
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.listitem: ListWidgetItem_SortsByOther | None = None

    def __lt__(self, other):
        if self.objx != other.objx:
            return self.objx < other.objx

        return self.objy < other.objy

    def ListString(self) -> str | None:
        """
        Returns a string that can be used to describe the item in a list
        """
        return None

    def itemChange(self, change, value):
        """
        Makes sure positions don't go out of bounds and updates them as necessary
        """
        if not globals_.mainWindow:
            return

        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Snap to 24x24
            newpos = value

            # Snap even further if Alt isn't held
            # but -only- if OverrideSnapping is off
            if (not globals_.OverrideSnapping) and (not self.autoPosChange):
                if self.scene() is None:
                    objectsSelected = False
                else:
                    objectsSelected = any(isinstance(thing, AbstractObjectItem) for thing in globals_.mainWindow.CurrentSelection)
                if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
                    # Alt is held; don't snap
                    newpos.setX(int(int((newpos.x() + 0.75) / 1.5) * 1.5))
                    newpos.setY(int(int((newpos.y() + 0.75) / 1.5) * 1.5))
                elif not objectsSelected and self.isSelected() and len(globals_.mainWindow.CurrentSelection) > 1:
                    # Snap to 8x8, but with the dragoffsets
                    dragoffsetx, dragoffsety = int(self.dragoffsetx), int(self.dragoffsety)

                    if dragoffsetx < -12:
                        dragoffsetx += 12
                    if dragoffsety < -12:
                        dragoffsety += 12
                    if dragoffsetx == 0:
                        dragoffsetx = -12
                    if dragoffsety == 0:
                        dragoffsety = -12

                    referenceX = int((newpos.x() + 6 + 12 + dragoffsetx) / 12) * 12
                    referenceY = int((newpos.y() + 6 + 12 + dragoffsety) / 12) * 12
                    newpos.setX(referenceX - (12 + dragoffsetx))
                    newpos.setY(referenceY - (12 + dragoffsety))
                elif objectsSelected and self.isSelected():
                    # Objects are selected, too; move in sync by snapping to whole blocks
                    dragoffsetx, dragoffsety = int(self.dragoffsetx), int(self.dragoffsety)

                    if dragoffsetx == 0:
                        dragoffsetx = -24
                    if dragoffsety == 0:
                        dragoffsety = -24

                    referenceX = int((newpos.x() + 12 + 24 + dragoffsetx) / 24) * 24
                    referenceY = int((newpos.y() + 12 + 24 + dragoffsety) / 24) * 24
                    newpos.setX(referenceX - (24 + dragoffsetx))
                    newpos.setY(referenceY - (24 + dragoffsety))
                else:
                    # Snap to 8x8
                    newpos.setX(int(int((newpos.x() + 6) / 12) * 12))
                    newpos.setY(int(int((newpos.y() + 6) / 12) * 12))

            x = newpos.x()
            y = newpos.y()

            # Don't let it get out of the boundaries
            newpos.setX(clamp(x, 0, 24552))
            newpos.setY(clamp(y, 0, 12264))

            # Update the data
            x = int(newpos.x() / 1.5)
            y = int(newpos.y() / 1.5)
            if x != self.objx or y != self.objy:
                updRect = QtCore.QRectF(
                    self.x() + self.BoundingRect.x(),
                    self.y() + self.BoundingRect.y(),
                    self.BoundingRect.width(),
                    self.BoundingRect.height(),
                )

                scene = self.scene()
                if scene is not None:
                    scene.update(updRect)

                oldx = self.objx
                oldy = self.objy
                self.objx = x
                self.objy = y
                if self.positionChanged is not None:
                    self.positionChanged(self, oldx, oldy, x, y)

                if not isinstance(self, PathEditorLineItem):
                    if len(globals_.mainWindow.CurrentSelection) == 1:
                        act = MoveItemUndoAction(self, oldx, oldy, x, y)
                        globals_.mainWindow.undoStack.addOrExtendAction(act)
                    elif len(globals_.mainWindow.CurrentSelection) > 1:
                        # This is certainly not the most efficient way to do this
                        # (the number of UndoActions > (selection size ^ 2)), but
                        # it works and I can't think of a better way to do it. :P
                        acts = set()
                        acts.add(MoveItemUndoAction(self, oldx, oldy, x, y))

                        for item in globals_.mainWindow.CurrentSelection:
                            if item is self:
                                continue

                            item = cast(LevelEditorItem, item)
                            act = MoveItemUndoAction(item, item.objx, item.objy, item.objx, item.objy)
                            acts.add(act)

                        act = SimultaneousUndoAction(acts)
                        globals_.mainWindow.undoStack.addOrExtendAction(act)

                SetDirty()

            return newpos

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def getFullRect(self):
        """
        Basic implementation that returns self.BoundingRect
        """
        return self.BoundingRect.translated(self.pos())

    def UpdateListItem(self, updateTooltipPreview=False):
        """
        Updates the list item
        """
        if not hasattr(self, 'listitem'):
            return

        if self.listitem is None:
            return

        if updateTooltipPreview:
            # It's just like Qt to make this overly complicated. XP
            img = self.renderInLevelIcon()
            byteArray = QtCore.QByteArray()
            buf = QtCore.QBuffer(byteArray)
            if img is not None:
                img.save(buf, 'PNG')
            byteObj = bytes(byteArray)
            b64 = base64.b64encode(byteObj).decode('utf-8')

            self.listitem.setToolTip('<img src="data:image/png;base64,' + b64 + '" />')

        self.listitem.setText(self.ListString())

    def renderInLevelIcon(self):
        """
        Renders an icon of this item as it appears in the level
        """
        if globals_.mainWindow is None:
            return

        # Constants:
        # Maximum size of the preview (it will be shrunk if it exceeds this)
        max_size = QtCore.QSize(256, 256)
        # Percentage of the size to use for margins
        margin_pct = 0.75
        # Maximum margin (24 = 1 block)
        max_margin = 96

        # Get the full bounding rectangle
        br = self.getFullRect()

        # Expand the rect to add extra margins around the edges
        marginX = br.width() * margin_pct
        marginY = br.height() * margin_pct
        marginX = min(marginX, max_margin)
        marginY = min(marginY, max_margin)
        br.setX(br.x() - marginX)
        br.setY(br.y() - marginY)
        br.setWidth(br.width() + marginX)
        br.setHeight(br.height() + marginY)

        # Take the screenshot
        ScreenshotImage = QtGui.QImage(br.size().toSize(), QtGui.QImage.Format.Format_ARGB32)
        ScreenshotImage.fill(QtCore.Qt.GlobalColor.transparent)

        RenderPainter = QtGui.QPainter(ScreenshotImage)
        globals_.mainWindow.scene.render(
            RenderPainter,
            QtCore.QRectF(0, 0, br.width(), br.height()),
            br,
        )
        RenderPainter.end()

        # Shrink it if it's too big
        final = ScreenshotImage
        if ScreenshotImage.width() > max_size.width() or ScreenshotImage.height() > max_size.height():
            final = ScreenshotImage.scaled(
                max_size,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )

        return final

    def boundingRect(self):
        """
        Required for Qt
        """
        return self.BoundingRect
