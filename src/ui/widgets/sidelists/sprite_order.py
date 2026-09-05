import base64

from PyQt6 import QtCore, QtWidgets

import globals_
from src.ui.widgets.sprite_table import SpriteTableWidget
from src.data.level.items.sprite import SpriteItem
from src.data.level.dirty import SetDirty


class SpriteOrderList(QtWidgets.QWidget):
    """
    Sprite order viewer, similar to the Sprite List, but without sorting.
    """

    def __init__(self):
        super().__init__()

        self.is_batch_add = False

        headers = [globals_.trans.string('Sprites', 21), globals_.trans.string('Sprites', 22)]

        self.table = SpriteTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Hide row numbers
        vertical_header = self.table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False)

        horizontal_header = self.table.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.table.setSortingEnabled(False)
        self.table.setMouseTracking(True) # For 'entered' signal

        # Only select one item at a time, and select the entire row
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        self.table.itemSelectionChanged.connect(self.select_item)
        self.table.itemDoubleClicked.connect(SpriteItem.moveToSprite)
        self.table.itemEntered.connect(self.toolTip)

        self.move_up_btn = QtWidgets.QPushButton(globals_.trans.string('Sprites', 25))
        self.move_down_btn = QtWidgets.QPushButton(globals_.trans.string('Sprites', 26))

        self.move_up_btn.clicked.connect(lambda: self.moveSprite(0))
        self.move_down_btn.clicked.connect(lambda: self.moveSprite(1))

        # Set initial button states
        self.select_item()

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.move_up_btn, 0, 0)
        layout.addWidget(self.move_down_btn, 0, 1)
        layout.addWidget(self.table, 1, 0, 1, 2)
        self.setLayout(layout)

    def getRowFor(self, sprite):
        """
        Returns the row number for a given sprite, or -1 if no row exists.
        """
        for i in range(self.table.rowCount()):
            id_item = self.table.item(i, 0)
            if id_item is not None and id_item.data(QtCore.Qt.ItemDataRole.UserRole) == sprite:
                return i

        return -1

    def prepareBatchAdd(self):
        """
        Enables batch-adding mode
        """
        self.is_batch_add = True

    def endBatchAdd(self):
        """
        Disables batch-adding mode
        """
        self.is_batch_add = False
        self.table.resizeRowsToContents()

    def addSprite(self, sprite):
        """
        Adds a sprite to the table
        """
        # add a new row
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Add the sprite id
        id_item = QtWidgets.QTableWidgetItem()
        id_item.setData(QtCore.Qt.ItemDataRole.DisplayRole, sprite.sprite_num)
        id_item.setData(QtCore.Qt.ItemDataRole.UserRole, sprite)
        id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, id_item)

        # Also add the sprite name
        name_item = QtWidgets.QTableWidgetItem(sprite.name)
        name_item.setData(QtCore.Qt.ItemDataRole.UserRole, sprite)
        name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, name_item)

        if not self.is_batch_add:
            # Profiling shows that this function is quite expensive, so if we're
            # in a batch add, don't resize the rows until the very end.
            self.table.resizeRowsToContents()

    def takeSprite(self, sprite):
        """
        Removes a sprite from the table
        """
        row = self.getRowFor(sprite)
        if row < 0:
            return

        self.table.removeRow(row)

    def moveSprite(self, action: int):
        """
        Moves a sprite up/down in the list
        """
        items = self.table.selectedItems()
        if not items:
            return

        # Items will always be a pair (the two columns of the table)
        # We only need a single item, and can only select one at a time,
        # so it's safe to just use item 0 here
        sprite = items[0].data(QtCore.Qt.ItemDataRole.UserRole)

        try:
            spr_idx = globals_.Area.sprites.index(sprite)
        except ValueError:
            return

        globals_.Area.sprites.pop(spr_idx)

        if action == 0:
            # Moving up
            new_idx = spr_idx - 1
        elif action == 1:
            # Moving down
            new_idx = spr_idx + 1
        else:
            new_idx = spr_idx

        globals_.Area.sprites.insert(new_idx, sprite)
        SetDirty()

        # Refresh the list
        self.clear()
        for spr in globals_.Area.sprites:
            self.addSprite(spr)

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

    def select_item(self):
        """
        Toggle buttons depending on the selected item index
        """
        row = self.table.currentRow()
        row_num = self.table.rowCount()

        enable_up = True
        enable_down = True

        # -1 means we have nothing selected
        if row == -1:
            enable_up = False
            enable_down = False
        else:
            if row == 0:
                enable_up = False
            if row == row_num - 1:
                enable_down = False

        self.move_up_btn.setEnabled(enable_up)
        self.move_down_btn.setEnabled(enable_down)

    def toolTip(self, item):
        """
        Creates a tooltip for the item
        """
        sprite = item.data(QtCore.Qt.ItemDataRole.UserRole)

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

    # Functions that are passed on to self.table
    def selectionModel(self):
        return self.table.selectionModel()

    def row(self, item):
        return self.table.row(item)
