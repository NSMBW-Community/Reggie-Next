from PyQt6 import QtWidgets

import globals_
import spritelib as SLib
from dirty import SetDirty
from ui import GetIcon

# TODO:
# - Batch feature
# - Import file for quick batch swapping
# - Selection multi-swapping (select sprites of different types, open dialog, already in batch mode with those IDs chosen)
class SpriteSwitchDialog(QtWidgets.QDialog):
    """
    Dialog to switch the types of selected sprites
    """

    def __init__(self, selected):
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('SwitchSpriteDlg', 0))
        self.setWindowIcon(GetIcon('move'))

        self.curr_type = QtWidgets.QSpinBox()
        self.new_type = QtWidgets.QSpinBox()

        self.curr_type.setValue(selected)

        self.curr_type.setRange(0, 65535)
        self.new_type.setRange(0, 65535)

        swap_layout = QtWidgets.QGridLayout()

        swap_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('SwitchSpriteDlg', 1)), 0, 0)
        swap_layout.addWidget(self.curr_type, 0, 1)

        swap_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('SwitchSpriteDlg', 2)), 1, 0)
        swap_layout.addWidget(self.new_type, 1, 1)

        self.button_box = QtWidgets.QDialogButtonBox()
        self.button_box.addButton(globals_.trans.string('SwitchSpriteDlg', 3), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(globals_.trans.string('SwitchSpriteDlg', 4), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
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
            self.switch_sprite_ids()
        else:
            self.reject()

    def switch_sprite_ids(self):
        """
        Updates the sprites' IDs
        """
        curr_type = self.curr_type.value()
        new_type = self.new_type.value()

        # Do we need to switch anything?
        if curr_type == new_type:
            return

        for sprite in globals_.Area.sprites:
            if sprite.sprite_num == curr_type:
                sprite.SetType(new_type)

                # Fixes sprite image issues
                image_classes = globals_.gamedef.getImageClasses()
                if sprite.sprite_num in image_classes:
                    sprite.setImageObj(image_classes[sprite.sprite_num])
                else:
                    sprite.setImageObj(SLib.SpriteImage)

                globals_.Area.InitialiseIdTypes()
                SetDirty()
