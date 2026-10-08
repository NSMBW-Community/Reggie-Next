from data.tileset.tile.tile_def import TileDef


class ObjectDef:
    """
    Class for the object definitions
    """

    def __init__(self) -> None:
        """
        Constructor
        """
        self.width = 0
        self.height = 0
        self.rows: list[list[TileDef]] = []

    def load(self, source: bytes, offset: int, tileoffset: int) -> None:
        """
        Load an object definition
        """
        i = offset
        row: list[TileDef] = []

        while True:
            cbyte = source[i]

            if cbyte == 0xFE:
                self.rows.append(row)
                i += 1
                row = []
            elif cbyte == 0xFF:
                break
            elif (cbyte & 0x80) != 0:
                row.append(TileDef(cbyte))
                i += 1
            else:
                extra = source[i + 2]
                tile = TileDef(cbyte, source[i + 1] | ((extra & 3) << 8), extra >> 2)
                row.append(tile)
                i += 3

        # Newer has this any-tileset-slot hack in place, so let's add it here
        for row in self.rows:
            for tile in row:
                if tile.is_slope_extra():
                    tile.repetition_type = (tile.repetition_type & 0xFF) + tileoffset
                elif tile.is_regular_tile() and tile.tilenum != 0:
                    tile.tilenum = (tile.tilenum & 0xFF) + tileoffset
