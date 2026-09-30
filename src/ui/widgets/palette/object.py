from PyQt6 import QtCore, QtWidgets

from src.data import globals_
from src.ui.theme.reggie_theme import GetIcon

from src.data.level.items.object import ObjectItem
from src.ui.widgets.sidelists.object_picker import ObjectPickerWidget

class ObjectTab(QtWidgets.QTabWidget):
    """
    Represents the Objects tab (and its child tabs) in the palette
    """
    def __init__(self):
        super().__init__(None)
        self.currentChanged.connect(self.slot_tab_changed)

        self.slot_tabs = [
            QtWidgets.QWidget(),
            QtWidgets.QWidget(),
            QtWidgets.QWidget(),
            QtWidgets.QWidget(),
        ]
        self.layer_buttons = [
            QtWidgets.QRadioButton(),
            QtWidgets.QRadioButton(),
            QtWidgets.QRadioButton()
        ]

        # Add the tileset tabs
        for i, slot in enumerate(self.slot_tabs):
            self.addTab(slot, GetIcon('objects'), str(i + 1))

        # Get strings for the layer change
        layer_change_str = globals_.trans.string('Palette', 38)
        tips = [
            globals_.trans.string('Palette', 1), # Layer 0
            globals_.trans.string('Palette', 2), # Layer 1
            globals_.trans.string('Palette', 3)  # Layer 2
        ]

        self.layer_button_group = QtWidgets.QButtonGroup(self)
        self.layer_button_group.buttonClicked.connect(lambda button: self.layer_changed(self.layer_button_group.id(button)))

        # Setup the radio buttons
        for i in range(3):
            self.layer_buttons[i] = QtWidgets.QRadioButton(str(i))
            self.layer_buttons[i].setToolTip(f'{tips[i]}{layer_change_str}')
            self.layer_button_group.addButton(self.layer_buttons[i], i)

        self.layer_change_button = QtWidgets.QPushButton(globals_.trans.string('Palette', 36))
        self.layer_change_button.clicked.connect(self.change_selection_layer)
        self.layer_change_button.setEnabled(False)

        layer_lyt = QtWidgets.QHBoxLayout()
        layer_lyt.addWidget(QtWidgets.QLabel(globals_.trans.string('Palette', 0)))
        for i in range(3):
            layer_lyt.addWidget(self.layer_buttons[i])
        layer_lyt.addStretch(1)
        layer_lyt.addWidget(self.layer_change_button)
        

        self.object_picker = ObjectPickerWidget()
        self.object_picker.ObjChanged.connect(self.object_selected)
        self.object_picker.ObjReplace.connect(lambda obj_num: ObjectItem.object_replaced(obj_num))

        main_layout = QtWidgets.QVBoxLayout(self.slot_tabs[0])
        main_layout.addLayout(layer_lyt)
        main_layout.addWidget(self.object_picker, 1)

        # Used to set the layout later
        self.tab_layout = main_layout

    def reset(self, is_new_level: bool, set_layer_1 = True):
        """
        Reset the Object Tab
        """
        if set_layer_1:
            self.layer_buttons[1].setChecked(True) # Toggle Layer 1
        self.object_picker.LoadFromTilesets()

        self.setCurrentIndex(0)

        if is_new_level:
            self.setTabEnabled(0, True)
            for i in range(1, 4):
                self.setTabEnabled(i, False)
        else: # Check tileset validity
            self.setTabEnabled(0, (globals_.Area.tileset0 != ''))
            self.setTabEnabled(1, (globals_.Area.tileset1 != ''))
            self.setTabEnabled(2, (globals_.Area.tileset2 != ''))
            self.setTabEnabled(3, (globals_.Area.tileset3 != ''))

    def slot_tab_changed(self, new_tab):
        """
        Handles the selected slot tab changing
        """
        if hasattr(self, 'object_picker'):
            if 0 <= new_tab <= 3:
                self.object_picker.ShowTileset(new_tab)
                self.slot_tabs[new_tab].setLayout(self.tab_layout)

            if globals_.mainWindow is not None:
                globals_.mainWindow.defaultPropDock.setVisible(False)

        globals_.CurrentPaintType = new_tab

    def change_selection_layer(self, checked):
        """
        Changes the layer of the selection to the current layer
        """
        ObjectItem.change_layer(globals_.CurrentLayer)

    def layer_changed(self, new_layer):
        """
        Handles the selected layer changing
        """
        globals_.CurrentLayer = new_layer

        # Only change layers when holding Alt
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
            ObjectItem.change_layer(new_layer)

    def object_selected(self, type_):
        """
        Handles a new object being chosen
        """
        globals_.CurrentObject = type_
