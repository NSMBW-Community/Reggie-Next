from PyQt6 import QtCore, QtWidgets

from data import globals_
from data.common.utils import clamp


class CameraSettingsLayout(QtWidgets.QFormLayout):
    """
    A layout that shows the camera mode / zoom settings for editing.
    Separate from Zone Options so it can be reused for Camera Profiles
    """
    edited = QtCore.pyqtSignal()
    updating = False

    def __init__(self, show_cam_mode_5: bool) -> None:
        super().__init__()
        self.updating = True

        combobox_size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.zoom_mode = -1

        self.mode_button_group = QtWidgets.QButtonGroup()
        mode_buttons = []
        for i, name, tooltip in [
            (0, globals_.trans.string('CameraSettings', 0),  globals_.trans.string('CameraSettings', 1)),  # Normal
            (3, globals_.trans.string('CameraSettings', 2),  globals_.trans.string('CameraSettings', 3)),  # Static
            (4, globals_.trans.string('CameraSettings', 4),  globals_.trans.string('CameraSettings', 5)),  # Static, Y Track
            (5, globals_.trans.string('CameraSettings', 6),  globals_.trans.string('CameraSettings', 7)),  # Static, Event
            (6, globals_.trans.string('CameraSettings', 8),  globals_.trans.string('CameraSettings', 9)),  # X Track
            (7, globals_.trans.string('CameraSettings', 10), globals_.trans.string('CameraSettings', 11)), # X Expand
            (1, globals_.trans.string('CameraSettings', 12), globals_.trans.string('CameraSettings', 13)), # Y Track
            (2, globals_.trans.string('CameraSettings', 14), globals_.trans.string('CameraSettings', 15)), # Y Expand
        ]:
            btn = QtWidgets.QRadioButton(name)
            btn.setToolTip(f'<b>{name}:</b><br>{tooltip}')
            self.mode_button_group.addButton(btn, i)
            mode_buttons.append(btn)

            # Hides "Static Zoom, Event Controlled"
            if i == 5 and not show_cam_mode_5:
                btn.setVisible(False)

            btn.clicked.connect(self.update_list)
            btn.clicked.connect(self.mode_changed)

        self.screen_sizes = QtWidgets.QComboBox()
        self.screen_sizes.setToolTip(globals_.trans.string('CameraSettings', 17))
        self.screen_sizes.setSizePolicy(combobox_size_policy)
        self.screen_sizes.currentIndexChanged.connect(self.screen_size_changed)

        modes_layout = QtWidgets.QGridLayout()
        for i, btn in enumerate(mode_buttons):
            modes_layout.addWidget(btn, i % 4, i // 4)

        self.addRow(modes_layout)
        self.addRow(globals_.trans.string('CameraSettings', 16), self.screen_sizes)

        self.updating = False

    def update_list(self) -> None:
        """
        Handles changing the available Screen Heights items
        """
        mode = self.mode_button_group.checkedId()
        old_list_choice = [1, 1, 2, 3, 3, 3, 1, 1][self.zoom_mode]
        new_list_choice = [1, 1, 2, 3, 3, 3, 1, 1][mode]

        if self.zoom_mode != -1 and old_list_choice == new_list_choice:
            return

        if new_list_choice == 1:
            sizes = [
                ([14, 19], ''),
                ([14, 19, 24], ''),
                ([14, 19, 28], ''),
                ([20, 24], ''),
                ([19, 24, 28], ''),
                ([17, 24], ''),
                ([17, 24, 28], ''),
                ([17, 20], ''),
                ([7, 11, 28], '**'),
                ([17, 20.5, 24], ''),
                ([17, 20, 28], ''),
            ]
        elif new_list_choice == 2:
            sizes = [
                ([14, 19], ''),
                ([14, 19, 24], ''),
                ([14, 19, 28], ''),
                ([19, 19, 24], ''),
                ([19, 24, 28], ''),
                ([19, 24, 28], ''),
                ([17, 24, 28], ''),
                ([17, 20.5, 24], ''),
            ]
        else:
            sizes = [
                ([14], ''),
                ([19], ''),
                ([24], ''),
                ([28], ''),
                ([17], ''),
                ([20], ''),
                ([16], ''),
                ([28], ''),
                ([7], '*'),
                ([10.5], '*'),
            ]

        items = []
        for i, (options, asterisk) in enumerate(sizes):
            items.append(', '.join(str(o) for o in options) + asterisk)

        self.screen_sizes.clear()
        self.screen_sizes.addItems(items)
        self.screen_sizes.setCurrentIndex(0)
        self.zoom_mode = mode

    def set_values(self, mode: int, zoom: int) -> None:
        self.updating = True
        mode = clamp(mode, 0, 7)

        button = self.mode_button_group.button(mode)
        if button is not None:
            button.setChecked(True)
        self.update_list()

        zoom = clamp(zoom, 0, self.screen_sizes.count())

        self.screen_sizes.setCurrentIndex(zoom)
        self.updating = False

    def mode_changed(self) -> None:
        """
        Handles the camera mode being changed
        """
        if self.updating:
            return
        self.update_list()
        self.edited.emit()

    def screen_size_changed(self) -> None:
        """
        Handles the screen size being changed
        """
        if self.updating:
            return
        self.edited.emit()
