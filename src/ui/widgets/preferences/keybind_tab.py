from PyQt6 import QtWidgets
import collections

import globals_
from misc import GetKeybind, SetKeybind

from src.ui.widgets.preferences.widgets.preference_tab import PreferenceTabWidget
from src.ui.widgets.preferences.widgets.keybind_line_edit import KeybindLineEdit
from src.ui.widgets.preferences.widgets.keybind_editor_tab import KeybindEditorTab

class KeybindTab(PreferenceTabWidget):
    """
    Keybind Tab
    """

    def __init__(self, info_text):
        """
        Initializes the Keybinds Tab
        """
        super().__init__(info_text)
        self.tab_widget = QtWidgets.QTabWidget()
        self.tabs = []

        # Create tabs
        for i in range(5):
            tab = KeybindEditorTab(i)
            self.tabs.append(tab)
            self.tab_widget.addTab(tab, globals_.trans.string('Menubar', i))

        # Reset button
        reset = QtWidgets.QPushButton(globals_.trans.string('PrefsDlg', 58))
        reset.clicked.connect(self.reset)

        # Check for Conflicts button
        self.check_conflict_button = QtWidgets.QPushButton(globals_.trans.string('PrefsDlg', 59))
        self.check_conflict_button.clicked.connect(self.check_conflicts)

        # Create the main layout
        L = QtWidgets.QGridLayout()
        L.addWidget(self.tab_widget, 0, 0, 1, 2)
        L.addWidget(reset, 1, 0, 1, 1)
        L.addWidget(self.check_conflict_button, 1, 1, 1, 1)
        self.setLayout(L)

    def reset(self):
        """
        Resets all keybinds to their original values
        """
        result = QtWidgets.QMessageBox.warning(None, globals_.trans.string('PrefsDlg', 61), globals_.trans.string('PrefsDlg', 62),
                                                QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            for tab in self.tabs:
                tab.reset_keys()

    def check_conflicts(self):
        """
        Checks for any conflicting (duplicate) keybinds
        """
        # Get all of the current keybinds
        curr_keys = {}
        tab: KeybindEditorTab
        key_edit: KeybindLineEdit

        for tab in self.tabs:
            for key_edit in tab.key_edits:
                if key_edit.keySequence().toString() != '': # Ignore blanks
                    curr_keys[key_edit.name] = key_edit.keySequence()

        # Group everything together
        sorted = collections.defaultdict(list)
        for key, value in curr_keys.items():
            sorted[value].append(key)

        conflicts = {
            value: keys
            for value, keys in sorted.items()
            if len(keys) > 1
        }

        groups = [
            globals_.FileKeybinds,
            globals_.EditKeybinds,
            globals_.ViewKeybinds,
            globals_.SettingsKeybinds,
            globals_.HelpKeybinds,
        ]

        if not conflicts:
            # No conflicts, show a quick tooltip
            pos = self.check_conflict_button.mapToGlobal(self.check_conflict_button.rect().center())
            QtWidgets.QToolTip.showText(pos, globals_.trans.string('PrefsDlg', 65), self.check_conflict_button)
        else:
            # Conflicts were detected, list them in a warning message
            out_string = ''

            for keybind, names in conflicts.items():
                out_string += f'* {keybind.toString()}: '

                # We have the shortname identifier, but we need
                # to show the translation string instead
                for i, name in enumerate(names):
                    for g in groups:
                        if name in g.keys():
                            # Formatting, italicize and separate entries
                            out_string += f'<i>{g[name][1]}</i>'
                            if i != len(names) - 1:
                                out_string += ', '
                out_string += '<br>'

            QtWidgets.QMessageBox.warning(None, globals_.trans.string('PrefsDlg', 63),
                                          globals_.trans.string('PrefsDlg', 64, '[conflicts]', out_string))
