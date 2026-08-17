from src.data.model.spritefield.sprite_field import SpriteField


class ValueSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        max: int,
        start: int,
        increment: int,
        overrides: list[tuple[int, int]],
        idtype: str | None,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.max = max
        self.start = start
        self.increment = increment
        self.overrides = overrides
        self.idtype = idtype
