from PyQt6 import QtWidgets, QtCore

import globals_
from src.data.level.dirty import SetDirty
from src.ui.theme.reggie_theme import GetIcon, createVertLine

class ObjectTypeSwapDialog(QtWidgets.QDialog):
    """
    Dialog to swap individual objects
    """

    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('SwapObjDlg', 0))
        self.setWindowIcon(GetIcon('swap'))

        # Create widgets
        self.curr_type = QtWidgets.QSpinBox()
        self.new_type = QtWidgets.QSpinBox()

        self.curr_tileset = QtWidgets.QComboBox()
        self.new_tileset = QtWidgets.QComboBox()

        slots = ('Pa0', 'Pa1', 'Pa2', 'Pa3')

        # Only offer slots that have a tileset
        if globals_.mainWindow is not None:
            for i in range(4):
                if globals_.mainWindow.objAllTab.isTabEnabled(i):
                    self.curr_tileset.addItem(slots[i])
                    self.new_tileset.addItem(slots[i])

        self.curr_tileset.currentIndexChanged.connect(self.set_object_counts)
        self.new_tileset.currentIndexChanged.connect(self.set_object_counts)

        # Call this manually to set maximums
        self.set_object_counts()

        self.exchange_objects = QtWidgets.QCheckBox(globals_.trans.string('SwapObjDlg', 5))

        # Swap layout
        swap_layout = QtWidgets.QGridLayout()
        swap_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('SwapObjDlg', 1)), 0, 0)
        swap_layout.addWidget(self.curr_type, 0, 1)
        swap_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('SwapObjDlg', 2)), 1, 0)
        swap_layout.addWidget(self.curr_tileset, 1, 1)

        swap_layout.addWidget(createVertLine(), 0, 2, 2, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)

        swap_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('SwapObjDlg', 3)), 0, 3)
        swap_layout.addWidget(self.new_type, 0, 4)
        swap_layout.addWidget(QtWidgets.QLabel(globals_.trans.string('SwapObjDlg', 4)), 1, 3)
        swap_layout.addWidget(self.new_tileset, 1, 4)

        self.button_box = QtWidgets.QDialogButtonBox()
        self.button_box.addButton(globals_.trans.string('SwapObjDlg', 6), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(globals_.trans.string('SwapObjDlg', 7), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        self.button_box.clicked.connect(self.button_clicked)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(swap_layout)
        main_layout.addWidget(self.exchange_objects)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def button_clicked(self, button):
        """
        Handles one of the buttons being pressed and calls the correct handler
        """
        role = self.button_box.buttonRole(button)

        if role == QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole:
            self.swap_tiles()
        else:
            self.reject()

    def swap_tiles(self):
        """
        Swaps the tile objects
        """
        from_type = self.curr_type.value()
        from_tileset = self.curr_tileset.currentIndex()
        to_type = self.new_type.value()
        to_tileset = self.new_tileset.currentIndex()
        do_exchange = self.exchange_objects.isChecked()

        # If we don't need to do anything, don't do anything
        if from_type == to_type and from_tileset == to_tileset:
            return

        for layer in globals_.Area.layers:
            for nsmbobj in layer:
                if nsmbobj.object_num == from_type and nsmbobj.tileset == from_tileset:
                    nsmbobj.SetType(to_tileset, to_type)
                    SetDirty()
                elif do_exchange and nsmbobj.object_num == to_type and nsmbobj.tileset == to_tileset:
                    nsmbobj.SetType(from_tileset, from_type)
                    SetDirty()

    def get_tileset_object_count(self, index):
        """
        Returns the number of objects in a tileset
        """
        if globals_.mainWindow is None:
            return 0

        return len(globals_.mainWindow.objPicker.models[index].ritems) - 1

    def set_object_counts(self):
        """
        Sets upper limits for the object spinboxes
        """
        from_tileset = self.curr_tileset.currentIndex()
        to_tileset = self.new_tileset.currentIndex()

        from_obj_num = self.get_tileset_object_count(from_tileset)
        to_obj_num = self.get_tileset_object_count(to_tileset)

        self.curr_type.setRange(0, from_obj_num)
        self.new_type.setRange(0, to_obj_num)

        # Make sure we aren't above the new maximums
        if self.curr_type.value() > from_obj_num:
            self.curr_type.setValue(from_obj_num)

        if self.new_type.value() > to_obj_num:
            self.new_type.setValue(to_obj_num)
