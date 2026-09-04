import base64

from PyQt6 import QtCore, QtWidgets

import globals_
from src.data.sprite.spritefield.list import ListSpriteField
from src.data.sprite.spritefield.sprite_field import SpriteField
from src.data.sprite.spritefield.value import ValueSpriteField
from src.ui.widgets.spriteeditor.propertydecoders.property_decoder import (
    PropertyDecoder,
)


class SpriteList(QtWidgets.QWidget):
    """
    Sprite list viewer
    """

    # These are straight from the spritedata xml
    # Don't translate these
    idtypes = (
        "Star Set", "Rotation", "Two Way Line", "Water Ball", "Mushroom",
        "Group", "Bolt", "Target Event", "Triggering Event", "Collection",
        "Location", "Physics", "Message", "Path", "Path Movement", "Red Coin",
        "Hill", "Stretch", "Ray", "Coaster", "Bubble Cannon", "Burner",
        "Wiggling", "Panel", "Colony", "Entrance", "Path Node"
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

        # Probably not the bext way to do this?
        class SpriteTableWidget(QtWidgets.QTableWidget):
            def keyPressEvent(self, event):
                if event.key() == QtCore.Qt.Key.Key_Space or event.key() == QtCore.Qt.Key.Key_Return:
                    SpriteList().moveToSprite(self.currentItem())

                super().keyPressEvent(event)

        sprite_translations = globals_.trans.stringList('Sprites', 23)
        self.table = SpriteTableWidget(0, len(sprite_translations if sprite_translations is not None else []) + 1)
        headers = [globals_.trans.string('Sprites', 21), globals_.trans.string('Sprites', 22)] + list(sprite_translations[1:] if sprite_translations is not None else [])
        self.table.setHorizontalHeaderLabels(headers)
        vertical_header = self.table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False) # hide row numbers
        horizontal_header = self.table.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setMouseTracking(True) # for 'entered' signal
        self.table.itemDoubleClicked.connect(self.moveToSprite)
        self.table.itemEntered.connect(self.toolTip)

        # populate filter box
        self.filterbox.addItems(globals_.trans.stringList('Sprites', 23))

        # Make a layout
        search_label_text = globals_.trans.string('Sprites', 19)
        filter_label_text = globals_.trans.string('Sprites', 20)
        search_label = QtWidgets.QLabel((search_label_text + ":") if search_label_text is not None else "")
        filter_label = QtWidgets.QLabel((filter_label_text + ":") if filter_label_text is not None else "")

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

        results = self.table.findItems(text, QtCore.Qt.MatchFlag.MatchContains | QtCore.Qt.MatchFlag.MatchRecursive)
        rows = {item.row() for item in results if item is not None}

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
        row_item = self.table.item(row, 0)
        if row_item is None:
            return
        sprite = row_item.data(QtCore.Qt.ItemDataRole.UserRole)

        if 0 <= sprite.sprite_num < globals_.NumSprites:
            sdef = globals_.Sprites[sprite.sprite_num]
        else:
            # No sprite definition -> hide
            self.table.setRowHidden(row, True)
            return

        # Loop over every field of the sprite and hide every row whose sprite
        # has no fields with the correct idtype.
        for field in sdef.fields:
            # Only values (1) and lists (2) have idtypes, so ignore the other
            # fields.
            if not isinstance(field, (ListSpriteField, ValueSpriteField)):
                continue

            # The idtype is the last element in the field tuple.
            if field.idtype == filtertype:
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
            if id_item is not None and id_item.data(QtCore.Qt.ItemDataRole.UserRole) == sprite:
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

        # Add an id for every idtype. These items should not be editable or
        # selectable.
        mask = ~(QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsSelectable)
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
            if item is None:
                continue

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
            self.SearchResults = {x if x < row else x - 1 for x in self.SearchResults if x != row}

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

    # TODO: Consider moving this to the SpriteItem class
    @staticmethod
    def moveToSprite(item):
        """
        Moves the view to the sprite and selects it.
        """
        sprite = item.data(QtCore.Qt.ItemDataRole.UserRole)

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
        if not 0 <= sprite.sprite_num < globals_.NumSprites:
            return {}

        sdef = globals_.Sprites[sprite.sprite_num]
        res = {}
        decoder = PropertyDecoder(SpriteField())
        data = sprite.spritedata

        for field in sdef.fields:
            # Only values (1) and fields (2) have idtypes, so ignore all other
            # fields.
            if not isinstance(field, (ValueSpriteField, ListSpriteField)):
                continue

            # The idtype is the last element in the field tuple, bit is the
            # third element in the field tuple (for both list and value).
            idtype = field.idtype

            # No id type specified
            if idtype is None:
                continue

            value = decoder.retrieve(data, field.bit)

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
