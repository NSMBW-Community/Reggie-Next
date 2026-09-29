class ToolbarAction:
    """Represents a menu action that can be assigned to the toolbar."""

    def __init__(self, id: str, name: str | None, active: bool = False):
        self.id = id
        self.name = name
        self.active = active
