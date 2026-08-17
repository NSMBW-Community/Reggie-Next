from PyQt6 import QtCore, QtWidgets

from src.data.model.spritefield.multi_dual_box import MultiDualBoxSpriteField
from src.ui.widgets.spriteeditor.propertydecoders.property_decoder import (
    PropertyDecoder,
)


class MultiDualboxPropertyDecoder(PropertyDecoder[MultiDualBoxSpriteField]):
    """
    Class that decodes/encodes sprite data to/from a row of dualboxes
    """

    def __init__(self, field, layout, row, parent_widget):
        """
        Creates the widget
        """
        super().__init__(field, layout, row, parent_widget)

        assert self.field.bit is not None and len(self.field.bit) == 1

        self.bitnum = self.field.bit[0][1] - self.field.bit[0][0]
        self.startbit = self.field.bit[0][0]

        self.widgets = []
        DualboxLayout = QtWidgets.QGridLayout()
        DualboxLayout.setContentsMargins(0, 0, 0, 0)

        for i in range(self.bitnum):
            buttons = [QtWidgets.QRadioButton(), QtWidgets.QRadioButton()]
            buttons[0].clicked.connect(self.HandleClicked)
            buttons[0].setAutoExclusive(False)
            buttons[1].clicked.connect(self.HandleClicked)
            buttons[1].setAutoExclusive(False)

            buttons[0].setChecked(True)

            button_group = QtWidgets.QButtonGroup()
            button_group.addButton(buttons[0], 1)
            button_group.addButton(buttons[1], 2)

            self.widgets.append(button_group)

            DualboxLayout.addWidget(buttons[0], 0, i)
            DualboxLayout.addWidget(buttons[1], 1, i)

        label1 = QtWidgets.QLabel(self.field.title)
        # label1.setWordWrap(True)
        label2 = QtWidgets.QLabel(self.field.title2)
        # label2.setWordWrap(True)

        labels = QtWidgets.QGridLayout()
        labels.addWidget(label1, 0, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        labels.addWidget(label2, 1, 0, QtCore.Qt.AlignmentFlag.AlignRight)

        labels_widget = QtWidgets.QWidget()
        labels_widget.setLayout(labels)

        dualbox_widget = QtWidgets.QWidget()
        dualbox_widget.setLayout(DualboxLayout)

        self.layout.addWidget(labels_widget, self.row, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(dualbox_widget, self.row, 1, 1, 2)

        self.init_comment_buttons()

    def HandleClicked(self, _):
        """
        Handles clicks on the radiobutton
        """
        self.updateData.emit(self)

    def update(self, data, first=False):
        """
        Updates the value shown by the widget
        """
        # check if requirements are met
        self.checkReq(data, first)

        value = self.retrieve(data)

        # run at most self.bitnum times
        for i in range(self.bitnum - 1, -1, -1):
            self.widgets[i].button(2).setChecked(value & 1)
            value >>= 1

    def assign(self, data):
        """
        Assigns the checkbox states to the data
        """
        value = 0

        # construct bitmask
        for i in range(self.bitnum):
            value = (value << 1) | (self.widgets[i].checkedId() - 1)

        return self.insertvalue(data, value)
