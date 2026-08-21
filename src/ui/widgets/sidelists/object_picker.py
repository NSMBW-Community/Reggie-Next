from PyQt6 import QtCore, QtGui, QtWidgets

import globals_
from src.data.tileset.object.renderers import RenderObject
from src.data.tileset.tile.tileset_tile import TilesetTile


class ObjectPickerWidget(QtWidgets.QListView):
    """
    Widget that shows a list of available objects
    """

    def __init__(self):
        """
        Initializes the widget
        """
        QtWidgets.QListView.__init__(self)
        self.setFlow(QtWidgets.QListView.Flow.LeftToRight)
        self.setLayoutMode(QtWidgets.QListView.LayoutMode.SinglePass)
        self.setMovement(QtWidgets.QListView.Movement.Static)
        self.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
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
        model = self.models[id_]
        self.setModel(model)
        self.setCurrentIndex(model.index(sel, 0, QtCore.QModelIndex()))

    def currentChanged(self, current, previous):
        """
        Throws a signal when the selected object changed
        """
        self.ObjChanged.emit(current.row())

    def HandleObjReplace(self, index):
        """
        Throws a signal when the selected object is used as a replacement
        """
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
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
            if painter is None:
                return

            if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            model = index.model()
            if model is None:
                return

            p = model.data(index, QtCore.Qt.ItemDataRole.DecorationRole)
            painter.drawPixmap(option.rect.x() + 2, option.rect.y() + 2, p)
            # painter.drawText(option.rect, str(index.row()))

        def sizeHint(self, option, index):
            """
            Returns the size for the object
            """
            model = index.model()
            if model is None:
                return QtCore.QSize(76, 76)

            p = model.data(index, QtCore.Qt.ItemDataRole.UserRole)
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

        def rowCount(self, parent=None):
            """
            Required by Qt
            """
            return len(self.items)

        def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
            """
            Get what we have for a specific row
            """
            if not index.isValid():
                return None

            n = index.row()
            if n < 0:
                return None

            if n >= len(self.items):
                return None

            if role == QtCore.Qt.ItemDataRole.DecorationRole:
                return self.ritems[n]

            if role == QtCore.Qt.ItemDataRole.BackgroundRole:
                return QtWidgets.QApplication.instance().palette().base()

            if role == QtCore.Qt.ItemDataRole.UserRole:
                return self.itemsize[n]

            if role == QtCore.Qt.ItemDataRole.ToolTipRole:
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
                pm.fill(QtCore.Qt.GlobalColor.transparent)
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
                                unknown_override = globals_.Overrides[globals_.OVERRIDE_UNKNOWN]
                                if unknown_override is None:
                                    continue
                                p.drawPixmap(x, y, unknown_override.getCurrentTile())
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
