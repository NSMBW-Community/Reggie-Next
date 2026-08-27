from PyQt6 import QtWidgets, QtCore

import globals_
from src.ui.theme.reggie_theme import createHorzLine
from src.data.level.dirty import SetDirty

from levelitems import LocationItem

class LocationEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing location properties
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))

        # Create widgets
        self.location_id = QtWidgets.QSpinBox()
        self.location_id.setToolTip(globals_.trans.string('LocationDataEditor', 1))
        self.location_id.setRange(0, 255)
        self.location_id.valueChanged.connect(self.handle_location_id_changed)

        self.location_x = QtWidgets.QSpinBox()
        self.location_x.setToolTip(globals_.trans.string('LocationDataEditor', 3))
        self.location_x.setRange(16, 65535)
        self.location_x.valueChanged.connect(self.handle_location_x_changed)

        self.location_y = QtWidgets.QSpinBox()
        self.location_y.setToolTip(globals_.trans.string('LocationDataEditor', 5))
        self.location_y.setRange(16, 65535)
        self.location_y.valueChanged.connect(self.handle_location_y_changed)

        self.location_width = QtWidgets.QSpinBox()
        self.location_width.setToolTip(globals_.trans.string('LocationDataEditor', 7))
        self.location_width.setRange(1, 65535)
        self.location_width.valueChanged.connect(self.handle_location_width_changed)

        self.location_height = QtWidgets.QSpinBox()
        self.location_height.setToolTip(globals_.trans.string('LocationDataEditor', 9))
        self.location_height.setRange(1, 65535)
        self.location_height.valueChanged.connect(self.handle_location_height_changed)

        self.snap_button = QtWidgets.QPushButton(globals_.trans.string('LocationDataEditor', 10))
        self.snap_button.clicked.connect(self.handle_snap_to_grid)

        # Create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Location #' label
        self.editingLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 0, 0, 1, 4, QtCore.Qt.AlignmentFlag.AlignTop)

        # Add labels
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 0)), 1, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)

        layout.addWidget(createHorzLine(), 2, 0, 1, 4)

        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 2)), 3, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 4)), 4, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)

        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 6)), 3, 2, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(QtWidgets.QLabel(globals_.trans.string('LocationDataEditor', 8)), 4, 2, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)

        # Add the widgets
        layout.addWidget(self.location_id, 1, 1, 1, 1)
        layout.addWidget(self.snap_button, 1, 3, 1, 1)

        layout.addWidget(self.location_x, 3, 1, 1, 1)
        layout.addWidget(self.location_y, 4, 1, 1, 1)

        layout.addWidget(self.location_width, 3, 3, 1, 1)
        layout.addWidget(self.location_height, 4, 3, 1, 1)

        self.loc = None
        self.update_flag = False

    def set_location(self, loc: LocationItem):
        """
        Change the location being edited by the editor, update all fields
        """
        self.loc = loc
        self.update_flag = True

        self.fix_title()
        self.location_id.setValue(loc.id)
        self.location_x.setValue(int(loc.objx))
        self.location_y.setValue(int(loc.objy))
        self.location_width.setValue(int(loc.width))
        self.location_height.setValue(int(loc.height))

        self.update_flag = False

    def fix_title(self):
        if self.loc is not None:
            self.editingLabel.setText(globals_.trans.string('LocationDataEditor', 11, '[id]', self.loc.id))

    def handle_location_id_changed(self, i):
        """
        Handler for the location ID changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.loc is not None:
            self.loc.id = i
            self.loc.update()
            self.loc.UpdateTitle()
        self.fix_title()

    def handle_location_x_changed(self, i):
        """
        Handler for the location X-pos changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.loc is not None:
            self.loc.objx = i
            self.loc.autoPosChange = True
            self.loc.setX(int(i * 1.5))
            self.loc.autoPosChange = False
            self.loc.UpdateRects()
            self.loc.update()

    def handle_location_y_changed(self, i):
        """
        Handler for the location Y-pos changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.loc is not None:
            self.loc.objy = i
            self.loc.autoPosChange = True
            self.loc.setY(int(i * 1.5))
            self.loc.autoPosChange = False
            self.loc.UpdateRects()
            self.loc.update()

    def handle_location_width_changed(self, i):
        """
        Handler for the location width changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.loc is not None:
            self.loc.width = i
            self.loc.UpdateRects()
            self.loc.update()

    def handle_location_height_changed(self, i):
        """
        Handler for the location height changing
        """
        if self.update_flag:
            return

        SetDirty()
        if self.loc is not None:
            self.loc.height = i
            self.loc.UpdateRects()
            self.loc.update()

    def handle_snap_to_grid(self):
        """
        Snaps the current location to an 8x8 grid
        """
        SetDirty()
        if self.loc is None:
            return

        loc = self.loc
        left = loc.objx
        top = loc.objy
        right = left + loc.width
        bottom = top + loc.height

        if left % 8 < 4:
            left -= (left % 8)
        else:
            left += 8 - (left % 8)

        if top % 8 < 4:
            top -= (top % 8)
        else:
            top += 8 - (top % 8)

        if right % 8 < 4:
            right -= (right % 8)
        else:
            right += 8 - (right % 8)

        if bottom % 8 < 4:
            bottom -= (bottom % 8)
        else:
            bottom += 8 - (bottom % 8)

        if right <= left:
            right += 8
        if bottom <= top:
            bottom += 8

        loc.objx = left
        loc.objy = top
        loc.width = right - left
        loc.height = bottom - top

        loc.setPos(int(left * 1.5), int(top * 1.5))
        loc.UpdateRects()
        loc.update()

        # Update fields
        self.set_location(loc)
