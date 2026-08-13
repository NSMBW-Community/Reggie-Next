from PyQt6 import QtCore, QtWidgets

from classlib import CheckBoxSpriteField
from src.ui.widgets.spriteeditor.propertydecoders.property_decoder import PropertyDecoder


class CheckBoxPropertyDecoder(PropertyDecoder[CheckBoxSpriteField]):
    """
    Class that decodes/encodes sprite data to/from a checkbox
    """

    def __init__(self, field, layout, row, parent_widget):
        """
        Creates the widget
        """
        super().__init__(field, layout, row, parent_widget)

        self.widget = QtWidgets.QCheckBox()
        self.widget.clicked.connect(self.HandleClick)

        label = QtWidgets.QLabel(self.field.title + ':')
        # label.setWordWrap(True)

        self.layout.addWidget(label, self.row, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.widget, self.row, 1)

        self.init_comment_buttons()

    def update(self, data, first=False):
        """
        Updates the value shown by the widget
        """
        # check if requirements are met
        self.checkReq(data, first)

        if self.field.full_nybble:
            value = (self.retrieve(data) != 0)
        else:
            value = ((self.retrieve(data) & self.field.mask) == self.field.mask)
        self.widget.setChecked(value)

    def assign(self, data):
        """
        Assigns the selected value to the data
        """
        value = self.retrieve(data)

        if self.widget.isChecked():
            value |= self.field.mask
        elif value & self.field.mask == self.field.mask:
            value = 0

        return self.insertvalue(data, value)

    def HandleClick(self, clicked=False):
        """
        Handles clicks on the checkbox
        """
        self.updateData.emit(self)
