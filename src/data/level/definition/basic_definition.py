from xml.etree.ElementTree import Element

from data import globals_
from data.common.list_property import ListPropertyModel
from data.editorfield.check_box import CheckBoxEditorField
from data.editorfield.dual_box import DualBoxEditorField
from data.editorfield.external import ExternalEditorField
from data.editorfield.list import ListEditorField
from data.editorfield.multi_dual_box import MultiDualBoxEditorField
from data.editorfield.editor_field import EditorField
from data.editorfield.value_list import ValueListEditorField
from data.editorfield.value import ValueEditorField


class BasicDefinition:
    """
    Base class for an item definition
    """

    def __init__(self) -> None:
        self.id: int = -1
        self.name: str | None = None
        self.notes: str | None = None
        self.noLayer: bool = False
        self.fields: list[EditorField] = []
        self.max_bit = -1

    def loadFrom(self, elem: Element) -> None:
        """
        Loads in all the field data from an XML node
        """
        fields = self.fields
        allowed = ['checkbox', 'list', 'value', 'dualbox', 'dependency', 'external', 'multidualbox', 'valuelist', 'layer']

        for field in elem:
            if field.tag not in allowed:
                continue

            attribs = field.attrib

            if field.tag == 'dualbox' or field.tag == 'multidualbox':
                title = attribs['title1'] + " / " + attribs['title2']
            elif 'title' in attribs:
                title = attribs['title']
            else:
                title = globals_.trans.string('dialog.sprite_data_editor.property_decoder.no_title')

            comment = comment2 = advancedcomment = required = idtype = None
            start = 0
            increment = 1

            if 'comment' in attribs:
                comment = globals_.trans.string('dialog.sprite_data_editor.comment', ('[name]', title), ('[note]', attribs['comment']))

            if 'comment2' in attribs:
                comment2 = globals_.trans.string('dialog.sprite_data_editor.comment', ('[name]', title), ('[note]', attribs['comment2']))

            if 'advancedcomment' in attribs:
                advancedcomment = globals_.trans.string('dialog.sprite_data_editor.comment', ('[name]', title), ('[note]', attribs['advancedcomment']))

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

            # NOTE: This must be the last member passed into a property field type
            if 'idtype' in attribs:
                idtype = attribs['idtype']

                if field.tag not in {'value', 'list'}:
                    raise ValueError("Only values and lists support idtypes.")

            # Parse the remaining type-specific attributes
            if field.tag == 'checkbox':
                bit, _ = self.parseBits(attribs.get("nybble"))
                mask = int(attribs.get('mask', 1))
                full_nybble = attribs.get('fullnybble', 'False') == "True"

                fields.append(CheckBoxEditorField(attribs['title'], comment, comment2, advancedcomment, required, bit, mask, full_nybble))

            elif field.tag == 'list':
                bit, _ = self.parseBits(attribs.get("nybble"))

                entries = []
                for entry in field:
                    if entry.tag != 'entry':
                        continue

                    entries.append((int(entry.attrib['value']), entry.text))

                model = ListPropertyModel(entries)
                fields.append(ListEditorField(title, comment, comment2, advancedcomment, required, bit, model, idtype))

            elif field.tag == 'value':
                bit, max_ = self.parseBits(attribs.get("nybble"))

                if 'start' in attribs:
                    start = int(attribs['start'])
    
                if 'increment' in attribs:
                    increment = int(attribs['increment'])

                overrides = []
                for override in field:
                    if override.tag != 'override':
                        continue

                    overrides.append((int(override.attrib['index']), int(override.attrib['value'])))

                fields.append(ValueEditorField(attribs['title'], comment, comment2, advancedcomment, required, bit, max_, start, increment, overrides, idtype))

            elif field.tag == 'dualbox':
                bit, _ = self.parseBits(attribs.get("nybble"))
                fullNybble = attribs.get('fullnybble', 'False') == "True"

                fields.append(DualBoxEditorField(attribs['title1'], comment, comment2, advancedcomment, required, bit, attribs['title2'], fullNybble))

            elif field.tag == 'external':
                # Uses a list from an external resource. This is used for big
                # lists like actors, sound effects etc.
                bit, _ = self.parseBits(attribs.get("nybble"))
                type_ = attribs['type']

                fields.append(ExternalEditorField(title, comment, comment2, advancedcomment, required, bit, type_))

            elif field.tag == 'multidualbox':
                bit, _ = self.parseBits(attribs.get("nybble"))

                fields.append(MultiDualBoxEditorField(attribs['title1'], comment, comment2, advancedcomment, required, bit, attribs['title2']))

            elif field.tag == 'valuelist':
                bit, max_ = self.parseBits(attribs.get("nybble"))
                entries = []

                for entry in field:
                    if entry.tag != 'entry':
                        continue

                    entries.append((int(entry.attrib['value']), entry.text))

                model = ListPropertyModel(entries)
                fields.append(ValueListEditorField(title, comment, comment2, advancedcomment, required, bit, model, max_))

            # Override name/comment for the default layer field
            elif field.tag == 'layer':
                self.layer_title = title
                self.layer_comment = comment

    def parseBits(self, nybble_val: str | None) -> tuple[list[tuple[int, int]], int]:
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
            if not 1 <= a < b + 1 <= self.max_bit:
                raise ValueError("Indexed bits out of bounds: " + str(range_) + "->" + str((a, b + 1)))

            bit_length += b - a + 1
            bit_ranges.append((a, b + 1))

        return bit_ranges, 1 << bit_length
