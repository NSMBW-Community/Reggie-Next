from typing import cast

from PyQt6 import QtWidgets


class CustomSortableListWidgetItem(QtWidgets.QListWidgetItem):
    """
    ListWidgetItem subclass that allows sorting by arbitrary key
    """
    sort_key = 0

    def __lt__(self, other):
        if hasattr(self, 'sort_key') and hasattr(other, 'sort_key'):
            other = cast(CustomSortableListWidgetItem, other)
            return self.sort_key < other.sort_key

        return False
