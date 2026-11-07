from PyQt6 import QtCore, QtGui, QtWidgets

from data import globals_
from data.tileset.object.renderers import RenderObject
from data.tileset.tile.tileset_tile import TilesetTile


class ObjectPickerWidget(QtWidgets.QListView):
    """
    Widget that shows a list of available objects
    """

    def __init__(self) -> None:
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

    def LoadFromTilesets(self) -> None:
        """
        Renders all the object previews
        """
        for i in range(4):
            self.models[i].LoadFromTileset(i)

    def ShowTileset(self, id: int) -> None:
        """
        Shows a specific tileset in the picker
        """
        sel = self.currentIndex().row()
        model = self.models[id]
        self.setModel(model)
        self.setCurrentIndex(model.index(sel, 0, QtCore.QModelIndex()))

    def currentChanged(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex) -> None:
        """
        Throws a signal when the selected object changed
        """
        self.ObjChanged.emit(current.row())

    def HandleObjReplace(self, index: QtCore.QModelIndex) -> None:
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

        def __init__(self) -> None:
            """
            Initializes the delegate
            """
            QtWidgets.QAbstractItemDelegate.__init__(self)

        def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
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

        def sizeHint(self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtCore.QSize:
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

        def __init__(self) -> None:
            """
            Initializes the model
            """
            self.items: list[list[list[int]]] = []
            self.ritems: list[QtGui.QPixmap] = []
            self.itemsize: list[QtCore.QSize] = []
            QtCore.QAbstractListModel.__init__(self)

        def rowCount(self, parent: QtWidgets.QWidget | None = None) -> int:
            """
            Required by Qt
            """
            return len(self.items)

        def data(
            self,
            index: QtCore.QModelIndex,
            role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole,
        ) -> QtGui.QPixmap | QtGui.QBrush | QtCore.QSize | str | None:
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

        def LoadFromTileset(self, idx: int) -> None:
            """
            Renders all the object previews for the model
            """
            self.beginResetModel()

            self.items = []
            self.ritems = []
            self.itemsize = []
            self.tooltips: list[str] = []

            if globals_.ObjectDefinitions[idx] is None:
                self.endResetModel()
                return

            defs = globals_.ObjectDefinitions[idx]

            for i in range(256):
                object_def = defs[i]
                if object_def is None: break
                obj = RenderObject(idx, i, object_def.width, object_def.height, True)
                self.items.append(obj)

                pm = QtGui.QPixmap(object_def.width * 24, object_def.height * 24)
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
                self.itemsize.append(QtCore.QSize(object_def.width * 24 + 4, object_def.height * 24 + 4))
                if (idx == 0) and (i in globals_.ObjDesc):
                    if isAnim:
                        self.tooltips.append(globals_.trans.string('palette.object.tooltip_desc_anim', ('[id]', i), ('[desc]', globals_.ObjDesc[i])))
                    else:
                        self.tooltips.append(globals_.trans.string('palette.object.tooltip_desc', ('[id]', i), ('[desc]', globals_.ObjDesc[i])))
                elif isAnim:
                    self.tooltips.append(globals_.trans.string('palette.object.tooltip_anim', ('[id]', i)))
                else:
                    self.tooltips.append(globals_.trans.string('palette.object.tooltip', ('[id]', i)))

            self.endResetModel()
