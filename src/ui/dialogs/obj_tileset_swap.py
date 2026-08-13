from PyQt6 import QtWidgets

import globals_
from ui import GetIcon

class ObjectTilesetSwapDialog(QtWidgets.QDialog):
    """
    Dialog to swap all objects of one tileset to another
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('SwapObjTilesDlg', 0))
        self.setWindowIcon(GetIcon('swap'))

        # Create widgets
        self.curr_tileset = QtWidgets.QComboBox()
        self.new_tileset = QtWidgets.QComboBox()

        slots = ('Pa0', 'Pa1', 'Pa2', 'Pa3')

        # Only offer slots that have a tileset
        if globals_.mainWindow is not None:
            for i in range(4):
                if globals_.mainWindow.objAllTab.isTabEnabled(i):
                    self.curr_tileset.addItem(slots[i])
                    self.new_tileset.addItem(slots[i])

        swap_layout = QtWidgets.QFormLayout()
        swap_layout.addRow(globals_.trans.string('SwapObjTilesDlg', 1), self.curr_tileset)
        swap_layout.addRow(globals_.trans.string('SwapObjTilesDlg', 2), self.new_tileset)

        self.exchange_tiles = QtWidgets.QCheckBox(globals_.trans.string('SwapObjTilesDlg', 3))

        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(globals_.trans.string('SwapObjTilesDlg', 4), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(globals_.trans.string('SwapObjTilesDlg', 5), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(swap_layout)
        main_layout.addWidget(self.exchange_tiles)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
