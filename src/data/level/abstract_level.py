from src.data.level.area import Area


class AbstractLevel:
    """
    Class for an abstract level from any game. Defines the API.
    """

    def __init__(self):
        """
        Initializes the level with default settings
        """
        self.filepath: str | None = None
        self.name: str = 'untitled'

        self.areas: list[Area] = []

    def load(self, data: bytes, areaNum: int):
        """
        Loads a level from bytes data. You MUST reimplement this in subclasses!
        """

    def save(self):
        """
        Returns the level as a bytes object. You MUST reimplement this in subclasses!
        """
        return b''

    def deleteArea(self, number: int):
        """
        Removes the area specified. Number is a 1-based value, not 0-based;
        so you would pass a 1 if you wanted to delete the first area.
        """
        del self.areas[number - 1]

        # change all later areas to use the correct num
        for i, area in enumerate(self.areas, 1):
            area.set_num(i)

        return True

    def changeArea(self, number: int):
        """
        Changes the current area to the specified area in the loaded level
        archive. Note that number is 1-based, not 0-based.
        """
        return False
