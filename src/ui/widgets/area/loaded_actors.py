from PyQt6 import QtCore, QtWidgets

from data import globals_
from ui.models.static_string_list import StaticStringListModel

# TODO: ADD RESOURCE LIST FROM THE ACTORDATA
class LoadedActorsTab(QtWidgets.QWidget):
    """
    Widget that represents the Loaded Actors tab of the Area Options dialog
    """

    def __init__(self) -> None:
        super().__init__()

        self.custom_model = QtCore.QStringListModel(self.get_force_actor_names())

        self.custom_list = QtWidgets.QListView()
        self.custom_list.setModel(self.custom_model)
        self.custom_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        model = self.custom_list.selectionModel()
        if model is not None:
            model.selectionChanged.connect(lambda: self.item_selected(True))

        self.actor_input = QtWidgets.QLineEdit()
        self.actor_input.setPlaceholderText(globals_.trans.string('AreaDlg', 52))
        self.actor_input.textChanged.connect(self.input_changed)

        self.add_button = QtWidgets.QPushButton(globals_.trans.string('AreaDlg', 47))
        self.add_button.clicked.connect(self.add_actor)
        self.add_button.setEnabled(False)

        self.remove_button = QtWidgets.QPushButton(globals_.trans.string('AreaDlg', 48))
        self.remove_button.clicked.connect(self.remove_actor)
        self.remove_button.setEnabled(False)

        custom_layout = QtWidgets.QGridLayout()
        custom_layout.addWidget(self.actor_input, 0, 0)
        custom_layout.addWidget(self.add_button, 0, 1)
        custom_layout.addWidget(self.remove_button, 1, 0, 1, 2)
        custom_layout.addWidget(self.custom_list, 2, 0, 1, 2)

        self.auto_model = StaticStringListModel(self.get_default_actor_names())

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
        self.res_list.setText(globals_.trans.string('AreaDlg', 56))

        actors_layout = QtWidgets.QGridLayout()
        actors_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('AreaDlg', 49)), 0, 0)
        actors_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('AreaDlg', 50)), 0, 1)
        actors_layout.addWidget(self.auto_list, 1, 0)
        actors_layout.addLayout(custom_layout, 1, 1)
        actors_layout.addWidget(self.res_label, 2, 0)
        actors_layout.addWidget(self.res_list, 3, 0, 1, 2)

        info_text = QtWidgets.QLabel(globals_.trans.string('AreaDlg', 51))
        info_text.setWordWrap(True)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(info_text)
        main_layout.addLayout(actors_layout)
        self.setLayout(main_layout)

    def save(self) -> None:
        """
        Saves the actor lists
        """
        # Extracting the actor id from the actor name is hacky, but it works.
        globals_.Area.loaded_sprites = set(int(desc.split(']')[0][1:]) for desc in self.auto_model.stringList())
        globals_.Area.force_loaded_sprites = set(int(desc.split(']')[0][1:]) for desc in self.custom_model.stringList())

    def get_default_actor_names(self) -> set:
        """
        Returns a list of strings with the names of all actors in the current
        area.
        """
        if globals_.Area.areanum == -1:
            return set()

        used_ids = {actor.sprite_num for actor in globals_.Area.sprites}

        return set(self.get_actor_strings(sorted(used_ids)))

    def get_force_actor_names(self) -> list[str]:
        """
        Returns a list of strings with the names of all actors that are forced
        to load in the current area.
        """
        if globals_.Area.areanum == -1:
            return []

        return self.get_actor_strings(sorted(globals_.Area.force_loaded_sprites))

    def get_actor_strings(self, actor_ids: list[int]) -> list[str]:
        """
        Turns a list of actors ids into a list of strings representing the
        actors.

        The precise format of this string is relied on by the code that reads
        and saves the entered values in reggie.py. This code is pretty hacky,
        but at least it works.
        """
        actors = []
        for x in actor_ids:
            if 0 <= x < globals_.NumSprites:
                name = globals_.Sprites[x].name
            else:
                name = globals_.trans.string('AreaDlg', 53)

            actors.append(f"[{x}] {name}")

        return actors

    def add_actor(self, _: QtWidgets.QAbstractButton) -> None:
        """
        Add a actor to the list of actors whose resources are forced to load.
        """
        text = self.actor_input.text()

        try:
            actor_id = int(text) & 0xFFFF  # Restrict value to unsigned short
        except ValueError:
            return

        # Add a row to the end that represents the entered actor.
        if not self.custom_model.insertRow(self.custom_model.rowCount()):
            return

        index = self.custom_model.index(self.custom_model.rowCount() - 1, 0)

        if 0 <= actor_id < globals_.NumSprites:
            name = globals_.Sprites[actor_id].name
        else:
            name = globals_.trans.string('AreaDlg', 53)

        self.custom_model.setData(index, f"[{actor_id}] {name}")

        # Clear the input so the user can enter a new actor number
        self.actor_input.clear()

    def remove_actor(self, _: QtWidgets.QAbstractButton) -> None:
        """
        Remove the currently selected actor.
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

        # Check if "Remove Actor" button should be toggled
        if is_custom_list:
            self.remove_button.setEnabled(bool(len(model.selectedIndexes())))

        # Check if anything is selected, set the placeholder strings if not
        selected = model.selectedIndexes()
        if len(selected) < 1:
            self.res_list.setText(globals_.trans.string('AreaDlg', 56))
            self.res_label.setText(None)
            return

        resources = globals_.trans.string('AreaDlg', 55) # 'No resources found.'

        # Get the actor ID from the name string
        actor_id = int(selected[0].data().split(']')[0][1:])

        if actor_id < globals_.NumActors:
            actor_res = globals_.Actors[actor_id].relatedObjFiles
            if actor_res is not None:
                # Remove the prefix used by the Actor Editor
                resources = actor_res.removeprefix('<b>This actor loads:</b><br>')

        # Update the display
        self.res_label.setText(globals_.trans.string('AreaDlg', 54, '[num]', actor_id))
        self.res_list.setText(resources)
