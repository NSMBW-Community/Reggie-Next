from PyQt6 import QtCore, QtWidgets

from data import globals_
from ui.models.static_string_list import StaticStringListModel

class LoadedSpritesTab(QtWidgets.QWidget):
    """
    Widget that represents the Loaded Sprites tab of the Area Options dialog
    """

    def __init__(self) -> None:
        super().__init__()

        self.custom_model = QtCore.QStringListModel(self.get_force_sprite_names())

        self.custom_list = QtWidgets.QListView()
        self.custom_list.setModel(self.custom_model)
        self.custom_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        model = self.custom_list.selectionModel()
        if model is not None:
            model.selectionChanged.connect(lambda: self.item_selected(True))

        self.sprite_input = QtWidgets.QLineEdit()
        self.sprite_input.setPlaceholderText(globals_.trans_new.string('dialog.area.tab.loaded_sprites.type_id'))
        self.sprite_input.textChanged.connect(self.input_changed)

        self.add_button = QtWidgets.QPushButton(globals_.trans_new.string('dialog.area.tab.loaded_sprites.add'))
        self.add_button.clicked.connect(self.add_sprite)
        self.add_button.setEnabled(False)

        self.remove_button = QtWidgets.QPushButton(globals_.trans_new.string('dialog.area.tab.loaded_sprites.remove_selected'))
        self.remove_button.clicked.connect(self.remove_sprite)
        self.remove_button.setEnabled(False)

        custom_layout = QtWidgets.QGridLayout()
        custom_layout.addWidget(self.sprite_input, 0, 0)
        custom_layout.addWidget(self.add_button, 0, 1)
        custom_layout.addWidget(self.remove_button, 1, 0, 1, 2)
        custom_layout.addWidget(self.custom_list, 2, 0, 1, 2)

        self.auto_model = StaticStringListModel(self.get_default_sprite_names())

        self.auto_list = QtWidgets.QListView()
        self.auto_list.setModel(self.auto_model)
        self.auto_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        model = self.auto_list.selectionModel()
        if model is not None:
            model.selectionChanged.connect(lambda: self.item_selected(False))

        self.res_label = QtWidgets.QLabel()

        self.res_list = QtWidgets.QTextEdit()
        self.res_list.setReadOnly(True)
        self.res_list.setMaximumHeight(84)
        self.res_list.setText(globals_.trans_new.string('dialog.area.tab.loaded_sprites.resources.select_to_view'))

        sprites_layout = QtWidgets.QGridLayout()
        sprites_layout.addWidget(QtWidgets.QLabel(globals_.trans_new.string('dialog.area.tab.loaded_sprites.present')), 0, 0)
        sprites_layout.addWidget(QtWidgets.QLabel(globals_.trans_new.string('dialog.area.tab.loaded_sprites.custom')), 0, 1)
        sprites_layout.addWidget(self.auto_list, 1, 0)
        sprites_layout.addLayout(custom_layout, 1, 1)
        sprites_layout.addWidget(self.res_label, 2, 0)
        sprites_layout.addWidget(self.res_list, 3, 0, 1, 2)

        info_text = QtWidgets.QLabel(globals_.trans_new.string('dialog.area.tab.loaded_sprites.info'))
        info_text.setWordWrap(True)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(info_text)
        main_layout.addLayout(sprites_layout)
        self.setLayout(main_layout)

    def save(self) -> None:
        """
        Saves the sprite lists
        """
        # Extracting the sprite ID from the sprite name is hacky, but it works
        globals_.Area.loaded_sprites = set(int(desc.split(']')[0][1:]) for desc in self.auto_model.stringList())
        globals_.Area.force_loaded_sprites = set(int(desc.split(']')[0][1:]) for desc in self.custom_model.stringList())

    def get_default_sprite_names(self) -> set:
        """
        Returns a list of strings with the names of all sprites in the current area.
        """
        if globals_.Area.areanum == -1:
            return set()

        used_ids = {sprite.sprite_num for sprite in globals_.Area.sprites}

        return set(self.get_sprite_strings(sorted(used_ids)))

    def get_force_sprite_names(self) -> list[str]:
        """
        Returns a list of strings with the names of all sprites that are forced
        to load in the current area.
        """
        if globals_.Area.areanum == -1:
            return []

        return self.get_sprite_strings(sorted(globals_.Area.force_loaded_sprites))

    def get_sprite_strings(self, sprite_ids: list[int]) -> list[str]:
        """
        Turns a list of sprite IDs into a list of strings representing the
        sprites.

        The precise format of this string is relied on by the code that reads
        and saves the entered values. This code is pretty hacky, but at least
        it works.
        """
        sprites = []

        for x in sprite_ids:
            if 0 <= x < globals_.NumSprites:
                name = globals_.Sprites[x].name
            else:
                name = globals_.trans_new.string('common.unknown_upper')

            sprites.append(f"[{x}] {name}")

        return sprites

    def add_sprite(self, _: QtWidgets.QAbstractButton) -> None:
        """
        Add a sprite to the list of sprites whose resources are forced to load.
        """
        text = self.sprite_input.text()

        try:
            sprite_id = int(text) & 0xFFFF  # Restrict value to unsigned short
        except ValueError:
            return

        # Add a row to the end that represents the entered sprite.
        if not self.custom_model.insertRow(self.custom_model.rowCount()):
            return

        index = self.custom_model.index(self.custom_model.rowCount() - 1, 0)

        if 0 <= sprite_id < globals_.NumSprites:
            name = globals_.Sprites[sprite_id].name
        else:
            name = globals_.trans_new.string('common.unknown_upper')

        self.custom_model.setData(index, f"[{sprite_id}] {name}")

        # Clear the input so the user can enter a new sprite number
        self.sprite_input.clear()

    def remove_sprite(self, _: QtWidgets.QAbstractButton) -> None:
        """
        Remove the currently selected sprite.
        """
        curr_idx = self.custom_list.currentIndex()
        self.custom_model.removeRow(curr_idx.row())

    def input_changed(self, new_text: str) -> None:
        """
        Enable "add" button when the text is changed to something not empty.
        """
        self.add_button.setEnabled(bool(new_text))

    def item_selected(self, is_custom_list: bool) -> None:
        """
        Updates the resource list when an item is selected
        """
        item_list = self.custom_list if is_custom_list else self.auto_list
        model = item_list.selectionModel()
        if model is None:
            return

        # Check if "Remove Sprite" button should be toggled
        if is_custom_list:
            self.remove_button.setEnabled(bool(len(model.selectedIndexes())))

        # Check if anything is selected, set the placeholder strings if not
        selected = model.selectedIndexes()
        if len(selected) < 1:
            self.res_list.setText(globals_.trans_new.string('dialog.area.tab.loaded_sprites.resources.select_to_view'))
            self.res_label.setText(None)
            return

        resources = globals_.trans_new.string('dialog.area.tab.loaded_sprites.resources.none_found') # 'No resources found.'

        # Get the sprite ID from the name string
        sprite_id = int(selected[0].data().split(']')[0][1:])

        if sprite_id < globals_.NumSprites:
            sprite_res = globals_.Sprites[sprite_id].relatedObjFiles
            if sprite_res is not None:
                # Remove the prefix used by the Sprite Editor
                resources = sprite_res.removeprefix('<b>This sprite loads:</b><br>')

        # Update the display
        self.res_label.setText(globals_.trans_new.string('dialog.area.tab.loaded_sprites.resources.loaded_by_id', ('[num]', sprite_id)))
        self.res_list.setText(resources)
