from PyQt6 import QtWidgets, QtGui
import os

import globals_
from src.data.common.utils import clamp
from ui import GetIcon

from src.ui.widgets.generic.hex_spin_box import HexSpinBox

class BackgroundDialog(QtWidgets.QDialog):
    """
    Dialog which lets you modify backgrounds
    """

    def __init__(self):
        """
        Creates and initializes the tab dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('BGDlg', 0))
        self.setWindowIcon(GetIcon('background'))

        self.tabWidget = QtWidgets.QTabWidget()
        self.bgTabs: list[BackgroundTab] = []

        for i, zone in enumerate(globals_.Area.zones):
            tab = BackgroundTab(zone)
            self.bgTabs.append(tab)

            name = globals_.trans.string('BGDlg', 2, '[num]', i + 1)
            self.tabWidget.addTab(tab, name)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

class BackgroundTab(QtWidgets.QWidget):
    def __init__(self, z):
        QtWidgets.QWidget.__init__(self)

        self.createSettings(z)
        self.createPreviews(z)

        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addWidget(self.bgASettings, 0, 0)
        mainLayout.addWidget(self.bgBSettings, 1, 0)
        mainLayout.addWidget(self.bgAPreview, 0, 1)
        mainLayout.addWidget(self.bgBPreview, 1, 1)
        self.setLayout(mainLayout)

        self.updatePreviews()

    def createSettings(self, z):
        """
        Creates the BG Settings for BGA and BGB
        """
        self.bgASettings = QtWidgets.QGroupBox(globals_.trans.string('BGDlg', 3)) # 'Scenery'
        self.bgBSettings = QtWidgets.QGroupBox(globals_.trans.string('BGDlg', 4)) # 'Backdrop'

        bgIDs = (z.bg1A, z.bg2A, z.bg3A), (z.bg1B, z.bg2B, z.bg3B)
        bgNames = globals_.BgANames, globals_.BgBNames
        bgPosVals = (z.XpositionA, -z.YpositionA), (z.XpositionB, -z.YpositionB)
        bgZooms = z.ZoomA, z.ZoomB
        bgScrollVals = (z.XscrollA, z.YscrollA), (z.XscrollB, z.YscrollB)

        self.hexBoxes: list[tuple[HexSpinBox, HexSpinBox, HexSpinBox]] = []
        self.nameBoxes: list[tuple[QtWidgets.QComboBox, QtWidgets.QComboBox, QtWidgets.QComboBox]] = []
        self.posBoxes: list[tuple[QtWidgets.QSpinBox, QtWidgets.QSpinBox]] = []
        self.scrollBoxes: list[tuple[QtWidgets.QComboBox, QtWidgets.QComboBox]] = []
        self.zoomBoxes: list[QtWidgets.QComboBox] = []

        for slotID, targetBox in enumerate((self.bgASettings, self.bgBSettings)):
            # Raw file IDs
            self.hexBoxes.append((HexSpinBox(), HexSpinBox(), HexSpinBox()))
            for box, value in zip(self.hexBoxes[-1], bgIDs[slotID]):
                box.setRange(0, 0xFFFF)
                box.setValue(value)
                box.valueChanged.connect(self.handleHexBox)

            # Name combobox
            self.nameBoxes.append((QtWidgets.QComboBox(), QtWidgets.QComboBox(), QtWidgets.QComboBox()))
            for box in self.nameBoxes[-1]:
                box.activated.connect(self.handleNameBox)

            # Fill the name comboboxes with values
            for i, (fileRaw, bgName) in enumerate(bgNames[slotID]):
                bfile = int(fileRaw, 16)
                for name in self.nameBoxes[-1]:
                    name.addItem(globals_.trans.string('BGDlg', 17, '[name]', bgName, '[hex]', '%04X' % bfile), bfile)

            # Find the correct one to select
            for nameBox, value in zip(self.nameBoxes[-1], bgIDs[slotID]):
                idx = nameBox.findData(value)

                if idx != -1: # Defined BG entry
                    nameBox.setCurrentIndex(idx)
                else: # Undefined BG entry
                    customText = globals_.trans.string('BGDlg', 18)
                    lastEntry = nameBox.itemText(nameBox.count() - 1)

                    if lastEntry != customText:
                        nameBox.addItem(customText)
                    nameBox.setCurrentIndex(nameBox.count() - 1)

            # Position
            self.posBoxes.append((QtWidgets.QSpinBox(), QtWidgets.QSpinBox()))
            for posBox, desc, val in zip(self.posBoxes[-1], (7, 9), bgPosVals[slotID]):
                posBox.setToolTip(globals_.trans.string('BGDlg', desc))
                posBox.setRange(-256, 255)
                posBox.setValue(val)

            # Scrolling
            self.scrollBoxes.append((QtWidgets.QComboBox(), QtWidgets.QComboBox()))

            # The list of background scroll rate names
            scrollNames = globals_.trans.stringList('BGDlg', 1)

            for scrollBox, val in zip(self.scrollBoxes[-1], bgScrollVals[slotID]):
                scrollBox.addItems(scrollNames)
                scrollBox.setToolTip(globals_.trans.string('BGDlg', 11))

                if scrollNames is not None:
                    val = clamp(val, 0, len(scrollNames) - 1)
                    scrollBox.setCurrentIndex(val)
                else:
                    scrollBox.setCurrentIndex(0)

            # Zoom
            zoomBox = QtWidgets.QComboBox()
            zoomBox.addItems(globals_.trans.stringList('BGDlg', 15))
            zoomBox.setToolTip(globals_.trans.string('BGDlg', 14))
            zoomBox.setCurrentIndex(bgZooms[slotID])

            self.zoomBoxes.append(zoomBox)

            # Labels
            bgLabel = QtWidgets.QLabel(globals_.trans.string('BGDlg', 19))
            positionLabel = QtWidgets.QLabel(globals_.trans.string('BGDlg', 5))
            scrollLabel = QtWidgets.QLabel(globals_.trans.string('BGDlg', 10))

            # Layouts
            posLyt = QtWidgets.QFormLayout()
            posLyt.addRow(globals_.trans.string('BGDlg', 6), self.posBoxes[-1][0])
            posLyt.addRow(globals_.trans.string('BGDlg', 8), self.posBoxes[-1][1])

            scrollLyt = QtWidgets.QFormLayout()
            scrollLyt.addRow(globals_.trans.string('BGDlg', 6), self.scrollBoxes[-1][0])
            scrollLyt.addRow(globals_.trans.string('BGDlg', 8), self.scrollBoxes[-1][1])

            zoomLyt = QtWidgets.QFormLayout()
            zoomLyt.addRow(globals_.trans.string('BGDlg', 13), zoomBox)

            mainLayout = QtWidgets.QGridLayout()
            mainLayout.addWidget(bgLabel, 0, 0, 1, 2)
            for i, box in enumerate(self.hexBoxes[-1]):
                mainLayout.addWidget(box, i + 1, 0)
            for i, box in enumerate(self.nameBoxes[-1]):
                mainLayout.addWidget(box, i + 1, 1)
            mainLayout.addWidget(positionLabel, 4, 0)
            mainLayout.addLayout(posLyt, 5, 0)
            mainLayout.addWidget(scrollLabel, 4, 1)
            mainLayout.addLayout(scrollLyt, 5, 1)
            mainLayout.addLayout(zoomLyt, 6, 0, 1, 2)
            mainLayout.setRowStretch(7, 1)

            targetBox.setLayout(mainLayout)

    def createPreviews(self, z):
        self.bgAPreview = QtWidgets.QGroupBox(globals_.trans.string('BGDlg', 16)) # Preview
        self.bgBPreview = QtWidgets.QGroupBox(globals_.trans.string('BGDlg', 16)) # Preview

        self.previewA = (QtWidgets.QLabel(), QtWidgets.QLabel(), QtWidgets.QLabel())
        self.alignA = QtWidgets.QLabel()
        self.alignNoteA = QtWidgets.QLabel()

        self.previewB = (QtWidgets.QLabel(), QtWidgets.QLabel(), QtWidgets.QLabel())
        self.alignB = QtWidgets.QLabel()
        self.alignNoteB = QtWidgets.QLabel()

        mainLayout = QtWidgets.QGridLayout()
        for i, preview in enumerate(self.previewA):
            slotLabel = globals_.trans.string('BGDlg', 22, '[i]', i + 1)
            mainLayout.addWidget(QtWidgets.QLabel(slotLabel), 0, i)
            mainLayout.addWidget(preview, 1, i)
        mainLayout.addWidget(self.alignA, 2, 0, 1, 3)
        mainLayout.addWidget(self.alignNoteA, 3, 0, 1, 3)
        mainLayout.setRowStretch(4, 1)

        self.bgAPreview.setLayout(mainLayout)

        mainLayout = QtWidgets.QGridLayout()
        for i, preview in enumerate(self.previewB):
            slotLabel = globals_.trans.string('BGDlg', 22, '[i]', i + 1)
            mainLayout.addWidget(QtWidgets.QLabel(slotLabel), 0, i)
            mainLayout.addWidget(preview, 1, i)
        mainLayout.addWidget(self.alignB, 2, 0, 1, 3)
        mainLayout.addWidget(self.alignNoteB, 3, 0, 1, 3)
        mainLayout.setRowStretch(4, 1)

        self.bgBPreview.setLayout(mainLayout)

    def handleHexBox(self):
        """
        Handles any hex box changing
        """
        for slotID, slot in enumerate(('A', 'B')):
            for boxnum in range(3):
                nameBox = self.nameBoxes[slotID][boxnum]
                customStr = globals_.trans.string('BGDlg', 18)
                val = self.hexBoxes[slotID][boxnum].value()
                idx = nameBox.findData(val)

                if idx != -1: # Defined BG entry
                    nameBox.setCurrentIndex(idx)
                    lastEntry = nameBox.itemText(nameBox.count() - 1)
                    if lastEntry == customStr:
                        nameBox.removeItem(nameBox.count() - 1)
                else: # Undefined BG entry
                    lastEntry = nameBox.itemText(nameBox.count() - 1)
                    if lastEntry != customStr:
                        nameBox.addItem(customStr)
                    nameBox.setCurrentIndex(nameBox.count() - 1)

        self.updatePreviews()

    def handleNameBox(self):
        """
        Handles any name box changing
        """
        for slotID, slot in enumerate(('A', 'B')):
            for boxNum in range(3):
                nameBox = self.nameBoxes[slotID][boxNum]
                val = nameBox.itemData(nameBox.currentIndex())

                # Check if '(custom)' was chosen
                if val is None:
                    continue

                self.hexBoxes[slotID][boxNum].setValue(val)

        self.updatePreviews()

    def updatePreviews(self):
        """
        Updates all 6 preview labels
        """
        scale = 0.75
        previews = (self.previewA, self.previewB)
        alignNotes = (self.alignNoteA, self.alignNoteB)

        for slotID, alignBox in enumerate((self.alignA, self.alignB)):
            for boxNum in range(3):
                val = '%04X' % self.hexBoxes[slotID][boxNum].value()

                filename = globals_.gamedef.bgFile(val + '.png', 'ab'[slotID])
                if not os.path.isfile(filename):
                    filename = os.path.join('reggiedata', ['bga', 'bgb'][slotID], 'no_preview.png')

                pix = QtGui.QPixmap(filename)
                pix = pix.scaled(int(pix.width() * scale), int(pix.height() * scale))
                previews[slotID][boxNum].setPixmap(pix)

            # Alignment mode
            box1 = self.hexBoxes[slotID][0].value()
            box2 = self.hexBoxes[slotID][1].value()
            box3 = self.hexBoxes[slotID][2].value()
            alignMode = calculateBgAlignmentMode(box1, box2, box3)

            alignList = globals_.trans.stringList('BGDlg', 21)
            if alignList is not None:
                alignBox.setText(globals_.trans.string('BGDlg', 20, '[mode]', alignList[alignMode]))

            if alignMode == 0: # No BGs
                alignNotes[slotID].setStyleSheet('color: orange;')
                alignNotes[slotID].setText(globals_.trans.string('BGDlg', 23))
            elif alignMode in (3, 4): # Crashes
                alignNotes[slotID].setStyleSheet('color: red;')
                alignNotes[slotID].setText(globals_.trans.string('BGDlg', 24))
            else:
                alignNotes[slotID].setText('')


def calculateBgAlignmentMode(idA, idB, idC):
    """
    Calculates alignment modes using the exact same logic as NSMBW
    """
    if idA == 0 and idC == 0 or idB == 0:
        return 0 # None, renders nothing in-game
    elif idA == idB and idB == idC:
        return 5 # 'Align to Screen, single BG'
    elif idA == idB and idB != idC and idC != 0:
        return 1 # 'Align Slot 3 to Bottom'
    elif idB == idC and idA != idB and idA != 0:
        return 2 # 'Align Slot 1 to Top'
    elif idC == 0 and idA != idB and idA != 0:
        return 3 # Crashes
    elif idA == 0 and idC != idB and idC != 0:
        return 4 # Also crashes
    elif idA == idC and idA != 0 and idC != 0:
        return 6 # 'Default'
    elif idA != 0 and idB != 0 and idC != 0:
        return 7 # 'Align to Screen, multiple BGs'

    # Doesn't fit into any of the above categories
    return 0
