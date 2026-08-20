class SpriteField:
    """Base class for all sprite editor fields."""

    def __init__(
        self,
        title: str | None = None,
        comment: str | None = None,
        comment2: str | None = None,
        advanced_comment: str | None = None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None = None,
        bit: list[tuple[int, int]] | None = None,
    ):
        self.title = title if title is not None else ""
        self.comment = comment
        self.comment2 = comment2
        self.advanced_comment = advanced_comment
        self.required = required
        self.bit = bit
