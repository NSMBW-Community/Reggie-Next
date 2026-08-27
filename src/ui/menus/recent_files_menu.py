from PyQt6 import QtWidgets, QtGui
import os

import globals_
from src.ui.theme.reggie_theme import GetIcon, clipStr
from src.data.common.settings import setting, setSetting

class RecentFilesMenu(QtWidgets.QMenu):
    """
    A menu which displays recently opened files
    """
    def __init__(self):
        """
        Creates and initializes the menu
        """
        QtWidgets.QMenu.__init__(self)
        self.setMinimumWidth(192)
        self.setToolTipsVisible(True)

        # Here's how this works:
        # - Upon startup, RecentFiles is obtained from QSettings and put into self.file_list
        # - All modifications to the menu thereafter are then applied to self.file_list
        # - The actions displayed in the menu are determined by whatever's in self.file_list
        # - Whenever self.file_list is changed, self.write_settings is called which writes
        #   it all back to the QSettings

        # Populate FileList upon startup
        if globals_.settings.contains('RecentFiles'):
            self.file_list = str(setting('RecentFiles')).split('|')

        else:
            self.file_list = ['']

        # This fixes bugs
        self.file_list = [path for path in self.file_list if path.lower() not in ('', 'none', 'false', 'true')]

        self.update_action_list()

    def write_settings(self):
        """
        Writes file_list back to the settings
        """
        setSetting('RecentFiles', str('|'.join(self.file_list)))

    def update_action_list(self):
        """
        Updates the actions visible in the menu
        """
        # Remove actions in the menu
        self.clear()
        ico = GetIcon('new')

        for i, filename in enumerate(self.file_list):
            filename = os.path.basename(filename)
            short = clipStr(filename, 72)
            if short is not None:
                filename = short + '...'

            act = QtGui.QAction(ico, filename, self)
            if globals_.UseRecentFileKeys:
                if i <= 9:
                    act.setShortcut(QtGui.QKeySequence(f'Ctrl+Alt+{i}'))
            act.setToolTip(str(self.file_list[i]))

            handler = self.handle_open_recent_(i)
            act.triggered.connect(handler)

            self.addAction(act)

    def add_to_list(self, path):
        """
        Adds an entry to the list
        """
        MaxLength = 16
        path = str(path)

        # Fixes bugs
        if path in ('None', 'True', 'False'):
            return

        new = [path]
        for filename in self.file_list:
            if filename != path:
                new.append(filename)

        self.file_list = new[:MaxLength]
        self.write_settings()
        self.update_action_list()

    def remove_from_list(self, index):
        """
        Removes an entry from the list
        """
        del self.file_list[index]
        self.write_settings()
        self.update_action_list()

    def clear_all(self):
        """
        Clears all recent files from the list and the registry
        """
        self.file_list = []
        self.write_settings()
        self.update_action_list()

    def handle_open_recent_(self, i):
        return (lambda e: self.handle_open_recent(i))

    def handle_open_recent(self, number):
        """
        Open a recently opened level picked from the main menu
        """
        if globals_.mainWindow is None:
            return

        if globals_.mainWindow.CheckDirty():
            return

        if not globals_.mainWindow.LoadLevel(self.file_list[number], True, 1):
            self.remove_from_list(number)
