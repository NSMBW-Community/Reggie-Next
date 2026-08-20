import os
from xml.etree import ElementTree

from PyQt6 import QtCore, QtWidgets

import globals_
from src.data.sprite.spritefield.external import ExternalSpriteField
from src.ui.dialogs.spriteeditor.external_sprite_option import (
    ExternalSpriteOptionDialog,
)
from src.ui.widgets.spriteeditor.propertydecoders.property_decoder import (
    PropertyDecoder,
)


class ExternalPropertyDecoder(PropertyDecoder[ExternalSpriteField]):

    def __init__(self, field, layout, row, parent_widget):
        """
        Creates the widget
        """
        super().__init__(field, layout, row, parent_widget)

        assert self.field.bit is not None and len(self.field.bit) == 1

        self.dispvalue = 0

        bits = self.field.bit[0][1] - self.field.bit[0][0]

        # button that contains the current value
        self.button = QtWidgets.QPushButton()
        self.button.clicked.connect(self.HandleClicked)

        # spinbox that contains the current value
        self.box = QtWidgets.QSpinBox()
        self.box.setRange(0, (2 ** bits) - 1)
        self.box.setValue(self.dispvalue)
        self.box.valueChanged.connect(self.HandleValueChanged)

        label = QtWidgets.QLabel(self.field.title + ":")
        # label.setWordWrap(True)

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

        self.dispvalue = self.retrieve(data)
        self.button.setText(self.getShortForValue(self.dispvalue))
        self.box.setValue(self.dispvalue)

    def assign(self, data):
        """
        Assigns the currently selected value to data
        """
        return self.insertvalue(data, self.dispvalue)

    def HandleClicked(self, e):
        """
        Handles the button being clicked.
        """
        dlg = ExternalSpriteOptionDialog(self.field.type, self.dispvalue)

        # only contine if the user pressed "OK"
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        # read set value from dlg and update self.dispwidget
        self.dispvalue = dlg.getValue()
        self.button.setText(self.getShortForValue(self.dispvalue))
        self.box.setValue(self.dispvalue)

        # update all other fields
        self.updateData.emit(self)

    def HandleValueChanged(self, value):
        """
        Handles the spin value being changed
        """
        self.dispvalue = value
        self.button.setText(self.getShortForValue(self.dispvalue))

        # update all other fields
        self.updateData.emit(self)

    def getShortForValue(self, value):
        """
        Gets the short form from the xml for a value
        """
        value = int(value)

        # find correct xml
        filename = globals_.gamedef.externalFile(self.field.type + '.xml')
        if not os.path.isfile(filename):
            raise ValueError("The external xml file cannot be found for type: " + self.field.type)

        # parse the xml
        tree = ElementTree.parse(filename)
        root = tree.getroot()

        fmt = root.attrib['short']

        option = None
        for option_ in root:
            # skip if this is not an <option> or it's not for the correct value
            if option_.tag.lower() == 'option' and int(option_.attrib['value'], 0) == value:
                option = option_
                break

        if option is None:
            return str(value)

        # Do replacements
        for prop in option:
            name = f"[{prop.attrib['name']}]"
            fmt = fmt.replace(name, prop.attrib['value'])

        del tree, root

        # Do some automatic replacements
        replace = {
            '[b]': '<b>',
            '[/b]': '</b>',
            '[i]': '<i>',
            '[/i]': '</i>',
        }

        for old, value in replace.items():
            fmt = fmt.replace(old, value)

        # only display the first 27 characters and ...
        # so len(fmt) is at most 30.
        if len(fmt) > 30:
            fmt = fmt[:27] + '...'

        # Return it
        return fmt
