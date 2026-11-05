import os
from xml.etree import ElementTree

from PyQt6 import QtCore, QtWidgets

from data import globals_
from data.sprite.spritefield.external import ExternalSpriteField
from ui.dialogs.spriteeditor.external_database import (
    ExternalDatabaseDialog,
)
from ui.widgets.spriteeditor.propertydecoders.property_decoder import (
    PropertyDecoder,
)


class ExternalPropertyDecoder(PropertyDecoder[ExternalSpriteField]):
    """
    Class that decodes/encodes sprite data to/from an external database (valuebox + button)
    """

    def __init__(self, field, layout, row, parent_widget):
        """
        Creates the widget
        """
        super().__init__(field, layout, row, parent_widget)

        assert self.field.bit is not None and len(self.field.bit) == 1

        self.disp_value = 0
        bits = self.field.bit[0][1] - self.field.bit[0][0]

        # Button that opens the database window
        self.button = QtWidgets.QPushButton()
        self.button.clicked.connect(self.button_clicked)

        # Spinbox that contains the current value
        self.box = QtWidgets.QSpinBox()
        self.box.setRange(0, (2 ** bits) - 1)
        self.box.setValue(self.disp_value)
        self.box.valueChanged.connect(self.value_changed)

        label = QtWidgets.QLabel(self.field.title + ":")

        self.layout.addWidget(label, self.row, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.button, self.row, 1)
        self.layout.addWidget(self.box, self.row, 2)

        self.init_comment_buttons()

    def update(self, data, first=False):
        """
        Updates the info
        """
        # check if requirements are met
        self.checkReq(data, first)

        self.disp_value = self.retrieve(data)
        self.button.setText(self.get_entry_name(self.disp_value))
        self.box.setValue(self.disp_value)

    def assign(self, data):
        """
        Assigns the currently selected value to data
        """
        return self.insertvalue(data, self.disp_value)

    def button_clicked(self) -> None:
        """
        Handles the button being clicked.
        """
        dlg = ExternalDatabaseDialog(self.field.type, self.disp_value)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        # Read set value from the dialog and update
        self.disp_value = dlg.get_value()
        self.button.setText(self.get_entry_name(self.disp_value))
        self.box.setValue(self.disp_value)

        # update all other fields
        self.updateData.emit(self)

    def value_changed(self, value: int) -> None:
        """
        Handles the spin value being changed
        """
        self.disp_value = value
        self.button.setText(self.get_entry_name(self.disp_value))

        # update all other fields
        self.updateData.emit(self)

    def get_entry_name(self, value: int) -> str:
        """
        Gets the name for the entry
        """
        value = int(value)
        text = str(globals_.trans.string('SpriteDataEditor', 36))

        # Find the correct XML
        filename = globals_.gamedef.externalFile(f'{self.field.type}.xml')
        if not os.path.isfile(filename):
            return text

        root = ElementTree.parse(filename).getroot()

        target_column = 0
        if 'name_column' in root.attrib:
            target_column = int(root.attrib['name_column'])

        # Search for the text of the "Name" column for this entry ID
        for node in root:
            if node.tag.lower() != 'entry':
                continue

            entry_id = int(node.attrib['id'])
            if entry_id != value:
                continue

            for prop in node:
                if prop.tag.lower() != 'column':
                    continue

                column_id = int(prop.attrib['id'])
                if column_id == target_column:
                    text = prop.attrib['text']

        # Do some automatic replacements
        replace = {
            '[b]': '<b>',
            '[/b]': '</b>',
            '[i]': '<i>',
            '[/i]': '</i>',
        }

        for old, new in replace.items():
            text = text.replace(old, new)

        # Limit the name to 60 characters
        if len(text) > 60:
            text = text[:57] + '...'

        return text
