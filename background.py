from PyQt5 import QtWidgets, QtGui
import os

import globals_
from ui import GetIcon, HexSpinBox

# Sets up the Background Dialog
class BGDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose among various from tabs
    """

    def __init__(self):
        """
        Creates and initializes the tab dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('BGDlg', 0))
        self.setWindowIcon(GetIcon('backgrounds'))

        self.tabWidget = QtWidgets.QTabWidget()

        self.BGTabs = []
        for i, zone in enumerate(globals_.Area.zones):
            tab = BGTab(zone)
            self.BGTabs.append(tab)

            name = globals_.trans.string('BGDlg', 2, '[num]', i + 1)
            self.tabWidget.addTab(tab, name)

        if self.tabWidget.count() > 5:
            for tab in range(self.tabWidget.count()):
                self.tabWidget.setTabText(tab, str(tab + 1))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

class BGTab(QtWidgets.QWidget):
    def __init__(self, z):
        QtWidgets.QWidget.__init__(self)

        self.createBGSettings(z)
        self.createBGViewers(z)

        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addWidget(self.BGASettings, 0, 0)
        mainLayout.addWidget(self.BGBSettings, 1, 0)
        mainLayout.addWidget(self.BGAViewer, 0, 1)
        mainLayout.addWidget(self.BGBViewer, 1, 1)
        self.setLayout(mainLayout)

        self.updatePreviews()

    def createBGSettings(self, z):
        """
        Creates the BG Settings for BGA and BGB
        """
        clamp = lambda v, mi, ma: min(max(v, mi), ma)

        self.BGASettings = QtWidgets.QGroupBox(
            globals_.trans.string('BGDlg', 3)  # 'Scenery'
        )

        self.BGBSettings = QtWidgets.QGroupBox(
            globals_.trans.string('BGDlg', 4)  # 'Backdrop'
        )

        bg_vals = (z.bg1A, z.bg2A, z.bg3A), (z.bg1B, z.bg2B, z.bg3B)
        bg_names = globals_.BgANames, globals_.BgBNames
        bg_pos_vals = (z.XpositionA, -z.YpositionA), (z.XpositionB, -z.YpositionB)
        bg_zooms = z.ZoomA, z.ZoomB
        bg_scroll_vals = (z.XscrollA, z.YscrollA), (z.XscrollB, z.YscrollB)

        self.hex_boxes = []
        self.name_boxes = []
        self.pos_boxes = []
        self.scroll_boxes = []
        self.zoom_boxes = []

        for slot_id, target_box in enumerate((self.BGASettings, self.BGBSettings)):
            # hex values
            self.hex_boxes.append((HexSpinBox(), HexSpinBox(), HexSpinBox()))

            for box, value in zip(self.hex_boxes[-1], bg_vals[slot_id]):
                box.setRange(0, 0xFFFF)
                box.setValue(value)
                box.valueChanged.connect(self.handleHexBox)

            # name combobox
            self.name_boxes.append((QtWidgets.QComboBox(), QtWidgets.QComboBox(), QtWidgets.QComboBox()))

            for box in self.name_boxes[-1]:
                box.activated.connect(self.handleNameBox)

            # Fill the name comboboxes with values
            for i, (bfile_raw, bname) in enumerate(bg_names[slot_id]):
                bfile = int(bfile_raw, 16)

                for name in self.name_boxes[-1]:
                    name.addItem(
                        globals_.trans.string(
                            'BGDlg', 17,
                            '[name]', bname,
                            '[hex]', '%04X' % bfile
                        ),
                        bfile
                    )

            # Find the correct ones to select
            for name_box, value in zip(self.name_boxes[-1], bg_vals[slot_id]):
                idx = name_box.findData(value)

                if idx != -1:
                    # it's a known BG value
                    name_box.setCurrentIndex(idx)
                else:
                    # it's an unknown BG value
                    lastEntry = name_box.itemText(name_box.count() - 1)
                    if lastEntry != globals_.trans.string('BGDlg', 18):
                        name_box.addItem(globals_.trans.string('BGDlg', 18))
                    name_box.setCurrentIndex(name_box.count() - 1)

            # Position
            self.pos_boxes.append((QtWidgets.QSpinBox(), QtWidgets.QSpinBox()))

            for pos_box, desc, val in zip(self.pos_boxes[-1], (7, 9), bg_pos_vals[slot_id]):
                pos_box.setToolTip(globals_.trans.string('BGDlg', desc))
                pos_box.setRange(-256, 255)
                pos_box.setValue(val)

            # Scrolling
            self.scroll_boxes.append((QtWidgets.QComboBox(), QtWidgets.QComboBox()))

            for scroll_box, val in zip(self.scroll_boxes[-1], bg_scroll_vals[slot_id]):
                val = clamp(val, 0, len(globals_.BgScrollRates))
                scroll_box.addItems(globals_.BgScrollRateStrings)
                scroll_box.setToolTip(globals_.trans.string('BGDlg', 11))
                scroll_box.setCurrentIndex(val)

            # Zoom
            zoom_box = QtWidgets.QComboBox()

            zoom_box.addItems(globals_.trans.stringList('BGDlg', 15))
            zoom_box.setToolTip(globals_.trans.string('BGDlg', 14))
            zoom_box.setCurrentIndex(bg_zooms[slot_id])

            self.zoom_boxes.append(zoom_box)

            # Labels
            bgLabel = QtWidgets.QLabel(globals_.trans.string('BGDlg', 19))
            positionLabel = QtWidgets.QLabel(globals_.trans.string('BGDlg', 5))
            scrollLabel = QtWidgets.QLabel(globals_.trans.string('BGDlg', 10))

            # Layouts
            Lpos = QtWidgets.QFormLayout()
            Lpos.addRow(globals_.trans.string('BGDlg', 6), self.pos_boxes[-1][0])
            Lpos.addRow(globals_.trans.string('BGDlg', 8), self.pos_boxes[-1][1])

            Lscroll = QtWidgets.QFormLayout()
            Lscroll.addRow(globals_.trans.string('BGDlg', 6), self.scroll_boxes[-1][0])
            Lscroll.addRow(globals_.trans.string('BGDlg', 8), self.scroll_boxes[-1][1])

            Lzoom = QtWidgets.QFormLayout()
            Lzoom.addRow(globals_.trans.string('BGDlg', 13), zoom_box)

            mainLayout = QtWidgets.QGridLayout()
            mainLayout.addWidget(bgLabel, 0, 0, 1, 2)
            for i, box in enumerate(self.hex_boxes[-1]):
                mainLayout.addWidget(box, i + 1, 0)
            for i, box in enumerate(self.name_boxes[-1]):
                mainLayout.addWidget(box, i + 1, 1)
            mainLayout.addWidget(positionLabel, 4, 0)
            mainLayout.addLayout(Lpos, 5, 0)
            mainLayout.addWidget(scrollLabel, 4, 1)
            mainLayout.addLayout(Lscroll, 5, 1)
            mainLayout.addLayout(Lzoom, 6, 0, 1, 2)
            mainLayout.setRowStretch(7, 1)

            target_box.setLayout(mainLayout)

    def createBGViewers(self, z):
        self.BGAViewer = QtWidgets.QGroupBox(globals_.trans.string('BGDlg', 16))  # Preview
        self.BGBViewer = QtWidgets.QGroupBox(globals_.trans.string('BGDlg', 16))  # Preview

        self.previewA = (QtWidgets.QLabel(), QtWidgets.QLabel(), QtWidgets.QLabel())
        self.alignA = QtWidgets.QLabel()

        self.previewB = (QtWidgets.QLabel(), QtWidgets.QLabel(), QtWidgets.QLabel())
        self.alignB = QtWidgets.QLabel()

        mainLayout = QtWidgets.QGridLayout()
        for i, preview in enumerate(self.previewA):
            mainLayout.addWidget(preview, 0, i)
        mainLayout.addWidget(self.alignA, 1, 0, 1, 3)
        mainLayout.setRowStretch(2, 1)

        self.BGAViewer.setLayout(mainLayout)

        mainLayout = QtWidgets.QGridLayout()
        for i, preview in enumerate(self.previewB):
            mainLayout.addWidget(preview, 0, i)
        mainLayout.addWidget(self.alignB, 1, 0, 1, 3)
        mainLayout.setRowStretch(2, 1)

        self.BGBViewer.setLayout(mainLayout)

    def handleHexBox(self):
        """
        Handles any hex box changing
        """
        for slot_id, slot in enumerate(('A', 'B')):
            for boxnum in range(3):
                name_box = self.name_boxes[slot_id][boxnum]
                val = self.hex_boxes[slot_id][boxnum].value()
                idx = name_box.findData(val)
                if idx != -1:
                    # it's a known BG value
                    name_box.setCurrentIndex(idx)
                    lastEntry = name_box.itemText(name_box.count() - 1)
                    if lastEntry == globals_.trans.string('BGDlg', 18):
                        name_box.removeItem(name_box.count() - 1)
                else:
                    # it's an unknown BG value
                    lastEntry = name_box.itemText(name_box.count() - 1)
                    if lastEntry != globals_.trans.string('BGDlg', 18):
                        name_box.addItem(globals_.trans.string('BGDlg', 18))
                    name_box.setCurrentIndex(name_box.count() - 1)

        self.updatePreviews()

    def handleNameBox(self):
        """
        Handles any name box changing
        """
        for slot_id, slot in enumerate(('A', 'B')):
            for box_num in range(3):
                name_box = self.name_boxes[slot_id][box_num]
                val = name_box.itemData(name_box.currentIndex())
                if val is None:
                    # the user chose '(Custom)'
                    continue

                self.hex_boxes[slot_id][box_num].setValue(val)

        self.updatePreviews()

    def updatePreviews(self):
        """
        Updates all 6 preview labels
        """
        scale = 0.75
        previews = (self.previewA, self.previewB)
        for slot_id, align_box in enumerate((self.alignA, self.alignB)):
            for box_num in range(3):
                val = '%04X' % self.hex_boxes[slot_id][box_num].value()

                filename = globals_.gamedef.bgFile(val + '.png', 'ab'[slot_id])
                if not os.path.isfile(filename):
                    filename = os.path.join('reggiedata', ['bga', 'bgb'][slot_id], 'no_preview.png')

                pix = QtGui.QPixmap(filename)
                pix = pix.scaled(int(pix.width() * scale), int(pix.height() * scale))
                previews[slot_id][box_num].setPixmap(pix)

            # Alignment mode
            box1 = self.hex_boxes[slot_id][0].value()
            box2 = self.hex_boxes[slot_id][1].value()
            box3 = self.hex_boxes[slot_id][2].value()
            alignText = globals_.trans.stringList('BGDlg', 21)[calculateBgAlignmentMode(box1, box2, box3)]
            alignText = globals_.trans.string('BGDlg', 20, '[mode]', alignText)
            align_box.setText(alignText)


def calculateBgAlignmentMode(idA, idB, idC):
    """
    Calculates alignment modes using the exact same logic as NSMBW
    """
    # This really is RE'd ASM translated to Python, mostly

    if idA <= 0x000A: idA = 0
    if idB <= 0x000A: idB = 0
    if idC <= 0x000A: idC = 0

    if idA == idB == 0 or idC == 0:
        # Either both the first two are empty or the last one is empty
        return 0
    elif idA == idC == idB:
        # They are all the same
        return 5
    elif idA == idC != idB and idB != 0:
        # The first and last ones are the same, but
        # the middle one is different (not empty, though)
        return 1
    elif idC == idB != idA and idA != 0:
        # The second and last ones are the same, but
        # the first one is different (not empty, though)
        return 2
    elif idB == 0 and idC != idA != 0:
        # The middle one is empty. The first and last
        # ones are different, and the first one is not
        # empty
        return 3
    elif idA == 0 and idC != idB != 0:
        # The first one is empty. The second and last
        # ones are different, and the second one is not
        # empty
        return 4
    elif idA == idB != 0:
        # The first two match, and are not empty
        return 6
    elif idA != 0 != idB:
        # Every single one is not empty
        # note that idC is guaranteed to be nonzero,
        # otherwise it'd have returned 0 already.
        return 7

    # Doesn't fit into any of the above categories
    return 0

