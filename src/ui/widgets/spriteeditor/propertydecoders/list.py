from PyQt6 import QtCore, QtWidgets

import globals_
from classlib import ListSpriteField
from misc import SpriteDefinition
from src.ui.widgets.spriteeditor.propertydecoders.property_decoder import PropertyDecoder
from src.ui.widgets.spriteeditor.abstract_sprite_editor import (
    AbstractSpriteEditorWidget,
)


class ListPropertyDecoder(PropertyDecoder[ListSpriteField]):
    """
    Class that decodes/encodes sprite data to/from a combobox
    """

    def __init__(self, field, layout, row, parent_widget):
        """
        Creates the widget
        """
        super().__init__(field, layout, row, parent_widget)

        self.prev_value = 0

        self.widget = QtWidgets.QComboBox()
        self.widget.setModel(field.model)
        self.widget.currentIndexChanged.connect(self.HandleIndexChanged)

        if isinstance(field.model, SpriteDefinition.ListPropertyModel):
            self.model = field.model

        label = QtWidgets.QLabel(field.title + ':')
        # label.setWordWrap(True)

        self.layout.addWidget(label, self.row, 0, QtCore.Qt.AlignmentFlag.AlignRight)

        if self.field.idtype is not None:
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

        for i, x in enumerate(self.model.entries):
            if x[0] == value:
                self.widget.setCurrentIndex(i)
                break
        else:
            self.widget.setCurrentIndex(-1)

        if first:
            self.prev_value = value

    def assign(self, data):
        """
        Assigns the selected value to the data
        """
        return self.insertvalue(data, self.model.entries[self.widget.currentIndex()][0])

    def HandleIndexChanged(self, index):
        """
        Handle the current index changing in the combobox
        """
        if index < 0:
            return

        self.updateData.emit(self)

        value = self.model.entries[index][0]
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
        current_value = self.model.entries[self.widget.currentIndex()][0]
        values = [value for value, text in self.model.entries]

        for next_id, value in enumerate(values):
            if value > current_value and value not in used_ids:
                break
        else:
            return

        self.widget.setCurrentIndex(next_id)
