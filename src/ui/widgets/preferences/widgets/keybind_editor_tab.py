from PyQt6 import QtWidgets

import globals_
from src.data.common.loaders import GetKeybind, SetKeybind
from src.ui.widgets.preferences.widgets.keybind_line_edit import KeybindLineEdit


class KeybindEditorTab(QtWidgets.QWidget):
    """
    Represents a tab within the Keybinds tab
    """
    def __init__(self, index):
        super().__init__()
        self.index = index
        widget = QtWidgets.QWidget()

        # Make the tab scrollable so the window doesn't become absurdly tall
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)

        scroll_lyt = QtWidgets.QFormLayout(widget)
        self.key_edits = []

        groups = [
            globals_.FileKeybinds,
            globals_.EditKeybinds,
            globals_.ViewKeybinds,
            globals_.SettingsKeybinds,
            globals_.HelpKeybinds,
        ]

        # Create each keybind entry
        for keybind in groups[index]:
            edit = KeybindLineEdit(GetKeybind(keybind.id), keybind.id)
            self.key_edits.append(edit)

            # Get the label from the keybind data
            label = keybind.name
            scroll_lyt.addRow(label, edit)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def reset_keys(self):
        """
        Resets keybinds for this tab
        """
        groups = [
            globals_.FileKeybinds,
            globals_.EditKeybinds,
            globals_.ViewKeybinds,
            globals_.SettingsKeybinds,
            globals_.HelpKeybinds,
        ]

        for key_edit in self.key_edits:
            for keybind in groups[self.index]:
                if keybind.id == key_edit.name:
                    # Get default and update the action's keybind
                    defKey = keybind.key_sequence
                    if defKey is None:
                        key_edit.clear()
                    else:
                        key_edit.setKeySequence(defKey)

                    # Restore default keybind
                    SetKeybind(key_edit.name, defKey)
