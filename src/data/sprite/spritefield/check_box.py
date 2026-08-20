from src.data.sprite.spritefield.sprite_field import SpriteField


class CheckBoxSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        mask: int,
        full_nybble: bool,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.mask = mask
        self.full_nybble = full_nybble
