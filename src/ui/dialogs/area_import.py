from PyQt6 import QtWidgets

import globals_
from src.ui.theme.reggie_theme import GetIcon

class AreaImportDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose an area to import
    """

    def __init__(self, area_count):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('AreaImportDlg', 0))
        self.setWindowIcon(GetIcon('area'))

        info_top = QtWidgets.QLabel()
        info_top.setText(globals_.trans.string('AreaImportDlg', 3))

        info_bottom = QtWidgets.QLabel()
        curr_area_count = len(globals_.Level.areas) + 1
        info_bottom.setText(globals_.trans.string('AreaImportDlg', 4, '[num]', curr_area_count))

        self.area_combo = QtWidgets.QComboBox()
        for i in range(area_count):
            self.area_combo.addItem(globals_.trans.string('AreaImportDlg', 1, '[num]', i + 1))

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(info_top)
        main_layout.addWidget(self.area_combo)
        main_layout.addWidget(info_bottom)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
