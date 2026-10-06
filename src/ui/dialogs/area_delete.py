from PyQt6 import QtWidgets

from data import globals_
from ui.theme.reggie_theme import GetIcon

class AreaDeleteDialog(QtWidgets.QDialog):
    """
    Dialog prompting you to delete the current area
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('DeleteArea', 1))
        self.setWindowIcon(GetIcon('wooden-box--minus'))

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Yes | QtWidgets.QDialogButtonBox.StandardButton.No)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('DeleteArea', 0)))
        main_layout.addWidget(button_box)
