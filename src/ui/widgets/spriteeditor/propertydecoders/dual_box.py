from PyQt6 import QtWidgets

from src.data.model.spritefield.dual_box import DualBoxSpriteField
from src.ui.widgets.spriteeditor.propertydecoders.property_decoder import (
    PropertyDecoder,
)


class DualBoxPropertyDecoder(PropertyDecoder[DualBoxSpriteField]):
    """
    Class that decodes/encodes sprite data to/from a dualbox
    """

    def __init__(self, field, layout, row, parent_widget):
        """
        Creates the widget
        """
        super().__init__(field, layout, row, parent_widget)

        self.buttons = [QtWidgets.QRadioButton(), QtWidgets.QRadioButton()]

        for button in self.buttons:
            button.clicked.connect(self.HandleClick)

        label1 = QtWidgets.QLabel(self.field.title)
        # label1.setWordWrap(True)

        label2 = QtWidgets.QLabel(self.field.title2)
        # label2.setWordWrap(True)

        L = QtWidgets.QHBoxLayout()
        L.addStretch(1)
        L.addWidget(label1)
        L.addWidget(self.buttons[0])
        L.addWidget(QtWidgets.QLabel("|"))
        L.addWidget(self.buttons[1])
        L.addWidget(label2)
        L.addStretch(1)
        L.setContentsMargins(0, 0, 0, 0)

        widget = QtWidgets.QWidget()
        widget.setLayout(L)

        # span three columns
        self.layout.addWidget(widget, self.row, 0, 1, 3)

        self.init_comment_buttons()


    def update(self, data, first=False):
        """
        Updates the value shown by the widget
        """
        # check if requirements are met
        self.checkReq(data, first)

        if self.field.full_nybble:
            value = self.retrieve(data) != 0
        else:
            value = self.retrieve(data) & 1

        self.buttons[value].setChecked(True)
        self.buttons[not value].setChecked(False)

    def assign(self, data):
        """
        Assigns the selected value to the data
        """
        value = self.buttons[1].isChecked()

        return self.insertvalue(data, value)

    def HandleClick(self, clicked=False):
        """
        Handles clicks on the checkbox
        """
        self.updateData.emit(self)
