#!/usr/bin/python
# -*- coding: latin-1 -*-

# Reggie Next - New Super Mario Bros. Wii Level Editor
# Milestone 4
# Copyright (C) 2009-2026 Treeki, Tempus, angelsl, JasonP27, Kamek64,
# MalStar1000, RoadrunnerWMC, AboodXD, John10v10, TheGrop, CLF78,
# Zementblock, Danster64

# This file is part of Reggie Next.

# Reggie Next is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Reggie Next is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Reggie Next.  If not, see <http://www.gnu.org/licenses/>.


# reggie.py
# This is the main executable for Reggie Next.


################################################################
################################################################

import sys

# Check the version of Python we're running
min_py_version = (3, 12)

try:
    if sys.version_info < min_py_version:
        error_msg = 'Reggie Next requires Python ' + '.'.join(map(str, min_py_version)) + \
                ' or greater in order to function. You are currently running on: ' + sys.version[:5]
        raise Exception(error_msg)
except Exception as e:
    print(e)
    input('\nPress Enter to exit...') # Keep the cmd/terminal window open, so this message can be seen
    sys.exit(1)

# Stdlib imports
import os.path
import time
import traceback

# Check for PyQt6 and import it
try:
    from PyQt6 import QtCore, QtGui, QtWidgets
except (ImportError, NameError, ModuleNotFoundError):
    print('PyQt6 is not installed for this Python installation. Go online and download it.')
    input('\nPress Enter to exit...')
    sys.exit(1)

# Now check the PyQt version
version = map(int, QtCore.QT_VERSION_STR.split('.'))
min_qt_version = '6.9'
pqt_min = map(int, min_qt_version.split('.'))

for v, c in zip(version, pqt_min):
    try:
        if c > v: # Lower version
            error_msg = 'Reggie Next requires PyQt ' + min_qt_version \
                    + ' or greater in order to function. You are currently using PyQt ' + QtCore.QT_VERSION_STR
            raise Exception(error_msg)
    except Exception as e:
        print(e)
        input('\nPress Enter to exit...')
        sys.exit(1)

Qt = QtCore.Qt

################################################################################
################################################################################
################################################################################

# Local imports
from data import globals_

import spritelib as SLib
from data.common.sprites import LoadBasics

from ui.theme.reggie_theme import SetAppStyle, LoadNumberFont, SetColorScheme, GetAppIcon
from data.common.loaders import LoadToolbarActionsLists, LoadTheme, LoadDefaultKeybinds, module_path
from data.common.utils import SetGamePaths, get_reggiedata_folder, get_root_path
from data.common.validators import FilesAreMissing, areValidGamePaths

from data.common.settings import setting, setSetting
from data.common.gamedef import LoadGameDef

from data.common.loaders import LoadOverrides

from data.common.loaders import LoadTranslation

from ui.dialogs.auto_save import AutoSaveDialog
from ui.widgets.reggie_window import ReggieWindow

def _excepthook(*exc_info):
    """
    Custom unhandled exceptions handler
    """
    separator = '-' * 80
    log_file = 'log.txt'
    notice = globals_.trans.string('Err_Common', 0, '[log]', log_file)
    if notice is None:
        notice = ''

    time_string = time.strftime('%Y-%m-%d, %H:%M:%S')

    e = ''.join(traceback.format_exception(*exc_info))
    sections = [separator, time_string, separator, e]
    msg = '\n'.join(sections)

    globals_.ErrMsg += msg

    try:
        with open(os.path.join(get_root_path(), log_file), 'w', encoding='utf-8') as f:
            f.write(globals_.ErrMsg)
    except IOError:
        pass

    error_box = QtWidgets.QMessageBox()
    error_box.setText(notice + msg)
    error_box.exec()

    globals_.DirtyOverride = 0


# Override the exception handler with ours
sys.excepthook = _excepthook

################################################################################
################################################################################
################################################################################

def main():
    """
    Main startup function for Reggie
    """
    # Set High-DPI-Displays-related attributes before creating an application
    if hasattr(QtGui.QGuiApplication, 'setHighDpiScaleFactorRoundingPolicy'):
        QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Round)

    # Create backup of settings
    if os.path.isfile(os.path.join(get_root_path(), 'settings.ini')):
        from shutil import copy2
        copy2(os.path.join(get_root_path(), 'settings.ini'), os.path.join(get_root_path(), 'settings.ini.bak'))
        del copy2

    # Load the settings
    globals_.settings = QtCore.QSettings(os.path.join(get_root_path(), 'settings.ini'), QtCore.QSettings.Format.IniFormat)

    globals_.IgnoreWinScale = setting('IgnoreWinScale', False)
    if globals_.IgnoreWinScale:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = '0'
        os.environ["QT_FONT_DPI"] = '96'

    # Add a unique ID for the app so the taskbar separates Reggie
    # from the default Python interpreter
    if sys.platform == 'win32':
        import ctypes
        app_id = f'reggie.next.{globals_.ReggieVersionShort}'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        del ctypes

    # Create an application
    globals_.app = QtWidgets.QApplication(sys.argv)

    # Go to the script path
    path = module_path()
    if path is not None:
        os.chdir(path)

    # Try to get the last commit ID, and append it to the version ID
    # (Only works when the repository's ".git" folder is present)
    import subprocess

    try:
        commit_id = subprocess.check_output(["git", "describe", "--always"], stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL).decode('utf-8').strip()
        globals_.ReggieVersionShort += f'-{commit_id}'
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    del subprocess

    # Check the version and set the UI style to Fusion by default
    if setting("ReggieVersion") is None:
        setSetting("ReggieVersion", globals_.ReggieVersionFloat)
        setSetting('uiStyle', "Fusion")

    # Set the default window name/icon (used for random popups and stuff)
    globals_.app.setWindowIcon(GetAppIcon())
    globals_.app.setApplicationDisplayName('Reggie! Next %s' % globals_.ReggieVersionShort)

    # 4.0 -> Oldest version with settings.ini compatible with the current version
    reggie_ver = setting("ReggieVersion")
    if reggie_ver is not None and reggie_ver < 4.0:
        QtWidgets.QMessageBox.critical(None, 'Unsupported settings file', 'Your settings.ini file is not supported by this version of Reggie Next.<br' \
                                       'Please remove it and run Reggie again.')
        sys.exit(1)

    # Load the translation (needs to happen first)
    LoadTranslation()

    # Check if required files are missing
    if FilesAreMissing():
        sys.exit(1)

    # Load some requirements for spritelib
    LoadTheme()
    LoadOverrides()

    # Initialise spritelib
    SLib.OutlineColor = globals_.theme.color('smi')
    SLib.main()

    # Load the gamedef (including sprite image path, for which we need spritelib)
    LoadGameDef(setting('LastGameDef'))
    LoadBasics()

    # Load remaining requirements
    LoadToolbarActionsLists()
    LoadDefaultKeybinds()
    LoadNumberFont()
    SetAppStyle()

    # Initialize some values from settings
    grid_type = setting('GridType')
    if grid_type not in ('checker', 'grid'):
        globals_.GridType = None
    else:
        globals_.GridType = grid_type

    globals_.CollisionsShown = setting('ShowCollisions', False)
    globals_.RealViewEnabled = setting('RealViewEnabled', True)
    globals_.ObjectsFrozen = setting('FreezeObjects', False)
    globals_.SpritesFrozen = setting('FreezeSprites', False)
    globals_.EntrancesFrozen  = setting('FreezeEntrances', False)
    globals_.LocationsFrozen = setting('FreezeLocations', False)
    globals_.PathsFrozen = setting('FreezePaths', False)
    globals_.CommentsFrozen = setting('FreezeComments', False)
    globals_.SpritesShown = setting('ShowSprites', True)
    globals_.SpriteImagesShown = setting('ShowSpriteImages', True)
    globals_.LocationsShown = setting('ShowLocations', True)
    globals_.EntrancesShown = setting('ShowEntrances', True)
    globals_.CommentsShown = setting('ShowComments', True)
    globals_.PathsShown = setting('ShowPaths', True)
    globals_.DrawEntIndicators = setting('ZoneEntIndicators', False)
    globals_.BoundsDrawn = setting('ZoneBoundIndicators', False)
    globals_.ResetDataWhenHiding = setting('ResetDataWhenHiding', False)
    globals_.EnablePadding = setting('EnablePadding', False)
    pad_len = setting('PaddingLength', 0)
    if pad_len is not None:
        globals_.PaddingLength = int(pad_len)
    globals_.PlaceObjectsAtFullSize = setting('PlaceObjectsAtFullSize', True)
    globals_.InsertPathNode = setting('InsertPathNode', False)
    globals_.UseRoundedRectangles = setting('UseRoundedRectangles', True)
    globals_.DarkMode = setting('DarkMode', False)
    globals_.UseFullFilepath = setting('UseFullFilepath', False)
    globals_.CursorMode = setting('CursorMode', 0)
    globals_.TilesetTabPos = setting('TilesetTabPos', 0)
    globals_.UseRecentFileKeys = setting('UseRecentFileKeys', True)
    globals_.AutoDiagEnabled = setting('AutoDiagEnabled', True)
    globals_.AutoDiagFrequency = setting('AutoDiagFrequency', 1)
    globals_.ShowUnknownSpriteWarning = setting('ShowUnknownSpriteWarning', True)
    globals_.MoveItemsWithArrowKeys = setting('MoveItemsWithArrowKeys', True)
    globals_.ShowTilesetPreview = setting('ShowTilesetPreview', True)
    SLib.RealViewEnabled = globals_.RealViewEnabled

    # Choose a folder for the game
    # Let the user pick a folder without restarting the editor if they fail
    while not areValidGamePaths():
        stage_path = QtWidgets.QFileDialog.getExistingDirectory(
            None,
            globals_.trans.string('ChangeGamePath', 0, '[game]', globals_.gamedef.name)
        )

        if stage_path == '':
            sys.exit(0)

        stage_path = str(stage_path)
        texture_path = os.path.join(stage_path, "Texture")

        while not os.path.isdir(texture_path):
            texture_path = QtWidgets.QFileDialog.getExistingDirectory(
                None,
                globals_.trans.string('ChangeGamePath', 4, '[game]', globals_.gamedef.name)
            )

            if texture_path == "":
                sys.exit(0)

        SetGamePaths(stage_path, texture_path)
        if areValidGamePaths():
            break

        if globals_.gamedef.custom:
            msg = globals_.trans.string('ChangeGamePath', 3, '[game]', globals_.gamedef.name)
        else:
            msg = globals_.trans.string('ChangeGamePath', 2)
        QtWidgets.QMessageBox.information(None, globals_.trans.string('ChangeGamePath', 1), msg)

    # Check to see if we have anything saved
    auto_file = setting('AutoSaveFilePath')
    auto_file_data = setting('AutoSaveFileData', 'x')
    if auto_file is not None and auto_file_data not in (None, 'x'):
        result = AutoSaveDialog(auto_file).exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            globals_.RestoredFromAutoSave = True
            globals_.AutoSavePath = auto_file
            globals_.AutoSaveData = bytes(auto_file_data)
        else:
            setSetting('AutoSaveFilePath', None)
            setSetting('AutoSaveFileData', 'x')

    # Toggle light/dark mode
    SetColorScheme()

    # Create and show the main window
    globals_.mainWindow = ReggieWindow()
    globals_.mainWindow.__init2__()
    globals_.mainWindow.show()

    # We might have something in the clipboard already, activate Paste if so
    globals_.mainWindow.TrackClipboardUpdates()

    if '-generatestringsxml' in sys.argv:
        globals_.trans.generateXML()

    exitcodesys = globals_.app.exec()
    globals_.app.deleteLater()
    sys.exit(exitcodesys)


if __name__ == '__main__': main()
