from PyQt6 import QtCore, QtWidgets


class StampListModel(QtCore.QAbstractListModel):
    """
    Model containing all the stamps
    """

    def __init__(self):
        """
        Initializes the model
        """
        QtCore.QAbstractListModel.__init__(self)

        self.items = []  # list of Stamp objects

    def rowCount(self, parent=None):
        """
        Required by Qt
        """
        return len(self.items)

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
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

    def setData(self, index, value, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """
        Set data for a specific row
        """
        if not index.isValid(): return
        n = index.row()
        if n < 0: return
        if n >= len(self.items): return

        if role == QtCore.Qt.ItemDataRole.UserRole:
            self.items[n].Name = value

    def addStamp(self, stamp):
        """
        Adds a stamp
        """

        # Start resetting
        self.beginResetModel()

        # Add the stamp to self.items
        self.items.append(stamp)

        # Finish resetting
        self.endResetModel()

    def removeStamp(self, stamp):
        """
        Removes a stamp
        """

        # Start resetting
        self.beginResetModel()

        # Remove the stamp from self.items
        self.items.remove(stamp)

        # Finish resetting
        self.endResetModel()
