from PyQt6 import QtCore, QtWidgets

import globals_
from src.data.model.tileset_category import TilesetCategory, TilesetFileEntry
from ui import GetIcon


class AreaOptionsDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose among various area options from tabs
    """

    def __init__(self):
        """
        Creates and initializes the tab dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('AreaDlg', 0))
        self.setWindowIcon(GetIcon('area'))

        self.tabWidget = QtWidgets.QTabWidget()
        self.tilesetsTab = TilesetsTab()
        self.settingsTab = SettingsTab()
        self.loadedSpritesTab = LoadedSpritesTab()
        self.tabWidget.addTab(self.tilesetsTab, globals_.trans.string('AreaDlg', 1))
        self.tabWidget.addTab(self.settingsTab, globals_.trans.string('AreaDlg', 2))
        self.tabWidget.addTab(self.loadedSpritesTab, globals_.trans.string('AreaDlg', 46))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class SettingsTab(QtWidgets.QWidget):
    """
    Widget that represents the area's settings
    """

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.timer = QtWidgets.QSpinBox()
        self.timer.setRange(0, 999)
        self.timer.setToolTip(globals_.trans.string('AreaDlg', 4))
        self.timer.setValue(globals_.Area.timeLimit + 200)

        self.entrance = QtWidgets.QSpinBox()
        self.entrance.setRange(0, 255)
        self.entrance.setToolTip(globals_.trans.string('AreaDlg', 6))
        self.entrance.setValue(globals_.Area.startEntrance)

        self.toadHouseType = QtWidgets.QComboBox()
        self.toadHouseType.addItems(globals_.trans.stringList('AreaDlg', 33))
        self.toadHouseType.setCurrentIndex(globals_.Area.toadHouseType)

        self.wrap = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 7))
        self.wrap.setToolTip(globals_.trans.string('AreaDlg', 8))
        self.wrap.setChecked(globals_.Area.wrapFlag)

        self.credits = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 34))
        self.credits.setToolTip(globals_.trans.string('AreaDlg', 35))
        self.credits.setChecked(globals_.Area.creditsFlag)

        self.faceLeft = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 36))
        self.faceLeft.setToolTip(globals_.trans.string('AreaDlg', 37))
        self.faceLeft.setChecked(globals_.Area.faceLeftFlag)

        self.unk1 = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 38))
        self.unk1.setToolTip(globals_.trans.string('AreaDlg', 39))
        self.unk1.setChecked(globals_.Area.unkFlag1)

        self.unk2 = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 40))
        self.unk2.setToolTip(globals_.trans.string('AreaDlg', 41))
        self.unk2.setChecked(globals_.Area.unkFlag2)

        self.unk3 = QtWidgets.QSpinBox()
        self.unk3.setRange(0, 999)
        self.unk3.setToolTip(globals_.trans.string('AreaDlg', 43))
        self.unk3.setValue(globals_.Area.unkVal1)

        self.unk4 = QtWidgets.QSpinBox()
        self.unk4.setRange(0, 999)
        self.unk4.setToolTip(globals_.trans.string('AreaDlg', 45))
        self.unk4.setValue(globals_.Area.unkVal2)

        settingsLayout = QtWidgets.QFormLayout()
        settingsLayout.addRow(globals_.trans.string('AreaDlg', 3), self.timer)
        settingsLayout.addRow(globals_.trans.string('AreaDlg', 5), self.entrance)
        settingsLayout.addRow(globals_.trans.string('AreaDlg', 32), self.toadHouseType)
        settingsLayout.addRow(self.wrap)
        settingsLayout.addRow(self.credits)
        settingsLayout.addRow(self.faceLeft)
        settingsLayout.addRow(self.unk1)
        settingsLayout.addRow(self.unk2)
        settingsLayout.addRow(globals_.trans.string('AreaDlg', 42), self.unk3)
        settingsLayout.addRow(globals_.trans.string('AreaDlg', 44), self.unk4)

        Layout = QtWidgets.QVBoxLayout()
        Layout.addLayout(settingsLayout)
        Layout.addStretch(1)
        self.setLayout(Layout)


class TilesetsTab(QtWidgets.QWidget):
    """
    The widget that represents the Tileset picker
    """

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setMinimumWidth(384)

        # Set up each tileset
        self.widgets = []
        self.trees = []
        self.lineEdits = []
        self.itemDict = [{}, {}, {}, {}]
        self.noneItems = []

        for slot in range(4):
            def treeSel(slot):
                return lambda: self.handleTreeSel(slot)

            def textEdit(slot):
                return lambda: self.handleTextEdit(slot)

            # Create the main widget
            widget = QtWidgets.QWidget()
            self.widgets.append(widget)

            # Create the tree widget
            tree = QtWidgets.QTreeWidget()
            tree.setColumnCount(2)

            # Hardcoded initial width because the default width is too small
            tree.setColumnWidth(0, 192)
            tree.setHeaderLabels([globals_.trans.string('AreaDlg', 28), globals_.trans.string('AreaDlg', 29)])  # ['Name', 'File']
            tree.setIndentation(16)
            tree.itemSelectionChanged.connect((lambda slot: treeSel(slot))(slot))
            self.trees.append(tree)

            # Add "None" entry
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, globals_.trans.string('AreaDlg', 15))  # 'None'
            tree.addTopLevelItem(item)
            self.noneItems.append(item)

            # Keep an unsorted list for the textbox autocomplete
            tilesetList = []

            categories = self.ParseCategory(globals_.TilesetNames[slot].children, tilesetList, slot)
            tree.addTopLevelItems(categories)

            # Create the line edit
            line = QtWidgets.QLineEdit()
            line.textChanged.connect((lambda slot: textEdit(slot))(slot))
            line.setCompleter(QtWidgets.QCompleter(tilesetList))
            line.setPlaceholderText(globals_.trans.string('AreaDlg', 30))  # '(None)'
            self.lineEdits.append(line)
            line.setText(eval('globals_.Area.tileset%d' % slot))

            # For some reason, PyQt doesn't automatically call
            # the handler if (globals_.Area.tileset%d % slot) == ''
            #self.handleTextEdit(slot)

            # Create the layout and add it to the widget
            L = QtWidgets.QGridLayout()
            L.addWidget(tree, 0, 0, 1, 2)
            L.addWidget(QtWidgets.QLabel(globals_.trans.string('AreaDlg', 31, '[slot]', slot)), 1, 0)  # 'Tilesets (Pa[slot])'
            L.addWidget(line, 1, 1)
            L.setRowStretch(0, 1)
            widget.setLayout(L)

        # Set up the tab widget
        T = QtWidgets.QTabWidget()

        # Set tab position based on the settings
        if globals_.TilesetTabPos == 0:
            T.setTabPosition(T.TabPosition.North)
        else:
            T.setTabPosition(T.TabPosition.West)

        T.setUsesScrollButtons(False)
        T.addTab(self.widgets[0], globals_.trans.string('AreaDlg', 11))  # 'Standard Suite'
        T.addTab(self.widgets[1], globals_.trans.string('AreaDlg', 12))  # 'Stage Suite'
        T.addTab(self.widgets[2], globals_.trans.string('AreaDlg', 13))  # 'Background Suite'
        T.addTab(self.widgets[3], globals_.trans.string('AreaDlg', 14))  # 'Interactive Suite'
        L = QtWidgets.QVBoxLayout()
        L.addWidget(T)
        self.setLayout(L)

    # Add entries for each tileset
    def ParseCategory(self, items: list[TilesetCategory | TilesetFileEntry], tilesets: list[str], tilesetSlot: int) -> tuple[QtWidgets.QTreeWidgetItem, ...]:
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
                self.itemDict[tilesetSlot][item.filename] = node
                tilesets.append(item.filename)
            else:
                # It's a category
                node.setText(0, item.name)
                node.setToolTip(0, item.name)
                node.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
                children = self.ParseCategory(item.children, tilesets, tilesetSlot)
                for cnode in children:
                    node.addChild(cnode)

            nodes.append(node)

        return tuple(nodes)

    def handleTreeSel(self, slot):
        """
        Handles changes to the selections in all tree widgets
        """
        selItems = self.trees[slot].selectedItems()
        if len(selItems) != 1:
            return

        item = selItems[0]

        value = str(item.text(1))
        self.lineEdits[slot].setText(value)

    def handleTextEdit(self, slot):
        """
        Handles changes made to the line-edit widgets
        """
        self.trees[slot].clearSelection()
        txt = str(self.lineEdits[slot].text())

        if (txt in self.itemDict[slot]) or (txt == ''):
            # Collapse all
            for i in range(self.trees[slot].topLevelItemCount()):
                self.trees[slot].collapseItem(self.trees[slot].topLevelItem(i))

            # If there's no text, just select None
            if txt == '':
                self.noneItems[slot].setSelected(True)
                return

            # Find the item matching the description, and select it
            item = self.itemDict[slot][txt]
            item.setSelected(True)

            # Expand all of its parents
            parent = item.parent()
            while parent is not None:
                parent.setExpanded(True)
                parent = parent.parent()

    def values(self):
        """
        Returns all 4 tileset choices
        """
        result = []
        for i in range(4):
            result.append(str(self.lineEdits[i].text()))
        return tuple(result)


class LoadedSpritesTab(QtWidgets.QWidget):
    """
    Tab widget that represents the list of loaded sprites.
    """

    class StaticModel(QtCore.QStringListModel):
        """
        Unselectable, uneditable string list model
        """

        def flags(self, index):
            return QtCore.Qt.ItemFlag.ItemNeverHasChildren

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        spritesLayout = QtWidgets.QGridLayout()

        self.customModel = QtCore.QStringListModel(self.getForceSpriteNames())

        self.customList = QtWidgets.QListView()
        self.customList.setModel(self.customModel)
        self.customList.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        model = self.customList.selectionModel()
        if model is not None:
            model.selectionChanged.connect(
                lambda *_: self.removeButton.setEnabled(bool(len(model.selectedIndexes())))
            )

        self.spriteInput = QtWidgets.QLineEdit()
        self.spriteInput.setPlaceholderText(globals_.trans.string('AreaDlg', 52))
        self.spriteInput.textChanged.connect(self.handleInputChange)

        self.addButton = QtWidgets.QPushButton(globals_.trans.string('AreaDlg', 47))
        self.addButton.clicked.connect(self.handleAddSprite)
        self.addButton.setEnabled(False)

        self.removeButton = QtWidgets.QPushButton(globals_.trans.string('AreaDlg', 48))
        self.removeButton.clicked.connect(self.handleRemoveSprite)
        self.removeButton.setEnabled(False)

        customLayout = QtWidgets.QGridLayout()
        customLayout.addWidget(self.spriteInput, 0, 0)
        customLayout.addWidget(self.addButton, 0, 1)
        customLayout.addWidget(self.removeButton, 1, 0, 1, 2)
        customLayout.addWidget(self.customList, 2, 0, 1, 2)

        self.autoModel = LoadedSpritesTab.StaticModel(self.getDefaultSpriteNames())

        autoList = QtWidgets.QListView()
        autoList.setModel(self.autoModel)
        autoList.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        # Dark mode readability fixes
        autoList.setStyleSheet("color: #7f7f7f;")

        spritesLayout.addWidget(QtWidgets.QLabel(globals_.trans.string('AreaDlg', 49)), 0, 0)
        spritesLayout.addWidget(QtWidgets.QLabel(globals_.trans.string('AreaDlg', 50)), 0, 1)
        spritesLayout.addWidget(autoList, 1, 0)
        spritesLayout.addLayout(customLayout, 1, 1)

        explanation = QtWidgets.QLabel(globals_.trans.string('AreaDlg', 51))
        explanation.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(explanation)
        layout.addLayout(spritesLayout)
        self.setLayout(layout)

    def getDefaultSpriteNames(self):
        """
        Returns a list of strings with the names of all sprites in the current
        area.
        """
        if globals_.Area.areanum == -1:
            return []

        usedIDs = set(sprite.type for sprite in globals_.Area.sprites)

        return self.stringifySprites(sorted(usedIDs))

    def getForceSpriteNames(self):
        """
        Returns a list of strings with the names of all sprites that are forced
        to load in the current area.
        """
        if globals_.Area.areanum == -1:
            return []

        return self.stringifySprites(sorted(globals_.Area.force_loaded_sprites))

    def stringifySprites(self, spriteIDs):
        """
        Turns a list of sprite ids into a list of strings representing the
        sprites.

        The precise format of this string is relied on by the code that reads
        and saves the entered values in reggie.py. This code is pretty hacky,
        but at least it works.
        """
        sprites = []
        for x in spriteIDs:
            if 0 <= x < globals_.NumSprites:
                name = globals_.Sprites[x].name
            else:
                name = globals_.trans.string('AreaDlg', 53)

            sprites.append("[%d] %s" % (x, name))

        return sprites

    def handleAddSprite(self, _):
        """
        Add a sprite to the list of sprites whose resources are forced to load.
        """
        text = self.spriteInput.text()

        try:
            spriteID = int(text) & 0xFFFF  # Restrict value to unsigned short
        except ValueError:
            return

        # Add a row to the end that represents the entered sprite.
        if not self.customModel.insertRow(self.customModel.rowCount()):
            return

        index = self.customModel.index(self.customModel.rowCount() - 1, 0)

        if 0 <= spriteID < globals_.NumSprites:
            name = globals_.Sprites[spriteID].name
        else:
            name = globals_.trans.string('AreaDlg', 53)
        self.customModel.setData(index, "[%d] %s" % (spriteID, name))

        # Clear the input so the user can enter a new sprite number
        self.spriteInput.clear()

    def handleRemoveSprite(self, _):
        """
        Remove the currently selected sprite.
        """
        currIdx = self.customList.currentIndex()
        self.customModel.removeRow(currIdx.row())

    def handleInputChange(self, newText):
        """
        Enable "add" button when the text is changed to something not empty.
        """
        self.addButton.setEnabled(bool(newText))
