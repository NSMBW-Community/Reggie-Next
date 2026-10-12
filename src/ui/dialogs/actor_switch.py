from PyQt6 import QtWidgets

from data import globals_
import actorlib
from data.level.dirty import SetDirty
from ui.theme.reggie_theme import GetIcon

# TODO:
# - Batch feature
# - Import file for quick batch swapping
# - Selection multi-swapping (select sprites of different IDs, open dialog, already in batch mode with those IDs chosen)
class ActorSwitchDialog(QtWidgets.QDialog):
    """
    Dialog to switch the IDs of selected actors
    """

    def __init__(self, selected):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('SwitchActorDlg', 0))
        self.setWindowIcon(GetIcon('arrow-curve'))

        self.curr_type = QtWidgets.QSpinBox()
        self.new_type = QtWidgets.QSpinBox()

        self.curr_type.setRange(0, 65535)
        self.new_type.setRange(0, 65535)

        # Set a default ID, if applicable
        self.curr_type.setValue(selected)

        swap_layout = QtWidgets.QGridLayout()

        swap_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('SwitchActorDlg', 1)), 0, 0)
        swap_layout.addWidget(self.curr_type, 0, 1)

        swap_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('SwitchActorDlg', 2)), 1, 0)
        swap_layout.addWidget(self.new_type, 1, 1)

        self.button_box = QtWidgets.QDialogButtonBox()
        self.button_box.addButton(globals_.trans.string('SwitchActorDlg', 3), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(globals_.trans.string('SwitchActorDlg', 4), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        self.button_box.clicked.connect(self.button_clicked)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(swap_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def button_clicked(self, button):
        """
        Handles one of the buttons being pressed and calls the correct handler
        """
        role = self.button_box.buttonRole(button)

        if role == QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole:
            self.switch_actor_ids()
        else:
            self.reject()

    def switch_actor_ids(self):
        """
        Updates the actors' IDs
        """
        curr_type = self.curr_type.value()
        new_type = self.new_type.value()

        # Do we need to switch anything?
        if curr_type == new_type:
            return

        for actor in globals_.Area.actors:
            if actor.sprite_num == curr_type:
                actor.SetType(new_type)

                # Fixes sprite image issues
                image_classes = globals_.gamedef.getImageClasses()
                if actor.sprite_num in image_classes:
                    actor.setImageObj(image_classes[actor.sprite_num])
                else:
                    actor.setImageObj(actorlib.ActorImage)

                globals_.Area.InitialiseIdTypes()
                SetDirty()
