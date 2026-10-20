import os

from PyQt6 import QtGui, QtWidgets

from data import globals_
from data.common.utils import clamp, get_reggiedata_folder
from data.level.items.zone import ZoneItem
from ui.widgets.generic.hex_spin_box import HexSpinBox

class BackgroundEditorLayout(QtWidgets.QHBoxLayout):
    """
    A layout that represents the settings and preview
    of either a Scenery or Backdrop background type.
    """

    def __init__(self, zone: ZoneItem, is_bgb: bool) -> None:
        """
        Initializes the widget
        """
        super().__init__()
        self.zone = zone
        self.is_bgb = is_bgb

        self.create_settings()
        self.create_preview()

        self.addWidget(self.settings_box)
        self.addWidget(self.preview_box)

        self.update_preview()

    def create_settings(self) -> None:
        """
        Creates the background settings
        """
        str_id = 4 if self.is_bgb else 3
        self.settings_box = QtWidgets.QGroupBox(globals_.trans.string('BGDlg', str_id))

        zone = self.zone

        # Get all of our data
        if self.is_bgb:
            bg_ids = (zone.bg1B, zone.bg2B, zone.bg3B)
            bg_files = globals_.BgBFiles
            bg_pos_offs = (zone.XpositionB, -zone.YpositionB)
            bg_zoom = zone.ZoomB
            bg_scroll_speeds = (zone.XscrollB, zone.YscrollB)
        else:
            bg_ids = (zone.bg1A, zone.bg2A, zone.bg3A)
            bg_files = globals_.BgAFiles
            bg_pos_offs = (zone.XpositionA, -zone.YpositionA)
            bg_zoom = zone.ZoomA
            bg_scroll_speeds = (zone.XscrollA, zone.YscrollA)

        self.hex_boxes: list[HexSpinBox] = []
        self.name_boxes: list[QtWidgets.QComboBox] = []
        self.pos_boxes: list[QtWidgets.QSpinBox] = []
        self.scroll_boxes: list[QtWidgets.QComboBox] = []

        # Raw file IDs
        for value in bg_ids:
            file_box = HexSpinBox()
            file_box.setRange(0, 0xFFFF)
            file_box.setValue(value)
            file_box.valueChanged.connect(self.set_hex_box)
            self.hex_boxes.append(file_box)

        # Name combobox
        for i in range(3):
            name_box = QtWidgets.QComboBox()
            name_box.activated.connect(self.set_name_box)

            # Fill in the BG list
            for file in bg_files:
                file_id = int(file.bg_id, 16)
                name_box.addItem(globals_.trans.string('BGDlg', 17, '[name]', file.name, '[hex]', f'{file_id:04X}'), file_id)

            # Find the correct one to select
            for value in bg_ids:
                idx = name_box.findData(value)
    
                if idx != -1: # Defined BG entry
                    name_box.setCurrentIndex(idx)
                else: # Undefined BG entry
                    custom_text = globals_.trans.string('BGDlg', 18)
                    last_entry = name_box.itemText(name_box.count() - 1)
    
                    if last_entry != custom_text:
                        name_box.addItem(custom_text)

                    name_box.setCurrentIndex(name_box.count() - 1)

            self.name_boxes.append(name_box)

        # Position offset
        for i in range(2):
            pos_box = QtWidgets.QSpinBox()
            pos_box.setToolTip(globals_.trans.string('BGDlg', [7, 9][i]))
            pos_box.setRange(-256, 255)
            pos_box.setValue(bg_pos_offs[i])
            self.pos_boxes.append(pos_box)

        # The list of background scroll rate names
        scroll_names = globals_.trans.stringList('BGDlg', 1)

        # Scroll speed
        for value in bg_scroll_speeds:
            scroll_box = QtWidgets.QComboBox()
            scroll_box.addItems(scroll_names)
            scroll_box.setToolTip(globals_.trans.string('BGDlg', 11))

            if scroll_names is not None:
                value = clamp(value, 0, len(scroll_names) - 1)
                scroll_box.setCurrentIndex(value)
            else:
                scroll_box.setCurrentIndex(0)

            self.scroll_boxes.append(scroll_box)

        # Zoom
        self.zoom_box = QtWidgets.QComboBox()
        self.zoom_box.addItems(globals_.trans.stringList('BGDlg', 15))
        self.zoom_box.setToolTip(globals_.trans.string('BGDlg', 14))
        self.zoom_box.setCurrentIndex(bg_zoom)

        # Labels
        bg_label = QtWidgets.QLabel(globals_.trans.string('BGDlg', 19))
        position_label = QtWidgets.QLabel(globals_.trans.string('BGDlg', 5))
        scroll_label = QtWidgets.QLabel(globals_.trans.string('BGDlg', 10))

        # Layouts
        pos_lyt = QtWidgets.QFormLayout()
        pos_lyt.addRow(globals_.trans.string('BGDlg', 6), self.pos_boxes[0])
        pos_lyt.addRow(globals_.trans.string('BGDlg', 8), self.pos_boxes[1])

        scroll_lyt = QtWidgets.QFormLayout()
        scroll_lyt.addRow(globals_.trans.string('BGDlg', 6), self.scroll_boxes[0])
        scroll_lyt.addRow(globals_.trans.string('BGDlg', 8), self.scroll_boxes[1])

        zoom_lyt = QtWidgets.QFormLayout()
        zoom_lyt.addRow(globals_.trans.string('BGDlg', 13), self.zoom_box)

        main_layout = QtWidgets.QGridLayout()
        main_layout.addWidget(bg_label, 0, 0, 1, 2)
        for i, box in enumerate(self.hex_boxes):
            main_layout.addWidget(box, i + 1, 0)
        for i, box in enumerate(self.name_boxes):
            main_layout.addWidget(box, i + 1, 1)
        main_layout.addWidget(position_label, 4, 0)
        main_layout.addLayout(pos_lyt, 5, 0)
        main_layout.addWidget(scroll_label, 4, 1)
        main_layout.addLayout(scroll_lyt, 5, 1)
        main_layout.addLayout(zoom_lyt, 6, 0, 1, 2)
        main_layout.setRowStretch(7, 1)

        self.settings_box.setLayout(main_layout)

    def create_preview(self) -> None:
        """
        Creates the background preview
        """
        self.preview_box = QtWidgets.QGroupBox(globals_.trans.string('BGDlg', 16)) # 'Preview'

        self.preview_label = (QtWidgets.QLabel(), QtWidgets.QLabel(), QtWidgets.QLabel())
        self.align_type = QtWidgets.QLabel()
        self.align_note = QtWidgets.QLabel()

        main_layout = QtWidgets.QGridLayout()
        for i, preview in enumerate(self.preview_label):
            slot_label = globals_.trans.string('BGDlg', 22, '[i]', i + 1)
            main_layout.addWidget(QtWidgets.QLabel(slot_label), 0, i)
            main_layout.addWidget(preview, 1, i)
        main_layout.addWidget(self.align_type, 2, 0, 1, 3)
        main_layout.addWidget(self.align_note, 3, 0, 1, 3)
        main_layout.setRowStretch(4, 1)

        self.preview_box.setLayout(main_layout)

    def set_hex_box(self) -> None:
        """
        Handles any hex box changing
        """
        for i in range(3):
            name_box = self.name_boxes[i]
            custom_str = globals_.trans.string('BGDlg', 18)
            val = self.hex_boxes[i].value()
            idx = name_box.findData(val)

            if idx != -1: # Defined BG entry
                name_box.setCurrentIndex(idx)
                last_entry = name_box.itemText(name_box.count() - 1)
                if last_entry == custom_str:
                    name_box.removeItem(name_box.count() - 1)
            else: # Undefined BG entry
                last_entry = name_box.itemText(name_box.count() - 1)
                if last_entry != custom_str:
                    name_box.addItem(custom_str)

                name_box.setCurrentIndex(name_box.count() - 1)

        self.update_preview()

    def set_name_box(self) -> None:
        """
        Handles any name box changing
        """
        for i in range(3):
            name_box = self.name_boxes[i]
            val = name_box.itemData(name_box.currentIndex())

            # Check if '(custom)' was chosen
            if val is None:
                continue

            self.hex_boxes[i].setValue(val)

        self.update_preview()

    def update_preview(self) -> None:
        """
        Updates all previews
        """
        scale = 0.75

        for i in range(3):
            img_name = f'{self.hex_boxes[i].value():04X}'

            for file in [globals_.BgAFiles, globals_.BgBFiles][self.is_bgb]:
                if file.bg_id == img_name:
                    img_name = file.image

            filename = globals_.gamedef.bgFile(img_name + '.png', 'ab'[self.is_bgb])
            if not os.path.isfile(filename):
                filename = os.path.join(get_reggiedata_folder(), ['bga', 'bgb'][self.is_bgb], 'no_preview.png')

            pix = QtGui.QPixmap(filename)
            pix = pix.scaled(int(pix.width() * scale), int(pix.height() * scale))
            self.preview_label[i].setPixmap(pix)

        # Figure out the alignment mode
        box1 = self.hex_boxes[0].value()
        box2 = self.hex_boxes[1].value()
        box3 = self.hex_boxes[2].value()
        align_mode = self.get_alignment_mode(box1, box2, box3)

        align_list = globals_.trans.stringList('BGDlg', 21)
        if align_list is not None:
            self.align_type.setText(globals_.trans.string('BGDlg', 20, '[mode]', align_list[align_mode]))

        # Show a message if needed
        if align_mode == 0: # No BGs
            self.align_note.setStyleSheet('color: orange;')
            self.align_note.setText(globals_.trans.string('BGDlg', 23))
        elif align_mode in (3, 4): # Crashes
            self.align_note.setStyleSheet('color: red;')
            self.align_note.setText(globals_.trans.string('BGDlg', 24))
        else:
            self.align_note.setText('')

    @staticmethod
    def get_alignment_mode(id_a: int, id_b: int, id_c: int) -> int:
        """
        Calculates alignment modes using the exact same logic as NSMBW
        """
        if id_a == 0 and id_c == 0 or id_b == 0:
            return 0 # None, renders nothing in-game
        elif id_a == id_b and id_b == id_c:
            return 5 # 'Align to Screen, single BG'
        elif id_a == id_b and id_b != id_c and id_c != 0:
            return 1 # 'Align Slot 3 to Bottom'
        elif id_b == id_c and id_a != id_b and id_a != 0:
            return 2 # 'Align Slot 1 to Top'
        elif id_c == 0 and id_a != id_b and id_a != 0:
            return 3 # Crashes
        elif id_a == 0 and id_c != id_b and id_c != 0:
            return 4 # Also crashes
        elif id_a == id_c and id_a != 0 and id_c != 0:
            return 6 # 'Default'
        elif id_a != 0 and id_b != 0 and id_c != 0:
            return 7 # 'Align to Screen, multiple BGs'

        # Doesn't fit into any of the above categories
        return 0
