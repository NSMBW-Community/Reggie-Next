class BackgroundFileEntry:
    """
    Object representation of a background in the list
    """

    def __init__(self, id: str, name: str, image: str) -> None:
        self.bg_id = id
        self.name = name
        self.image = image
