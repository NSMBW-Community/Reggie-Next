from PyQt6 import QtGui, QtWidgets, QtCore

import globals_

class KeybindLineEdit(QtWidgets.QKeySequenceEdit):
    """
    A wrapper for QtWidgets.QKeySequenceEdit
    """
    def __init__(self, keySequence: QtGui.QKeySequence | None, name: str):
        QtWidgets.QKeySequenceEdit.__init__(self, keySequence)
        self.name = name

        # Only record one sequence input
        self.setMaximumSequenceLength(1)

        self.setClearButtonEnabled(True)

        # Set placeholder text on the QLineEdit
        lineEdit = self.findChild(QtWidgets.QLineEdit, "qt_keysequenceedit_lineedit")
        if lineEdit is not None:
            lineEdit.setPlaceholderText(globals_.trans.string('PrefsDlg', 60)) # No keybind set

    def keyPressEvent(self, a0: QtGui.QKeyEvent | None):
        """
        Clears the current keybind if Delete or Backspace is pressed
        """
        super().keyPressEvent(a0)
        if a0 is not None:
            if a0.key() in (QtCore.Qt.Key.Key_Delete, QtCore.Qt.Key.Key_Backspace):
                self.clear()
