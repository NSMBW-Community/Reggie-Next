from typing import Literal

class SpriteIDType:
    """
    Representation of a Sprite ID-Type
    """

    def __init__(self, id_type: str, name: str, data_type: Literal['value', 'text']) -> None:
        self.id_type = id_type
        self.name = name
        self.data_type = data_type
