from PyQt6 import QtWidgets
import sys
import os
from xml.etree import ElementTree

################################################################################
################################################################################
################################################################################

import globals_

################################################################################
################################################################################
################################################################################

def module_path():
    """
    This will get us the program's directory, even if we are frozen using
    PyInstaller.
    """
    if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):  # PyInstaller
        if sys.platform == 'darwin':  # macOS
            # sys.executable is /x/y/z/reggie.app/Contents/MacOS/reggie
            # We need to return /x/y/z/reggie.app/Contents/Resources/

            macos = os.path.dirname(sys.executable)
            if os.path.basename(macos) != 'MacOS':
                return None

            return os.path.join(os.path.dirname(macos), 'Resources')

        else:  # Windows, Linux
            return os.path.dirname(sys.executable)

    if __name__ == 'misc':
        return os.path.dirname(os.path.abspath(__file__))

    return None


def checkContent(data):
    if not data.startswith(b'U\xAA8-'):
        return False

    required = (b'course\0', b'course1.bin\0', b'\0\0\0\x80')
    for r in required:
        if r not in data:
            return False

    return True


def IsNSMBLevel(filename):
    """
    Does some basic checks to confirm a file is a NSMB level
    """
    if not os.path.isfile(filename): return False

    with open(filename, 'rb') as f:
        data = f.read()

    if (data[0] & 0xF0) == 0x40 or not data.startswith(b"U\xAA8-"):  # If LH-compressed or LZ-compressed
        return True

    return checkContent(data)


def FilesAreMissing():
    """
    Checks to see if any of the required files for Reggie are missing
    """

    if not os.path.isdir('reggiedata'):
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingFiles', 0), globals_.trans.string('Err_MissingFiles', 1))
        return True

    required = ['icon.png', ]

    missing = []

    for check in required:
        if not os.path.isfile(os.path.join('reggiedata', check)):
            missing.append(check)

    if missing:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingFiles', 0),
                                      globals_.trans.string('Err_MissingFiles', 2, '[files]', ', '.join(missing)))
        return True

    return False


def SetGamePaths(new_stage_path, new_texture_path):
    """
    Sets the NSMBW game path
    """
    # os.path.join crashes if QStrings are used, so we must change the paths to
    # a Python string manually
    globals_.gamedef.SetStageGamePath(str(new_stage_path))
    globals_.gamedef.SetTextureGamePath(str(new_texture_path))


def areValidGamePaths(stage_check='ug', texture_check='ug'):
    """
    Checks to see if the path for NSMBW contains a valid game
    """
    if stage_check == 'ug':
        stage_check = globals_.gamedef.GetStageGamePath()

    if texture_check == 'ug':
        texture_check = globals_.gamedef.GetTextureGamePath()

    if not stage_check or not texture_check:
        return False

    # Check that both the stage and texture folders exist
    if not os.path.isdir(stage_check) or not os.path.isdir(texture_check):
        return False

    # Check that at least one readable level is located in the stage folder
    files = [f for f in os.listdir(stage_check) if os.path.isfile(os.path.join(stage_check, f))]
    for fname in files:
        if os.path.isfile(os.path.join(stage_check, fname)):
            name, ext = os.path.splitext(os.path.join(stage_check, fname))

            # For compressed files, splitting only gives us the LH/LZ extension, while '.arc' is considered part of the filename
            if ext in ('.LH', '.LZ'):
                ext = globals_.FileExtentions[0] + ext
                name = name.removesuffix('.arc')

            if ext in globals_.FileExtentions:
                globals_.FirstStageFilename = name + ext
                return True

    return False
