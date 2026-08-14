from PyQt6 import QtWidgets

class ToolbarCheckBox(QtWidgets.QCheckBox):
    """
    Simple wrapper for QCheckBox with an internal name identifier
    """
    internal_name: str
