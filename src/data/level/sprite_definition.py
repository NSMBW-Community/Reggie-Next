import globals_
from classlib import (
    CheckBoxSpriteField,
    DualBoxSpriteField,
    ExternalSpriteField,
    ListSpriteField,
    MultiDualBoxSpriteField,
    SpriteField,
    SpriteTexSpriteField,
    ValueSpriteField,
)
from src.data.model.list_property import ListPropertyModel


class SpriteDefinition:
    """
    Stores and manages the data info for a specific sprite
    """

    def __init__(self):
        self.id: int = -1
        self.name: str | None = None
        self.notes: str | None = None
        self.advNotes: str | None = None
        self.relatedObjFiles: str | None = None
        self.yoshiNotes: str | None = None
        self.noyoshi: bool = False
        self.asm: bool = False
        self.size: bool = False
        self.noLayer: bool = False
        self.dependencies: list[tuple[int, int]] = []
        self.dependencynotes: str | None = None
        self.fields: list[SpriteField] = []


    def loadFrom(self, elem):
        """
        Loads in all the field data from an XML node
        """
        fields = self.fields
        allowed = ['checkbox', 'list', 'value', 'dualbox', 'dependency', 'external', 'multidualbox', 'spritetex']

        for field in elem:
            if field.tag not in allowed:
                continue

            attribs = field.attrib

            if field.tag == 'dualbox':
                title = attribs['title1'] + " / " + attribs['title2']
            elif field.tag == 'multidualbox':
                title = attribs['title1'] + " / " + attribs['title2']
            elif 'title' in attribs:
                title = attribs['title']
            else:
                title = globals_.trans.string('SpriteDataEditor', 28)

            advanced = attribs.get("advanced", "False") == "True"
            comment = comment2 = advancedcomment = required = idtype = None
            start = 0
            increment = 1

            if 'comment' in attribs:
                comment = globals_.trans.string('SpriteDataEditor', 1, '[name]', title, '[note]', attribs['comment'])

            if 'comment2' in attribs:
                comment2 = globals_.trans.string('SpriteDataEditor', 1, '[name]', title, '[note]', attribs['comment2'])

            if 'advancedcomment' in attribs:
                advancedcomment = globals_.trans.string('SpriteDataEditor', 1, '[name]', title, '[note]', attribs['advancedcomment'])

            if 'requirednybble' in attribs:
                bit_ranges, _ = self.parseBits(attribs.get("requirednybble"))
                required = []

                if 'requiredval' in attribs:
                    vals = attribs['requiredval'].split(",")

                    if len(bit_ranges) != len(vals):
                        raise ValueError("Required bits and vals have different lengths.")
                else:
                    vals = [None] * len(bit_ranges)

                # The associated values are a comma-separated list of values or
                # (inclusive) ranges.
                for bit_range, sval in zip(bit_ranges, vals):
                    if sval is None:
                        a = 1
                        b = (1 << (bit_range[1] - bit_range[0] + 1)) - 1
                    elif '-' not in sval:
                        a = b = int(sval)
                    else:
                        a, b = map(int, sval.split('-'))

                    required.append(((bit_range,), (a, b + 1)))

            # NOTE: idtype must be the LAST field passed to a sprite
            if 'idtype' in attribs:
                idtype = attribs['idtype']

                if field.tag not in {'value', 'list'}:
                    raise ValueError("Only values and lists support idtypes.")

            if 'start' in attribs:
                start = int(attribs['start'])

                if field.tag != 'value':
                    raise ValueError("Only values support a start index.")

            if 'increment' in attribs:
                increment = int(attribs['increment'])

                if field.tag != 'value':
                    raise ValueError("Only values support an increment.")

            # Parse the remaining type-specific attributes.
            # TODO: Make proper field classes in classlib.py instead of using tuples and relying on index 0 for the field type.
            if field.tag == 'checkbox':
                bit, _ = self.parseBits(attribs.get("nybble"))
                mask = int(attribs.get('mask', 1))
                fullNybble = attribs.get('fullnybble', 'False') == "True"

                fields.append(CheckBoxSpriteField(attribs['title'], comment, comment2, advancedcomment, required, bit, mask, fullNybble))

            elif field.tag == 'list':
                bit, _ = self.parseBits(attribs.get("nybble"))

                entries = []
                for e in field:
                    if e.tag != 'entry': continue

                    entries.append((int(e.attrib['value']), e.text))

                model = ListPropertyModel(entries)
                fields.append(ListSpriteField(title, comment, comment2, advancedcomment, required, bit, model, idtype))

            elif field.tag == 'value':
                bit, max_ = self.parseBits(attribs.get("nybble"))

                overrides = []
                for o in field:
                    if o.tag != 'override': continue

                    overrides.append((int(o.attrib['index']), int(o.attrib['value'])))

                fields.append(ValueSpriteField(attribs['title'], comment, comment2, advancedcomment, required, bit, max_, start, increment, overrides, idtype))

            elif field.tag == 'dualbox':
                bit, _ = self.parseBits(attribs.get("nybble"))
                fullNybble = attribs.get('fullnybble', 'False') == "True"

                fields.append(DualBoxSpriteField(attribs['title1'], comment, comment2, advancedcomment, required, bit, attribs['title2'], fullNybble))

            elif field.tag == 'dependency':
                type_dict = {'required': 0, 'suggested': 1, 'resource': 2, 'suggestedresource': 3}

                for entry in field:
                    if entry.attrib['sprite'] == "":
                        continue

                    self.dependencies.append((int(entry.attrib['sprite']), type_dict[entry.tag]))

                self.dependencynotes = attribs.get('notes')

            elif field.tag == 'external':
                # Uses a list from an external resource. This is used for big
                # lists like actors, sound effects etc.
                bit, _ = self.parseBits(attribs.get("nybble"))
                type_ = attribs['type']

                fields.append(ExternalSpriteField(title, comment, comment2, advancedcomment, required, bit, type_))

            elif field.tag == 'multidualbox':
                # multibox but with dualboxes instead of checkboxes
                bit, _ = self.parseBits(attribs.get("nybble"))

                fields.append(MultiDualBoxSpriteField(attribs['title1'], comment, comment2, advancedcomment, required, bit, attribs['title2']))

            elif field.tag == 'spritetex':
                bit, max_ = self.parseBits(attribs.get("nybble"))

                entries = []
                for e in field:
                    if e.tag != 'entry': continue

                    entries.append((int(e.attrib['value']), e.text))

                model = ListPropertyModel(entries)
                fields.append(SpriteTexSpriteField(title, comment, comment2, advancedcomment, required, bit, model, max_))

    def parseBits(self, nybble_val) -> tuple[list[tuple[int, int]], int]:
        """
        Parses a description of the bits a setting affects into a tuple of a
        list of ranges and the number of possible values. Ranges include the
        start and exclude the end. The most significant bit is considered 1.
        Precise bits can be specified by adding a period after the number,
        followed by a number from 1 to 4, where 1 is the most significant bit in
        a nybble, and 4 the least significant bit.

        Raises a ValueError if 'nybble_val' is None or if any of the specified
        ranges refer to bits that are not in the first 8 bytes.
        """
        if nybble_val is None:
            raise ValueError("No nybble specification given.")

        # The total number of bits that can be controlled.
        bit_length = 0
        # A list of tuples (start_bit, end_bit) that represent inclusive ranges.
        bit_ranges: list[tuple[int, int]] = []

        for range_ in nybble_val.split(","):
            if "-" in range_:
                # Multiple nybbles
                a, b = range_.split("-")
            else:
                # Just a nybble
                a = b = range_

            if "." in a:
                nybble, bits = map(int, a.split("."))
            else:
                nybble, bits = int(a), 1

            a = 4 * (nybble - 1) + bits

            if "." in b:
                nybble, bits = map(int, b.split("."))
            else:
                nybble, bits = int(b), 4

            b = 4 * (nybble - 1) + bits

            # Check if the resulting range would be valid.
            if not 1 <= a < b + 1 <= 65:
                raise ValueError("Indexed bits out of bounds: " + str(range_) + "->" + str((a, b + 1)))

            bit_length += b - a + 1
            bit_ranges.append((a, b + 1))

        return bit_ranges, 1 << bit_length
