class ZoneThemeEntry:
    """
    Object representation of a Zone Theme in the list
    """

    def __init__(self, id: str, name: str, desc: str | None) -> None:
        self.idx = id
        self.name = name
        self.desc = desc
