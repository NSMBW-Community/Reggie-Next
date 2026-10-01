import os

from PyQt6 import QtWidgets

from data import globals_
from data.common.utils import get_reggiedata_folder


def checkContent(data: bytes) -> bool:
    if not data.startswith(b'U\xAA8-'):
        return False

    required = (b'course\0', b'course1.bin\0', b'\0\0\0\x80')
    for r in required:
        if r not in data:
            return False

    return True


def IsNSMBLevel(filename: str) -> bool:
    """
    Does some basic checks to confirm a file is a NSMB level
    """
    if not os.path.isfile(filename): return False

    with open(filename, 'rb') as f:
        data = f.read()

    if (data[0] & 0xF0) == 0x40 or not data.startswith(b"U\xAA8-"):  # If LH-compressed or LZ-compressed
        return True

    return checkContent(data)


def FilesAreMissing() -> bool:
    """
    Checks to see if any of the required files for Reggie are missing
    """

    if not os.path.isdir(get_reggiedata_folder()):
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingFiles', 0), globals_.trans.string('Err_MissingFiles', 1))
        return True

    required = ['icon.png', ]

    missing = []

    for check in required:
        if not os.path.isfile(os.path.join(get_reggiedata_folder(), check)):
            missing.append(check)

    if missing:
        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_MissingFiles', 0),
                                      globals_.trans.string('Err_MissingFiles', 2, '[files]', ', '.join(missing)))
        return True

    return False


def areValidGamePaths(stage_check: str = 'ug', texture_check: str = 'ug') -> bool:
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
