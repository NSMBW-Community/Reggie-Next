import typing

from PyQt6 import QtWidgets

from data import globals_
from ui.theme.reggie_theme import GetIcon
from ui.widgets.preferences.appearance_tab import AppearanceTab
from ui.widgets.preferences.general_tab import GeneralTab
from ui.widgets.preferences.keybind_tab import KeybindTab
from ui.widgets.preferences.toolbar_tab import ToolbarTab
from ui.widgets.preferences.widgets.preference_tab import PreferenceTabWidget


class PreferencesDialog(QtWidgets.QDialog):
    """
    Dialog which lets you customize Reggie
    """

    def __init__(self) -> None:
        """
        Creates and initializes the dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('PrefsDlg', 0))
        self.setWindowIcon(GetIcon('gear'))

        # Create the tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.currentChanged.connect(self.tab_changed)

        self.info_label = QtWidgets.QLabel()
        self.general_tab = GeneralTab(globals_.trans.string('PrefsDlg', 4))
        self.toolbar_tab = ToolbarTab(globals_.trans.string('PrefsDlg', 5))
        self.keybind_tab = KeybindTab(globals_.trans.string('PrefsDlg', 57))
        self.appearance_tab = AppearanceTab(globals_.trans.string('PrefsDlg', 6))

        self.tab_widget.addTab(self.general_tab, GetIcon('gear'), globals_.trans.string('PrefsDlg', 1))
        self.tab_widget.addTab(self.toolbar_tab, GetIcon('toolbox'), globals_.trans.string('PrefsDlg', 2))
        self.tab_widget.addTab(self.keybind_tab, GetIcon('keyboard-full'), globals_.trans.string('PrefsDlg', 56))
        self.tab_widget.addTab(self.appearance_tab, GetIcon('monitor'), globals_.trans.string('PrefsDlg', 3))

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

        # Set the initial info text
        self.tab_changed()

    def tab_changed(self) -> None:
        """
        Handles the current tab being changed
        """
        tab = typing.cast(PreferenceTabWidget, self.tab_widget.currentWidget())
        self.info_label.setText(tab.info)

    def save_preferences(self) -> None:
        """
        Saves the preference settings
        """
        restart_1 = self.general_tab.save()
        restart_2 = self.toolbar_tab.save()
        restart_3 = self.keybind_tab.save()
        restart_4 = self.appearance_tab.save()

        # Warn the user that they may need to restart
        if restart_1 or restart_2 or restart_3 or restart_4:
            QtWidgets.QMessageBox.warning(None, globals_.trans.string('PrefsDlg', 0), globals_.trans.string('PrefsDlg', 30))
