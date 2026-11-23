import base64

from PyQt6 import QtCore, QtWidgets

from data import globals_
from data.level.items.sprite import SpriteItem
from data.sprite.sprite_id_type import SpriteIDType
from data.editorfield.list import ListEditorField
from data.editorfield.editor_field import EditorField
from data.editorfield.value import ValueEditorField
from ui.widgets.sprite_table import SpriteTableWidget
from ui.widgets.propertydecoders.property_decoder import (
    PropertyDecoder,
)


class SpriteList(QtWidgets.QWidget):
    """
    Sprite list viewer
    """

    def __init__(self) -> None:
        super().__init__()

        self.searchbox = QtWidgets.QLineEdit()
        self.searchbox.textEdited.connect(self.search)

        self.filterbox = QtWidgets.QComboBox()
        self.filterbox.currentIndexChanged.connect(self.filter)

        self.is_batch_add = False

        # Set of row ids
        self.SearchResults = set()

        self.table = SpriteTableWidget()
        self.set_table_columns()

        vertical_header = self.table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setVisible(False) # hide row numbers
        horizontal_header = self.table.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.table.setSortingEnabled(True)
        self.table.setMouseTracking(True) # for 'entered' signal

        # Only select one item at a time, and select the entire row
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        self.table.itemDoubleClicked.connect(SpriteItem.moveToSprite)
        self.table.itemEntered.connect(self.toolTip)

        # Make a layout
        search_label_text = globals_.trans.string('common.search_colon')
        filter_label_text = globals_.trans.string('palette.sprite.current.filter')
        search_label = QtWidgets.QLabel(search_label_text if search_label_text is not None else "")
        filter_label = QtWidgets.QLabel((filter_label_text) if filter_label_text is not None else "")

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

    def set_table_columns(self) -> None:
        """
        Sets the table columns and headers based on the Sprite ID-Type info
        """
        idtypes_list: list[str] = [globals_.trans.string('palette.sprite.current.any')]
        for type in globals_.SpriteIDTypes:
            idtypes_list.append(type.name)

        self.table.setColumnCount(len(idtypes_list if idtypes_list is not None else []) + 1)

        headers = [globals_.trans.string('common.id'), globals_.trans.string('common.name')] + idtypes_list[1:]
        self.table.setHorizontalHeaderLabels(headers)

        # Populate filter box
        self.filterbox.clear()
        self.filterbox.addItems(idtypes_list)

        # Update each sprite to make sure it gets an ID
        for sprite in globals_.Area.sprites:
            self.updateSprite(sprite)

    def search(self, text: str) -> None:
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

    def filter(self, newidx: int) -> None:
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

    def filterRow(self, row: int, filteridx: int = 0) -> None:
        """
        Filters one row of the table.
        """
        # Special case: no filtering
        if filteridx == 0:
            self.table.setRowHidden(row, False)
            return

        # Get the sprite defintion and the id type that is filtered by.
        filtertype = globals_.SpriteIDTypes[filteridx - 1].id_type
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
            if not isinstance(field, (ListEditorField, ValueEditorField)):
                continue

            # The idtype is the last element in the field tuple.
            if field.idtype == filtertype:
                self.table.setRowHidden(row, False)
                return

        # No field had the correct id type, so hide this row.
        self.table.setRowHidden(row, True)

    def updateItems(self) -> None:
        self.search(self.searchbox.text())
        self.filter(self.filterbox.currentIndex())

    def getRowFor(self, sprite: SpriteItem) -> int:
        """
        Returns the row number for a given sprite, or -1 if no row exists.
        """
        for i in range(self.table.rowCount()):
            id_item = self.table.item(i, 0)
            if id_item is not None and id_item.data(QtCore.Qt.ItemDataRole.UserRole) == sprite:
                return i

        return -1

    def prepareBatchAdd(self) -> None:
        """
        Disables sorting, because sorting every time a new element is added is
        pretty bad performance-wise. We'll sort them once afterwards.
        """
        self.is_batch_add = True
        self.table.setSortingEnabled(False)

    def endBatchAdd(self) -> None:
        """
        Re-enables sorting after a batch adding is finished.
        """
        self.is_batch_add = False
        self.table.resizeRowsToContents()
        self.table.setSortingEnabled(True)
        self.updateItems()

    def addSprite(self, sprite: SpriteItem) -> None:
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
        name_item = QtWidgets.QTableWidgetItem(globals_.Sprites[sprite.sprite_num].name)
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

        for col, idtype in enumerate(globals_.SpriteIDTypes):
            id_values = ids.get(idtype.id_type, '')
            id_value = -1
            has_multiple_ids = True

            if isinstance(id_values, list) and len(id_values) == 1:
                has_multiple_ids = False
                id_value = int(id_values[0])

            entry_item = QtWidgets.QTableWidgetItem()
            if has_multiple_ids:
                entry_item.setText(str(id_values))
            else:
                entry_item.setData(QtCore.Qt.ItemDataRole.EditRole, id_value)

            entry_item.setFlags(entry_item.flags() & mask)
            self.table.setItem(row, 2 + col, entry_item)

        # Re-enable sorting
        if not self.is_batch_add:
            self.table.setSortingEnabled(True)
            self.updateItems()

    def updateSprite(self, sprite: SpriteItem) -> None:
        """
        Updates the data of the given sprite
        """
        ids = self.getIDsFor(sprite)

        # Temporarily disable sorting so our updates happen to the same row.
        self.table.setSortingEnabled(False)
        row = self.getRowFor(sprite)

        # Add the sprite ID
        id_item = QtWidgets.QTableWidgetItem()
        id_item.setData(QtCore.Qt.ItemDataRole.DisplayRole, sprite.sprite_num)
        id_item.setData(QtCore.Qt.ItemDataRole.UserRole, sprite)
        id_item.setFlags(id_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, id_item)

        # Also add the sprite name
        name_item = QtWidgets.QTableWidgetItem(globals_.Sprites[sprite.sprite_num].name)
        name_item.setData(QtCore.Qt.ItemDataRole.UserRole, sprite)
        name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, name_item)

        item_mask = ~(QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsSelectable)

        # Skip the first columns (the id and name)
        for i in range(2, self.table.columnCount()):
            id_values = ids.get(globals_.SpriteIDTypes[i - 2].id_type, '')
            id_value = -1
            has_multiple_ids = True

            if isinstance(id_values, list) and len(id_values) == 1:
                has_multiple_ids = False
                id_value = int(id_values[0])

            item = self.table.item(row, i)
            if item is None:
                item = QtWidgets.QTableWidgetItem()
                item.setFlags(item.flags() & item_mask)
                self.table.setItem(row, i, item)

            if has_multiple_ids:
                item.setText(str(id_values))
            else:
                item.setData(QtCore.Qt.ItemDataRole.EditRole, id_value)

        # Re-enable sorting
        self.table.setSortingEnabled(True)

    def takeSprite(self, sprite: SpriteItem) -> None:
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

    def clear(self) -> None:
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

    def toolTip(self, item: QtWidgets.QGraphicsItem) -> None:
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

    @staticmethod
    def getIDsFor(sprite: SpriteItem) -> dict[str, list[int]]:
        """
        Returns an (idtype, [values]) dict for every
        idtype this sprite has
        """
        if not 0 <= sprite.sprite_num < globals_.NumSprites:
            return {}

        sdef = globals_.Sprites[sprite.sprite_num]
        res: dict[str, list[int]] = {}
        decoder = PropertyDecoder(EditorField())
        data = sprite.spritedata

        for field in sdef.fields:
            # Only values (1) and fields (2) have idtypes, so ignore all other
            # fields.
            if not isinstance(field, (ValueEditorField, ListEditorField)):
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
    def selectionModel(self) -> QtCore.QItemSelectionModel | None:
        return self.table.selectionModel()

    def row(self, item: QtWidgets.QTableWidgetItem) -> int:
        return self.table.row(item)
