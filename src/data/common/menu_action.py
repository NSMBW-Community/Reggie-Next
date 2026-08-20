class MenuAction:
    """Represents a menu action."""

    def __init__(self, id: str, name: str | None, active: bool = False):
        self.id = id
        self.name = name
        self.active = active
