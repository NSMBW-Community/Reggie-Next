from PyQt6 import QtCore, QtWidgets


class MenuAction:
    """Represents a menu action."""

    def __init__(self, id: str, text: str | None, active: bool = False):
        self.id = id
        self.text = text
        self.active = active


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


class TilesetFileEntry:
    """Object representation of a tileset file entry in the tileset picker."""

    def __init__(self, filename: str, name: str):
        self.filename = filename
        self.name = name


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


class SpriteField:
    """Base class for all sprite editor fields."""

    def __init__(
        self,
        title: str | None = None,
        comment: str | None = None,
        comment2: str | None = None,
        advanced_comment: str | None = None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None = None,
        bit: list[tuple[int, int]] | None = None,
    ):
        self.title = title if title is not None else ""
        self.comment = comment
        self.comment2 = comment2
        self.advanced_comment = advanced_comment
        self.required = required
        self.bit = bit


class CheckBoxSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        mask: int,
        full_nybble: bool,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.mask = mask
        self.full_nybble = full_nybble


class ListSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        model: QtCore.QAbstractItemModel,
        idtype: str | None,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.model = model
        self.idtype = idtype


class ValueSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        max: int,
        start: int,
        increment: int,
        overrides: list[tuple[int, int]],
        idtype: str | None,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.max = max
        self.start = start
        self.increment = increment
        self.overrides = overrides
        self.idtype = idtype


class BitFieldSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        start_bit: int,
        bit_num: int,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, [])
        self.start_bit = start_bit
        self.bit_num = bit_num


class MultiBoxSpriteField(SpriteField):
    pass


class DualBoxSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        title2: str | None,
        full_nybble: bool,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.title2 = title2
        self.full_nybble = full_nybble


class ExternalSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        type: str | None,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.type = type or ""


class MultiDualBoxSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        title2: str | None,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.title2 = title2


class SpriteTexSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        model: QtCore.QAbstractItemModel,
        max: int,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.model = model
        self.max = max
