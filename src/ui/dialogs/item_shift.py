from PyQt6 import QtWidgets

import globals_
from src.ui.theme.reggie_theme import GetIcon

class ItemShiftDialog(QtWidgets.QDialog):
    """
    Dialog to shift selected items by a certain number of units
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('ShftItmDlg', 0))
        self.setWindowIcon(GetIcon('move'))

        self.offset_x = QtWidgets.QSpinBox()
        self.offset_x.setRange(-16384, 16383)

        self.offset_y = QtWidgets.QSpinBox()
        self.offset_y.setRange(-8192, 8191)

        offset_label = QtWidgets.QLabel(globals_.trans.string('ShftItmDlg', 2))
        offset_label.setWordWrap(True)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        move_lyt = QtWidgets.QFormLayout()
        move_lyt.addWidget(offset_label)
        move_lyt.addRow(globals_.trans.string('ShftItmDlg', 3), self.offset_x)
        move_lyt.addRow(globals_.trans.string('ShftItmDlg', 4), self.offset_y)

        move_box = QtWidgets.QGroupBox(globals_.trans.string('ShftItmDlg', 1))
        move_box.setLayout(move_lyt)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(move_box)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
