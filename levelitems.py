from PyQt5 import QtCore, QtGui, QtWidgets
import os
import random
import base64

import spritelib as SLib
import globals_
import common
from tiles import RenderObject
from ui import GetIcon, clipStr
from dirty import SetDirty
from undo import MoveItemUndoAction, SimultaneousUndoAction

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
            field[1] = None

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
            if self.matches(item):
                return item


class InstanceDefinition_ObjectItem(InstanceDefinition):
    """
    Definition of an instance of ObjectItem
    """
    fieldNames = (
        'tileset',
        'type',
        'layer',
        'width',
        'height',
    )

    @staticmethod
    def itemList():
        # list concatenation here
        return globals_.Area.layers[0] + globals_.Area.layers[1] + globals_.Area.layers[2]

    def createNew(self):
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
        return LocationItem(self.objx, self.objy, *(field[1] for field in self.fields))


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
        return EntranceItem(self.objx, self.objy, *(field[1] for field in self.fields))


class InstanceDefinition_PathItem(InstanceDefinition):
    """
    Definition of an instance of PathItem
    """
    fieldNames = (
        'pathid',
        'nodeid',
        'path',
    )

    @staticmethod
    def itemList():
        return globals_.Area.paths

    def createNew(self):
        return PathItem(self.objx, self.objy, *(field[1] for field in self.fields))


class InstanceDefinition_CommentItem(InstanceDefinition):
    """
    Definition of an instance of CommentItem
    """
    fieldNames = (
        'text',
    )

    @staticmethod
    def itemList():
        return globals_.Area.comments

    def createNew(self):
        return CommentItem(self.objx, self.objy, self.fields[0][1])


class ListWidgetItem_SortsByOther(QtWidgets.QListWidgetItem):
    """
    A ListWidgetItem that defers sorting to another object.
    """

    def __init__(self, reference, text=''):
        super().__init__(text)
        self.reference = reference

    def __lt__(self, other):
        return self.reference < other.reference


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

    def __init__(self):
        """
        Generic constructor for level editor items
        """
        QtWidgets.QGraphicsItem.__init__(self)
        self.setFlag(self.ItemSendsGeometryChanges, True)

    def __lt__(self, other):
        if self.objx != other.objx:
            return self.objx < other.objx
        return self.objy < other.objy

    def itemChange(self, change, value):
        """
        Makes sure positions don't go out of bounds and updates them as necessary
        """

        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            # snap to 24x24
            newpos = value

            # snap even further if Alt isn't held
            # but -only- if OverrideSnapping is off
            if (not globals_.OverrideSnapping) and (not self.autoPosChange):
                if self.scene() is None:
                    objectsSelected = False
                else:
                    objectsSelected = any([isinstance(thing, ObjectItem) for thing in globals_.mainWindow.CurrentSelection])
                if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
                    # Alt is held; don't snap
                    newpos.setX(int(int((newpos.x() + 0.75) / 1.5) * 1.5))
                    newpos.setY(int(int((newpos.y() + 0.75) / 1.5) * 1.5))
                elif not objectsSelected and self.isSelected() and len(globals_.mainWindow.CurrentSelection) > 1:
                    # Snap to 8x8, but with the dragoffsets
                    dragoffsetx, dragoffsety = int(self.dragoffsetx), int(self.dragoffsety)
                    if dragoffsetx < -12: dragoffsetx += 12
                    if dragoffsety < -12: dragoffsety += 12
                    if dragoffsetx == 0: dragoffsetx = -12
                    if dragoffsety == 0: dragoffsety = -12
                    referenceX = int((newpos.x() + 6 + 12 + dragoffsetx) / 12) * 12
                    referenceY = int((newpos.y() + 6 + 12 + dragoffsety) / 12) * 12
                    newpos.setX(referenceX - (12 + dragoffsetx))
                    newpos.setY(referenceY - (12 + dragoffsety))
                elif objectsSelected and self.isSelected():
                    # Objects are selected, too; move in sync by snapping to whole blocks
                    dragoffsetx, dragoffsety = int(self.dragoffsetx), int(self.dragoffsety)
                    if dragoffsetx == 0: dragoffsetx = -24
                    if dragoffsety == 0: dragoffsety = -24
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

            # don't let it get out of the boundaries
            if x < 0: newpos.setX(0)
            if x > 24552: newpos.setX(24552)
            if y < 0: newpos.setY(0)
            if y > 12264: newpos.setY(12264)

            # update the data
            x = int(newpos.x() / 1.5)
            y = int(newpos.y() / 1.5)
            if x != self.objx or y != self.objy:
                updRect = QtCore.QRectF(
                    self.x() + self.BoundingRect.x(),
                    self.y() + self.BoundingRect.y(),
                    self.BoundingRect.width(),
                    self.BoundingRect.height(),
                )
                if self.scene() is not None:
                    self.scene().update(updRect)

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
                            if item is self: continue
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
        if not hasattr(self, 'listitem'): return
        if self.listitem is None: return

        if updateTooltipPreview:
            # It's just like Qt to make this overly complicated. XP
            img = self.renderInLevelIcon()
            byteArray = QtCore.QByteArray()
            buf = QtCore.QBuffer(byteArray)
            img.save(buf, 'PNG')
            byteObj = bytes(byteArray)
            b64 = base64.b64encode(byteObj).decode('utf-8')

            self.listitem.setToolTip('<img src="data:image/png;base64,' + b64 + '" />')

        self.listitem.setText(self.ListString())

    def renderInLevelIcon(self):
        """
        Renders an icon of this item as it appears in the level
        """
        # Constants:
        # Maximum size of the preview (it will be shrunk if it exceeds this)
        maxSize = QtCore.QSize(256, 256)
        # Percentage of the size to use for margins
        marginPct = 0.75
        # Maximum margin (24 = 1 block)
        maxMargin = 96

        # Get the full bounding rectangle
        br = self.getFullRect()

        # Expand the rect to add extra margins around the edges
        marginX = br.width() * marginPct
        marginY = br.height() * marginPct
        marginX = min(marginX, maxMargin)
        marginY = min(marginY, maxMargin)
        br.setX(br.x() - marginX)
        br.setY(br.y() - marginY)
        br.setWidth(br.width() + marginX)
        br.setHeight(br.height() + marginY)

        # Take the screenshot
        ScreenshotImage = QtGui.QImage(br.size().toSize(), QtGui.QImage.Format_ARGB32)
        ScreenshotImage.fill(QtCore.Qt.transparent)

        RenderPainter = QtGui.QPainter(ScreenshotImage)
        globals_.mainWindow.scene.render(
            RenderPainter,
            QtCore.QRectF(0, 0, br.width(), br.height()),
            br,
        )
        RenderPainter.end()

        # Shrink it if it's too big
        final = ScreenshotImage
        if ScreenshotImage.width() > maxSize.width() or ScreenshotImage.height() > maxSize.height():
            final = ScreenshotImage.scaled(
                maxSize,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )

        return final

    def boundingRect(self):
        """
        Required for Qt
        """
        return self.BoundingRect


class ObjectItem(LevelEditorItem):
    """
    Level editor item that represents an ingame object
    """
    instanceDef = InstanceDefinition_ObjectItem

    def __init__(self, tileset, type, layer, x, y, width, height, z):
        """
        Creates an object with specific data
        """
        LevelEditorItem.__init__(self)

        self.tileset = tileset
        self.type = type
        self.objx = x
        self.objy = y
        self.layer = layer
        self.width = width
        self.height = height
        self.objdata = None

        self.wasExtended = False

        self.TLGrabbed = self.TRGrabbed = self.BLGrabbed = self.BRGrabbed = False
        self.MTGrabbed = self.MLGrabbed = self.MBGrabbed = self.MRGrabbed = False

        self.setFlag(self.ItemIsMovable, not globals_.ObjectsFrozen)
        self.setFlag(self.ItemIsSelectable, not globals_.ObjectsFrozen)

        self.UpdateRects()

        self.dragging = False
        self.dragstartx = -1
        self.dragstarty = -1
        self.objsDragging = {}

        # global globals_.DirtyOverride
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

    def SetType(self, tileset, type):
        """
        Sets the type of the object
        """
        self.tileset = tileset
        self.type = type
        self.updateObjCache()
        self.update()

        self.UpdateTooltip()

    def UpdateTooltip(self):
        """
        Updates the tooltip
        """
        self.setToolTip(
            globals_.trans.string('Objects', 0, '[tileset]', self.tileset + 1, '[obj]', self.type, '[width]', self.width,
                         '[height]', self.height, '[layer]', self.layer))

    def updateObjCache(self):
        """
        Updates the rendered object data
        """
        self.objdata = RenderObject(self.tileset, self.type, self.width, self.height)
        self.randomise()

    def isBottomRowSpecial(self):
        """
        Returns whether the bottom row of self.objdata contains the special
        vdouble top tile.
        """
        if globals_.TilesetFilesLoaded[self.tileset] is None or globals_.TilesetInfo is None:
            # no randomisation info -> false
            return False

        name = self.get_tileset_base_name()

        if name not in globals_.TilesetInfo:
            # tileset not randomised -> false
            return False

        tileset_info = globals_.TilesetInfo[name]

        for x in range(self.width):
            # get the special data for this tile
            tile = self.objdata[-1][x] & 0xFF

            try:
                *_, special = tileset_info[tile]
            except KeyError:
                # tile not randomised -> continue with next position
                continue

            if special & 0b01:
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

        if globals_.TilesetInfo is None or globals_.TilesetFilesLoaded[self.tileset] is None:
            # no randomisation info -> exit
            return

        if globals_.ObjectDefinitions[self.tileset][self.type] is None or \
                len(globals_.ObjectDefinitions[self.tileset][self.type].rows[0][0]) == 1:
            # slope -> exit
            return

        name = self.get_tileset_base_name()

        if name not in globals_.TilesetInfo:
            # tileset not randomised -> exit
            return

        tileset_info = globals_.TilesetInfo[name]

        if width is None:
            width = self.width

        if height is None:
            height = self.height

        # randomise every tile in this region
        for y in range(starty, starty + height):
            for x in range(startx, startx + width):
                # should we randomise this tile?
                tile = self.objdata[y][x] & 0xFF

                try:
                    tiles, direction, special = tileset_info[tile]
                except KeyError:
                    # tile not randomised -> continue with next position
                    continue

                # If the special indicates the top, don't randomise it now, but
                # randomise it when we come across the bottom.
                if special & 0b01:
                    continue

                tiles_ = tiles[:]

                # Take direction into account - chosen tile must be different from
                # the tile to the left/top. Using try/except here so the value has
                # to be looked up only once.

                # direction is 2 bits:
                # highest := vertical direction; lowest := horizontal direction
                if direction & 0b01 and x > 0:
                    # only look at the left neighbour, since we will generate the
                    # right neighbour later
                    try:
                        tiles_.remove(self.objdata[y][x-1] & 0xFF)
                    except ValueError:
                        pass

                if direction & 0b10 and y > 0:
                    # only look at the above neighbour, since we will generate the
                    # neighbour below later
                    try:
                        tiles_.remove(self.objdata[y-1][x] & 0xFF)
                    except ValueError:
                        pass

                # if we removed all options, just use the original tiles
                if not tiles_:
                    tiles_ = tiles

                choice = (self.tileset << 8) | random.choice(tiles_)
                self.objdata[y][x] = choice

                # Bottom of special, so change the tile above to the tile in the
                # previous row of the tileset image (at offset choice - 0x10).
                if special & 0b10:
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
        filename = os.path.splitext(os.path.basename(tileset_path))[0]

        if "." in filename:
            # The tileset file is probably LH-compressed.
            filename = os.path.splitext(filename)[0]

        return filename

    def updateObjCacheWH(self, width, height):
        """
        Updates the rendered object data with custom width and height
        """
        # if we don't have to randomise, simply rerender everything
        if globals_.TilesetFilesLoaded[self.tileset] is None \
           or globals_.TilesetInfo is None \
           or globals_.ObjectDefinitions is None \
           or globals_.ObjectDefinitions[self.tileset] is None \
           or globals_.ObjectDefinitions[self.tileset][self.type] is None \
           or globals_.ObjectDefinitions[self.tileset][self.type].rows is None \
           or globals_.ObjectDefinitions[self.tileset][self.type].rows[0] is None \
           or globals_.ObjectDefinitions[self.tileset][self.type].rows[0][0] is None \
           or len(globals_.ObjectDefinitions[self.tileset][self.type].rows[0][0]) == 1:
            # no randomisation info -> exit
            save = (self.width, self.height)
            self.width, self.height = width, height
            self.updateObjCache()
            self.width, self.height = save
            return

        name = self.get_tileset_base_name()
        tile = globals_.ObjectDefinitions[self.tileset][self.type].rows[0][0][1] & 0xFF

        if name not in globals_.TilesetInfo or tile not in globals_.TilesetInfo[name]:
            # no randomisation needed -> exit
            save = (self.width, self.height)
            self.width, self.height = width, height
            self.updateObjCache()
            self.width, self.height = save
            return

        if width == self.width and height == self.height:
            # Width and height did not change, so there is nothing to do
            return

        if height < self.height:
            self.objdata = self.objdata[:height]
        elif height > self.height:
            # add extra rows at the bottom
            if self.isBottomRowSpecial():
                # re-render the bottom row as well
                self.objdata = self.objdata[:-1]
                self.height -= 1

            self.objdata += RenderObject(self.tileset, self.type, self.width, height - self.height)
            self.randomise(0, self.height, self.width, height - self.height)

        if width < self.width:
            for y in range(len(self.objdata)):
                self.objdata[y] = self.objdata[y][:width]
        elif width > self.width:
            new = RenderObject(self.tileset, self.type, width - self.width, height)
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

        # make sure the grabbers don't overlap
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

        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            scene = self.scene()
            if scene is None: return value

            # snap to 24x24
            newpos = value
            newpos.setX(int((newpos.x() + 12) / 24) * 24)
            newpos.setY(int((newpos.y() + 12) / 24) * 24)
            x = newpos.x()
            y = newpos.y()

            # don't let it get out of the boundaries
            if x < 0: newpos.setX(0)
            if x > 24576: newpos.setX(24576)
            if y < 0: newpos.setY(0)
            if y > 12288: newpos.setY(12288)

            # update the data
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

                # updRect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
                # scene.invalidate(updRect)

                scene.invalidate(self.x(), self.y(), self.width * 24, self.height * 24,
                                 QtWidgets.QGraphicsScene.BackgroundLayer)
                # scene.invalidate(newpos.x(), newpos.y(), self.width*24, self.height*24, QtWidgets.QGraphicsScene.BackgroundLayer)

            return newpos

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def paint(self, painter, option, widget):
        """
        Paints the object
        """
        # global theme

        if not self.isSelected():
            return

        painter.setPen(QtGui.QPen(globals_.theme.color('object_lines_s'), 1, QtCore.Qt.DashLine))
        painter.drawRect(self.SelectionRect)
        painter.fillRect(self.SelectionRect, globals_.theme.color('object_fill_s'))

        if self.TLGrabbed:
            painter.fillRect(self.GrabberRectTL, globals_.theme.color('object_lines_r'))
        else:
            painter.fillRect(self.GrabberRectTL, globals_.theme.color('object_lines_s'))

        if self.TRGrabbed:
            painter.fillRect(self.GrabberRectTR, globals_.theme.color('object_lines_r'))
        else:
            painter.fillRect(self.GrabberRectTR, globals_.theme.color('object_lines_s'))

        if self.BLGrabbed:
            painter.fillRect(self.GrabberRectBL, globals_.theme.color('object_lines_r'))
        else:
            painter.fillRect(self.GrabberRectBL, globals_.theme.color('object_lines_s'))

        if self.BRGrabbed:
            painter.fillRect(self.GrabberRectBR, globals_.theme.color('object_lines_r'))
        else:
            painter.fillRect(self.GrabberRectBR, globals_.theme.color('object_lines_s'))

        if self.MTGrabbed:
            painter.fillRect(self.GrabberRectMT, globals_.theme.color('object_lines_r'))
        else:
            painter.fillRect(self.GrabberRectMT, globals_.theme.color('object_lines_s'))

        if self.MLGrabbed:
            painter.fillRect(self.GrabberRectML, globals_.theme.color('object_lines_r'))
        else:
            painter.fillRect(self.GrabberRectML, globals_.theme.color('object_lines_s'))

        if self.MBGrabbed:
            painter.fillRect(self.GrabberRectMB, globals_.theme.color('object_lines_r'))
        else:
            painter.fillRect(self.GrabberRectMB, globals_.theme.color('object_lines_s'))

        if self.MRGrabbed:
            painter.fillRect(self.GrabberRectMR, globals_.theme.color('object_lines_r'))
        else:
            painter.fillRect(self.GrabberRectMR, globals_.theme.color('object_lines_s'))

    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for resizing
        """
        if event.button() == QtCore.Qt.LeftButton:
            if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                new_item = globals_.mainWindow.CreateObject(
                    self.tileset, self.type, self.layer, self.objx,
                    self.objy, self.width, self.height
                )

                # swap the Z values so it doesn't look like the
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
            # start dragging
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
        self.scene().update(updaterect)

    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed for resizing
        """
        if event.buttons() != QtCore.Qt.NoButton and self.dragging:
            # resize it
            dsx = self.dragstartx
            dsy = self.dragstarty

            clickedx = int((event.pos().x() - 12) / 24)
            clickedy = int((event.pos().y() - 12) / 24)

            cx = self.objx
            cy = self.objy

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
        self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())

    def mouseReleaseEvent(self, event):
        """
        Overrides releasing the mouse after a move
        """
        LevelEditorItem.mouseReleaseEvent(self, event)

        self.TLGrabbed = self.TRGrabbed = self.BLGrabbed = self.BRGrabbed = False
        self.MTGrabbed = self.MLGrabbed = self.MBGrabbed = self.MRGrabbed = False
        self.update()


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
            if block[0] == id: bgABlock = block

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
            if block[0] == id: bgBBlock = block

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
        if hasattr(globals_.mainWindow, 'ZoomLevel'):
            grabberWidth = 480 / globals_.mainWindow.ZoomLevel
            if grabberWidth < 4.8: grabberWidth = 4.8
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

    def paint(self, painter, option, widget):
        """
        Paints the zone on screen
        """
        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Paint an indicator line to show the leftmost edge of where entrances
        # can be safely placed.
        if globals_.DrawEntIndicators:
            # This function could be called only when a sprite or entrance is
            # moved or created. If this starts giving trouble, do that.
            self.updateEntranceIndicator()

            # Only draw the indicator if we should
            if self.ent_indicator_show and self.ent_indicator_offset < self.DrawRect.width():
                offset = self.ent_indicator_offset

                painter.setPen(QtGui.QPen(globals_.theme.color('zone_entrance_helper'), 2))
                lineStart = QtCore.QPointF(self.DrawRect.x() + offset, self.DrawRect.y())
                lineEnd = QtCore.QPointF(self.DrawRect.x() + offset, self.DrawRect.y() + self.DrawRect.height())
                painter.drawLine(lineStart, lineEnd)

        # Paint liquids/fog
        if globals_.SpritesShown and globals_.RealViewEnabled:
            zoneRect = self.mapRectToScene(self.DrawRect)
            from sprites import SpriteImage_LiquidOrFog as liquidOrFogType
            from sprites import SpriteImage_BubbleGen as bubbleGenType

            for sprite in globals_.Area.sprites:
                if isinstance(sprite.ImageObj, liquidOrFogType) and sprite.ImageObj.paintZone() and self.id == sprite.ImageObj.zoneId:
                    sprite.ImageObj.realViewZone(painter, zoneRect)
                if isinstance(sprite.ImageObj, bubbleGenType) and hasattr(sprite, 'zoneID') and self.id == sprite.zoneID:
                    sprite.ImageObj.realViewZone(painter, zoneRect)

        # Now paint the borders
        painter.setPen(QtGui.QPen(globals_.theme.color('zone_lines'), 3))
        if self.visibility >= 32 and globals_.RealViewEnabled:
            painter.setBrush(QtGui.QBrush(globals_.theme.color('zone_dark_fill')))
        painter.drawRect(self.DrawRect)

        # And text
        painter.setPen(QtGui.QPen(globals_.theme.color('zone_text'), 3))
        painter.setFont(self.font)
        painter.drawText(self.TitlePos, self.title)

        # And corners ("grabbers")
        GrabberColor = globals_.theme.color('zone_corner')
        painter.fillRect(self.GrabberRectTL, GrabberColor)
        painter.fillRect(self.GrabberRectTR, GrabberColor)
        painter.fillRect(self.GrabberRectBL, GrabberColor)
        painter.fillRect(self.GrabberRectBR, GrabberColor)

        # Draw the bounds indicator rectangle
        if globals_.BoundsDrawn:
            painter.setBrush(QtGui.QBrush(QtGui.QColor.fromRgb(255,255,255,42)))
            painter.setPen(QtCore.Qt.NoPen)
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
            # start dragging
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

        if event.buttons() != QtCore.Qt.NoButton and self.dragging:
            # resize it
            clickedx = int(event.scenePos().x() / 1.5)
            clickedy = int(event.scenePos().y() / 1.5)

            x1 = self.draginitialx1
            y1 = self.draginitialy1
            x2 = self.draginitialx2
            y2 = self.draginitialy2

            # if alt is not held, snap to 8x8 grid
            if QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.AltModifier:
                clickedx = 8 * round(clickedx / 8)
                clickedy = 8 * round(clickedy / 8)
                x1 = 8 * round(x1 / 8)
                y1 = 8 * round(y1 / 8)
                x2 = 8 * round(x2 / 8)
                y2 = 8 * round(y2 / 8)

            MIN_X = 16
            MIN_Y = 16
            MIN_W = 300
            MIN_H = 200

            if self.dragcorner == 1: # TL
                # rect from (x2, y2) to clicked
                x1 = clickedx
                y1 = clickedy
                if x1 < MIN_X: x1 = MIN_X
                if y1 < MIN_Y: y1 = MIN_Y
                if x2 - x1 < MIN_W: x1 = x2 - MIN_W
                if y2 - y1 < MIN_H: y1 = y2 - MIN_H

            elif self.dragcorner == 2: # TR
                # rect from (x1, y2) to clicked
                x2 = clickedx
                y1 = clickedy
                if y1 < MIN_Y: y1 = MIN_Y
                if x2 - x1 < MIN_W: x2 = x1 + MIN_W
                if y2 - y1 < MIN_H: y1 = y2 - MIN_H

            elif self.dragcorner == 3: # BL
                # rect from (x2, y1) to clicked
                x1 = clickedx
                y2 = clickedy
                if x1 < MIN_X: x1 = MIN_X
                if x2 - x1 < MIN_W: x1 = x2 - MIN_W
                if y2 - y1 < MIN_H: y2 = y1 + MIN_H

            elif self.dragcorner == 4: # BR
                # rect from (x1, y1) to clicked
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

            self.scene().update(updaterect)

            globals_.mainWindow.levelOverview.update()

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

        self.font = globals_.NumberFont
        self.objx = x
        self.objy = y
        self.width = width
        self.height = height
        self.id = id
        self.listitem = None

        self.UpdateTitle()
        self.UpdateRects()

        self.setFlag(self.ItemIsMovable, not globals_.LocationsFrozen)
        self.setFlag(self.ItemIsSelectable, not globals_.LocationsFrozen)

        # global globals_.DirtyOverride
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

        # since font never changes, we can just define TitleRect here
        metrics = QtGui.QFontMetrics(self.font)
        self.TitleRect = QtCore.QRectF(metrics.boundingRect(self.title))
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
        qpp.setFillRule(QtCore.Qt.WindingFill)
        qpp.addRect(self.BoundingRectWithoutTitleRect)
        qpp.addRect(self.TitleRect)
        return qpp

    def paint(self, painter, option, widget):
        """
        Paints the location on screen
        """
        # global theme

        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Paint liquids/fog
        if globals_.SpritesShown and globals_.RealViewEnabled:
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
            painter.setPen(QtGui.QPen(globals_.theme.color('location_lines_s'), 1, QtCore.Qt.DashLine))
        painter.drawRect(self.DrawRect)

        # Draw the ID
        painter.setPen(QtGui.QPen(globals_.theme.color('location_text')))
        painter.setFont(self.font)
        painter.drawText(self.TitleRect, self.title)

        # Draw the resizer rectangle, if selected
        if self.isSelected():
            painter.fillRect(self.GrabberRect, globals_.theme.color('location_lines_s'))

    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for resizing
        """
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
        if event.buttons() != QtCore.Qt.NoButton and self.dragging:
            # Resize the location.
            change = self.dragResize(event.scenePos(), self.dragstartx, self.dragstarty)

            if change:
                SetDirty()
                globals_.mainWindow.levelOverview.update()

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
        clickx = common.clamp(int(clicked.x() / 1.5), 0, 65535)
        clicky = common.clamp(int(clicked.y() / 1.5), 0, 65535)

        # if alt is not held, snap to 8x8 grid
        if QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.AltModifier:
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
            self.scene().update(updaterect)
            change = True

        return change

    def delete(self):
        """
        Delete the location from the level
        """
        loclist = globals_.mainWindow.locationList
        globals_.mainWindow.UpdateFlag = True
        loclist.takeItem(loclist.row(self.listitem))
        globals_.mainWindow.UpdateFlag = False
        loclist.selectionModel().clearSelection()
        globals_.Area.locations.remove(self)
        self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())


class SpriteItem(LevelEditorItem):
    """
    Level editor item that represents a sprite
    """
    instanceDef = InstanceDefinition_SpriteItem
    BoundingRect = QtCore.QRectF(0, 0, 24, 24)
    SelectionRect = QtCore.QRectF(0, 0, 23, 23)

    def __init__(self, type_, x, y, data):
        """
        Creates a sprite with specific data
        """
        LevelEditorItem.__init__(self)
        self.setZValue(26000)

        self.font = globals_.NumberFont
        self.type = type_
        self.objx = x
        self.objy = y
        self.spritedata = data
        self.LevelRect = QtCore.QRectF(self.objx / 16, self.objy / 16, 1.5, 1.5)
        self.ChangingPos = False

        self.ImageObj = SLib.SpriteImage(self)

        if 0 <= type_ < globals_.NumSprites:
            self.name = globals_.Sprites[type_].name
        else:
            self.name = "UNKNOWN"

        self.InitializeSprite()

        self.setFlag(self.ItemIsMovable, not globals_.SpritesFrozen)
        self.setFlag(self.ItemIsSelectable, not globals_.SpritesFrozen)

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

    def SetType(self, type_):
        """
        Sets the type of the sprite
        """
        if 0 <= type_ < globals_.NumSprites:
            self.name = globals_.Sprites[type_].name
        else:
            self.name = "UNKNOWN"

        self.setToolTip(globals_.trans.string('Sprites', 0, '[type]', type_, '[name]', self.name))
        self.type = type_

        self.InitializeSprite()

        self.UpdateListItem()

    def ListString(self):
        """
        Returns a string that can be used to describe the sprite in a list
        """
        baseString = globals_.trans.string('Sprites', 1, '[name]', self.name, '[x]', self.objx, '[y]', self.objy)

        # global globals_.SpriteListData
        SpritesThatActivateAnEvent = set(globals_.SpriteListData[0])
        SpritesThatActivateAnEventNyb0 = set(globals_.SpriteListData[1])
        SpritesTriggeredByAnEventNyb1 = set(globals_.SpriteListData[2])
        SpritesTriggeredByAnEventNyb0 = set(globals_.SpriteListData[3])
        StarCoinNumbers = set(globals_.SpriteListData[4])
        SpritesWithSetIDs = set(globals_.SpriteListData[5])
        SpritesWithMovementIDsNyb2 = set(globals_.SpriteListData[6])
        SpritesWithMovementIDsNyb3 = set(globals_.SpriteListData[7])
        SpritesWithMovementIDsNyb5 = set(globals_.SpriteListData[8])
        SpritesWithRotationIDs = set(globals_.SpriteListData[9])
        SpritesWithLocationIDsNyb5 = set(globals_.SpriteListData[10])
        SpritesWithLocationIDsNyb5and0xF = set(globals_.SpriteListData[11])
        SpritesWithLocationIDsNyb4 = set(globals_.SpriteListData[12])
        AndController = set(globals_.SpriteListData[13])
        OrController = set(globals_.SpriteListData[14])
        MultiChainer = set(globals_.SpriteListData[15])
        Random = set(globals_.SpriteListData[16])
        Clam = set(globals_.SpriteListData[17])
        Coin = set(globals_.SpriteListData[18])
        MushroomScrewPlatforms = set(globals_.SpriteListData[19])
        SpritesWithMovementIDsNyb5Type2 = set(globals_.SpriteListData[20])
        BowserFireballArea = set(globals_.SpriteListData[21])
        CheepCheepArea = set(globals_.SpriteListData[22])
        PoltergeistItem = set(globals_.SpriteListData[23])

        # Triggered by an Event
        if self.type in SpritesTriggeredByAnEventNyb1 and self.spritedata[1] != '\0':
            baseString += globals_.trans.string('Sprites', 2, '[event]', self.spritedata[1])
        elif self.type in SpritesTriggeredByAnEventNyb0 and self.spritedata[0] != '\0':
            baseString += globals_.trans.string('Sprites', 2, '[event]', self.spritedata[0])
        elif self.type in AndController:
            baseString += globals_.trans.string('Sprites', 3, '[event1]', self.spritedata[0], '[event2]', self.spritedata[2],
                                       '[event3]', self.spritedata[3], '[event4]', self.spritedata[4])
        elif self.type in OrController:
            baseString += globals_.trans.string('Sprites', 4, '[event1]', self.spritedata[0], '[event2]', self.spritedata[2],
                                       '[event3]', self.spritedata[3], '[event4]', self.spritedata[4])

        # Activates an Event
        if (self.type in SpritesThatActivateAnEvent) and (self.spritedata[1] != '\0'):
            baseString += globals_.trans.string('Sprites', 5, '[event]', self.spritedata[1])
        elif (self.type in SpritesThatActivateAnEventNyb0) and (self.spritedata[0] != '\0'):
            baseString += globals_.trans.string('Sprites', 5, '[event]', self.spritedata[0])
        elif (self.type in MultiChainer):
            baseString += globals_.trans.string('Sprites', 6, '[event1]', self.spritedata[0], '[event2]', self.spritedata[1])
        elif (self.type in Random):
            baseString += globals_.trans.string('Sprites', 7, '[event1]', self.spritedata[0], '[event2]', self.spritedata[2],
                                       '[event3]', self.spritedata[3], '[event4]', self.spritedata[4])

        # Star Coin
        if (self.type in StarCoinNumbers):
            number = (self.spritedata[4] & 15) + 1
            baseString += globals_.trans.string('Sprites', 8, '[num]', number)
        elif (self.type in Clam) and (self.spritedata[5] & 15) == 1:
            baseString += globals_.trans.string('Sprites', 9)

        # Set ID
        if self.type in SpritesWithSetIDs:
            baseString += globals_.trans.string('Sprites', 10, '[id]', self.spritedata[5] & 15)
        elif self.type in Coin and self.spritedata[2] != '\0':
            baseString += globals_.trans.string('Sprites', 11, '[id]', self.spritedata[2])

        # Movement ID (Nybble 2)
        if self.type in SpritesWithMovementIDsNyb2 and self.spritedata[2] != '\0':
            baseString += globals_.trans.string('Sprites', 12, '[id]', self.spritedata[2])
        elif self.type in MushroomScrewPlatforms and self.spritedata[2] >> 4 != '\0':
            baseString += globals_.trans.string('Sprites', 12, '[id]', self.spritedata[2] >> 4)

        # Movement ID (Nybble 3)
        if self.type in SpritesWithMovementIDsNyb3 and self.spritedata[3] >> 4 != '\0':
            baseString += globals_.trans.string('Sprites', 12, '[id]', (self.spritedata[3] >> 4))

        # Movement ID (Nybble 5)
        if self.type in SpritesWithMovementIDsNyb5 and self.spritedata[5] >> 4:
            baseString += globals_.trans.string('Sprites', 12, '[id]', (self.spritedata[5] >> 4))
        elif self.type in SpritesWithMovementIDsNyb5Type2 and self.spritedata[5] != '\0':
            baseString += globals_.trans.string('Sprites', 12, '[id]', self.spritedata[5])

        # Rotation ID
        if self.type in SpritesWithRotationIDs and self.spritedata[5] != '\0':
            baseString += globals_.trans.string('Sprites', 13, '[id]', self.spritedata[5])

        # Location ID (Nybble 5)
        if self.type in SpritesWithLocationIDsNyb5 and self.spritedata[5] != '\0':
            baseString += globals_.trans.string('Sprites', 14, '[id]', self.spritedata[5])
        elif self.type in SpritesWithLocationIDsNyb5and0xF and self.spritedata[5] & 15 != '\0':
            baseString += globals_.trans.string('Sprites', 14, '[id]', self.spritedata[5] & 15)
        elif self.type in SpritesWithLocationIDsNyb4 and self.spritedata[4] != '\0':
            baseString += globals_.trans.string('Sprites', 14, '[id]', self.spritedata[4])
        elif self.type in BowserFireballArea and self.spritedata[3] != '\0':
            baseString += globals_.trans.string('Sprites', 14, '[id]', self.spritedata[3])
        elif self.type in CheepCheepArea:  # nybble 8-9
            if (((self.spritedata[3] & 0xF) << 4) | ((self.spritedata[4] & 0xF0) >> 4)) != '\0':
                baseString += globals_.trans.string('Sprites', 14, '[id]',
                                           (((self.spritedata[3] & 0xF) << 4) | ((self.spritedata[4] & 0xF0) >> 4)))
        elif self.type in PoltergeistItem and (
            ((self.spritedata[4] & 0xF) << 4) | ((self.spritedata[5] & 0xF0) >> 4)) != '\0':  # nybble 10-11
            baseString += globals_.trans.string('Sprites', 14, '[id]',
                                       (((self.spritedata[4] & 0xF) << 4) | ((self.spritedata[5] & 0xF0) >> 4)))

        # Add ')' to the end
        baseString += globals_.trans.string('Sprites', 15)

        return baseString

    def __lt__(self, other):
        # Sort by objx, then objy, then sprite type
        score = lambda sprite: (sprite.objx, sprite.objy, sprite.type)

        return score(self) < score(other)

    def InitializeSprite(self):
        """
        Initializes sprite and creates any auxiliary objects needed
        """
        type_ = self.type

        if not 0 <= type_ < globals_.NumSprites:
            print('Tried to initialize a sprite of type %d, but this is out of range %d.' % (type_, globals_.NumSprites))
            return

        self.name = globals_.Sprites[type_].name
        self.setToolTip(globals_.trans.string('Sprites', 0, '[type]', self.type, '[name]', self.name))

        imgs = globals_.gamedef.getImageClasses()
        if type_ in imgs:
            self.setImageObj(imgs[type_])

    def setImageObj(self, obj):
        """
        Sets a new sprite image object for this SpriteItem
        """
        for auxObj in self.ImageObj.aux:
            if auxObj.scene() is None: continue
            auxObj.scene().removeItem(auxObj)

        self.setZValue(26000)
        self.resetTransform()

        if (self.type in globals_.gamedef.getImageClasses()) and (self.type not in SLib.SpriteImagesLoaded):
            globals_.gamedef.getImageClasses()[self.type].loadImages()
            SLib.SpriteImagesLoaded.add(self.type)

        self.ImageObj = obj(self) if obj else SLib.SpriteImage(self)

        # show auxiliary objects properly
        for aux in self.ImageObj.aux:
            aux.setVisible(globals_.SpriteImagesShown)

        self.UpdateDynamicSizing()

    def UpdateDynamicSizing(self):
        """
        Updates the sizes for dynamically sized sprites
        """
        CurrentRect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        CurrentAuxRects = []
        for auxObj in self.ImageObj.aux:
            CurrentAuxRects.append(QtCore.QRectF(
                auxObj.x() + self.x(),
                auxObj.y() + self.y(),
                auxObj.boundingRect().width(),
                auxObj.boundingRect().height(),
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

        if self.scene() is not None:
            self.scene().update(CurrentRect)
            self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
            for auxUpdateRect in CurrentAuxRects:
                self.scene().update(auxUpdateRect)

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

        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            if self.scene() is None: return value
            if self.ChangingPos: return value

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
            if globals_.OverrideSnapping or QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
                # Snap the smallest amount possible -> 1/16th of a block
                snap_level = 1
            elif self.isSelected() and len(globals_.mainWindow.CurrentSelection) > 1:
                objects_selected = any(isinstance(x, ObjectItem) for x in globals_.mainWindow.CurrentSelection)

                # dragoffsetx and y are in 24 = 1 block units, so convert it to
                # 16 = 1 block units
                drag_offset = QtCore.QPointF(self.dragoffsetx, self.dragoffsety) / 1.5

                origin_pos += drag_offset

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
            x = common.clamp(origin_pos.x(), 0, 16368)
            y = common.clamp(origin_pos.y(), 0, 8176)

            # When snapping, round to the nearest multiple of snap_level. Round
            # up when two multiples are equally far apart.
            origin_pos.setX(int((x + (snap_level / 2)) // snap_level) * snap_level)
            origin_pos.setY(int((y + (snap_level / 2)) // snap_level) * snap_level)

            if drag_offset is not None:
                origin_pos -= drag_offset

            # Move position back to sprite image space by adding the image offset
            # and calculate objx and objy based on the sprite origin position.
            new_pos = QtCore.QPointF(origin_pos + offset_point) * 1.5

            x = origin_pos.x()
            y = origin_pos.y()

            if x != self.objx or y != self.objy:
                updRect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
                self.scene().update(updRect)

                self.LevelRect.moveTo(new_pos / 24)

                for auxObj in self.ImageObj.aux:
                    auxUpdRect = QtCore.QRectF(
                        self.pos() + auxObj.pos(),
                        auxObj.boundingRect().size(),
                    )
                    self.scene().update(auxUpdRect)

                self.scene().update(
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
        if event.button() != QtCore.Qt.LeftButton or QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.ControlModifier:
            if not globals_.SpriteImagesShown:
                oldpos = (self.objx, self.objy)

            LevelEditorItem.mousePressEvent(self, event)

            if not globals_.SpriteImagesShown:
                self.setNewObjPos(*oldpos)

            return

        globals_.mainWindow.CreateSprite(self.objx, self.objy, self.type, self.spritedata)
        globals_.mainWindow.scene.clearSelection()
        self.setSelected(True)

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
        if self.scene() is not None: self.scene().update()

    def paint(self, painter, option=None, widget=None, overrideGlobals=False):
        """
        Paints the sprite
        """

        # Setup stuff
        if option is not None:
            painter.setClipRect(option.exposedRect)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Turn aux things on or off
        for aux in self.ImageObj.aux:
            aux.setVisible(globals_.SpriteImagesShown)

        # Default spritebox
        drawSpritebox = True
        spriteboxRect = QtCore.QRectF(1, 1, 22, 22)

        if globals_.SpriteImagesShown or overrideGlobals:
            self.ImageObj.paint(painter)

            drawSpritebox = self.ImageObj.spritebox.shown

            # Draw the selected-sprite-image overlay box
            if self.isSelected() and (not drawSpritebox or self.ImageObj.size != (16, 16)):
                painter.setPen(QtGui.QPen(globals_.theme.color('sprite_lines_s'), 1, QtCore.Qt.DashLine))
                painter.drawRect(self.SelectionRect)
                painter.fillRect(self.SelectionRect, globals_.theme.color('sprite_fill_s'))

            # Determine the spritebox position
            if drawSpritebox:
                spriteboxRect = self.ImageObj.spritebox.RoundedRect

        # Draw the spritebox if applicable
        if drawSpritebox:
            if self.isSelected():
                painter.setBrush(QtGui.QBrush(globals_.theme.color('spritebox_fill_s')))
                painter.setPen(QtGui.QPen(globals_.theme.color('spritebox_lines_s'), 1))
            else:
                painter.setBrush(QtGui.QBrush(globals_.theme.color('spritebox_fill')))
                painter.setPen(QtGui.QPen(globals_.theme.color('spritebox_lines'), 1))

            if globals_.theme.useRoundedRectangles:
                painter.drawRoundedRect(spriteboxRect, 4, 4)
            else:
                painter.drawRect(spriteboxRect)

            painter.setFont(self.font)
            painter.drawText(spriteboxRect, QtCore.Qt.AlignCenter, str(self.type))

    def scene(self):
        """
        Solves a small bug
        """
        return globals_.mainWindow.scene

    def delete(self):
        """
        Delete the sprite from the level
        """
        self.ImageObj.remove()
        globals_.mainWindow.UpdateFlag = True
        globals_.mainWindow.spriteList.takeSprite(self)
        globals_.mainWindow.UpdateFlag = False
        globals_.mainWindow.spriteList.selectionModel().clearSelection()
        globals_.Area.RemoveSprite(self)
        self.scene().update()  # The zone painters need for the whole thing to update


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
            self.parent = parent
            self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
            self.setFlag(QtWidgets.QGraphicsItem.ItemStacksBehindParent, True)
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
            else:
                self.setPos(0, 0)
                self.BoundingRect = QtCore.QRectF(0, 0, 24, 24)

        def paint(self, painter, option, widget):
            """
            Paints the entrance aux
            """

            painter.setClipRect(option.exposedRect)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)

            if self.parent.enttype == 20:
                # Jumping facing right

                path = QtGui.QPainterPath(QtCore.QPoint(12, 276))
                path.cubicTo(QtCore.QPoint(40, -24), QtCore.QPoint(50, -24), QtCore.QPoint(60, 36))
                path.lineTo(QtCore.QPoint(96, 300))

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

                path = QtGui.QPainterPath(QtCore.QPoint(86, 276))
                path.cubicTo(QtCore.QPoint(58, -24), QtCore.QPoint(48, -24), QtCore.QPoint(38, 36))
                path.lineTo(QtCore.QPoint(2, 300))

                painter.setPen(SLib.OutlinePen)
                painter.drawPath(path)

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

        self.setFlag(self.ItemIsMovable, not globals_.EntrancesFrozen)
        self.setFlag(self.ItemIsSelectable, not globals_.EntrancesFrozen)

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
        globals_.mainWindow.scene.update(old_rect.united(self.getFullRect()))
        globals_.mainWindow.levelOverview.update()

    def paint(self, painter, option, widget):
        """
        Paints the entrance
        """
        # global theme

        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(globals_.theme.color('entrance_fill_s')))
            painter.setPen(QtGui.QPen(globals_.theme.color('entrance_lines_s')))
        else:
            painter.setBrush(QtGui.QBrush(globals_.theme.color('entrance_fill')))
            painter.setPen(QtGui.QPen(globals_.theme.color('entrance_lines')))

        if globals_.theme.useRoundedRectangles:
            painter.drawRoundedRect(self.RoundedRect, 4, 4)
        else:
            painter.drawRect(self.RoundedRect)

        icontype = 0
        enttype = self.enttype
        if enttype == 0 or enttype == 1: icontype = 1  # normal
        if enttype == 2: icontype = 2  # door exit
        if enttype == 3: icontype = 4  # pipe up
        if enttype == 4: icontype = 5  # pipe down
        if enttype == 5: icontype = 6  # pipe left
        if enttype == 6: icontype = 7  # pipe right
        if enttype == 8: icontype = 12  # ground pound
        if enttype == 9: icontype = 13  # sliding
        # 0F/15 is unknown?
        if enttype == 16: icontype = 8  # mini pipe up
        if enttype == 17: icontype = 9  # mini pipe down
        if enttype == 18: icontype = 10  # mini pipe left
        if enttype == 19: icontype = 11  # mini pipe right
        if enttype == 20: icontype = 15  # jump out facing right
        if enttype == 21: icontype = 17  # vine entrance
        if enttype == 23: icontype = 14  # boss battle entrance
        if enttype == 24: icontype = 16  # jump out facing left
        if enttype == 27: icontype = 3  # door entrance

        painter.drawPixmap(0, 0, EntranceItem.EntranceImages[icontype])

        painter.setFont(self.font)
        painter.drawText(3, 12, str(self.entid))

    def delete(self):
        """
        Delete the entrance from the level
        """
        elist = globals_.mainWindow.entranceList
        globals_.mainWindow.UpdateFlag = True
        elist.takeItem(elist.row(self.listitem))
        globals_.mainWindow.UpdateFlag = False
        elist.selectionModel().clearSelection()
        globals_.Area.entrances.remove(self)
        self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())

    def itemChange(self, change, value):
        """
        Handle movement
        """
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
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


class Path:
    """
    Class that manages a path and the line that connects the nodes.
    """

    class NodeData:
        """
        A simple class to store the data belonging to a node.
        """
        def __init__(self, speed, accel, delay):
            self.speed = speed
            self.accel = accel
            self.delay = delay

    def __init__(self, path_id, scene, loops = False):
        self._id = path_id
        self._scene = scene
        self._loops = loops
        self._nodes = []
        self._node_data = []
        self._line_item = PathEditorLineItem(self)
        self._has_line = False

    def add_to_scene(self):
        """
        This adds all nodes to the scene. This function mainly exists to keep
        the API of this class similar to the LevelItem classes.
        """
        for node in self._nodes:
            self._scene.addItem(node)

        if not self._has_line:
            self._scene.addItem(self._line_item)
            self._has_line = True

    def set_id(self, new_id):
        """
        Changes the path's id and returns whether the path's id changed.
        """
        if self._id == new_id:
            return False

        self._id = new_id

        for node in self._nodes:
            node.set_path_id(new_id)

        return True

    def set_node_data(self, node, speed=None, accel=None, delay=None):
        """
        This function can change the speed, accel and delay values associated
        with a specific node. It only changes the parameters that are given, and
        returns whether a change was made.
        """
        data = self._node_data[self.get_index(node)]

        old_data = (data.speed, data.accel, data.delay)

        if speed is not None:
            data.speed = speed
        if accel is not None:
            data.accel = accel
        if delay is not None:
            data.delay = delay

        return (data.speed, data.accel, data.delay) != old_data

    def set_loops(self, value):
        """
        Changes whether the path loops or not. Returns True if the value was
        changed.
        """
        if self._loops == value:
            return False

        self._loops = value
        self._line_item.update_path()

        return True

    def set_freeze(self, frozen):
        """
        (Un)freezes this path, based on the boolean argument. Passing True causes
        all nodes to not be selectable or movable. Passing False does the opposite.
        """
        flag1 = QtWidgets.QGraphicsItem.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.ItemIsMovable

        for node in self._nodes:
            node.setFlag(flag1, not frozen)
            node.setFlag(flag2, not frozen)

    def setVisible(self, value):
        """
        Shows or hides the path.
        """
        for node in self._nodes:
            node.setVisible(value)

        self._line_item.setVisible(value)

    def get_loops(self):
        return self._loops

    def get_index(self, node):
        return self._nodes.index(node)

    def get_node_data(self, index):
        """
        Returns a tuple containing the data required for the binary representation
        of the node at the specified index: x, y, speed, accel, delay.
        """
        node = self._nodes[index]
        data = self._node_data[index]

        return node.objx, node.objy, data.speed, data.accel, data.delay

    def get_points(self):
        """
        Returns a list of the positions of the nodes of this path. If this path
        loops, the first node's position is also the last position in the list.
        """
        points = []

        for node in self._nodes:
            points.append(QtCore.QPointF(node.objx, node.objy) * 1.5)

        if self._loops and points:
            points.append(points[0])

        return points

    def get_data_for_node(self, node_id):
        data = self._node_data[node_id]
        return data.speed, data.accel, data.delay

    def add_node(self, x, y, speed = 0.5, accel = 0.00498, delay = 0, index = None, add_to_list = True, add_to_scene = True):
        """
        Adds a node to the path at the specified position. If no index is given,
        the node is appended to the end of the path.
        """

        if index is None:
            index = len(self._nodes)

        node = PathItem(x, y, self._id, index, self)

        self._nodes.insert(index, node)
        self._node_data.insert(index, Path.NodeData(speed, accel, delay))

        if add_to_scene:
            self._scene.addItem(node)

        if add_to_list:
            node.positionChanged = globals_.mainWindow.HandlePathPosChange
            globals_.mainWindow.pathList.addItem(node.listitem)

        # Update ids of all nodes after the newly created node
        for new_id, later_node in enumerate(self._nodes[index + 1:], index + 1):
            later_node.update_id(new_id)

        # Update line item
        if not self._has_line:
            self._scene.addItem(self._line_item)
            self._has_line = True

        self._line_item.update_path()

        return node

    def remove_node(self, index):
        """
        Removes the node at a given index. Returns whether the path is empty after
        this node has been removed.
        """
        node = self._nodes[index]

        # hacky stuff
        plist = globals_.mainWindow.pathList

        globals_.mainWindow.UpdateFlag = True
        plist.takeItem(plist.row(node.listitem))
        globals_.mainWindow.UpdateFlag = False

        plist.selectionModel().clearSelection()

        # Remove node from internal lists
        del self._nodes[index]
        del self._node_data[index]

        # Update ids of later nodes
        for new_id, later_node in enumerate(self._nodes[index:], index):
            later_node.nodeid = new_id
            later_node.update()

        # Update line item
        self._line_item.update_path()

        return len(self._nodes) == 0

    def move_node(self, node, new_id):
        """
        This function moves a given node to a new position in the path. All items
        between the original position of the given node and the new id are shifted
        by 1 position.
        """
        old_id = self.get_index(node)

        if old_id == new_id:
            return

        node_data = self._node_data[old_id]

        if old_id < new_id:
            # Move all nodes [old_id: new_id] one position back
            self._nodes[old_id:new_id] = self._nodes[old_id + 1:new_id + 1]
            self._node_data[old_id:new_id] = self._node_data[old_id + 1:new_id + 1]
        else:
            # Move all nodes [new_id: old_id] one position forward
            self._nodes[new_id + 1:old_id + 1] = self._nodes[new_id:old_id]
            self._node_data[new_id + 1:old_id + 1] = self._node_data[new_id:old_id]

        # Move node to position new_id
        self._nodes[new_id] = node
        self._node_data[new_id] = node_data

        # Update all the nodes that moved, and the line item
        for new_id, node in enumerate(self._nodes):
            node.update_id(new_id)

        self._line_item.update_path()

    def node_moved(self, node):
        self._line_item.update_path()

    def __len__(self):
        """
        Returns the number of nodes.
        """
        return len(self._nodes)


class PathItem(LevelEditorItem):
    """
    Level editor item that represents a path node
    """
    instanceDef = InstanceDefinition_PathItem
    BoundingRect = QtCore.QRectF(0, 0, 24, 24)
    RoundedRect = QtCore.QRectF(1, 1, 22, 22)

    def __init__(self, objx, objy, path_id, node_id, parent):
        """
        Creates a path node with specific data
        """
        LevelEditorItem.__init__(self)

        self.font = globals_.NumberFont
        self.objx = objx
        self.objy = objy
        self.pathid = path_id
        self.nodeid = node_id
        self.path = parent

        self.listitem = ListWidgetItem_SortsByOther(self, self.ListString())

        self.LevelRect = QtCore.QRectF(self.objx / 16, self.objy / 16, 1.5, 1.5)
        self.setFlag(self.ItemIsMovable, not globals_.PathsFrozen)
        self.setFlag(self.ItemIsSelectable, not globals_.PathsFrozen)

        old_snap = globals_.OverrideSnapping
        globals_.OverrideSnapping = True

        globals_.DirtyOverride += 1
        self.setPos(objx * 1.5, objy * 1.5)
        globals_.DirtyOverride -= 1

        globals_.OverrideSnapping = old_snap

        self.setZValue(25003)
        self.UpdateTooltip()
        self.UpdateListItem()

    def set_path_id(self, new_id):
        self.pathid = new_id

        self.UpdateTooltip()
        self.listitem.setText(self.ListString())
        self.update()

    def UpdateTooltip(self):
        """
        Updates the path node's tooltip
        """
        self.setToolTip(globals_.trans.string('Paths', 0, '[path]', self.pathid, '[node]', self.nodeid))

    def ListString(self):
        """
        Returns a string that can be used to describe the path node in a list
        """
        return globals_.trans.string('Paths', 1, '[path]', self.pathid, '[node]', self.nodeid)

    def __lt__(self, other):
        return (self.pathid, self.nodeid) < (other.pathid, other.nodeid)

    def updatePos(self):
        """
        Our x/y was changed, update path info
        """
        print("Deprecated: PathItem.updatePos was called")

    def update_id(self, new_id):
        """
        Path was changed, find our new node id
        """
        self.nodeid = new_id
        self.UpdateTooltip()
        self.UpdateListItem()
        self.update()

    def paint(self, painter, option, widget):
        """
        Paints the path node
        """
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setClipRect(option.exposedRect)

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(globals_.theme.color('path_fill_s')))
            painter.setPen(QtGui.QPen(globals_.theme.color('path_lines_s')))
        else:
            painter.setBrush(QtGui.QBrush(globals_.theme.color('path_fill')))
            painter.setPen(QtGui.QPen(globals_.theme.color('path_lines')))

        if globals_.theme.useRoundedRectangles:
            painter.drawRoundedRect(self.RoundedRect, 4, 4)
        else:
            painter.drawRect(self.RoundedRect)

        painter.setFont(self.font)
        painter.drawText(4, 11, str(self.pathid))
        painter.drawText(4, 9 + QtGui.QFontMetrics(self.font).height(), str(self.nodeid))

    def delete(self):
        """
        Delete the path from the level
        """
        was_last = self.path.remove_node(self.path.get_index(self))

        if was_last:
            globals_.Area.paths.remove(self.path)


class PathEditorLineItem(QtWidgets.QGraphicsPathItem):
    """
    Level editor item to draw a line between the path nodes that belong to the
    same path.
    """

    def __init__(self, path):
        """
        Creates a path line that belongs to a given path.
        """
        super().__init__()

        self._path = path

        self.setFlag(self.ItemIsMovable, False)
        self.setFlag(self.ItemIsSelectable, False)

        color = globals_.theme.color('path_connector')
        self.setPen(QtGui.QPen(color, 3, join=QtCore.Qt.RoundJoin, cap=QtCore.Qt.RoundCap))

        self.update_path()
        self.setZValue(25002)

    def update_path(self):
        """
        Updates the path. This should be called whenever at least one of the
        nodes of the path moves, is added or is deleted.
        """
        points = self._path.get_points()

        line_path = QtGui.QPainterPath()
        line_path.addPolygon(QtGui.QPolygonF(points))

        old_rect = self.boundingRect()

        self.setPath(line_path)

        # Bug in Qt? The old rect of the path is not updated, so artifacts
        # remain on the scene if we do not update the scene manually...
        if old_rect:
            globals_.mainWindow.scene.update(old_rect)


class CommentItem(LevelEditorItem):
    """
    Level editor item that represents a in-level comment
    """
    instanceDef = InstanceDefinition_CommentItem
    BoundingRect = QtCore.QRectF(-8, -8, 48, 48)
    SelectionRect = QtCore.QRectF(-4, -4, 4, 4)
    Circle = QtCore.QRectF(0, 0, 32, 32)

    def __init__(self, x, y, text=''):
        """
        Creates a in-level comment
        """
        LevelEditorItem.__init__(self)
        zval = 50000
        self.zval = zval

        self.text = text

        self.objx = x
        self.objy = y
        self.listitem = None
        self.LevelRect = (QtCore.QRectF(self.objx / 16, self.objy / 16, 2.25, 2.25))

        self.setFlag(self.ItemIsMovable, not globals_.CommentsFrozen)
        self.setFlag(self.ItemIsSelectable, not globals_.CommentsFrozen)

        # global globals_.DirtyOverride
        globals_.DirtyOverride += 1
        self.setPos(int(x * 1.5), int(y * 1.5))
        globals_.DirtyOverride -= 1

        self.setZValue(zval + 1)
        self.UpdateTooltip()

        self.TextEdit = QtWidgets.QPlainTextEdit()
        self.TextEditProxy = globals_.mainWindow.scene.addWidget(self.TextEdit)
        self.TextEditProxy.setZValue(self.zval)
        self.TextEditProxy.setCursor(QtCore.Qt.IBeamCursor)
        self.TextEditProxy.boundingRect = lambda self: QtCore.QRectF(0, 0, 4000, 4000)
        self.TextEdit.setVisible(False)
        self.TextEdit.setMaximumWidth(192)
        self.TextEdit.setMaximumHeight(128)
        self.TextEdit.setPlainText(self.text)
        self.TextEdit.textChanged.connect(self.handleTextChanged)
        self.reposTextEdit()

    def mousePressEvent(self, e):
        """
        Override the mouse press event to delegate it to the text edit
        if required. This ensures the user can select the first characters of the
        comment text.
        """
        # Also check the position to only allow clicks in the region that
        # overlaps with the text edit.
        if self.isSelected() and e.pos().x() > 22 and e.pos().y() > 15:
            e.ignore()
            return

        # We're not selected yet. Pass the event to the base class so we get
        # selected properly.
        LevelEditorItem.mousePressEvent(self, e)

    def UpdateTooltip(self):
        """
        For compatibility, just in case
        """
        self.setToolTip(globals_.trans.string('Comments', 1, '[x]', self.objx, '[y]', self.objy))

    def ListString(self):
        """
        Returns a string that can be used to describe the comment in a list
        """
        t = self.OneLineText()
        return globals_.trans.string('Comments', 0, '[x]', self.objx, '[y]', self.objy, '[text]', t)

    def OneLineText(self):
        """
        Returns the text of this comment in a format that can be written on one line
        """
        t = str(self.text)
        if not t.strip():
            t = globals_.trans.string('Comments', 3)

        while '\n\n' in t:
            t = t.replace('\n\n', '\n')

        t = t.replace('\n', globals_.trans.string('Comments', 2))

        f = None
        if self.listitem is not None: f = self.listitem.font()
        t2 = clipStr(t, 128, f)
        if t2 is not None: t = t2 + '...'

        return t

    def paint(self, painter, option, widget):
        """
        Paints the comment
        """
        # global theme

        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(globals_.theme.color('comment_fill_s')))
            p = QtGui.QPen(globals_.theme.color('comment_lines_s'))
            p.setWidth(3)
            painter.setPen(p)
        else:
            painter.setBrush(QtGui.QBrush(globals_.theme.color('comment_fill')))
            p = QtGui.QPen(globals_.theme.color('comment_lines'))
            p.setWidth(3)
            painter.setPen(p)

        painter.drawEllipse(self.Circle)
        if not self.isSelected(): painter.setOpacity(.5)
        painter.drawPixmap(4, 4, GetIcon('comments', 24).pixmap(24, 24))
        painter.setOpacity(1)

        # Set the text edit visibility
        try:
            shouldBeVisible = (len(globals_.mainWindow.scene.selectedItems()) == 1) and self.isSelected()
        except RuntimeError:
            shouldBeVisible = False
        try:
            self.TextEdit.setVisible(shouldBeVisible)
        except RuntimeError:
            # Sometimes Qt deletes my text edit.
            # Therefore, I need to make a new one.
            self.TextEdit = QtWidgets.QPlainTextEdit()
            self.TextEditProxy = globals_.mainWindow.scene.addWidget(self.TextEdit)
            self.TextEditProxy.setZValue(self.zval)
            self.TextEditProxy.setCursor(QtCore.Qt.IBeamCursor)
            self.TextEditProxy.BoundingRect = QtCore.QRectF(0, 0, 4000, 4000)
            self.TextEditProxy.boundingRect = lambda self: self.BoundingRect
            self.TextEdit.setMaximumWidth(192)
            self.TextEdit.setMaximumHeight(128)
            self.TextEdit.setPlainText(self.text)
            self.TextEdit.textChanged.connect(self.handleTextChanged)
            self.reposTextEdit()
            self.TextEdit.setVisible(shouldBeVisible)

    def handleTextChanged(self):
        """
        Handles the text being changed
        """
        self.text = str(self.TextEdit.toPlainText())
        if hasattr(self, 'textChanged'): self.textChanged(self)

    def reposTextEdit(self):
        """
        Repositions the text edit
        """
        self.TextEditProxy.setPos((self.objx * 3 / 2) + 24, (self.objy * 3 / 2) + 16)

    def handlePosChange(self, oldx, oldy):
        """
        Handles the position changing
        """
        self.reposTextEdit()

        # Manual scene update :(
        w = 192 + 24
        h = 128 + 24
        oldx *= 1.5
        oldy *= 1.5
        oldRect = QtCore.QRectF(oldx, oldy, w, h)
        self.scene().update(oldRect)

    def delete(self):
        """
        Delete the comment from the level
        """
        clist = globals_.mainWindow.commentList
        globals_.mainWindow.UpdateFlag = True
        clist.takeItem(clist.row(self.listitem))
        globals_.mainWindow.UpdateFlag = False
        clist.selectionModel().clearSelection()
        p = self.TextEditProxy
        p.setSelected(False)
        globals_.mainWindow.scene.removeItem(p)
        globals_.Area.comments.remove(self)
        self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        globals_.mainWindow.SaveComments()

