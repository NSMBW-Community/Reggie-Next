from PyQt6 import QtWidgets

from collections.abc import Callable

class DiagnosticListWidgetItem(QtWidgets.QListWidgetItem):
    """
    Simple wrapper for QListWidgetItem that includes the fix function
    """
    fix: Callable[[str], bool | None]
