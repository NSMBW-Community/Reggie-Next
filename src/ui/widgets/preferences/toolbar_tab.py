
from PyQt6 import QtWidgets

import globals_
from dirty import setting

from src.ui.widgets.preferences.widgets.preference_tab import PreferenceTabWidget
from src.ui.widgets.preferences.widgets.toolbar_check_box import ToolbarCheckBox

class ToolbarTab(PreferenceTabWidget):
    """
    Toolbar Tab
    """

    def __init__(self, info_text):
        """
        Initializes the Toolbar Tab
        """
        QtWidgets.QWidget.__init__(self)
        self.info = info_text

        # Determine which keys are activated
        if setting('ToolbarActs') in (None, 'None', 'none', '', 0):
            # Get the default settings
            toggled = {}
            for list in (globals_.FileActions, globals_.EditActions, globals_.ViewActions, globals_.SettingsActions, globals_.HelpActions):
                for action in list:
                    toggled[action.id] = action.active
        else:
            # Get the settings from the .ini
            toggled = setting('ToolbarActs')
            if toggled is not None:
                # Replace the QString keys with python string keys
                toggled = {str(key): toggled[key] for key in toggled}

        # Create some data
        self.file_boxes = []
        self.edit_boxes = []
        self.view_boxes = []
        self.settings_boxes = []
        self.help_boxes = []

        file_lyt = QtWidgets.QVBoxLayout()
        edit_lyt = QtWidgets.QVBoxLayout()
        view_lyt = QtWidgets.QVBoxLayout()
        settings_lyt = QtWidgets.QVBoxLayout()
        help_lyt = QtWidgets.QVBoxLayout()

        file_box = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 0))
        edit_box = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 1))
        view_box = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 2))
        settings_box = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 3))
        help_box = QtWidgets.QGroupBox(globals_.trans.string('Menubar', 4))

        # Arrange this data so it can be iterated over
        menu_items = (
            (globals_.FileActions, self.file_boxes, file_lyt, file_box),
            (globals_.EditActions, self.edit_boxes, edit_lyt, edit_box),
            (globals_.ViewActions, self.view_boxes, view_lyt, view_box),
            (globals_.SettingsActions, self.settings_boxes, settings_lyt, settings_box),
            (globals_.HelpActions, self.help_boxes, help_lyt, help_box),
        )

        # Set up the menus by iterating over the above data
        for defaults, boxes, layout, group in menu_items:
            for action in defaults:
                box = ToolbarCheckBox(action.text)
                boxes.append(box)
                layout.addWidget(box)
                if toggled is None:
                    break

                try:
                    box.setChecked(toggled[action.id])
                except KeyError:
                    pass

                # Used to save these later
                box.internal_name = action.id

            group.setLayout(layout)

        # Create the always-enabled Current Area checkbox
        current_area = QtWidgets.QCheckBox(globals_.trans.string('PrefsDlg', 19))
        current_area.setChecked(True)
        current_area.setEnabled(False)

        # Create the Reset button
        reset = QtWidgets.QPushButton(globals_.trans.string('PrefsDlg', 20))
        reset.clicked.connect(self.reset)

        # Create the main layout
        L = QtWidgets.QGridLayout()
        L.addWidget(reset, 0, 0, 1, 1)
        L.addWidget(file_box, 1, 0, 3, 1)
        L.addWidget(edit_box, 1, 1, 3, 1)
        L.addWidget(view_box, 1, 2, 3, 1)
        L.addWidget(settings_box, 1, 3, 1, 1)
        L.addWidget(help_box, 2, 3, 1, 1)
        L.addWidget(current_area, 3, 3, 1, 1)
        self.setLayout(L)

    def reset(self):
        """
        This is called when the Reset button is clicked
        """
        items = (
            (self.file_boxes, globals_.FileActions),
            (self.edit_boxes, globals_.EditActions),
            (self.view_boxes, globals_.ViewActions),
            (self.settings_boxes, globals_.SettingsActions),
            (self.help_boxes, globals_.HelpActions)
        )

        for boxes, defaults in items:
            for box, default in zip(boxes, defaults):
                box.setChecked(default[1])
