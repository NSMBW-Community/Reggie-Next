from PyQt6 import QtWidgets

from data import globals_
from data.level.items.object import ObjectItem
from data.level.dirty import SetDirty
from ui.theme.reggie_theme import GetIcon


class ItemShiftDialog(QtWidgets.QDialog):
    """
    Dialog to shift selected items by a certain number of units
    """

    def __init__(self) -> None:
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('ShftItmDlg', 0))
        self.setWindowIcon(GetIcon('arrow-move'))

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

    def shift_items(self) -> None:
        """
        Shifts items by the specified amounts
        """
        items = globals_.mainWindow.scene.selectedItems()
        if not items:
            return

        offs_x = self.offset_x.value()
        offs_y = self.offset_y.value()

        # Do we need to do anything?
        if offs_x == 0 and offs_y == 0:
            return

        if ((offs_x % 16) != 0) or ((offs_y % 16) != 0):
            # Warn if any objects exist
            objects_exist = False
            type_obj = ObjectItem

            for obj in items:
                if isinstance(obj, type_obj):
                    objects_exist = True
                    break

            if objects_exist:
                # Objects are selected and the offset is not a multiple of 16.
                # We should warn the user that we will round the offset to the
                # nearest multiple of 16, because objects can only be placed on
                # the grid.
                result = QtWidgets.QMessageBox.warning(None, globals_.trans.string('ShftItmDlg', 5), globals_.trans.string('ShftItmDlg', 6),
                                                       QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
                if result == QtWidgets.QMessageBox.StandardButton.No:
                    return

                # Round the offset to the nearest multiple of 16
                offs_x = 16 * round(offs_x / 16)
                offs_y = 16 * round(offs_y / 16)

        pos_offs_x = offs_x * 1.5
        pos_offs_y = offs_y * 1.5

        globals_.OverrideSnapping = True

        for obj in items:
            obj.setPos(obj.x() + pos_offs_x, obj.y() + pos_offs_y)

        globals_.OverrideSnapping = False
        SetDirty()
