import base64

from PyQt5 import QtWidgets, QtGui, QtCore

import globals_
from tiles import RenderObject, TilesetTile
from ui import ListWidgetWithToolTipSignal
from misc import LoadSpriteData, LoadSpriteListData, LoadSpriteCategories
from spriteeditor import SpriteEditorWidget

class LevelOverviewWidget(QtWidgets.QWidget):
    """
    Widget that shows an overview of the level and can be clicked to move the view
    """
    moveIt = QtCore.pyqtSignal(float, float)

    def __init__(self):
        """
        Constructor for the level overview widget
        """
        QtWidgets.QWidget.__init__(self)
        self.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding))

        self.bgbrush = QtGui.QBrush(globals_.theme.color('bg'))
        self.objbrush = QtGui.QBrush(globals_.theme.color('overview_object'))
        self.viewbrush = QtGui.QBrush(globals_.theme.color('overview_zone_fill'))
        self.view = QtCore.QRectF()
        self.spritebrush = QtGui.QBrush(globals_.theme.color('overview_sprite'))
        self.entrancebrush = QtGui.QBrush(globals_.theme.color('overview_entrance'))
        self.locationbrush = QtGui.QBrush(globals_.theme.color('overview_location_fill'))

        self.Reset()

        self.Xposlocator = 0
        self.Yposlocator = 0
        self.Hlocator = 50
        self.Wlocator = 80
        self.mainWindowScale = 1

    def Reset(self):
        """
        Resets the max and scale variables
        """
        self.maxX = 100
        self.maxY = 40
        self.Rescale()

    def mouseMoveEvent(self, event):
        """
        Handles mouse movement over the widget
        """
        QtWidgets.QWidget.mouseMoveEvent(self, event)

        if event.buttons() == QtCore.Qt.LeftButton:
            self.moveIt.emit(event.pos().x() * self.posmult, event.pos().y() * self.posmult)

    def mousePressEvent(self, event):
        """
        Handles mouse pressing events over the widget
        """
        QtWidgets.QWidget.mousePressEvent(self, event)

        if event.button() == QtCore.Qt.LeftButton:
            self.moveIt.emit(event.pos().x() * self.posmult, event.pos().y() * self.posmult)

    def paintEvent(self, event):
        """
        Paints the level overview widget
        """
        if not hasattr(globals_.Area, 'layers'):
            # fixes race condition where this widget is painted after
            # the level is created, but before it's loaded
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        self.CalcSize()
        self.Rescale()

        painter.fillRect(event.rect(), self.bgbrush)
        painter.scale(self.scale, self.scale)

        transform = QtGui.QTransform() / 24

        dr = painter.drawRect
        fr = painter.fillRect

        b = self.viewbrush
        painter.setPen(QtGui.QPen(globals_.theme.color('overview_zone_lines'), 1))

        for zone in globals_.Area.zones:
            rect = transform.mapRect(zone.sceneBoundingRect())
            fr(rect, b)
            dr(rect)

        b = self.objbrush

        for layer in globals_.Area.layers:
            for obj in layer:
                fr(obj.LevelRect, b)

        b = self.spritebrush

        for sprite in globals_.Area.sprites:
            fr(sprite.LevelRect, b)

        b = self.entrancebrush

        for ent in globals_.Area.entrances:
            fr(ent.LevelRect, b)

        b = self.locationbrush
        painter.setPen(QtGui.QPen(globals_.theme.color('overview_location_lines'), 1))

        for location in globals_.Area.locations:
            rect = transform.mapRect(location.sceneBoundingRect())
            fr(rect, b)
            dr(rect)

        painter.setPen(QtGui.QPen(globals_.theme.color('overview_viewbox'), 1))

        scalar = 1 / (24 * self.mainWindowScale)
        painter.drawRect(QtCore.QRectF(
            scalar * self.Xposlocator, scalar * self.Yposlocator,
            scalar * self.Wlocator, scalar * self.Hlocator
        ))

    def CalcSize(self):
        """
        Calculates self.maxX and self.maxY.
        """
        if globals_.Area is None:
            # fixes race condition where this widget's size is calculated
            # after the level is created, but before it's loaded
            self.maxX = 100
            self.maxY = 40
            return

        transform = QtGui.QTransform() / 24
        rect = QtCore.QRectF()

        for zone in globals_.Area.zones:
            rect |= transform.mapRect(zone.sceneBoundingRect())

        for layer in globals_.Area.layers:
            for obj in layer:
                rect |= obj.LevelRect

        for sprite in globals_.Area.sprites:
            rect |= sprite.LevelRect

        for ent in globals_.Area.entrances:
            rect |= ent.LevelRect

        for location in globals_.Area.locations:
            rect |= transform.mapRect(location.sceneBoundingRect())

        _, _, self.maxX, self.maxY = rect.getCoords()

    def Rescale(self):
        """
        Calculates self.scale and self.posmult.
        """
        x_scale = self.width() / (self.maxX + 45)
        y_scale = self.height() / (self.maxY + 25)

        self.scale = max(0.002, min(x_scale, y_scale))
        self.posmult = 24 / self.scale


class ObjectPickerWidget(QtWidgets.QListView):
    """
    Widget that shows a list of available objects
    """

    def __init__(self):
        """
        Initializes the widget
        """
        QtWidgets.QListView.__init__(self)
        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setLayoutMode(QtWidgets.QListView.SinglePass)
        self.setMovement(QtWidgets.QListView.Static)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setWrapping(True)

        self.models = [
            ObjectPickerWidget.ObjectListModel(),
            ObjectPickerWidget.ObjectListModel(),
            ObjectPickerWidget.ObjectListModel(),
            ObjectPickerWidget.ObjectListModel(),
        ]

        self.setModel(self.models[0])

        self.setItemDelegate(ObjectPickerWidget.ObjectItemDelegate())

        self.clicked.connect(self.HandleObjReplace)

    def LoadFromTilesets(self):
        """
        Renders all the object previews
        """
        for i in range(4):
            self.models[i].LoadFromTileset(i)

    def ShowTileset(self, id_):
        """
        Shows a specific tileset in the picker
        """
        sel = self.currentIndex().row()
        self.setModel(self.models[id_])
        self.setCurrentIndex(self.model().index(sel, 0, QtCore.QModelIndex()))

    def currentChanged(self, current, previous):
        """
        Throws a signal when the selected object changed
        """
        self.ObjChanged.emit(current.row())

    def HandleObjReplace(self, index):
        """
        Throws a signal when the selected object is used as a replacement
        """
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
            self.ObjReplace.emit(index.row())

    ObjChanged = QtCore.pyqtSignal(int)
    ObjReplace = QtCore.pyqtSignal(int)

    class ObjectItemDelegate(QtWidgets.QAbstractItemDelegate):
        """
        Handles tileset objects and their rendering
        """

        def __init__(self):
            """
            Initializes the delegate
            """
            QtWidgets.QAbstractItemDelegate.__init__(self)

        def paint(self, painter, option, index):
            """
            Paints an object
            """
            if option.state & QtWidgets.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            p = index.model().data(index, QtCore.Qt.DecorationRole)
            painter.drawPixmap(option.rect.x() + 2, option.rect.y() + 2, p)
            # painter.drawText(option.rect, str(index.row()))

        def sizeHint(self, option, index):
            """
            Returns the size for the object
            """
            p = index.model().data(index, QtCore.Qt.UserRole)
            return p
            # return QtCore.QSize(76,76)

    class ObjectListModel(QtCore.QAbstractListModel):
        """
        Model containing all the objects in a tileset
        """

        def __init__(self):
            """
            Initializes the model
            """
            self.items = []
            self.ritems = []
            self.itemsize = []
            QtCore.QAbstractListModel.__init__(self)

            # for i in range(256):
            #    self.items.append(None)
            #    self.ritems.append(None)

        def rowCount(self, parent=None):
            """
            Required by Qt
            """
            return len(self.items)

        def data(self, index, role=QtCore.Qt.DisplayRole):
            """
            Get what we have for a specific row
            """
            if not index.isValid(): return None
            n = index.row()
            if n < 0: return None
            if n >= len(self.items): return None

            if role == QtCore.Qt.DecorationRole:
                return self.ritems[n]

            if role == QtCore.Qt.BackgroundRole:
                return QtWidgets.qApp.palette().base()

            if role == QtCore.Qt.UserRole:
                return self.itemsize[n]

            if role == QtCore.Qt.ToolTipRole:
                return self.tooltips[n]

            return None

        def LoadFromTileset(self, idx):
            """
            Renders all the object previews for the model
            """
            if globals_.ObjectDefinitions[idx] is None: return

            self.beginResetModel()

            self.items = []
            self.ritems = []
            self.itemsize = []
            self.tooltips = []
            defs = globals_.ObjectDefinitions[idx]

            for i in range(256):
                if defs[i] is None: break
                obj = RenderObject(idx, i, defs[i].width, defs[i].height, True)
                self.items.append(obj)

                pm = QtGui.QPixmap(defs[i].width * 24, defs[i].height * 24)
                pm.fill(QtCore.Qt.transparent)
                p = QtGui.QPainter()
                p.begin(pm)
                y = 0
                isAnim = False

                for row in obj:
                    x = 0
                    for tile_num in row:
                        if tile_num > 0:
                            tile = globals_.Tiles[tile_num]
                            if tile is None:
                                p.drawPixmap(x, y, globals_.Overrides[globals_.OVERRIDE_UNKNOWN].getCurrentTile())
                            elif isinstance(tile.main, QtGui.QImage):
                                p.drawImage(x, y, tile.main)
                            else:
                                p.drawPixmap(x, y, tile.main)

                            if isinstance(tile, TilesetTile) and tile.isAnimated: isAnim = True
                        x += 24
                    y += 24
                p.end()

                self.ritems.append(pm)
                self.itemsize.append(QtCore.QSize(defs[i].width * 24 + 4, defs[i].height * 24 + 4))
                if (idx == 0) and (i in globals_.ObjDesc):
                    if isAnim:
                        self.tooltips.append(globals_.trans.string('Objects', 4, '[id]', i, '[desc]', globals_.ObjDesc[i]))
                    else:
                        self.tooltips.append(globals_.trans.string('Objects', 3, '[id]', i, '[desc]', globals_.ObjDesc[i]))
                elif isAnim:
                    self.tooltips.append(globals_.trans.string('Objects', 2, '[id]', i))
                else:
                    self.tooltips.append(globals_.trans.string('Objects', 1, '[id]', i))

            self.endResetModel()


class StampChooserWidget(QtWidgets.QListView):
    """
    Widget that shows a list of available stamps
    """
    selectionChangedSignal = QtCore.pyqtSignal()

    def __init__(self):
        """
        Initializes the widget
        """
        QtWidgets.QListView.__init__(self)

        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setLayoutMode(QtWidgets.QListView.SinglePass)
        self.setMovement(QtWidgets.QListView.Static)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setWrapping(True)

        self.model = StampListModel()
        self.setModel(self.model)

        self.setItemDelegate(StampChooserWidget.StampItemDelegate())

    class StampItemDelegate(QtWidgets.QStyledItemDelegate):
        """
        Handles stamp rendering
        """

        def __init__(self):
            """
            Initializes the delegate
            """
            QtWidgets.QStyledItemDelegate.__init__(self)

        def createEditor(self, parent, option, index):
            """
            Creates a stamp name editor
            """
            return QtWidgets.QLineEdit(parent)

        def setEditorData(self, editor, index):
            """
            Sets the data for the stamp name editor from the data at index
            """
            editor.setText(index.model().data(index, QtCore.Qt.UserRole + 1))

        def setModelData(self, editor, model, index):
            """
            Set the data in the model for the data at index
            """
            index.model().setData(index, editor.text())

        def paint(self, painter, option, index):
            """
            Paints a stamp
            """

            if option.state & QtWidgets.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            painter.drawPixmap(option.rect.x() + 2, option.rect.y() + 2, index.model().data(index, QtCore.Qt.DecorationRole))

        def sizeHint(self, option, index):
            """
            Returns the size for the stamp
            """
            return index.model().data(index, QtCore.Qt.DecorationRole).size() + QtCore.QSize(4, 4)

    def addStamp(self, stamp):
        """
        Adds a stamp
        """
        self.model.addStamp(stamp)

    def removeStamp(self, stamp):
        """
        Removes a stamp
        """
        self.model.removeStamp(stamp)

    def currentlySelectedStamp(self):
        """
        Returns the currently selected stamp
        """
        idxobj = self.currentIndex()
        if idxobj.row() == -1: return
        return self.model.items[idxobj.row()]

    def selectionChanged(self, selected, deselected):
        """
        Called when the selection changes.
        """
        val = super().selectionChanged(selected, deselected)
        self.selectionChangedSignal.emit()
        return val


class StampListModel(QtCore.QAbstractListModel):
    """
    Model containing all the stamps
    """

    def __init__(self):
        """
        Initializes the model
        """
        QtCore.QAbstractListModel.__init__(self)

        self.items = []  # list of Stamp objects

    def rowCount(self, parent=None):
        """
        Required by Qt
        """
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        Get what we have for a specific row
        """
        if not index.isValid(): return None
        n = index.row()
        if n < 0: return None
        if n >= len(self.items): return None

        if role == QtCore.Qt.DecorationRole:
            return self.items[n].Icon

        elif role == QtCore.Qt.BackgroundRole:
            return QtWidgets.qApp.palette().base()

        elif role == QtCore.Qt.UserRole:
            return self.items[n].Name

        elif role == QtCore.Qt.StatusTipRole:
            return self.items[n].Name

        else:
            return None

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        """
        Set data for a specific row
        """
        if not index.isValid(): return None
        n = index.row()
        if n < 0: return None
        if n >= len(self.items): return None

        if role == QtCore.Qt.UserRole:
            self.items[n].Name = value

    def addStamp(self, stamp):
        """
        Adds a stamp
        """

        # Start resetting
        self.beginResetModel()

        # Add the stamp to self.items
        self.items.append(stamp)

        # Finish resetting
        self.endResetModel()

    def removeStamp(self, stamp):
        """
        Removes a stamp
        """

        # Start resetting
        self.beginResetModel()

        # Remove the stamp from self.items
        self.items.remove(stamp)

        # Finish resetting
        self.endResetModel()


class Stamp:
    """
    Class that represents a stamp in the list
    """

    def __init__(self, ReggieClip=None, Name=''):
        """
        Initializes the stamp
        """

        self.ReggieClip = ReggieClip
        self.Name = Name
        self.Icon = self.render()

    def renderPreview(self):
        """
        Renders the stamp preview
        """

        minX, minY, maxX, maxY = 24576, 12288, 0, 0

        layers, sprites = globals_.mainWindow.getEncodedObjects(self.ReggieClip)

        # Go through the sprites and find the maxs and mins
        for spr in sprites:

            br = spr.getFullRect()

            x1 = br.topLeft().x()
            y1 = br.topLeft().y()
            x2 = x1 + br.width()
            y2 = y1 + br.height()

            if x1 < minX: minX = x1
            if x2 > maxX: maxX = x2
            if y1 < minY: minY = y1
            if y2 > maxY: maxY = y2

        # Go through the objects and find the maxs and mins
        for layer in layers:
            for obj in layer:
                x1 = (obj.objx * 24)
                x2 = x1 + (obj.width * 24)
                y1 = (obj.objy * 24)
                y2 = y1 + (obj.height * 24)

                if x1 < minX: minX = x1
                if x2 > maxX: maxX = x2
                if y1 < minY: minY = y1
                if y2 > maxY: maxY = y2

        # Calculate offset amounts (snap to 24x24 increments)
        offsetX = int(minX // 24) * 24
        offsetY = int(minY // 24) * 24
        drawOffsetX = offsetX - minX
        drawOffsetY = offsetY - minY

        # Go through the things again and shift them by the offset amount
        for spr in sprites:
            spr.objx -= offsetX / 1.5
            spr.objy -= offsetY / 1.5
        for layer in layers:
            for obj in layer:
                obj.objx -= offsetX // 24
                obj.objy -= offsetY // 24

        # Calculate the required pixmap size
        pixmapSize = (maxX - minX, maxY - minY)

        # Create the pixmap, and a painter
        pix = QtGui.QPixmap(pixmapSize[0], pixmapSize[1])
        pix.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pix)
        painter.setRenderHint(painter.Antialiasing)

        # Paint all objects
        objw, objh = int(pixmapSize[0] // 24) + 1, int(pixmapSize[1] // 24) + 1
        for layer in reversed(layers):
            tmap = []
            for i in range(objh):
                tmap.append([-1] * objw)
            for obj in layer:
                startx = int(obj.objx)
                starty = int(obj.objy)

                desty = starty
                for row in obj.objdata:
                    destrow = tmap[desty]
                    destx = startx
                    for tile in row:
                        if tile > 0:
                            destrow[destx] = tile
                        destx += 1
                    desty += 1

                painter.save()
                desty = 0
                for row in tmap:
                    destx = 0
                    for tile in row:
                        if tile > 0:
                            if globals_.Tiles[tile] is None: continue
                            r = globals_.Tiles[tile].main
                            painter.drawPixmap(destx + drawOffsetX, desty + drawOffsetY, r)
                        destx += 24
                    desty += 24
                painter.restore()

        # Paint all sprites
        for spr in sprites:
            offx = ((spr.objx + spr.ImageObj.xOffset) * 1.5) + drawOffsetX
            offy = ((spr.objy + spr.ImageObj.yOffset) * 1.5) + drawOffsetY

            painter.save()
            painter.translate(offx, offy)

            spr.paint(painter, None, None, True)

            painter.restore()

            # Paint any auxiliary things
            for aux in spr.ImageObj.aux:
                painter.save()
                painter.translate(
                    offx + aux.x(),
                    offy + aux.y(),
                )

                aux.paint(painter, None, None)

                painter.restore()

        # End painting
        painter.end()
        del painter

        # Scale it
        maxW, maxH = 96, 96
        w, h = pix.width(), pix.height()
        if w > h and w > maxW:
            pix = pix.scaledToWidth(maxW)
        elif h > w and h > maxH:
            pix = pix.scaledToHeight(maxH)

        # Return it
        return pix

    def render(self):
        """
        Renders the stamp icon, preview AND text
        """

        # Get the preview icon
        prevIcon = self.renderPreview()

        # Calculate the total size of the icon
        textSize = self.calculateTextSize(self.Name)
        totalWidth = max(prevIcon.width(), textSize.width())
        totalHeight = prevIcon.height() + 2 + textSize.height()

        # Make a pixmap and painter
        pix = QtGui.QPixmap(int(totalWidth), int(totalHeight))
        pix.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pix)

        # Draw the preview
        iconXOffset = (totalWidth - prevIcon.width()) / 2
        painter.drawPixmap(int(iconXOffset), 0, prevIcon)

        # Draw the text
        textRect = QtCore.QRectF(0, prevIcon.height() + 2, totalWidth, textSize.height())
        painter.setFont(QtGui.QFont())
        painter.drawText(textRect, QtCore.Qt.AlignTop | QtCore.Qt.TextWordWrap, self.Name)

        # Return the pixmap
        return pix

    @staticmethod
    def calculateTextSize(text):
        """
        Calculates the size of text. Crops to 96 pixels wide.
        """
        fontMetrics = QtGui.QFontMetrics(QtGui.QFont())
        fontRect = fontMetrics.boundingRect(QtCore.QRect(0, 0, 96, 48), QtCore.Qt.TextWordWrap, text)
        w, h = fontRect.width(), fontRect.height()
        return QtCore.QSizeF(min(w, 96), h)

    def update(self):
        """
        Updates the stamp icon
        """
        self.Icon = self.render()


class SpritePickerWidget(QtWidgets.QTreeWidget):
    """
    Widget that shows a list of available sprites
    """

    def __init__(self):
        """
        Initializes the widget
        """
        super().__init__()
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.currentItemChanged.connect(self.HandleItemChange)

        LoadSpriteData()
        LoadSpriteListData()
        LoadSpriteCategories()
        self.LoadItems()

    def UpdateSpriteNames(self):
        """
        Updates all spritenames
        """
        for viewname, view, nodelist in globals_.SpriteCategories:
            for cnode in nodelist:
                for i in range(cnode.childCount()):
                    snode = cnode.child(i)

                    if snode == self.NoSpritesFound:
                        # Don't change the name of the "no sprites found" marker
                        continue

                    id_ = snode.data(0, QtCore.Qt.UserRole)

                    if 0 <= id_ < globals_.NumSprites:
                        sdef = globals_.Sprites[id_]
                    else:
                        sdef = None

                    if sdef is None:
                        name = 'UNKNOWN'
                    else:
                        name = sdef.name

                    snode.setText(0, globals_.trans.string('Sprites', 18, '[id]', id_, '[name]', name))

    def LoadItems(self):
        """
        Loads tree widget items
        """
        self.clear()

        for viewname, view, nodelist in globals_.SpriteCategories:
            for n in nodelist: nodelist.remove(n)
            for catname, category in view:
                cnode = QtWidgets.QTreeWidgetItem()
                cnode.setText(0, catname)
                cnode.setData(0, QtCore.Qt.UserRole, -1)

                isSearch = (catname == globals_.trans.string('Sprites', 16))
                if isSearch:
                    self.SearchResultsCategory = cnode
                    SearchableItems = []

                for id_ in category:
                    snode = QtWidgets.QTreeWidgetItem()
                    if id_ == 9999:
                        snode.setText(0, globals_.trans.string('Sprites', 17))
                        snode.setData(0, QtCore.Qt.UserRole, -2)
                        self.NoSpritesFound = snode
                    else:
                        if 0 <= id_ < globals_.NumSprites:
                            sdef = globals_.Sprites[id_]
                        else:
                            sdef = None

                        if sdef is None:
                            sname = "UNKNOWN"
                        else:
                            sname = sdef.name

                        snode.setText(0, globals_.trans.string('Sprites', 18, '[id]', id_, '[name]', sname))
                        snode.setData(0, QtCore.Qt.UserRole, id_)

                    if isSearch:
                        SearchableItems.append(snode)

                    cnode.addChild(snode)

                self.addTopLevelItem(cnode)
                cnode.setHidden(True)
                nodelist.append(cnode)

        self.ShownSearchResults = SearchableItems
        self.NoSpritesFound.setHidden(True)

        self.itemClicked.connect(self.HandleSprReplace)

        self.SwitchView(globals_.SpriteCategories[0])

    def SwitchView(self, view):
        """
        Changes the selected sprite view
        """
        for i in range(self.topLevelItemCount()):
            self.topLevelItem(i).setHidden(True)

        for node in view[2]:
            node.setHidden(False)

    def HandleItemChange(self, current, previous):
        """
        Throws a signal when the selected object changed
        """
        if current is None: return
        id_ = current.data(0, QtCore.Qt.UserRole)
        if id_ != -1:
            self.SpriteChanged.emit(id_)

    def SetSearchString(self, searchfor):
        """
        Shows the items containing that string
        """
        check = self.SearchResultsCategory

        rawresults = self.findItems(searchfor, QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
        results = list(filter((lambda x: x.parent() == check), rawresults))

        for x in self.ShownSearchResults: x.setHidden(True)
        for x in results: x.setHidden(False)
        self.ShownSearchResults = results

        self.NoSpritesFound.setHidden(bool(results))
        self.SearchResultsCategory.setExpanded(True)

    def HandleSprReplace(self, item, column):
        """
        Throws a signal when the selected sprite is used as a replacement
        """
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
            id_ = item.data(0, QtCore.Qt.UserRole)
            if id_ != -1:
                self.SpriteReplace.emit(id_)

    SpriteChanged = QtCore.pyqtSignal(int)
    SpriteReplace = QtCore.pyqtSignal(int)


class SpriteList(QtWidgets.QWidget):
    """
    Sprite list viewer
    """
    # TODO: Make this translatable

    # These are straight from the spritedata xml
    # Don't translate these
    idtypes = (
        "Star Set", "Rotation", "Two Way Line", "Water Ball", "Mushroom",
        "Group", "Bolt", "Target Event", "Triggering Event", "Collection",
        "Location", "Physics", "Message", "Path", "Path Movement", "Red Coin",
        "Hill", "Stretch", "Ray", "Coaster", "Bubble Cannon", "Burner",
        "Wiggling", "Panel", "Colony", "Entrance", "Path Node"
    )

    # This should be translated
    idtype_names = (
        "Any",
        "Star Set ID", "Rotation ID", "Two Way Line ID", "Water Ball ID",
        "Mushroom ID", "Group ID", "Bolt ID", "Target Event ID",
        "Triggering Event ID", "Collection ID", "Location ID", "Physics ID",
        "Message ID", "Path ID", "Path Movement ID", "Red Coin ID", "Hill ID",
        "Stretch ID", "Ray ID", "Coaster ID", "Bubble Cannon ID", "Burner ID",
        "Wiggling ID", "Panel ID", "Colony ID", "Entrance ID", "Path Node ID"
    )

    def __init__(self):
        super().__init__()

        self.searchbox = QtWidgets.QLineEdit()
        self.searchbox.textEdited.connect(self.search)

        self.filterbox = QtWidgets.QComboBox()
        self.filterbox.currentIndexChanged.connect(self.filter)

        self.is_batch_add = False

        # Set of row ids
        self.SearchResults = set()

        self.table = QtWidgets.QTableWidget(0, len(self.idtype_names) + 1)
        headers = ["ID", "Name"] + list(self.idtype_names[1:])
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False) # hide row numbers
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setMouseTracking(True) # for 'entered' signal
        self.table.itemDoubleClicked.connect(self.moveToSprite)
        self.table.itemEntered.connect(self.toolTip)

        # populate filter box
        self.filterbox.addItems(self.idtype_names)

        # Make a layout
        search_label = QtWidgets.QLabel(globals_.trans.string('Sprites', 19) + ":")
        filter_label = QtWidgets.QLabel("Filter" + ":")

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(search_label, 0, 0)
        layout.addWidget(self.searchbox, 0, 1)

        layout.addWidget(filter_label, 1, 0)
        layout.addWidget(self.filterbox, 1, 1)

        # colspan = 2, since we want the table to use both
        # columns
        layout.addWidget(self.table, 2, 0, 1, 2)

        self.setLayout(layout)

    def search(self, text):
        """
        Search the table
        """
        if text == "":
            # Optimisation for when no search is given -> show everything
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)

            self.SearchResults = set(range(self.table.rowCount()))
            return

        results = self.table.findItems(text, QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
        rows = set(item.row() for item in results if item is not None)

        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, row not in rows)

        self.SearchResults = rows

    def filter(self, newidx):
        """
        Filters all search results
        """
        for row in self.SearchResults:
            self.filterRow(row, newidx)

        # Only show columns 0 (id), 1 (name) and newidx + 1 (the filtered column)
        for col in range(self.table.columnCount()):
            if col in (0, 1, newidx + 1):
                self.table.showColumn(col)
            else:
                self.table.hideColumn(col)

    def filterRow(self, row, filteridx = 0):
        """
        Filters one row of the table.
        """
        # Special case: no filtering
        if filteridx == 0:
            self.table.setRowHidden(row, False)
            return

        # Get the sprite defintion and the id type that is filtered by.
        filtertype = self.idtypes[filteridx - 1]
        sprite = self.table.item(row, 0).data(QtCore.Qt.UserRole)

        if 0 <= sprite.type < globals_.NumSprites:
            sdef = globals_.Sprites[sprite.type]
        else:
            # No sprite definition -> hide
            self.table.setRowHidden(row, True)
            return

        # Loop over every field of the sprite and hide every row whose sprite
        # has no fields with the correct idtype.
        for field in sdef.fields:
            # Only values (1) and lists (2) have idtypes, so ignore the other
            # fields.
            if field[0] < 1 or field[0] > 2:
                continue

            # The idtype is the last element in the field tuple.
            if field[-1] == filtertype:
                self.table.setRowHidden(row, False)
                return

        # No field had the correct id type, so hide this row.
        self.table.setRowHidden(row, True)

    def updateItems(self):
        self.search(self.searchbox.text())
        self.filter(self.filterbox.currentIndex())

    def getRowFor(self, sprite):
        """
        Returns the row number for a given sprite, or -1 if no row exists.
        """
        for i in range(self.table.rowCount()):
            id_item = self.table.item(i, 0)
            if id_item.data(QtCore.Qt.UserRole) == sprite:
                return i

        return -1

    def prepareBatchAdd(self):
        """
        Disables sorting, because sorting every time a new element is added is
        pretty bad performance-wise. We'll sort them once afterwards.
        """
        self.is_batch_add = True
        self.table.setSortingEnabled(False)

    def endBatchAdd(self):
        """
        Re-enables sorting after a batch adding is finished.
        """
        self.is_batch_add = False
        self.table.resizeRowsToContents()
        self.table.setSortingEnabled(True)
        self.updateItems()

    def addSprite(self, sprite):
        """
        Adds a sprite to the table
        """
        if not self.is_batch_add:
            # temporarily disable sorting so our new row
            # gets added properly
            self.table.setSortingEnabled(False)

        # add a new row
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Add the sprite id
        id_item = QtWidgets.QTableWidgetItem()
        id_item.setData(QtCore.Qt.DisplayRole, sprite.type)
        id_item.setData(QtCore.Qt.UserRole, sprite)
        id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.table.setItem(row, 0, id_item)

        # Also add the sprite name
        name_item = QtWidgets.QTableWidgetItem(sprite.name)
        name_item.setData(QtCore.Qt.UserRole, sprite)
        name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.table.setItem(row, 1, name_item)

        if not self.is_batch_add:
            # Profiling shows that this function is quite expensive, so if we're
            # in a batch add, don't resize the rows until the very end.
            self.table.resizeRowsToContents()

        # Add an id for every idtype. These items should not be editable or
        # selectable.
        mask = ~(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable)
        ids = self.getIDsFor(sprite)

        for col, idtype in enumerate(self.idtypes):
            id_values = ids.get(idtype, "")

            if len(id_values) == 1:
                id_values = id_values[0]

            entry_item = QtWidgets.QTableWidgetItem(str(id_values))
            entry_item.setFlags(entry_item.flags() & mask)

            self.table.setItem(row, 2 + col, entry_item)

        # re-enable sorting
        if not self.is_batch_add:
            self.table.setSortingEnabled(True)
            self.updateItems()

    def updateSprite(self, sprite):
        """
        Updates the IDs of the given sprite
        """
        ids = self.getIDsFor(sprite)

        # Temporarily disable sorting so our updates happen to the same row.
        self.table.setSortingEnabled(False)
        row = self.getRowFor(sprite)

        # Skip the first columns (the id and name)
        for i in range(2, self.table.columnCount()):
            id_values = ids.get(self.idtypes[i - 2], [""])

            if len(id_values) == 1:
                id_values = id_values[0]

            item = self.table.item(row, i)
            item.setText(str(id_values))

        # re-enable sorting
        self.table.setSortingEnabled(True)

    def takeSprite(self, sprite):
        """
        Removes a sprite from the table
        """
        row = self.getRowFor(sprite)

        if row < 0:
            return

        self.table.removeRow(row)

        # Update search results
        if row in self.SearchResults:
            self.SearchResults = set(x if x < row else x - 1 for x in self.SearchResults if x != row)

    def clear(self):
        """
        Clears the sprite list.
        """
        # Ensure all rows are removed. For some reason, just calling the
        # 'clearContents' method does not remove the underlying items, causing
        # way too many items to be searched after a few Area switches.
        for i in range(self.table.rowCount() - 1, -1, -1):
            self.table.removeRow(i)

        self.table.clearContents()
        self.searchbox.setText("")
        self.filterbox.setCurrentIndex(0)
        self.SearchResults = set()

    def toolTip(self, item):
        """
        Creates a tooltip for the item
        """
        sprite = item.data(QtCore.Qt.UserRole)

        if sprite is None:
            return

        img = sprite.renderInLevelIcon()
        byteArray = QtCore.QByteArray()
        buf = QtCore.QBuffer(byteArray)
        img.save(buf, 'PNG')
        byteObj = bytes(byteArray)
        b64 = base64.b64encode(byteObj).decode('utf-8')

        item.setToolTip(
            '<img src="data:image/png;base64,' + b64 + '" />'
        )

    # TODO: Consider moving this to the SpriteItem class
    @staticmethod
    def moveToSprite(item):
        """
        Moves the view to the sprite and selects it.
        """
        sprite = item.data(QtCore.Qt.UserRole)

        if sprite is None:
            return

        sprite.ensureVisible(xMargin=192, yMargin=192)
        sprite.scene().clearSelection()
        sprite.setSelected(True)

    @staticmethod
    def getIDsFor(sprite):
        """
        Returns an (idtype, [values]) dict for every
        idtype this sprite has
        """
        if not 0 <= sprite.type < globals_.NumSprites:
            return {}

        sdef = globals_.Sprites[sprite.type]
        res = {}
        decoder = SpriteEditorWidget.PropertyDecoder()
        data = sprite.spritedata

        for field in sdef.fields:
            # Only values (1) and fields (2) have idtypes, so ignore all other
            # fields.
            if field[0] < 1 or field[0] > 2:
                continue

            # The idtype is the last element in the field tuple, bit is the
            # third element in the field tuple (for both list and value).
            idtype = field[-1]

            # No id type specified
            if idtype is None:
                continue

            value = decoder.retrieve(data, field[2])

            try:
                res[idtype].append(value)
            except KeyError:
                res[idtype] = [value]

        return res

    # Functions that are passed on to self.table
    def selectionModel(self):
        return self.table.selectionModel()

    def row(self, item):
        return self.table.row(item)

    def clearSelection(self):
        self.table.setCurrentItem(None)
