class MenuAction:
    """Represents a menu action."""

    def __init__(self, id: str, text: str | None, active: bool = False):
        self.id = id
        self.text = text
        self.active = active
