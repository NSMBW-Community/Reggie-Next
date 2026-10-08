class TileDef:
    def __init__(
        self, repetition_type: int, tilenum: int = -1, extra_behaviour: int = -1
    ) -> None:
        self.repetition_type: int = repetition_type
        self.tilenum: int = tilenum
        self.extra_behaviour: int = extra_behaviour

    def is_slope_extra(self) -> bool:
        return (
            (self.repetition_type & 0x80) != 0
            and self.tilenum == -1
            and self.extra_behaviour == -1
        )

    def is_regular_tile(self) -> bool:
        return self.tilenum != -1 and self.extra_behaviour != -1
