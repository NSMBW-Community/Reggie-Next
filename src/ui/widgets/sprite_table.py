
from PyQt6 import QtCore, QtWidgets
from src.data.level.items.sprite import SpriteItem

class SpriteTableWidget(QtWidgets.QTableWidget):
    """
    Simple wrapper for QTableWidget that can select
    """
    def keyPressEvent(self, e):
        if e is not None:
            if e.key() == QtCore.Qt.Key.Key_Space or e.key() == QtCore.Qt.Key.Key_Return:
                SpriteItem.moveToSprite(self.currentItem())

        super().keyPressEvent(e)
