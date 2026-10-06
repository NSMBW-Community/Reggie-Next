from PyQt6 import QtCore, QtGui, QtWidgets

from data.stamp.stamp import Stamp


class StampListModel(QtCore.QAbstractListModel):
    """
    Model containing all the stamps
    """

    def __init__(self) -> None:
        """
        Initializes the model
        """
        QtCore.QAbstractListModel.__init__(self)

        self.items: list[Stamp] = []

    def rowCount(self, parent: QtCore.QModelIndex | None = None) -> int:
        """
        Required by Qt
        """
        return len(self.items)

    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole) -> QtGui.QPixmap | str | None:
        """
        Get what we have for a specific row
        """
        if not index.isValid(): return None
        n = index.row()
        if n < 0: return None
        if n >= len(self.items): return None

        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            return self.items[n].Icon

        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            return QtWidgets.QApplication.instance().palette().base()

        elif role == QtCore.Qt.ItemDataRole.UserRole or role == QtCore.Qt.ItemDataRole.StatusTipRole:
            return self.items[n].Name

        else:
            return None

    def setData(self, index: QtCore.QModelIndex, value: str, role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole) -> None:
        """
        Set data for a specific row
        """
        if not index.isValid(): return
        n = index.row()
        if n < 0: return
        if n >= len(self.items): return

        if role == QtCore.Qt.ItemDataRole.UserRole:
            self.items[n].Name = value

    def addStamp(self, stamp: Stamp) -> None:
        """
        Adds a stamp
        """

        # Start resetting
        self.beginResetModel()

        # Add the stamp to self.items
        self.items.append(stamp)

        # Finish resetting
        self.endResetModel()

    def removeStamp(self, stamp: Stamp) -> None:
        """
        Removes a stamp
        """

        # Start resetting
        self.beginResetModel()

        # Remove the stamp from self.items
        self.items.remove(stamp)

        # Finish resetting
        self.endResetModel()
