from PyQt6 import QtWidgets


class MenuAction:
    """Represents a menu action."""

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

    def __init__(
        self,
        categoryName: str | None,
        subCategories: list[SpriteSubCategory],
        nodes: list[QtWidgets.QTreeWidgetItem],
    ):
        self.name = categoryName
        self.subCategories = subCategories
        self.nodes = nodes


class TilesetFileEntry:
    """Object representation of a tileset file entry in the tileset picker."""

    def __init__(self, filename: str, name: str):
        self.filename = filename
        self.displayName = name


class TilesetCategory:
    """Object representation of a tileset category in the tileset picker."""

    def __init__(self, name="root"):
        self.name = name
        self.children: list[TilesetCategory | TilesetFileEntry] = []
        self.sorted = False


class RandTileSelection:
    """Object representation of a tile group selection with randomisation.

    :param tiles: List of tile IDs to select from.
    :param direction: Direction of randomisation (0b00 = none, 0b01 = horizontal, 0b10 = vertical, 0b11 = both).
    :param special: Special tile type (0b00 = none, 0b01 = double-top, 0b10 = double-bottom).
    """

    def __init__(self, tiles: list[int], direction: int, special: int):
        # lower 4 bits represent x, upper 4 bits represent y
        self.tiles: list[int] = tiles
        self.direction = direction
        self.special = special
