from PyQt6 import QtWidgets

import globals_
from src.ui.theme.reggie_theme import GetIcon

class AutoSaveDialog(QtWidgets.QDialog):
    """
    Dialog specifying that auto-save data exists
    """

    def __init__(self, filename):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('AutoSaveDlg', 0))
        self.setWindowIcon(GetIcon('save'))

        info = QtWidgets.QLabel(globals_.trans.string('AutoSaveDlg', 1, '[path]', filename))
        info.setWordWrap(True)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Yes | QtWidgets.QDialogButtonBox.StandardButton.No)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(info)
        main_layout.addWidget(button_box)
