from PyQt6 import QtWidgets


class MenuAction:
    """Represents a menu action with an id, text, and active state."""
    def __init__(self, id: str, text: str | None, active: bool = False):
        self.id = id
        self.text = text
        self.active = active

class SpriteSubCategory:
    """Object representation of a sprite subcategory."""
    def __init__(self, name: str | None, spriteIds: list[int]):
        self.name = name
        self.spriteIds = spriteIds

class SpriteCategory:
    """Object representation of a top-level sprite category."""
    def __init__(self, categoryName: str | None, subCategories: list[SpriteSubCategory], nodes: list[QtWidgets.QTreeWidgetItem]):
        self.name = categoryName
        self.subCategories = subCategories
        self.nodes = nodes
