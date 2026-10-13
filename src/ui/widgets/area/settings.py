from PyQt6 import QtWidgets

from data import globals_

class SettingsTab(QtWidgets.QWidget):
    """
    Widget that represents the Settings tab of the Area Options dialog
    """

    def __init__(self) -> None:
        super().__init__()

        self.timer = QtWidgets.QSpinBox()
        self.timer.setRange(0, 999)
        self.timer.setToolTip(globals_.trans.string('AreaDlg', 4))
        self.timer.setValue(globals_.Area.time_limit + 200)

        self.initial_entrance = QtWidgets.QSpinBox()
        self.initial_entrance.setRange(0, 255)
        self.initial_entrance.setToolTip(globals_.trans.string('AreaDlg', 6))
        self.initial_entrance.setValue(globals_.Area.start_entrance)

        self.toad_house_type = QtWidgets.QComboBox()
        self.toad_house_type.addItems(globals_.trans.stringList('AreaDlg', 33))
        self.toad_house_type.setCurrentIndex(globals_.Area.toad_house_type)

        self.screen_wrap = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 7))
        self.screen_wrap.setToolTip(globals_.trans.string('AreaDlg', 8))
        self.screen_wrap.setChecked(globals_.Area.screen_wrap_flag)

        self.credits = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 34))
        self.credits.setToolTip(globals_.trans.string('AreaDlg', 35))
        self.credits.setChecked(globals_.Area.credits_flag)

        self.face_left = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 36))
        self.face_left.setToolTip(globals_.trans.string('AreaDlg', 37))
        self.face_left.setChecked(globals_.Area.face_left_flag)

        self.unused_flag_1 = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 38))
        self.unused_flag_1.setToolTip(globals_.trans.string('AreaDlg', 39))
        self.unused_flag_1.setChecked(globals_.Area.unused_flag_1)

        self.unused_flag_2 = QtWidgets.QCheckBox(globals_.trans.string('AreaDlg', 40))
        self.unused_flag_2.setToolTip(globals_.trans.string('AreaDlg', 41))
        self.unused_flag_2.setChecked(globals_.Area.unused_flag_2)

        self.unused_val_1 = QtWidgets.QSpinBox()
        self.unused_val_1.setRange(0, 999)
        self.unused_val_1.setToolTip(globals_.trans.string('AreaDlg', 43))
        self.unused_val_1.setValue(globals_.Area.unused_val_1)

        self.unused_val_2 = QtWidgets.QSpinBox()
        self.unused_val_2.setRange(0, 999)
        self.unused_val_2.setToolTip(globals_.trans.string('AreaDlg', 45))
        self.unused_val_2.setValue(globals_.Area.unused_val_2)

        main_layout = QtWidgets.QFormLayout()
        main_layout.addRow(globals_.trans.string('AreaDlg', 3), self.timer)
        main_layout.addRow(globals_.trans.string('AreaDlg', 5), self.initial_entrance)
        main_layout.addRow(globals_.trans.string('AreaDlg', 32), self.toad_house_type)
        main_layout.addRow(self.screen_wrap)
        main_layout.addRow(self.credits)
        main_layout.addRow(self.face_left)
        main_layout.addRow(self.unused_flag_1)
        main_layout.addRow(self.unused_flag_2)
        main_layout.addRow(globals_.trans.string('AreaDlg', 42), self.unused_val_1)
        main_layout.addRow(globals_.trans.string('AreaDlg', 44), self.unused_val_2)
        self.setLayout(main_layout)

    def save(self) -> None:
        """
        Saves the settings
        """
        globals_.Area.time_limit = self.timer.value() - 200
        globals_.Area.start_entrance = self.initial_entrance.value()
        globals_.Area.toad_house_type = self.toad_house_type.currentIndex()
        globals_.Area.screen_wrap_flag = self.screen_wrap.isChecked()
        globals_.Area.credits_flag = self.credits.isChecked()
        globals_.Area.face_left_flag = self.face_left.isChecked()
        globals_.Area.unused_flag_1 = self.unused_flag_1.isChecked()
        globals_.Area.unused_flag_2 = self.unused_flag_2.isChecked()
        globals_.Area.unused_val_1 = self.unused_val_1.value()
        globals_.Area.unused_val_2 = self.unused_val_2.value()
