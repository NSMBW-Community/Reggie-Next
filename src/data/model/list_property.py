from PyQt6 import QtCore


class ListPropertyModel(QtCore.QAbstractListModel):
    """
    Contains all the possible values for a list property on a sprite
    """

    def __init__(self, entries, hideVal=False):
        """
        Constructor
        """
        QtCore.QAbstractListModel.__init__(self)
        self.entries = entries
        self.hideVal = hideVal

    def rowCount(self, parent=None):
        """
        Required by Qt
        """
        return len(self.entries)

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """
        Get what we have for a specific row
        """
        if not index.isValid() or role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        n = index.row()
        if not 0 <= n < len(self.entries):
            return None

        if self.hideVal:
            return '%s' % self.entries[n][1]
        else:
            return '%d: %s' % self.entries[n]
