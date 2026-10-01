from PyQt6 import QtWidgets, QtCore

from data import globals_
from typing import cast

from ui.widgets.sidelists.stamp_picker import StampPickerWidget
from data.stamp.stamp import Stamp
from data.stamp.stamp_list import StampListModel
from data.common.reggie_clip import ReggieClip

class StampTab(QtWidgets.QWidget):
    """
    Represents the Stamps tab in the palette
    """
    def __init__(self):
        super().__init__(None)
        label = QtWidgets.QLabel(globals_.trans.string('Palette', 27))

        self.add_button = QtWidgets.QPushButton(globals_.trans.string('Palette', 28))
        self.add_button.clicked.connect(self.add_stamp)
        self.add_button.setEnabled(False)

        self.remove_button = QtWidgets.QPushButton(globals_.trans.string('Palette', 29))
        self.remove_button.clicked.connect(self.remove_stamp)
        self.remove_button.setEnabled(False)

        menu = QtWidgets.QMenu()
        menu.addAction(globals_.trans.string('Palette', 31), self.open_stamps) # 'Open Set...'
        menu.addAction(globals_.trans.string('Palette', 32), self.save_stamps) # 'Save Set As...'

        self.tool_button = QtWidgets.QToolButton()
        self.tool_button.setText(globals_.trans.string('Palette', 30))
        self.tool_button.setMenu(menu)
        self.tool_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tool_button.setSizePolicy(self.add_button.sizePolicy())
        self.tool_button.setMinimumHeight(self.add_button.height() // 20)

        self.copy_button = QtWidgets.QPushButton(globals_.trans.string('Palette', 37))
        self.copy_button.clicked.connect(self.copy_stamp)
        self.copy_button.setEnabled(False)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setEnabled(False)
        self.name_edit.textChanged.connect(self.stamp_name_edited)

        name_label = QtWidgets.QLabel(globals_.trans.string('Palette', 35))
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)

        self.stamp_picker = StampPickerWidget()
        self.stamp_picker.selectionChangedSignal.connect(self.stamp_selected)

        main_layout = QtWidgets.QGridLayout(self)
        main_layout.addWidget(label, 0, 0, 1, 3)
        main_layout.addWidget(self.add_button, 1, 0)
        main_layout.addWidget(self.remove_button, 1, 1)
        main_layout.addWidget(self.tool_button, 1, 2)
        main_layout.addWidget(self.copy_button, 2, 0, 1, 3)
        main_layout.addLayout(name_layout, 3, 0, 1, 3)
        main_layout.addWidget(self.stamp_picker, 4, 0, 1, 3)

    def add_stamp(self):
        """
        Handles the "Add Stamp" btn being clicked
        """
        if globals_.mainWindow is None:
            return

        sel_items = globals_.mainWindow.scene.selectedItems()
        if not sel_items:
            return

        # Get a ReggieClip from selected item
        clip = ReggieClip.get_reggie_clip(sel_items)

        # Create a Stamp
        self.stamp_picker.addStamp(Stamp(clip, f'{globals_.trans.string('Palette', 41)}'))

    def remove_stamp(self):
        """
        Handles the "Remove Stamp" btn being clicked
        """
        self.stamp_picker.removeStamp(self.stamp_picker.currentlySelectedStamp())
        self.stamp_selected()

    def copy_stamp(self):
        """
        Handles the "Copy Selected to Clipboard" btn being clicked
        """
        if globals_.mainWindow is None:
            return

        stamp = self.stamp_picker.currentlySelectedStamp()
        if stamp is None or globals_.mainWindow.systemClipboard is None:
            return

        globals_.mainWindow.systemClipboard.setText(stamp.ReggieClip)

    def open_stamps(self):
        """
        Handles the "Open Set..." btn being clicked
        """
        filetypes = f'{globals_.trans.string('FileDlgs', 7)}  (*.stamps);; {globals_.trans.string('FileDlgs', 2)} (*)'

        fn = QtWidgets.QFileDialog.getOpenFileName(self, globals_.trans.string('FileDlgs', 6), '', filetypes)[0]
        if fn == '':
            return

        with open(fn, 'r', encoding='utf-8') as file:
            filedata = file.read()

        if not filedata.startswith('stamps\n------\n'):
            return

        filesplit = filedata.split('\n')[3:]
        for i in range(0, len(filesplit), 3):
            try:
                # Get data
                name = filesplit[i]
                rc = filesplit[i + 1]
            except IndexError:
                break

            self.stamp_picker.addStamp(Stamp(rc, name))

    def save_stamps(self):
        """
        Handles the "Save Set As..." btn being clicked
        """
        filetypes = f'{globals_.trans.string('FileDlgs', 7)}  (*.stamps);; {globals_.trans.string('FileDlgs', 2)} (*)'

        fn = QtWidgets.QFileDialog.getSaveFileName(self, globals_.trans.string('FileDlgs', 3), '', filetypes)[0]
        if fn == '':
            return

        newdata = ''
        newdata += 'stamps\n'
        newdata += '------\n'

        model = cast(StampListModel, self.stamp_picker.model())
        for stamp_obj in model.items:
            newdata += '\n'
            newdata += stamp_obj.Name + '\n'
            newdata += stamp_obj.ReggieClip + '\n'

        with open(fn, 'w', encoding='utf-8') as f:
            f.write(newdata)

    def stamp_selected(self):
        """
        Called when the stamp selection is changed
        """
        new_stamp = self.stamp_picker.currentlySelectedStamp()
        stampSelected = new_stamp is not None

        self.remove_button.setEnabled(stampSelected)
        self.copy_button.setEnabled(stampSelected)
        self.name_edit.setEnabled(stampSelected)

        new_name = '' if not stampSelected else new_stamp.Name
        self.name_edit.setText(new_name)

    def stamp_name_edited(self):
        """
        Called when the user edits the name of the current stamp
        """
        stamp = self.stamp_picker.currentlySelectedStamp()
        if not stamp:
            return

        text = self.name_edit.text()
        stamp.Name = text
        stamp.update()

        self.stamp_picker.updateGeometries()
        self.stamp_picker.update(self.stamp_picker.currentIndex())
        self.stamp_picker.update()
        self.stamp_picker.repaint()
