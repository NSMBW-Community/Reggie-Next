class TilesetFileEntry:
    """Object representation of a tileset file entry in the tileset picker."""

    def __init__(self, filename: str, name: str) -> None:
        self.filename = filename
        self.name = name


class TilesetCategory:
    """Object representation of a tileset category in the tileset picker."""

    def __init__(self, name: str = "root") -> None:
        self.name = name
        self.children: list[TilesetCategory | TilesetFileEntry] = []
        self.sorted: bool = False
