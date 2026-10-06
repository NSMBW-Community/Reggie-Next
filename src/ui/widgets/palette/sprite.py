from PyQt6 import QtWidgets, QtCore
Qt = QtCore.Qt

from data import globals_

from ui.theme.reggie_theme import GetIcon
from data.common.loaders import LoadSpriteCategories
from data.level.dirty import SetDirty

from ui.widgets.sidelists.sprite_picker import SpritePickerWidget
from ui.widgets.sidelists.sprite_list import SpriteList
from ui.widgets.sidelists.sprite_order import SpriteOrderList

from data.level.items.sprite import SpriteItem
from spritelib import SpriteImage

class SpriteTab(QtWidgets.QTabWidget):
    """
    Represents the Sprites tab in the palette
    """
    def __init__(self):
        super().__init__(None)
        self.currentChanged.connect(self.tab_changed)

        # Add Sprites tab
        self.add_sprite_tab = QtWidgets.QWidget()
        self.addTab(self.add_sprite_tab, GetIcon('rocket-small-plus'), globals_.trans.string('Palette', 25))

        view_lyt = QtWidgets.QHBoxLayout()
        view_lyt.addWidget(QtWidgets.QLabel(globals_.trans.string('Palette', 4)))

        self.search_lyt = QtWidgets.QHBoxLayout()
        self.search_lyt.addWidget(QtWidgets.QLabel(globals_.trans.string('Palette', 5)))

        LoadSpriteCategories()

        self.view_picker = QtWidgets.QComboBox()
        for view in globals_.SpriteCategories:
            self.view_picker.addItem(view.name)
        self.view_picker.currentIndexChanged.connect(self.curr_view_changed)

        view_lyt.addWidget(self.view_picker, 1)

        self.search_box = QtWidgets.QLineEdit()
        self.search_box.textChanged.connect(self.set_search_string)
        self.search_lyt.addWidget(self.search_box, 1)

        self.sprite_picker = SpritePickerWidget()
        self.sprite_picker.SpriteChanged.connect(self.sprite_selected)
        self.sprite_picker.SpriteReplace.connect(self.sprite_replaced)
        self.sprite_picker.SwitchView(globals_.SpriteCategories[0])

        self.default_prop_button = QtWidgets.QPushButton(globals_.trans.string('Palette', 6))
        self.default_prop_button.setEnabled(False)
        self.default_prop_button.clicked.connect(self.show_default_props_dock)

        sdpl = QtWidgets.QHBoxLayout()
        sdpl.addStretch(1)
        sdpl.addWidget(self.default_prop_button)
        sdpl.addStretch(1)

        add_sprite_lyt = QtWidgets.QVBoxLayout(self.add_sprite_tab)
        add_sprite_lyt.addLayout(view_lyt)
        add_sprite_lyt.addLayout(self.search_lyt)
        add_sprite_lyt.addWidget(self.sprite_picker, 1)
        add_sprite_lyt.addLayout(sdpl)


        # Current sprites
        self.current_sprite_tab = QtWidgets.QWidget()
        self.addTab(self.current_sprite_tab, GetIcon('rocket-document-list'), globals_.trans.string('Palette', 26))

        curr_label = QtWidgets.QLabel(globals_.trans.string('Palette', 11))
        curr_label.setWordWrap(True)

        self.sprite_list = SpriteList()

        curr_sprite_lyt = QtWidgets.QVBoxLayout(self.current_sprite_tab)
        curr_sprite_lyt.addWidget(curr_label)
        curr_sprite_lyt.addWidget(self.sprite_list)


        # Sprite Order
        self.sprite_order_tab = QtWidgets.QWidget()
        self.addTab(self.sprite_order_tab, GetIcon('rocket-small-arrow'), globals_.trans.string('Palette', 39))

        order_label = QtWidgets.QLabel(globals_.trans.string('Palette', 40))
        order_label.setWordWrap(True)
        self.sprite_order_list = SpriteOrderList()

        order_layout = QtWidgets.QVBoxLayout(self.sprite_order_tab)
        order_layout.addWidget(order_label)
        order_layout.addWidget(self.sprite_order_list)

    def tab_changed(self, new_tab):
        """
        Handles the selected tab changing
        """
        if new_tab == 0:
            paint_type = 4 # Sprites
        else:
            paint_type = -1 # None

        globals_.CurrentPaintType = paint_type

    def sprite_selected(self, sprite_num):
        """
        Handles a new sprite being chosen
        """
        if globals_.mainWindow is None:
            return

        globals_.CurrentSprite = sprite_num

        if sprite_num != 1000 and sprite_num >= 0:
            globals_.mainWindow.defaultDataEditor.setSprite(sprite_num, initial_data=bytes(10))
            self.default_prop_button.setEnabled(True)
        else:
            self.default_prop_button.setEnabled(False)
            globals_.mainWindow.defaultPropDock.setVisible(False)
            globals_.mainWindow.defaultDataEditor.updateFields()

    def sprite_replaced(self, sprite_num):
        """
        Handles a new sprite type being chosen to replace the selected sprites
        """
        if globals_.mainWindow is None:
            return

        items = globals_.mainWindow.scene.selectedItems()
        changed = False

        for spr in items:
            if isinstance(spr, SpriteItem):
                # Reset spritedata
                spr.spritedata = globals_.mainWindow.defaultDataEditor.data
                spr.SetType(sprite_num)
                spr.update()

                # Assign the new sprite image class
                image_classes = globals_.gamedef.getImageClasses()
                if sprite_num in image_classes:
                    spr.setImageObj(image_classes[sprite_num])
                else:
                    spr.setImageObj(SpriteImage)
                changed = True

        if changed:
            # Fixes any issues from outdated types
            globals_.Area.InitialiseIdTypes()
            SetDirty()

        globals_.mainWindow.ChangeSelectionHandler()

    def curr_view_changed(self, type):
        """
        Handles a new sprite view being chosen
        """
        cat = globals_.SpriteCategories[type]
        self.sprite_picker.SwitchView(cat)

        isSearch = (type == 0)
        layout = self.search_lyt

        # Show/hide the searchbar
        # Item 0 is "Search:", 1 is the box itself
        for i in range(2):
            item = layout.itemAt(i)
            if item is None:
                return

            widget = item.widget()
            if widget is None:
                return

            widget.setVisible(isSearch)

    def set_search_string(self, text):
        """
        Handles a new sprite search term being entered
        """
        self.sprite_picker.SetSearchString(text)

    def show_default_props_dock(self):
        """
        Handles the Show Default Properties button being clicked
        """
        if globals_.mainWindow is not None:
            globals_.mainWindow.defaultPropDock.setVisible(True)

    def prepare_batch_add(self):
        """
        Helper to prepare adding sprites in batch
        """
        self.sprite_list.prepareBatchAdd()
        self.sprite_order_list.prepareBatchAdd()

    def add_sprite(self, sprite):
        """
        Helper to add a sprite to the lists
        """
        self.sprite_list.addSprite(sprite)
        self.sprite_order_list.addSprite(sprite)

    def end_batch_add(self):
        """
        Helper to end batch-adding
        """
        self.sprite_list.endBatchAdd()
        self.sprite_order_list.endBatchAdd()
