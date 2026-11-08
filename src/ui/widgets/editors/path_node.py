from PyQt6 import QtWidgets

from data import globals_
from data.level.dirty import SetDirty
from data.level.items.path import PathItem
from data.level.path import Path
from ui.theme.reggie_theme import createHorzLine


class PathNodeEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing path node properties
    """

    def __init__(self) -> None:
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
        self.speed.setToolTip(globals_.trans.string('dialog.path_data_editor.speed.tooltip'))
        self.speed.setDecimals(FLT_DIG)
        self.speed.valueChanged.connect(self.handle_speed_changed)

        self.accel = QtWidgets.QDoubleSpinBox()
        self.accel.setRange(-FLT_MAX, FLT_MAX)
        self.accel.setToolTip(globals_.trans.string('dialog.path_data_editor.accel.tooltip'))
        self.accel.setDecimals(FLT_DIG)
        self.accel.valueChanged.connect(self.handle_accel_changed)

        self.delay = QtWidgets.QSpinBox()
        self.delay.setRange(0, 65535)
        self.delay.setToolTip(globals_.trans.string('dialog.path_data_editor.delay.tooltip'))
        self.delay.valueChanged.connect(self.handle_delay_changed)

        self.loops = QtWidgets.QCheckBox()
        self.loops.setToolTip(globals_.trans.string('dialog.path_data_editor.loops.tooltip'))
        self.loops.clicked.connect(self.handle_loops_changed)

        self.mode_button = QtWidgets.QPushButton()
        self.mode_button.clicked.connect(self.handle_mode_changed)
        self.mode_button.setToolTip(globals_.trans.string('dialog.path_data_editor.placement_mode.tooltip'))
        self.set_mode_text()

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
        layout.addRow(globals_.trans.string('common.id_colon'), self.path_id)
        layout.addRow(globals_.trans.string('dialog.path_data_editor.loops.label'), self.loops)
        layout.addRow(self.mode_button)
        layout.addRow(createHorzLine())

        layout.addRow(self.editing_label)
        layout.addRow(globals_.trans.string('common.id_colon'), self.node_id)
        layout.addRow(globals_.trans.string('dialog.path_data_editor.speed.label'), self.speed)
        layout.addRow(globals_.trans.string('dialog.path_data_editor.accel.label'), self.accel)
        layout.addRow(globals_.trans.string('dialog.path_data_editor.delay.label'), self.delay)

        self.set_dummy()

        self.path_node = None
        self.update_flag = False

    def set_widget_visibility(self, enabled: bool) -> None:
        """
        Quickly show/hide all child widgets
        """
        layout = self.layout()
        if layout is None:
            return

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setVisible(enabled)

    def set_dummy(self) -> None:
        """
        Hide all fields and put the editor into a blank state
        """
        self.set_widget_visibility(False)

        self.editing_label.setText(globals_.trans.string('dialog.path_data_editor.none_selected'))
        self.editing_label.setVisible(True)

    def setPath(self, path_item: PathItem) -> None:
        """
        Change the path being edited by the editor, update all fields
        """
        if self.path_node == path_item:
            return

        self.set_widget_visibility(True)

        self.path_node = path_item

        self.editing_path_label.setText(globals_.trans.string('dialog.path_data_editor.info.path', ('[id]', path_item.pathid)))
        self.editing_label.setText(globals_.trans.string('dialog.path_data_editor.info.node', ('[id]', path_item.nodeid)))

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

    def update_path_length(self) -> None:
        """
        The length of the path changed, so update the range of the Node ID editor.
        """
        if self.path_node is not None:
            self.node_id.setRange(0, len(self.path_node.path) - 1)

    def handle_speed_changed(self, i: int) -> None:
        """
        Handler for the speed changing
        """
        if self.update_flag:
            return

        if self.path_node is not None and self.path_node.path.set_node_data(self.path_node, speed=i):
            SetDirty()

    def handle_accel_changed(self, i: int) -> None:
        """
        Handler for the accel changing
        """
        if self.update_flag:
            return

        if self.path_node is not None and self.path_node.path.set_node_data(self.path_node, accel=i):
            SetDirty()

    def handle_delay_changed(self, i: int) -> None:
        """
        Handler for the delay changing
        """
        if self.update_flag:
            return

        if self.path_node is not None and  self.path_node.path.set_node_data(self.path_node, delay=i):
            SetDirty()

    def handle_loops_changed(self, checked: bool) -> None:
        if self.path_node is None:
            return

        if self.update_flag or self.path_node.path._loops == checked:
            return

        self.path_node.path.set_loops(checked)
        SetDirty()

    def handle_path_id_changed(self, i: int) -> None:
        if self.path_node is None:
            return

        if self.update_flag or self.path_node.pathid == i:
            return

        self.path_node.path.set_id(i)
        SetDirty()

    def handle_node_id_changed(self, i: int) -> None:
        if self.path_node is None:
            return

        if self.update_flag or self.path_node.nodeid == i:
            return

        self.path_node.path.move_node(self.path_node, i)
        SetDirty()

    def set_mode_text(self) -> None:
        """
        Sets the mode button text
        """
        text_id = 'insert' if globals_.InsertPathNode else 'append'
        self.mode_button.setText(globals_.trans.string(f'dialog.path_data_editor.placement_mode.names.{text_id}'))

    def handle_mode_changed(self) -> None:
        """
        Handles the placement mode being switched
        """
        globals_.InsertPathNode = not globals_.InsertPathNode
        self.set_mode_text()
