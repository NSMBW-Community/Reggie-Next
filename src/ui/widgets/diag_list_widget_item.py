from collections.abc import Callable

from PyQt6 import QtWidgets


class DiagnosticListWidgetItem(QtWidgets.QListWidgetItem):
    """
    Simple wrapper for QListWidgetItem that includes the fix function
    """
    fix: Callable[[str], bool | None]
