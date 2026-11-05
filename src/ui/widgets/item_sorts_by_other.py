from typing import cast

from PyQt6 import QtWidgets
from data.level.items.basic import LevelEditorItem


class ListWidgetItem_SortsByOther(QtWidgets.QListWidgetItem):
    """
    A ListWidgetItem that defers sorting to another object.
    """

    def __init__(self, reference: LevelEditorItem, text: str = '') -> None:
        super().__init__(text)
        self.reference = reference

    def __lt__(self, other: QtWidgets.QListWidgetItem) -> bool:
        other = cast(ListWidgetItem_SortsByOther, other)
        return self.reference < other.reference
