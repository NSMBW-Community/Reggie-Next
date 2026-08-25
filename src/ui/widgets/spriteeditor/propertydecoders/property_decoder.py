from PyQt6 import QtCore, QtWidgets

import globals_
from src.data.sprite.spritefield.sprite_field import SpriteField
from src.ui.widgets.spriteeditor.abstract_sprite_editor import (
    AbstractSpriteEditorWidget,
)
from src.ui.theme.reggie_theme import GetIcon


class PropertyDecoder[T: SpriteField](QtCore.QObject):
    """
    Base class for all the sprite data decoder/encoders
    """
    updateData = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(
        self,
        field: T,
        layout: QtWidgets.QGridLayout | None = None,
        row: int | None = None,
        parent_widget: QtWidgets.QWidget | None = None,
    ):
        super().__init__()
        self.field = field
        self.layout = layout if layout is not None else QtWidgets.QGridLayout()
        self.row = row if row is not None else 0
        self.parent_widget = parent_widget if parent_widget is not None else QtWidgets.QWidget()
        self.button_com: QtWidgets.QToolButton | None = None
        self.button_com2: QtWidgets.QToolButton | None = None
        self.button_adv: QtWidgets.QToolButton | None = None

        if self.field.comment is not None:
            self.button_com = QtWidgets.QToolButton()
            self.button_com.setIcon(GetIcon('setting-comment'))
            self.button_com.setStyleSheet("border-radius: 50%")
            self.button_com.clicked.connect(lambda: self.show_comment(self.field.comment))
            self.button_com.setAutoRaise(True)

        if self.field.comment2 is not None:
            self.button_com2 = QtWidgets.QToolButton()
            self.button_com2.setIcon(GetIcon('setting-comment2'))
            self.button_com2.setStyleSheet("border-radius: 50%")
            self.button_com2.clicked.connect(lambda: self.show_comment(self.field.comment2))
            self.button_com2.setAutoRaise(True)

        if self.field.advanced_comment is not None:
            self.button_adv = QtWidgets.QToolButton()
            self.button_adv.setIcon(GetIcon('setting-comment-adv'))
            self.button_adv.setStyleSheet("border-radius: 50%")
            self.button_adv.clicked.connect(lambda: self.show_comment(self.field.advanced_comment))
            self.button_adv.setAutoRaise(True)

    def init_comment_buttons(self):
        col = 3
        for button in [self.button_com, self.button_com2, self.button_adv]:
            if button is not None:
                self.layout.addWidget(button, self.row, col)
                col += 1

    def retrieve(self, data, bits: list[tuple[int, int]] | None = None):
        """
        Extracts the value from the specified bit(s). Bit numbering is ltr BE
        and starts at 1.
        """
        if bits is None:
            bits = self.field.bit

        if bits is None:
            return 0

        value = 0

        for ran in bits:
            bit_len = ran[1] - ran[0]

            if bit_len == 7 and ran[0] & 7 == 1:
                # optimise if it's just one byte
                value = (value << bit_len) | data[ran[0] >> 3]
                continue

            # we have to calculate it
            for n in range(ran[0] - 1, ran[1] - 1):
                value <<= 1
                value |= (data[n >> 3] >> (7 - (n & 7))) & 1

        return value

    def insertvalue(self, data, value, bits=None):
        """
        Assigns a value to the specified bit(s)
        """
        if bits is None:
            bits = self.field.bit

        if bits is None:
            return data

        sdata = list(data)

        for ran in reversed(bits):
            # find the size of the range
            l = ran[1] - ran[0]

            # Extract the bits that need to be set in this iteration.
            value, v = value >> l, value & ((1 << l) - 1)

            # just one byte, this is easier
            if l == 7 and ran[0] & 7 == 1:
                sdata[ran[0] >> 3] = v & 0xFF
                continue

            # set the value bit by bit
            for n in reversed(range(ran[0], ran[1])):
                off = 1 << (7 - ((n - 1) & 7))

                if v & 1 != 0:  # set the bit
                    sdata[(n - 1) >> 3] |= off
                else:  # mask the bit out
                    sdata[(n - 1) >> 3] &= 0xFF ^ off

                v >>= 1

        return bytes(sdata)

    def checkReq(self, data, first=False):
        """
        Checks the requirements
        """
        if self.field.required is None or self.layout is None:
            return

        show = True
        for pos, ran in self.field.required:
            show = show and ran[0] <= self.retrieve(data, pos) < ran[1]

        layoutItem = self.layout.itemAtPosition(self.row, 0)
        widget = layoutItem.widget() if layoutItem is not None else None
        visibleNow = widget is not None and widget.isVisible()

        if show == visibleNow and not first:
            return

        # show/hide all widgets in this row
        for i in range(self.layout.columnCount()):
            w = self.layout.itemAtPosition(self.row, i)
            if w is None:
                continue
            layoutWidget = w.widget()
            if layoutWidget is None:
                continue
            layoutWidget.clearFocus()
            layoutWidget.setVisible(show)

        # maybe reset hidden stuff
        if globals_.ResetDataWhenHiding and not show:
            self.insertvalue(data, 0)

    def show_comment(self, comment: str | None):
        """
        Sets the current comment text
        """
        if self.parent_widget is None or not isinstance(self.parent_widget, AbstractSpriteEditorWidget):
            return

        self.parent_widget.com_main.setText(comment)
        self.parent_widget.com_main.setVisible(True)
        self.parent_widget.com_more.setVisible(False)
        self.parent_widget.com_extra.setVisible(False)
        self.parent_widget.com_box.setVisible(True)
