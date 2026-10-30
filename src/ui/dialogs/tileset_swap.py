from PyQt6 import QtWidgets

from data import globals_
from data.level.dirty import SetDirty
from ui.theme.reggie_theme import GetIcon


class TilesetSwapDialog(QtWidgets.QDialog):
    """
    Dialog to swap all objects of one tileset to another
    """

    def __init__(self) -> None:
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('SwapObjTilesDlg', 0))
        self.setWindowIcon(GetIcon('arrow-switch-block'))

        # Create widgets
        self.curr_tileset = QtWidgets.QComboBox()
        self.new_tileset = QtWidgets.QComboBox()

        slots = ('Pa0', 'Pa1', 'Pa2', 'Pa3')

        # Only offer slots that have a tileset
        for i in range(4):
            if globals_.mainWindow.palette_dock.object_tab.isTabEnabled(i):
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

    def swap_tilesets(self) -> None:
        """
        Swaps all tileset objects
        """
        from_tileset = self.curr_tileset.currentIndex()
        to_tileset = self.new_tileset.currentIndex()
        do_exchange = self.exchange_tiles.isChecked()

        if from_tileset == to_tileset:
            return

        for layer in globals_.Area.layers:
            for nsmbobj in layer:
                if nsmbobj.tileset == from_tileset:
                    nsmbobj.SetType(to_tileset, nsmbobj.object_num)
                    SetDirty()
                elif do_exchange and nsmbobj.tileset == to_tileset:
                    nsmbobj.SetType(from_tileset, nsmbobj.object_num)
                    SetDirty()
