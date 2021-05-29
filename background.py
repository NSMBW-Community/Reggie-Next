from PyQt5 import QtWidgets, QtGui
import os

import globals_
from ui import GetIcon, HexSpinBox
from common import clamp

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

        self.inner_layout = QtWidgets.QVBoxLayout()
        self.bga_tabWidget = QtWidgets.QTabWidget()
        self.bgb_tabWidget = QtWidgets.QTabWidget()

        self.inner_layout.addWidget(self.bga_tabWidget)
        self.inner_layout.addWidget(self.bgb_tabWidget)

        self.BGATabs = []
        self.BGBTabs = []

        for background in globals_.Area.backgrounds_A:
            tab = BGTab(background, True)
            self.BGATabs.append(tab)

            name = globals_.trans.string('BGDlg', 2, '[num]', background.id)
            self.bga_tabWidget.addTab(tab, name)

        for background in globals_.Area.backgrounds_B:
            tab = BGTab(background, False)
            self.BGBTabs.append(tab)

            name = globals_.trans.string('BGDlg', 2, '[num]', background.id)
            self.bgb_tabWidget.addTab(tab, name)

        for bgs, tabwidget in zip((globals_.Area.backgrounds_A, globals_.Area.backgrounds_B), (self.bga_tabWidget, self.bgb_tabWidget)):
            if tabwidget.count() > 5:
                for tab in range(tabwidget.count()):
                    tabwidget.setTabText(tab, str(bgs[tab].id))

        self.bga_add = QtWidgets.QPushButton("Add Scenery")
        self.bgb_add = QtWidgets.QPushButton("Add Backdrop")
        self.bga_remove = QtWidgets.QPushButton("Remove Scenery")
        self.bgb_remove = QtWidgets.QPushButton("Remove Backdrop")
        self.bga_add.clicked.connect(lambda e: self.handleAdd(True))
        self.bgb_add.clicked.connect(lambda e: self.handleAdd(False))
        self.bga_remove.clicked.connect(lambda e: self.handleRemove(True))
        self.bgb_remove.clicked.connect(lambda e: self.handleRemove(False))

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(self.bga_add)
        buttonLayout.addWidget(self.bgb_add)
        buttonLayout.addWidget(self.bga_remove)
        buttonLayout.addWidget(self.bgb_remove)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(self.inner_layout)
        mainLayout.addLayout(buttonLayout)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def handleAdd(self, is_bga):
        if is_bga:
            tabwidget = self.bga_tabWidget
            tablist = self.BGATabs
            backgrounds = globals_.Area.backgrounds_A
        else:
            tabwidget = self.bgb_tabWidget
            tablist = self.BGBTabs
            backgrounds = globals_.Area.backgrounds_B

        used_ids = sorted([bg.id for bg in backgrounds])
        id_ = next(i for i, e in enumerate(used_ids + [None]) if i != e)

        default_background = Background(id_, 0, 0, 0, 0, 10, 10, 10, 0, is_bga)
        backgrounds.append(default_background)

        tab = BGTab(default_background, True)
        tablist.append(tab)

        tabamount = tabwidget.count()

        if tabamount < 6:
            name = globals_.trans.string('BGDlg', 2, '[num]', id_)
        else:
            name = str(id_)

        tabwidget.addTab(tab, name)

        if tabamount == 6:
            for tab, background in zip(range(tabamount), backgrounds):
                tabwidget.setTabText(tab, str(background.id))

    def handleRemove(self, is_bga):
        if is_bga:
            tabwidget = self.bga_tabWidget
            tablist = self.BGATabs
            backgrounds = globals_.Area.backgrounds_A
        else:
            tabwidget = self.bgb_tabWidget
            tablist = self.BGBTabs
            backgrounds = globals_.Area.backgrounds_B

        idx = tabwidget.currentIndex()
        if idx == -1:  # No tab selected
            return

        tabwidget.removeTab(idx)
        del backgrounds[idx]
        del tablist[idx]

        if tabwidget.count() == 5:
            self.fix_names(tabwidget, backgrounds, True)

    def fix_names(self, tabwidget, backgrounds, full_name):
        for tab in range(tabwidget.count()):
            if full_name:
                name = globals_.trans.string('BGDlg', 2, '[num]', backgrounds[tab].id)
            else:
                name = str(backgrounds[tab].id)

            tabwidget.setTabText(tab, name)



class BGTab(QtWidgets.QWidget):
    def __init__(self, background, is_bga):
        QtWidgets.QWidget.__init__(self)

        self.is_bga = is_bga

        self.createBGSettings(background, is_bga)
        self.createBGViewers()

        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addWidget(self.BGSettings, 0, 0)
        mainLayout.addWidget(self.BGViewer, 0, 1)
        self.setLayout(mainLayout)

        self.updatePreviews()

    def createBGSettings(self, background, is_bga):
        """
        Creates the BG Settings for BGA and BGB
        """

        self.BGSettings = QtWidgets.QGroupBox(
            globals_.trans.string('BGDlg', 3 if is_bga else 4)
        )

        bg_vals = (background.bg1, background.bg2, background.bg3)
        bg_names = globals_.BgANames if is_bga else globals_.BgBNames
        bg_pos_vals = (background.x_position, -background.y_position)
        bg_zooms = background.zoom
        bg_scroll_vals = (background.x_scroll, background.y_scroll)

        # hex values
        self.hex_boxes = (HexSpinBox(), HexSpinBox(), HexSpinBox())

        for box, value in zip(self.hex_boxes, bg_vals):
            box.setDisplayIntegerBase(16)
            box.setRange(0, 0xFFFF)
            box.setValue(value)
            box.valueChanged.connect(self.handleHexBox)

        # name combobox
        self.name_boxes = (QtWidgets.QComboBox(), QtWidgets.QComboBox(), QtWidgets.QComboBox())

        for box in self.name_boxes:
            box.activated.connect(self.handleNameBox)

        # Fill the name comboboxes with values
        for i, (bfile_raw, bname) in enumerate(bg_names):
            bfile = int(bfile_raw, 16)

            for name in self.name_boxes:
                name.addItem(
                    globals_.trans.string(
                        'BGDlg', 17,
                        '[name]', bname,
                        '[hex]', '%04X' % bfile
                    ),
                    bfile
                )

        # Find the correct ones to select
        for name_box, value in zip(self.name_boxes, bg_vals):
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
        self.pos_boxes = (QtWidgets.QSpinBox(), QtWidgets.QSpinBox())

        for pos_box, desc, val in zip(self.pos_boxes, (7, 9), bg_pos_vals):
            pos_box.setToolTip(globals_.trans.string('BGDlg', desc))
            pos_box.setRange(-32768, 32767)
            pos_box.setValue(val)

        # Scrolling
        self.scroll_boxes = (QtWidgets.QComboBox(), QtWidgets.QComboBox())

        for scroll_box, val in zip(self.scroll_boxes, bg_scroll_vals):
            val = clamp(val, 0, len(globals_.BgScrollRates))
            scroll_box.addItems(globals_.BgScrollRateStrings)
            scroll_box.setToolTip(globals_.trans.string('BGDlg', 11))
            scroll_box.setCurrentIndex(val)

        # Zoom
        zoom_box = QtWidgets.QComboBox()

        zoom_box.addItems(globals_.trans.stringList('BGDlg', 15))
        zoom_box.setToolTip(globals_.trans.string('BGDlg', 14))
        zoom_box.setCurrentIndex(bg_zooms)

        self.zoom_box = zoom_box

        # Labels
        bgLabel = QtWidgets.QLabel(globals_.trans.string('BGDlg', 19))
        positionLabel = QtWidgets.QLabel(globals_.trans.string('BGDlg', 5))
        scrollLabel = QtWidgets.QLabel(globals_.trans.string('BGDlg', 10))

        # Layouts
        Lpos = QtWidgets.QFormLayout()
        Lpos.addRow(globals_.trans.string('BGDlg', 6), self.pos_boxes[0])
        Lpos.addRow(globals_.trans.string('BGDlg', 8), self.pos_boxes[1])

        Lscroll = QtWidgets.QFormLayout()
        Lscroll.addRow(globals_.trans.string('BGDlg', 6), self.scroll_boxes[0])
        Lscroll.addRow(globals_.trans.string('BGDlg', 8), self.scroll_boxes[1])

        Lzoom = QtWidgets.QFormLayout()
        Lzoom.addRow(globals_.trans.string('BGDlg', 13), zoom_box)

        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addWidget(bgLabel, 0, 0, 1, 2)
        for i, box in enumerate(self.hex_boxes):
            mainLayout.addWidget(box, i + 1, 0)
        for i, box in enumerate(self.name_boxes):
            mainLayout.addWidget(box, i + 1, 1)
        mainLayout.addWidget(positionLabel, 4, 0)
        mainLayout.addLayout(Lpos, 5, 0)
        mainLayout.addWidget(scrollLabel, 4, 1)
        mainLayout.addLayout(Lscroll, 5, 1)
        mainLayout.addLayout(Lzoom, 6, 0, 1, 2)
        mainLayout.setRowStretch(7, 1)

        self.BGSettings.setLayout(mainLayout)

    def createBGViewers(self):
        self.BGViewer = QtWidgets.QGroupBox(globals_.trans.string('BGDlg', 16))  # Preview

        self.preview = (QtWidgets.QLabel(), QtWidgets.QLabel(), QtWidgets.QLabel())
        self.align = QtWidgets.QLabel()

        mainLayout = QtWidgets.QGridLayout()
        for i, preview in enumerate(self.preview):
            mainLayout.addWidget(preview, 0, i)
        mainLayout.addWidget(self.align, 1, 0, 1, 3)
        mainLayout.setRowStretch(2, 1)

        self.BGViewer.setLayout(mainLayout)

    def handleHexBox(self):
        """
        Handles any hex box changing
        """
        for boxnum in range(3):
            name_box = self.name_boxes[boxnum]
            val = self.hex_boxes[boxnum].value()
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
        for box_num in range(3):
            name_box = self.name_boxes[box_num]
            val = name_box.itemData(name_box.currentIndex())
            if val is None:
                # the user chose '(Custom)'
                continue

            self.hex_boxes[box_num].setValue(val)

        self.updatePreviews()

    def updatePreviews(self):
        """
        Updates all 6 preview labels
        """
        scale = 0.75

        for box_num in range(3):
            val = '%04X' % self.hex_boxes[box_num].value()

            filename = globals_.gamedef.bgFile(val + ".png", "a" if self.is_bga else "b")
            if not os.path.isfile(filename):
                filename = os.path.join("reggiedata", "bga" if self.is_bga else "bgb", "no_preview.png")

            pix = QtGui.QPixmap(filename)
            pix = pix.scaled(pix.width() * scale, pix.height() * scale)
            self.preview[box_num].setPixmap(pix)

        # Alignment mode
        box1 = self.hex_boxes[0].value()
        box2 = self.hex_boxes[1].value()
        box3 = self.hex_boxes[2].value()
        alignText = globals_.trans.stringList('BGDlg', 21)[calculateBgAlignmentMode(box1, box2, box3)]
        alignText = globals_.trans.string('BGDlg', 20, '[mode]', alignText)
        self.align.setText(alignText)

class Background():
    def __init__(self, a, b, c, d, e, f, g, h, i, is_bga):
        self.is_bga = is_bga

        self.id = a
        self.x_scroll = b
        self.y_scroll = c
        self.y_position = d
        self.x_position = e
        self.bg1 = f
        self.bg2 = g
        self.bg3 = h
        self.zoom = i


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

