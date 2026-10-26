class ExternalNote:
    """
    Object representation of a notes box in the External Sprite Databases
    """

    def __init__(self, entry_id: int, column_id: int, text: str) -> None:
        self.entry_id = entry_id
        self.column_id = column_id
        self.text = text
