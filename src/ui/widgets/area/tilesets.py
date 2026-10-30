from PyQt6 import QtCore, QtWidgets, QtGui
import os

from collections.abc import Callable
from typing import cast

from data import globals_
from data.tileset.tileset_category import TilesetCategory, TilesetFileEntry

from data.common import archive
from libs import lh, lz77
from data.common.loaders import LoadTexture_NSMBW, LoadTileset, UnloadTileset
from data.tileset.tile.tileset_tile import TilesetTile

class TilesetsTab(QtWidgets.QWidget):
    """
    The widget that represents the Tilesets tab of the Area Options
    """

    def __init__(self) -> None:
        super().__init__()

        self.widgets: list[QtWidgets.QWidget] = []
        self.trees: list[QtWidgets.QTreeWidget] = []
        self.previews: list[QtWidgets.QGridLayout] = []
        self.line_edit: list[QtWidgets.QLineEdit] = []
        self.item_dict: list[dict[str, QtWidgets.QTreeWidgetItem]] = [{}, {}, {}, {}]
        self.none_items: list[QtWidgets.QTreeWidgetItem] = []
        self.preview_tiles: list[TilesetTile | None] = cast(list[TilesetTile | None], [None] * 0x200 * 4)

        # Set up each tileset
        for slot in range(4):
            def _tree_selected(slot: int) -> Callable[[], None]:
                return lambda: self.tree_selected(slot)

            def _text_edited(slot: int) -> Callable[[], None]:
                return lambda: self.text_edited(slot)

            # Create the main widget
            widget = QtWidgets.QWidget()
            self.widgets.append(widget)

            # Create the tree widget
            tree = QtWidgets.QTreeWidget()
            tree.setColumnCount(2)

            # Hardcoded initial width because the default width is too small
            tree.setColumnWidth(0, 192)
            tree.setHeaderLabels([globals_.trans_new.string('common.name'), globals_.trans_new.string('common.file')])
            tree.setIndentation(16)
            tree.itemSelectionChanged.connect((lambda slot: _tree_selected(slot))(slot))
            self.trees.append(tree)

            # Add "None" entry
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, globals_.trans_new.string('common.none'))  # 'None'
            tree.addTopLevelItem(item)
            self.none_items.append(item)

            # Keep an unsorted list for the textbox autocomplete
            tileset_list = []

            categories = self.parse_category(globals_.TilesetNames[slot].children, tileset_list, slot)
            tree.addTopLevelItems(categories)

            # Tileset preview
            preview_grid = QtWidgets.QGridLayout()
            preview_grid.setSpacing(0)
            self.previews.append(preview_grid)

            self.set_preview(slot, globals_.Area.tilesets[slot])

            # Create the line edit
            line = QtWidgets.QLineEdit()
            line.textChanged.connect((lambda slot: _text_edited(slot))(slot))
            line.setCompleter(QtWidgets.QCompleter(tileset_list))
            line.setPlaceholderText(globals_.trans_new.string('common.none_paren'))  # '(None)'
            self.line_edit.append(line)
            line.setText(globals_.Area.tilesets[slot])

            # Create the layout and add it to the widget
            tab_layout = QtWidgets.QGridLayout()
            tab_layout.addWidget(tree, 0, 0, 1, 2)
            if globals_.ShowTilesetPreview:
                tab_layout.addLayout(preview_grid, 0, 2)
            tab_layout.addWidget(QtWidgets.QLabel(globals_.trans_new.string('dialog.area.tab.tilesets.slot_title', ('[slot]', slot))), 1, 0)  # 'Tilesets (Pa[slot])'
            tab_layout.addWidget(line, 1, 1)
            tab_layout.setRowStretch(0, 1)

            width = 2 if globals_.ShowTilesetPreview else 0
            tab_layout.setRowStretch(width, 1)
            widget.setLayout(tab_layout)

        # Set up the tab widget
        tabs = QtWidgets.QTabWidget()

        # Set tab position based on the settings
        if globals_.TilesetTabPos == 0:
            tabs.setTabPosition(tabs.TabPosition.North)
        else:
            tabs.setTabPosition(tabs.TabPosition.West)

        tabs.setUsesScrollButtons(False)
        tabs.addTab(self.widgets[0], globals_.trans_new.string('dialog.area.tab.tilesets.slot.0'))  # 'Standard Suite'
        tabs.addTab(self.widgets[1], globals_.trans_new.string('dialog.area.tab.tilesets.slot.1'))  # 'Stage Suite'
        tabs.addTab(self.widgets[2], globals_.trans_new.string('dialog.area.tab.tilesets.slot.2'))  # 'Background Suite'
        tabs.addTab(self.widgets[3], globals_.trans_new.string('dialog.area.tab.tilesets.slot.3'))  # 'Interactive Suite'

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

    def save(self) -> None:
        """
        Saves the tileset data
        """
        tileset_num = 0
        for idx, name in enumerate(self.values()):
            if name in ('', None):
                name = ''
            elif name.startswith(str(globals_.trans_new.string('dialog.area.tab.tilesets.custom'))):
                name = name[len(str(globals_.trans_new.string('dialog.area.tab.tilesets.custom_with_name', ('[name]', '')))):]

            globals_.Area.tilesets[idx] = name

            if name != '':
                tileset_num += 1
                LoadTileset(idx, name)
            else:
                UnloadTileset(idx)

        globals_.mainWindow.palette_dock.object_tab.reset(False, False)

        for layer in globals_.Area.layers:
            for obj in layer:
                obj.updateObjCache()

        globals_.mainWindow.action_list['swapobjectstypes'].setEnabled(tileset_num != 0)
        globals_.mainWindow.action_list['swapobjectstilesets'].setEnabled(tileset_num != 0)

    # Add entries for each tileset
    def parse_category(self, items: list[TilesetCategory | TilesetFileEntry], tilesets: list[str], slot: int) -> tuple[QtWidgets.QTreeWidgetItem, ...]:
        """
        Parses a list of strings and returns a tuple of `QTreeWidgetItem`s
        """
        nodes: list[QtWidgets.QTreeWidgetItem] = []

        for item in items:
            node = QtWidgets.QTreeWidgetItem()

            # Check if it's a tileset or a category
            if isinstance(item, TilesetFileEntry):
                # It's a tileset
                node.setText(0, item.name)
                node.setText(1, item.filename)
                node.setToolTip(0, item.name)
                node.setToolTip(1, item.filename)
                self.item_dict[slot][item.filename] = node
                tilesets.append(item.filename)
            else:
                # It's a category
                node.setText(0, item.name)
                node.setToolTip(0, item.name)
                node.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
                children = self.parse_category(item.children, tilesets, slot)
                for cnode in children:
                    node.addChild(cnode)

            nodes.append(node)

        return tuple(nodes)

    def tree_selected(self, slot: int) -> None:
        """
        Handles changes to the selections in all tree widgets
        """
        selItems = self.trees[slot].selectedItems()
        if len(selItems) != 1:
            return

        item = selItems[0]

        value = str(item.text(1))
        self.line_edit[slot].setText(value)
        self.set_preview(slot, value)

    def text_edited(self, slot: int) -> None:
        """
        Handles changes made to the line-edit widgets
        """
        self.trees[slot].clearSelection()
        txt = str(self.line_edit[slot].text())
        self.set_preview(slot, txt)

        if (txt in self.item_dict[slot]) or (txt == ''):
            # Collapse all
            for i in range(self.trees[slot].topLevelItemCount()):
                self.trees[slot].collapseItem(self.trees[slot].topLevelItem(i))

            # If there's no text, just select None
            if txt == '':
                self.none_items[slot].setSelected(True)
                return

            # Find the item matching the description, and select it
            item = self.item_dict[slot][txt]
            item.setSelected(True)

            # Expand all of its parents
            parent = item.parent()
            while parent is not None:
                parent.setExpanded(True)
                parent = parent.parent()

    def values(self) -> tuple[str, ...]:
        """
        Returns all 4 tileset choices
        """
        result = []
        for i in range(4):
            result.append(str(self.line_edit[i].text()))

        return tuple(result)

    def get_preview(self, idx: int, name: str) -> bool:
        """
        Prepares a tileset preview
        """
        tileset_paths = reversed(globals_.gamedef.GetTexturePaths())

        found = False
        compressed = False
        arcname = ''
        for path in tileset_paths:
            if path is None:
                break

            arcname = os.path.join(path, name + ".arc.LH")

            # Prioritise .arc.LH over regular .arc, just like Newer does.
            if os.path.isfile(arcname):
                compressed = True
                found = True
                break

            # Now check for LZ compression
            arcname = os.path.join(path, name + ".arc.LZ")
            if os.path.isfile(arcname):
                compressed = True
                found = True
                break

            # Strip away the suffix (check for no compression)
            arcname = os.path.splitext(arcname)[0]
            if os.path.isfile(arcname):
                compressed = False
                found = True
                break

        if not found:
            return False

        # Get the data
        with open(arcname, 'rb') as fileobj:
            arcdata = fileobj.read()

        if compressed:
            if (arcdata[0] & 0xF0) == 0x40:  # If LH-compressed
                try:
                    arcdata = lh.UncompressLH(arcdata)
                except IndexError:
                    return False
            elif not arcdata.startswith(b"U\xAA8-"):  # If LZ-compressed
                try:
                    arcdata = lz77.UncompressLZ77(arcdata)
                except IndexError:
                    return False

        arc = archive.U8.load(arcdata)

        def exists(fn: str) -> bool:
            nonlocal arc
            try:
                arc[fn]
            except (IndexError, KeyError):
                return False
            return True

        # Decompress the texture
        if not exists(f'BG_tex/{name}_tex.bin.LZ'):
            return False

        comptiledata = arc[f'BG_tex/{name}_tex.bin.LZ']

        # Load in the textures
        data = lz77.UncompressLZ77(comptiledata)
        if not isinstance(data, bytes):
            return False

        img = LoadTexture_NSMBW(data)

        # Divide it into individual tiles
        dest = QtGui.QPixmap.fromImage(img)
        sourcex = 4
        sourcey = 4
        tileoffset = idx * 256
        for i in range(tileoffset, tileoffset + 256):
            tile = TilesetTile(dest.copy(sourcex, sourcey, 24, 24))
            self.preview_tiles[i] = tile

            sourcex += 32
            if sourcex >= 1024:
                sourcex = 4
                sourcey += 32

        return True

    def set_preview(self, idx: int, name: str) -> None:
        if not globals_.ShowTilesetPreview:
            return

        loaded = False
        if name != '' and self.get_preview(idx, name):
            loaded = True

        # Remove the existing widgets
        while self.previews[idx].count():
            item = self.previews[idx].takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        # In the event that we don't or cannot show a tileset,
        # make this so we can preview it
        dummy_pixmap = QtGui.QPixmap(24, 24)
        dummy_pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        columns = 16

        tileoffset = idx * 256
        for i in range(tileoffset, tileoffset + 256):
            row = i // columns
            col = i % columns

            label = QtWidgets.QLabel()
            if name != '' and loaded:
                preview_tile = self.preview_tiles[i]
                if preview_tile is not None:
                    label.setPixmap(preview_tile.main)
            else:
                label.setPixmap(dummy_pixmap)
            self.previews[idx].addWidget(label, row, col)
