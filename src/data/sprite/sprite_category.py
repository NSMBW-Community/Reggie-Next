from PyQt6 import QtWidgets


class SpriteSubCategory:
    """Object representation of a sprite subcategory."""

    def __init__(self, name: str | None, sprite_ids: list[int]):
        self.name = name
        self.sprite_ids = sprite_ids


class SpriteCategory:
    """Object representation of a top-level sprite category."""

    def __init__(
        self,
        name: str | None,
        sub_categories: list[SpriteSubCategory],
        nodes: list[QtWidgets.QTreeWidgetItem],
    ):
        self.name = name
        self.sub_categories = sub_categories
        self.nodes = nodes
