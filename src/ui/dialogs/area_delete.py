from PyQt6 import QtWidgets

from data import globals_
from ui.theme.reggie_theme import GetIcon


class AreaDeleteDialog(QtWidgets.QDialog):
    """
    Dialog prompting you to delete the current area
    """

    def __init__(self) -> None:
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

    def delete_area(self) -> None:
        """
        Deletes the current area
        """
        mw = globals_.mainWindow

        # Save the current area in case something goes wrong.
        if not mw.save():
            return

        area_to_delete = globals_.Area.areanum
        new_area_one = 1 if area_to_delete != 1 else 2

        # Load the new area 1 before deleting the old area to avoid glitches
        # when the old area was area 1.
        mw.load_level(mw.fileSavePath, True, new_area_one)

        # Actually delete the area
        globals_.Level.deleteArea(area_to_delete)

        mw.action_list['deletearea'].setEnabled(len(globals_.Level.areas) > 1)

        # Update the area selection combobox
        mw.area_combo_box.clear()
        for area in globals_.Level.areas:
            mw.area_combo_box.addItem(globals_.trans.string('AreaCombobox', 0, '[num]', area.areanum))

        mw.area_combo_box.setCurrentIndex(0)

        # Save the level without the area as promised
        mw.save()
