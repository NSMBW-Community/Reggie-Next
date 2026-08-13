from PyQt6 import QtCore, QtWidgets

import globals_
from classlib import SpriteTexSpriteField
from misc import SpriteDefinition
from src.ui.widgets.spriteeditor.propertydecoders.property_decoder import PropertyDecoder
from src.ui.widgets.generic.int_spin_box import IntSpinBox


class SpriteTexPropertyDecoder(PropertyDecoder[SpriteTexSpriteField]):
    """
    Class that decodes/encodes sprite data to/from a SpriteTex element (valuebox + list)
    """

    def __init__(self, field, layout, row, parent_widget):
        """
        Creates the widgets
        """
        super().__init__(field, layout, row, parent_widget)

        self.spinBox = IntSpinBox()
        self.spinBox.setRange(0, self.field.max - 1)
        self.spinBox.valueChanged.connect(self.HandleValueChanged)

        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.setModel(self.field.model)
        self.comboBox.currentIndexChanged.connect(self.HandleIndexChanged)

        self.prev_value = None
        self.editWidget = 0 # 0 = spin box, 1 = combo box

        label = QtWidgets.QLabel(self.field.title + ':')

        #texIdLayout = QtWidgets.QFormLayout()
        #texIdLayout.addRow('Raw ID:', self.spinBox)
        #layout.addLayout(texIdLayout, row, 2, 1, 1)

        self.layout.addWidget(label, self.row, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.comboBox, self.row, 1, 1, 1)
        self.layout.addWidget(self.spinBox,  self.row, 2, 1, 1)

        self.init_comment_buttons()

    def update(self, data, first=False):
        """
        Updates the value shown by the widgets
        """
        # check if requirements are met
        self.checkReq(data, first)

        value = self.retrieve(data)
        self.spinBox.setValue(value)
        model = self.field.model
        if not isinstance(model, SpriteDefinition.ListPropertyModel):
            return

        for i, x in enumerate(model.entries):
            if x[0] == value:
                self.comboBox.setCurrentIndex(i)
                break
        else:
            self.comboBox.setCurrentIndex(-1)

    def assign(self, data):
        """
        Assigns the selected value to the data
        """
        model = self.field.model
        if not isinstance(model, SpriteDefinition.ListPropertyModel):
            return

        if self.editWidget == 0:
            return self.insertvalue(data, self.spinBox.value())
        else:
            return self.insertvalue(data, model.entries[self.comboBox.currentIndex()][0])

    def HandleDataChanged(self, value):
        """
        Handle the data changing in either widget
        """
        model = self.field.model
        if not isinstance(model, SpriteDefinition.ListPropertyModel):
            return

        self.updateData.emit(self)
        self.spinBox.setValue(value)

        for i, x in enumerate(model.entries):
            if x[0] == value:
                self.comboBox.setCurrentIndex(i)
                break
        else:
            self.comboBox.setPlaceholderText(globals_.trans.string('SpriteDataEditor', 35, '[id]', str(value)))
            self.comboBox.setCurrentIndex(-1)

    def HandleValueChanged(self, value):
        """
        Handle the value changing in the spinbox
        """
        self.editWidget = 0
        self.HandleDataChanged(value)

    def HandleIndexChanged(self, index):
        """
        Handle the current index changing in the combobox
        """
        model = self.field.model
        if index < 0 or not isinstance(model, SpriteDefinition.ListPropertyModel):
            return

        self.editWidget = 1
        self.HandleDataChanged(model.entries[index][0])
