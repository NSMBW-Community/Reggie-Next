from xml.etree.ElementTree import Element
from data.level.definition.basic_definition import BasicDefinition


class SpriteDefinition(BasicDefinition):
    """
    Stores and manages the data info for a specific sprite
    """

    def __init__(self) -> None:
        super().__init__()
        self.advNotes: str | None = None
        self.relatedObjFiles: str | None = None
        self.yoshiNotes: str | None = None
        self.noyoshi: bool = False
        self.asm: bool = False
        self.size: bool = False
        self.dependencies: list[tuple[int, int]] = []
        self.dependencynotes: str | None = None
        self.max_bit = 81

    def loadFrom(self, elem: Element) -> None:
        """
        Loads in all the field data from an XML node
        """
        super().loadFrom(elem)
        allowed = ['dependency']

        for field in elem:
            if field.tag not in allowed:
                continue

            attribs = field.attrib

            if field.tag == 'dependency':
                type_dict = {'required': 0, 'suggested': 1, 'resource': 2, 'suggestedresource': 3}

                for entry in field:
                    if entry.attrib['sprite'] == "":
                        continue

                    sprite_ids = str(entry.attrib['sprite']).split(',')

                    for id in sprite_ids:
                        self.dependencies.append((int(id), type_dict[entry.tag]))

                self.dependencynotes = attribs.get('notes')
