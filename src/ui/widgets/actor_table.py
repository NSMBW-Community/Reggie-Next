
from PyQt6 import QtCore, QtWidgets
from data.level.items.actor import ActorItem

class ActorTableWidget(QtWidgets.QTableWidget):
    """
    Simple wrapper for QTableWidget that can select actors in the level
    """
    def keyPressEvent(self, e):
        if e is not None:
            if e.key() == QtCore.Qt.Key.Key_Space or e.key() == QtCore.Qt.Key.Key_Return:
                ActorItem.moveToActor(self.currentItem())

        super().keyPressEvent(e)
