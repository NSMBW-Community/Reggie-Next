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

        self.custom_model = QtCore.QStringListModel(self.getForceActorNames())

        self.custom_list = QtWidgets.QListView()
        self.custom_list.setModel(self.custom_model)
        self.custom_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        model = self.custom_list.selectionModel()
        if model is not None:
            model.selectionChanged.connect(
                lambda *_: self.remove_button.setEnabled(bool(len(model.selectedIndexes())))
            )

        self.actor_input = QtWidgets.QLineEdit()
        self.actor_input.setPlaceholderText(globals_.trans.string('AreaDlg', 52))
        self.actor_input.textChanged.connect(self.handleInputChange)

        self.add_button = QtWidgets.QPushButton(globals_.trans.string('AreaDlg', 47))
        self.add_button.clicked.connect(self.handleAddActor)
        self.add_button.setEnabled(False)

        self.remove_button = QtWidgets.QPushButton(globals_.trans.string('AreaDlg', 48))
        self.remove_button.clicked.connect(self.handleRemoveActor)
        self.remove_button.setEnabled(False)

        custom_layout = QtWidgets.QGridLayout()
        custom_layout.addWidget(self.actor_input, 0, 0)
        custom_layout.addWidget(self.add_button, 0, 1)
        custom_layout.addWidget(self.remove_button, 1, 0, 1, 2)
        custom_layout.addWidget(self.custom_list, 2, 0, 1, 2)

        self.auto_model = StaticStringListModel(self.getDefaultActorNames())

        auto_list = QtWidgets.QListView()
        auto_list.setModel(self.auto_model)
        auto_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        actors_layout = QtWidgets.QGridLayout()
        actors_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('AreaDlg', 49)), 0, 0)
        actors_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('AreaDlg', 50)), 0, 1)
        actors_layout.addWidget(auto_list, 1, 0)
        actors_layout.addLayout(custom_layout, 1, 1)

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
        globals_.Area.loaded_actors = set(int(desc.split(']')[0][1:]) for desc in self.auto_model.stringList())
        globals_.Area.force_loaded_actors = set(int(desc.split(']')[0][1:]) for desc in self.custom_model.stringList())

    def getDefaultActorNames(self) -> set:
        """
        Returns a list of strings with the names of all actors in the current
        area.
        """
        if globals_.Area.areanum == -1:
            return set()

        used_ids = {actor.actor_num for actor in globals_.Area.actors}

        return set(self.stringifyActors(sorted(used_ids)))

    def getForceActorNames(self) -> list[str]:
        """
        Returns a list of strings with the names of all actors that are forced
        to load in the current area.
        """
        if globals_.Area.areanum == -1:
            return []

        return self.stringifyActors(sorted(globals_.Area.force_loaded_actors))

    def stringifyActors(self, actor_ids: list[int]) -> list[str]:
        """
        Turns a list of actors ids into a list of strings representing the
        actors.

        The precise format of this string is relied on by the code that reads
        and saves the entered values in reggie.py. This code is pretty hacky,
        but at least it works.
        """
        actors = []
        for x in actor_ids:
            if 0 <= x < globals_.NumActors:
                name = globals_.Actors[x].name
            else:
                name = globals_.trans.string('AreaDlg', 53)

            actors.append(f"[{x}] {name}")

        return actors

    def handleAddActor(self, _: QtWidgets.QAbstractButton) -> None:
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

        if 0 <= actor_id < globals_.NumActors:
            name = globals_.Actors[actor_id].name
        else:
            name = globals_.trans.string('AreaDlg', 53)

        self.custom_model.setData(index, f"[{actor_id}] {name}")

        # Clear the input so the user can enter a new actor number
        self.actor_input.clear()

    def handleRemoveActor(self, _: QtWidgets.QAbstractButton) -> None:
        """
        Remove the currently selected actor.
        """
        curr_idx = self.custom_list.currentIndex()
        self.custom_model.removeRow(curr_idx.row())

    def handleInputChange(self, new_text: str) -> None:
        """
        Enable "add" button when the text is changed to something not empty.
        """
        self.add_button.setEnabled(bool(new_text))
