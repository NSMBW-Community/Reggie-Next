from PyQt6 import QtCore

class StaticStringListModel(QtCore.QStringListModel):
    """
    Unselectable, uneditable string list model
    """

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        return QtCore.Qt.ItemFlag.ItemNeverHasChildren
