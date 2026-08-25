from PyQt6 import QtWidgets

import globals_
from src.ui.theme.reggie_theme import createHorzLine
from dirty import SetDirty

from levelitems import Path, PathItem

class PathNodeEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing path node properties
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))

        # Some single point float constants. Note that we cannot use the ones
        # provided by sys.float_info, since those relate to double precision
        # floats, and the speed and acceleration fields are single precision
        # floats. As such, we just hardcode these values.
        FLT_DIG = 6
        FLT_MAX = 3.402823466e+38

        # Create widgets
        self.speed = QtWidgets.QDoubleSpinBox()
        self.speed.setRange(-FLT_MAX, FLT_MAX)
        self.speed.setToolTip(globals_.trans.string('PathDataEditor', 3))
        self.speed.setDecimals(FLT_DIG)
        self.speed.valueChanged.connect(self.handle_speed_changed)

        self.accel = QtWidgets.QDoubleSpinBox()
        self.accel.setRange(-FLT_MAX, FLT_MAX)
        self.accel.setToolTip(globals_.trans.string('PathDataEditor', 5))
        self.accel.setDecimals(FLT_DIG)
        self.accel.valueChanged.connect(self.handle_accel_changed)

        self.delay = QtWidgets.QSpinBox()
        self.delay.setRange(0, 65535)
        self.delay.setToolTip(globals_.trans.string('PathDataEditor', 7))
        self.delay.valueChanged.connect(self.handle_delay_changed)

        self.loops = QtWidgets.QCheckBox()
        self.loops.setToolTip(globals_.trans.string('PathDataEditor', 1))
        self.loops.clicked.connect(self.handle_loops_changed)

        # Create a layout
        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        # 'Editing Path #' label
        self.editing_label = QtWidgets.QLabel('-')
        self.editing_path_label = QtWidgets.QLabel('-')

        self.path_id = QtWidgets.QSpinBox()
        self.path_id.setRange(0, 255)
        self.path_id.valueChanged.connect(self.handle_path_id_changed)

        self.node_id = QtWidgets.QSpinBox()
        self.node_id.setRange(0, 255)
        self.node_id.valueChanged.connect(self.handle_node_id_changed)

        layout.addRow(self.editing_path_label)

        # Add labels
        layout.addRow(globals_.trans.string('PathDataEditor', 11), self.path_id)
        layout.addRow(globals_.trans.string('PathDataEditor', 0), self.loops)
        layout.addRow(createHorzLine())

        layout.addRow(self.editing_label)
        layout.addRow(globals_.trans.string('PathDataEditor', 11), self.node_id)
        layout.addRow(globals_.trans.string('PathDataEditor', 2), self.speed)
        layout.addRow(globals_.trans.string('PathDataEditor', 4), self.accel)
        layout.addRow(globals_.trans.string('PathDataEditor', 6), self.delay)

        self.path_node = None
        self.update_flag = False

    def setPath(self, path_item: PathItem):
        """
        Change the path being edited by the editor, update all fields
        """
        if self.path_node == path_item:
            return

        self.path_node = path_item

        self.editing_path_label.setText(globals_.trans.string('PathDataEditor', 8, '[id]', path_item.pathid))
        self.editing_label.setText(globals_.trans.string('PathDataEditor', 9, '[id]', path_item.nodeid))

        path: Path = path_item.path
        speed, accel, delay = path.get_data_for_node(path_item.nodeid)
        loops = path.get_loops()
        path_len = len(path)

        self.update_flag = True

        self.node_id.setRange(0, path_len - 1)
        self.node_id.setEnabled(path_len > 1)
        self.node_id.setValue(path_item.nodeid)
        self.path_id.setValue(path_item.pathid)
        self.speed.setValue(speed)
        self.accel.setValue(accel)
        self.delay.setValue(delay)
        self.loops.setChecked(loops)

        self.update_flag = False

    def update_path_length(self):
        """
        The length of the path changed, so update the range of the Node ID editor.
        """
        if self.path_node is not None:
            self.node_id.setRange(0, len(self.path_node.path) - 1)

    def handle_speed_changed(self, i):
        """
        Handler for the speed changing
        """
        if self.update_flag:
            return

        if self.path_node is not None:
            if self.path_node.path.set_node_data(self.path_node, speed=i):
                SetDirty()

    def handle_accel_changed(self, i):
        """
        Handler for the accel changing
        """
        if self.update_flag:
            return

        if self.path_node is not None:
            if self.path_node.path.set_node_data(self.path_node, accel=i):
                SetDirty()

    def handle_delay_changed(self, i):
        """
        Handler for the delay changing
        """
        if self.update_flag:
            return

        if self.path_node is not None:
            if self.path_node.path.set_node_data(self.path_node, delay=i):
                SetDirty()

    def handle_loops_changed(self, checked):
        if self.path_node is None:
            return

        if self.update_flag or self.path_node.path._loops == checked:
            return

        self.path_node.path.set_loops(checked)
        SetDirty()

    def handle_path_id_changed(self, i):
        if self.path_node is None:
            return

        if self.update_flag or self.path_node.pathid == i:
            return

        self.path_node.path.set_id(i)
        SetDirty()

    def handle_node_id_changed(self, i):
        if self.path_node is None:
            return

        if self.update_flag or self.path_node.nodeid == i:
            return

        self.path_node.path.move_node(self.path_node, i)
        SetDirty()
