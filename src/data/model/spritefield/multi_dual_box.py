from src.data.model.spritefield.sprite_field import SpriteField


class MultiDualBoxSpriteField(SpriteField):
    def __init__(
        self,
        title: str | None,
        comment: str | None,
        comment2: str | None,
        advanced_comment: str | None,
        required: list[tuple[list[tuple[int, int]], tuple[int, int]]] | None,
        bit: list[tuple[int, int]] | None,
        title2: str | None,
    ):
        super().__init__(title, comment, comment2, advanced_comment, required, bit)
        self.title2 = title2
