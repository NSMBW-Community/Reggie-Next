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
