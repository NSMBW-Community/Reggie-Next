
from PyQt6 import QtCore, QtGui, QtWidgets

from data.level.items.sprite import SpriteItem


class SpriteTableWidget(QtWidgets.QTableWidget):
    """
    Simple wrapper for QTableWidget that can select
    """
    def keyPressEvent(self, e: QtGui.QKeyEvent | None) -> None:
        if e is not None and (e.key() == QtCore.Qt.Key.Key_Space or e.key() == QtCore.Qt.Key.Key_Return):
            SpriteItem.moveToSprite(self.currentItem())

        super().keyPressEvent(e)
