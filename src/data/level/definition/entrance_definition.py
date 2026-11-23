from xml.etree.ElementTree import Element
from data.level.definition.basic_definition import BasicDefinition


class EntranceDefinition(BasicDefinition):
    """
    Stores and manages the data info for a specific entrance
    """

    def __init__(self) -> None:
        super().__init__()
        self.max_bit = 129
