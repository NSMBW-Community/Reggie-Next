from PyQt6 import QtWidgets

import globals_
from src.ui.theme.reggie_theme import GetIcon

class ScreenshotDialog(QtWidgets.QDialog):
    """
    Dialog to take screenshots
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('ScrShtDlg', 0))
        self.setWindowIcon(GetIcon('screenshot'))

        self.target_combo = QtWidgets.QComboBox()
        self.target_combo.addItem(globals_.trans.string('ScrShtDlg', 1)) # Current Screen
        self.target_combo.addItem(globals_.trans.string('ScrShtDlg', 2)) # All Zones

        # Individual zones
        for i in range(len(globals_.Area.zones)):
            self.target_combo.addItem(globals_.trans.string('ScrShtDlg', 3, '[zone]', i + 1))

        self.grid_type = QtWidgets.QComboBox()
        self.grid_type.addItems(globals_.trans.stringList('ScrShtDlg', 9))

        curr_grid = 0
        if globals_.GridType is not None:
            if globals_.GridType == 'grid':
                curr_grid = 1
            else:
                curr_grid = 2

        self.grid_type.setCurrentIndex(curr_grid)

        self.hide_background = QtWidgets.QCheckBox()
        self.save_img = QtWidgets.QRadioButton()
        self.save_clip = QtWidgets.QRadioButton()

        self.save_img.setChecked(True)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        save_type_layout = QtWidgets.QHBoxLayout()
        save_type_layout.addWidget(self.save_img)
        save_type_layout.addWidget(QtWidgets.QLabel('|'))
        save_type_layout.addWidget(self.save_clip)
        save_type_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('ScrShtDlg', 7)))

        main_layout = QtWidgets.QFormLayout()
        main_layout.addRow(globals_.trans.string('ScrShtDlg', 4), self.target_combo)
        main_layout.addRow(globals_.trans.string('ScrShtDlg', 8), self.grid_type)
        main_layout.addRow(globals_.trans.string('ScrShtDlg', 5), self.hide_background)
        main_layout.addRow(globals_.trans.string('ScrShtDlg', 6), save_type_layout)
        main_layout.addRow(button_box)
        self.setLayout(main_layout)
