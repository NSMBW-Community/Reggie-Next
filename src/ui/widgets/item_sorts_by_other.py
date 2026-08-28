from typing import cast

from PyQt6 import QtWidgets


class ListWidgetItem_SortsByOther(QtWidgets.QListWidgetItem):
    """
    A ListWidgetItem that defers sorting to another object.
    """

    def __init__(self, reference, text=''):
        super().__init__(text)
        self.reference = reference

    def __lt__(self, other):
        other = cast(ListWidgetItem_SortsByOther, other)
        return self.reference < other.reference
