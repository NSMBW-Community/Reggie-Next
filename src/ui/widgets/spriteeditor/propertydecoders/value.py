from PyQt6 import QtCore, QtWidgets

import globals_
from src.data.common.utils import find_first_available_id
from src.data.sprite.spritefield.value import ValueSpriteField
from src.ui.widgets.generic.int_spin_box import IntSpinBox
from src.ui.widgets.spriteeditor.abstract_sprite_editor import (
    AbstractSpriteEditorWidget,
)
from src.ui.widgets.spriteeditor.propertydecoders.property_decoder import (
    PropertyDecoder,
)


class ValuePropertyDecoder(PropertyDecoder[ValueSpriteField]):
    """
    Class that decodes/encodes sprite data to/from a spinbox
    """

    def __init__(self, field, layout, row, parent_widget):
        """
        Creates the widget
        """
        super().__init__(field, layout, row, parent_widget)

        self.widget = IntSpinBox(None, field.start, field.increment, field.overrides)
        self.widget.setRange(0, field.max - 1)
        self.widget.valueChanged.connect(self.HandleValueChanged)

        self.prev_value = None

        label = QtWidgets.QLabel(field.title + ':')
        # label.setWordWrap(True)

        self.layout.addWidget(label, self.row, 0, QtCore.Qt.AlignmentFlag.AlignRight)

        if field.idtype is not None:
            next_free_button = QtWidgets.QPushButton(globals_.trans.string('SpriteDataEditor', 29))
            next_free_button.clicked.connect(self.handle_next_free)

            self.layout.addWidget(self.widget, self.row, 1)
            self.layout.addWidget(next_free_button, self.row, 2)
        else:
            self.layout.addWidget(self.widget, self.row, 1, 1, 2)

        self.init_comment_buttons()

    def update(self, data, first=False):
        """
        Updates the value shown by the widget
        """
        # check if requirements are met
        self.checkReq(data, first)

        value = self.retrieve(data)
        self.widget.setValue(value)

        if first:
            self.prev_value = value

    def assign(self, data):
        """
        Assigns the selected value to the data
        """
        return self.insertvalue(data, self.widget.value())

    def HandleValueChanged(self, value):
        """
        Handle the value changing in the spinbox
        """
        self.updateData.emit(self)

        old_value = self.prev_value
        self.prev_value = value

        # No idtype is set, the widget is updating because of an automatic
        # change in spritedata or this is the default data editor.
        if (
            self.field.idtype is None
            or self.parent_widget is None
            or not isinstance(self.parent_widget, AbstractSpriteEditorWidget)
            or self.parent_widget.AutoFlag
            or self.parent_widget.DefaultMode
        ):
            return

        # Increment the count of the new value
        used_ids = globals_.Area.sprite_idtypes[self.field.idtype]
        used_ids[value] = used_ids.get(value, 0) + 1

        # Decrement (and remove if 0) the count of the old value
        if used_ids[old_value] == 1:
            del used_ids[old_value]
        else:
            used_ids[old_value] -= 1

    def handle_next_free(self):
        """
        Sets the value to the next free id of the id type of this property.
        """
        if self.field.idtype is None: return

        used_ids = globals_.Area.sprite_idtypes[self.field.idtype]
        next_id = find_first_available_id(used_ids, self.widget.maximum(), (self.widget.value() or 0) + 1)

        self.widget.setValue(next_id)
