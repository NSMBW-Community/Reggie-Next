from PyQt6 import QtWidgets, QtCore

import globals_
from ui import createHorzLine
from dirty import SetDirty
from src.data.common.loaders import LoadEntranceNames

from levelitems import EntranceItem

class EntranceEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing entrance properties
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))

        LoadEntranceNames()
        self.supports_shift_left = {0, 1, 7, 8, 9, 12, 20, 21, 22, 23, 24, 27}
        self.supports_connected_pipe = {3, 4, 5, 6, 16, 17, 18, 19}
        self.supports_forward_pipe = {3, 4, 5, 6}

        # Create widgets
        self.entrance_id = QtWidgets.QSpinBox()
        self.entrance_id.setRange(0, 255)
        self.entrance_id.setToolTip(globals_.trans.string('EntranceDataEditor', 1))
        self.entrance_id.valueChanged.connect(self.handle_entrance_id_changed)

        self.entrance_type = QtWidgets.QComboBox()
        self.entrance_type.addItems(globals_.EntranceTypeNames.values())
        self.entrance_type.setToolTip(globals_.trans.string('EntranceDataEditor', 3))
        self.entrance_type.activated.connect(self.handle_entrance_type_changed)

        self.dest_area = QtWidgets.QSpinBox()
        self.dest_area.setRange(0, 4)
        self.dest_area.setToolTip(globals_.trans.string('EntranceDataEditor', 7))
        self.dest_area.valueChanged.connect(self.handle_dest_area_changed)

        self.dest_entrance = QtWidgets.QSpinBox()
        self.dest_entrance.setRange(0, 255)
        self.dest_entrance.setToolTip(globals_.trans.string('EntranceDataEditor', 5))
        self.dest_entrance.valueChanged.connect(self.handle_dest_entrance_changed)

        self.is_enterable_box = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 8))
        self.is_enterable_box.setToolTip(globals_.trans.string('EntranceDataEditor', 9))
        self.is_enterable_box.clicked.connect(self.handle_is_enterable_clicked)

        self.unk_flag_box = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 10))
        self.unk_flag_box.setToolTip(globals_.trans.string('EntranceDataEditor', 11))
        self.unk_flag_box.clicked.connect(self.handle_unk_flag_clicked)

        self.connect_pipe_box = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 12))
        self.connect_pipe_box.setToolTip(globals_.trans.string('EntranceDataEditor', 13))
        self.connect_pipe_box.clicked.connect(self.handle_connect_pipe_clicked)

        self.connect_pipe_reverse_box = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 14))
        self.connect_pipe_reverse_box.setToolTip(globals_.trans.string('EntranceDataEditor', 15))
        self.connect_pipe_reverse_box.clicked.connect(self.handle_connect_pipe_reverse_clicked)

        self.path_id = QtWidgets.QSpinBox()
        self.path_id.setRange(0, 255)
        self.path_id.setToolTip(globals_.trans.string('EntranceDataEditor', 17))
        self.path_id.valueChanged.connect(self.handle_path_id_changed)

        self.forward_pipe_box = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 18))
        self.forward_pipe_box.setToolTip(globals_.trans.string('EntranceDataEditor', 19))
        self.forward_pipe_box.clicked.connect(self.handle_forward_pipe_clicked)

        self.layer_id = QtWidgets.QComboBox()
        self.layer_id.addItems(globals_.trans.stringList('EntranceDataEditor', 21))
        self.layer_id.setToolTip(globals_.trans.string('EntranceDataEditor', 22))
        self.layer_id.activated.connect(self.handle_layer_id_changed)

        self.exit_level_box = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 29))
        self.exit_level_box.setToolTip(globals_.trans.string('EntranceDataEditor', 30))
        self.exit_level_box.clicked.connect(self.handle_exit_level_clicked)

        self.shift_left_box = QtWidgets.QCheckBox(globals_.trans.string('EntranceDataEditor', 31))
        self.shift_left_box.setToolTip(globals_.trans.string('EntranceDataEditor', 32))
        self.shift_left_box.clicked.connect(self.handle_shift_left_clicked)

        self.connect_exit_dir = QtWidgets.QComboBox()
        self.connect_exit_dir.addItems(globals_.trans.stringList('EntranceDataEditor', 27))
        self.connect_exit_dir.setToolTip(globals_.trans.string('EntranceDataEditor', 26))
        self.connect_exit_dir.activated.connect(self.handle_connect_exit_dir_changed)

        # Create the layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Entrance #' label
        self.editing_label = QtWidgets.QLabel('-')
        layout.addWidget(self.editing_label, 0, 0, 1, 4, QtCore.Qt.AlignmentFlag.AlignTop)

        # add labels
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 0)), 3, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 2)), 1, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)

        layout.addWidget(createHorzLine(), 2, 0, 1, 4)

        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 4)), 3, 2, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 6)), 4, 2, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)

        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 20)), 4, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)

        self.path_id_label = QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 16))
        self.pipe_exit_dir_label = QtWidgets.QLabel(globals_.trans.string('EntranceDataEditor', 25))

        # Add the widgets
        layout.addWidget(self.entrance_id, 3, 1, 1, 1)
        layout.addWidget(self.entrance_type, 1, 1, 1, 3)

        layout.addWidget(self.dest_entrance, 3, 3, 1, 1)
        layout.addWidget(self.layer_id, 4, 1, 1, 1)
        layout.addWidget(self.dest_area, 4, 3, 1, 1)
        layout.addWidget(createHorzLine(), 5, 0, 1, 4)
        layout.addWidget(self.is_enterable_box, 6, 0, 1, 2)
        layout.addWidget(self.unk_flag_box, 6, 2, 1, 2)
        layout.addWidget(self.exit_level_box, 7, 0, 1, 2)
        layout.addWidget(self.shift_left_box, 7, 2, 1, 2)
        layout.addWidget(self.forward_pipe_box, 8, 0, 1, 2)
        layout.addWidget(self.connect_pipe_box, 8, 2, 1, 2)

        self.connect_pipe_line = createHorzLine()
        layout.addWidget(self.connect_pipe_line, 9, 0, 1, 4)
        layout.addWidget(self.connect_pipe_reverse_box, 10, 0, 1, 2)
        layout.addWidget(self.path_id, 10, 3, 1, 1)
        layout.addWidget(self.path_id_label, 10, 2, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)

        layout.addWidget(self.pipe_exit_dir_label, 11, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.connect_exit_dir, 11, 2, 1, 2)

        self.ent = None
        self.update_flag = False

    def set_entrance(self, ent: EntranceItem):
        """
        Change the entrance being edited by the editor, update all fields
        """
        if self.ent == ent:
            return

        self.editing_label.setText(globals_.trans.string('EntranceDataEditor', 23, '[id]', ent.entid))
        self.ent = ent
        self.update_flag = True

        self.entrance_id.setValue(ent.entid)

        idx = list(globals_.EntranceTypeNames).index(ent.enttype)
        self.entrance_type.setCurrentIndex(idx)
        self.dest_area.setValue(ent.destarea)
        self.dest_entrance.setValue(ent.destentrance)

        self.is_enterable_box.setChecked(((ent.entsettings & 0x80) == 0))
        self.unk_flag_box.setChecked(((ent.entsettings & 2) != 0))
        self.exit_level_box.setChecked(ent.leave_level)

        self.shift_left_box.setVisible(ent.enttype in self.supports_shift_left)
        self.shift_left_box.setChecked(((ent.entsettings & 0x40) != 0))

        self.connect_pipe_box.setVisible(ent.enttype in self.supports_connected_pipe)
        self.connect_pipe_box.setChecked(((ent.entsettings & 8) != 0))

        self.connect_pipe_reverse_box.setVisible(ent.enttype in self.supports_connected_pipe and ((ent.entsettings & 8) != 0))
        self.connect_pipe_reverse_box.setChecked(((ent.entsettings & 1) != 0))

        self.forward_pipe_box.setVisible(ent.enttype in self.supports_forward_pipe)
        self.forward_pipe_box.setChecked(((ent.entsettings & 4) != 0))

        self.path_id.setVisible(ent.enttype in self.supports_connected_pipe and ((ent.entsettings & 8) != 0))
        self.path_id.setValue(ent.entpath)
        self.path_id_label.setVisible(ent.enttype in self.supports_connected_pipe and ((ent.entsettings & 8) != 0))

        self.connect_exit_dir.setVisible(ent.enttype in self.supports_connected_pipe and ((ent.entsettings & 8) != 0) and globals_.DispConnectedPipeDir)
        self.connect_exit_dir.setCurrentIndex(ent.cpdirection)
        self.pipe_exit_dir_label.setVisible(ent.enttype in self.supports_connected_pipe and ((ent.entsettings & 8) != 0) and globals_.DispConnectedPipeDir)
        self.connect_pipe_line.setVisible(ent.enttype in self.supports_connected_pipe and ((ent.entsettings & 8) != 0))

        self.layer_id.setCurrentIndex(ent.entlayer)

        self.update_flag = False

    def handle_entrance_id_changed(self, i):
        """
        Handler for the entrance ID changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            self.ent.entid = i
            self.ent.update()
            self.ent.UpdateTooltip()
            self.ent.UpdateListItem()
            self.editing_label.setText(globals_.trans.string('EntranceDataEditor', 23, '[id]', i))

    def handle_shift_left_clicked(self, checked):
        """
        Handle for the Spawn Half a Tile Left checkbox being clicked
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            if checked:
                self.ent.entsettings |= 0x40
            else:
                self.ent.entsettings &= ~0x40

    def handle_entrance_type_changed(self, new_index):
        """
        Handler for the entrance type changing
        """
        i = list(globals_.EntranceTypeNames)[new_index]
        if self.ent is None:
            return

        has_left_shift = i in self.supports_shift_left
        has_connect_pipe = i in self.supports_connected_pipe
        ent_has_connect_pipe = self.ent.enttype in self.supports_connected_pipe
        has_forward_pipe = i in self.supports_forward_pipe
        connect_pipe_toggled = (self.ent.entsettings & 8) != 0

        self.shift_left_box.setVisible(has_left_shift)
        self.connect_pipe_box.setVisible(has_connect_pipe)
        self.connect_pipe_reverse_box.setVisible(has_connect_pipe and connect_pipe_toggled)
        self.path_id_label.setVisible(i and connect_pipe_toggled)
        self.path_id.setVisible(i and connect_pipe_toggled)
        self.connect_exit_dir.setVisible(ent_has_connect_pipe and connect_pipe_toggled and globals_.DispConnectedPipeDir)
        self.connect_exit_dir.setVisible(ent_has_connect_pipe and connect_pipe_toggled and globals_.DispConnectedPipeDir)
        self.connect_pipe_line.setVisible(ent_has_connect_pipe and connect_pipe_toggled)
        self.forward_pipe_box.setVisible(has_forward_pipe)

        if self.update_flag:
            return

        SetDirty()
        self.ent.enttype = i
        self.ent.TypeChange()
        self.ent.update()
        self.ent.UpdateTooltip()
        if globals_.mainWindow is not None:
            globals_.mainWindow.scene.update()
        self.ent.UpdateListItem()

    def handle_dest_area_changed(self, i):
        """
        Handler for the destination area changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            self.ent.destarea = i
            self.ent.UpdateTooltip()
            self.ent.UpdateListItem()

    def handle_dest_entrance_changed(self, i):
        """
        Handler for the destination entrance changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            self.ent.destentrance = i
            self.ent.UpdateTooltip()
            self.ent.UpdateListItem()

    def handle_is_enterable_clicked(self, checked):
        """
        Handle for the Allow Entry checkbox being clicked
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            if not checked:
                self.ent.entsettings |= 0x80
            else:
                self.ent.entsettings &= ~0x80
            self.ent.UpdateTooltip()
            self.ent.UpdateListItem()

    def handle_unk_flag_clicked(self, checked):
        """
        Handle for the Unknown Flag checkbox being clicked
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            if checked:
                self.ent.entsettings |= 2
            else:
                self.ent.entsettings &= ~2

    def handle_exit_level_clicked(self, checked):
        """
        Handle the Send to World Map checkbox being clicked
        """
        if self.ent is None:
            return

        if self.update_flag or self.ent.leave_level == checked:
            return

        SetDirty()
        self.ent.leave_level = checked
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()

    def handle_connect_pipe_clicked(self, checked):
        """
        Handle for the connected pipe checkbox being clicked
        """
        self.connect_pipe_reverse_box.setVisible(checked)
        self.path_id.setVisible(checked)
        self.path_id_label.setVisible(checked)
        self.connect_exit_dir.setVisible(checked and globals_.DispConnectedPipeDir)
        self.pipe_exit_dir_label.setVisible(checked and globals_.DispConnectedPipeDir)
        self.connect_pipe_line.setVisible(checked)

        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            if checked:
                self.ent.entsettings |= 8
            else:
                self.ent.entsettings &= ~8

    def handle_connect_pipe_reverse_clicked(self, checked):
        """
        Handle for the connected pipe reverse checkbox being clicked
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            if checked:
                self.ent.entsettings |= 1
            else:
                self.ent.entsettings &= ~1

    def handle_path_id_changed(self, i):
        """
        Handler for the path ID changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            self.ent.entpath = i

    def handle_forward_pipe_clicked(self, checked):
        """
        Handle for the forward pipe checkbox being clicked
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            if checked:
                self.ent.entsettings |= 4
            else:
                self.ent.entsettings &= ~4

            # Update exit indicator
            self.ent.TypeChange()
            self.ent.update()

    def handle_layer_id_changed(self, i):
        """
        Handle for the active layer changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            self.ent.entlayer = i

    def handle_connect_exit_dir_changed(self, i):
        """
        Handle for CP Direction changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.ent is not None:
            self.ent.cpdirection = i
