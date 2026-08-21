class ObjectDef:
    """
    Class for the object definitions
    """

    def __init__(self):
        """
        Constructor
        """
        self.width = 0
        self.height = 0
        self.rows = []

    def load(self, source, offset, tileoffset):
        """
        Load an object definition
        """
        i = offset
        row = []

        while True:
            cbyte = source[i]

            if cbyte == 0xFE:
                self.rows.append(row)
                i += 1
                row = []
            elif cbyte == 0xFF:
                break
            elif (cbyte & 0x80) != 0:
                row.append([cbyte, ])
                i += 1
            else:
                extra = source[i + 2]
                tile = [cbyte, source[i + 1] | ((extra & 3) << 8), extra >> 2]
                row.append(tile)
                i += 3

        # Newer has this any-tileset-slot hack in place, so let's add it here
        for row in self.rows:
            for tile in row:
                if len(tile) == 1 and tile[0] != 0:
                    tile[0] = (tile[0] & 0xFF) + tileoffset
                elif len(tile) == 3 and tile[1] != 0:
                    tile[1] = (tile[1] & 0xFF) + tileoffset
