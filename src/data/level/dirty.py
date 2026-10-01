from data import globals_
from PyQt6 import QtWidgets


def SetDirty(noautosave=False):
    if globals_.DirtyOverride > 0:
        return

    if not noautosave:
        globals_.AutoSaveDirty = True
    if globals_.Dirty:
        return

    globals_.Dirty = True
    try:
        if globals_.mainWindow is not None:
            globals_.mainWindow.UpdateTitle()
    except Exception:
        pass

def CheckDirty():
    """
    Checks if the level is unsaved and attempts to save it if so.
    Returns whether the level still contains unsaved changes.
    """
    if not globals_.Dirty:
        return False
    if globals_.mainWindow is None:
        return

    msg = QtWidgets.QMessageBox()
    msg.setText(globals_.trans.string('AutoSaveDlg', 2))
    msg.setInformativeText(globals_.trans.string('AutoSaveDlg', 3))
    msg.setStandardButtons(
        QtWidgets.QMessageBox.StandardButton.Save | QtWidgets.QMessageBox.StandardButton.Discard | QtWidgets.QMessageBox.StandardButton.Cancel)
    msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Save)
    ret = msg.exec()

    if ret == QtWidgets.QMessageBox.StandardButton.Save:
        # If the save failed, the file is still dirty, so we need to negate
        # the return value.
        return not globals_.mainWindow.HandleSave()

    elif ret == QtWidgets.QMessageBox.StandardButton.Cancel:
        return True

    return False
