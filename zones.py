from PyQt6 import QtWidgets, QtCore
from typing import cast

import common
import globals_
from ui import GetIcon
from levelitems import ZoneItem

class ZonesDialog(QtWidgets.QDialog):
    """
    Dialog which lets you modify zones
    """

    def __init__(self):
        """
        Creates and initializes the tab dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('ZonesDlg', 0))
        self.setWindowIcon(GetIcon('zones'))

        self.tabWidget = QtWidgets.QTabWidget()
        self.zoneTabs: list[ZoneTab]
        self.zoneTabs = []

        for i, z in enumerate(globals_.Area.zones):
            tabName = globals_.trans.string('ZonesDlg', 3, '[num]', z.id + 1)

            tab = ZoneTab(z)
            self.zoneTabs.append(tab)
            self.tabWidget.addTab(tab, tabName)

        self.newButton = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 4))
        self.copyButton = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 107))
        self.deleteButton = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 5))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttonBox.addButton(self.newButton, buttonBox.ButtonRole.ActionRole)
        buttonBox.addButton(self.copyButton, buttonBox.ButtonRole.ActionRole)
        buttonBox.addButton(self.deleteButton, buttonBox.ButtonRole.ActionRole)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.newButton.clicked.connect(self.handleNewZone)
        self.copyButton.clicked.connect(self.handleCopyZone)
        self.deleteButton.clicked.connect(self.handleDeleteZone)

        self.updateCopyDelete()

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def handleNewZone(self):
        """
        Handles creating a new zone
        """
        # Show warning about the zone 'limit'
        if len(self.zoneTabs) >= 6:
            result = QtWidgets.QMessageBox.warning(self, globals_.trans.string('ZonesDlg', 6), globals_.trans.string('ZonesDlg', 7),
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if result == QtWidgets.QMessageBox.StandardButton.No:
                return

        if globals_.mainWindow is None:
            return

        zone = globals_.mainWindow.CreateZone(256, 256)
        tabName = globals_.trans.string('ZonesDlg', 3, '[num]', zone.id + 1)

        tab = ZoneTab(zone)
        self.zoneTabs.append(tab)
        self.tabWidget.addTab(tab, tabName)

        tabCount = self.tabWidget.count()
        self.tabWidget.setCurrentIndex(tabCount - 1)
        self.updateCopyDelete()
    
    def handleCopyZone(self):
        """
        Handles copying the current zone data to a new one
        """
        if len(self.zoneTabs) >= 6:
            result = QtWidgets.QMessageBox.warning(self, globals_.trans.string('ZonesDlg', 6), globals_.trans.string('ZonesDlg', 7),
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if result == QtWidgets.QMessageBox.StandardButton.No:
                return

        if globals_.mainWindow is None:
            return

        z = globals_.mainWindow.CreateZone(256, 256)
        widget = cast(ZoneTab, self.tabWidget.widget(self.tabWidget.currentIndex()))
        widget.copyZoneData(z, self.tabWidget.currentIndex())

        tabName = globals_.trans.string('ZonesDlg', 3, '[num]', z.id + 1)

        tab = ZoneTab(z)
        self.zoneTabs.append(tab)
        self.tabWidget.addTab(tab, tabName)

        tabCount = self.tabWidget.count()
        self.tabWidget.setCurrentIndex(tabCount - 1)
        self.updateCopyDelete()

    def handleDeleteZone(self):
        """
        Handles deleting the current zone
        """
        tabCount = self.tabWidget.count()
        if tabCount == 0:
            return

        index = self.tabWidget.currentIndex()
        self.tabWidget.removeTab(index)
        self.zoneTabs.pop(index)
        self.updateCopyDelete()

    def updateCopyDelete(self):
        """
        Toggles the Copy and Delete buttons
        """
        tabCount = self.tabWidget.count()
        self.copyButton.setEnabled(tabCount != 0)
        self.deleteButton.setEnabled(tabCount != 0)

class ZoneTab(QtWidgets.QWidget):
    """
    Represents an individial zone
    """

    def __init__(self, zone: ZoneItem):
        QtWidgets.QWidget.__init__(self)

        self.zoneObj = zone
        self.autoChangeSize = False

        # Create the different sections of the tab
        self.createDimensions(zone)
        self.createRendering(zone)
        self.createAudio(zone)

        self.createCamera(zone)
        self.createBounds(zone)

        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.addWidget(self.dimensions)
        leftLayout.addWidget(self.rendering)
        leftLayout.addWidget(self.audio)

        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(self.camera)
        rightLayout.addWidget(self.bounds)

        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.addLayout(leftLayout)
        mainLayout.addLayout(rightLayout)
        self.setLayout(mainLayout)

    def createDimensions(self, zone: ZoneItem):
        """
        Creates the "Dimensions" section of the tab
        """
        self.dimensions = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 8))

        self.zPosX = QtWidgets.QSpinBox()
        self.zPosX.setRange(16, 65535)
        self.zPosX.setToolTip(globals_.trans.string('ZonesDlg', 10))
        self.zPosX.setValue(zone.objx)

        self.zPosY = QtWidgets.QSpinBox()
        self.zPosY.setRange(16, 65535)
        self.zPosY.setToolTip(globals_.trans.string('ZonesDlg', 12))
        self.zPosY.setValue(zone.objy)

        self.snapButton8 = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 76))
        self.snapButton8.clicked.connect(self.handleSnapGrid8)

        self.snapButton16 = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 77))
        self.snapButton16.clicked.connect(self.handleSnapGrid16)

        self.zWidth = QtWidgets.QSpinBox()
        self.zWidth.setRange(204, 65535)
        self.zWidth.setToolTip(globals_.trans.string('ZonesDlg', 14))
        self.zWidth.setValue(zone.width)
        self.zWidth.valueChanged.connect(self.handlePresetChanged)

        self.zHeight = QtWidgets.QSpinBox()
        self.zHeight.setRange(112, 65535)
        self.zHeight.setToolTip(globals_.trans.string('ZonesDlg', 16))
        self.zHeight.setValue(zone.height)
        self.zHeight.valueChanged.connect(self.handlePresetChanged)

        # Common retail zone presets:
        # 416 x 224 (used with minigames)
        # 448 x 224 (used with boss battles)
        # 512 x 272 (used in many, many places)
        # 560 x 304
        # 608 x 320 (actually 609x320; rounded it down myself)
        # 784 x 320 (not added to list because it's just an expansion of 608x320)
        # 704 x 384 (used multiple times; therefore it's important)
        # 944 x 448 (used in 9-3 zone 3)
        self.sizePresets = (
            '204x112', '308x168', '408x224', '468x256', '496x272', '556x304', '584x320', '700x384', '816x448'
        )

        self.presetChooser = QtWidgets.QComboBox()
        self.presetChooser.addItems(self.sizePresets)
        self.presetChooser.setToolTip(globals_.trans.string('ZonesDlg', 18))
        self.presetChooser.currentIndexChanged.connect(self.handlePresetSelected)

        # Initialize self.presetChooser
        self.handlePresetChanged()

        zonePosLyt = QtWidgets.QFormLayout()
        zonePosLyt.addRow(globals_.trans.string('ZonesDlg', 9), self.zPosX)
        zonePosLyt.addRow(globals_.trans.string('ZonesDlg', 11), self.zPosY)

        zoneSizeLyt = QtWidgets.QFormLayout()
        zoneSizeLyt.addRow(globals_.trans.string('ZonesDlg', 13), self.zWidth)
        zoneSizeLyt.addRow(globals_.trans.string('ZonesDlg', 15), self.zHeight)
        zoneSizeLyt.addRow(globals_.trans.string('ZonesDlg', 17), self.presetChooser)

        snapLayout = QtWidgets.QHBoxLayout()
        snapLayout.addWidget(self.snapButton8)
        snapLayout.addWidget(self.snapButton16)

        innerLayout = QtWidgets.QHBoxLayout()
        innerLayout.addLayout(zonePosLyt)
        innerLayout.addLayout(zoneSizeLyt)

        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.addLayout(innerLayout)
        verticalLayout.addLayout(snapLayout)

        self.dimensions.setLayout(verticalLayout)

    def handleSnapGrid8(self):
        """
        Snaps the current zone to an 8x8 grid
        """
        left = self.zPosX.value()
        top = self.zPosY.value()
        right = left + self.zWidth.value()
        bottom = top + self.zHeight.value()

        if left % 8 < 4:
            left -= (left % 8)
        else:
            left += 8 - (left % 8)

        if top % 8 < 4:
            top -= (top % 8)
        else:
            top += 8 - (top % 8)

        if right % 8 < 4:
            right -= (right % 8)
        else:
            right += 8 - (right % 8)

        if bottom % 8 < 4:
            bottom -= (bottom % 8)
        else:
            bottom += 8 - (bottom % 8)

        if right <= left:
            right += 8
        if bottom <= top:
            bottom += 8

        right -= left
        bottom -= top

        # Keep zone size within reasonable bounds
        left = common.clamp(left, 16, 65528)
        top = common.clamp(top, 16, 65528)
        right = common.clamp(right, 304, 65528)
        bottom = common.clamp(bottom, 200, 65528)

        self.zPosX.setValue(left)
        self.zPosY.setValue(top)
        self.zWidth.setValue(right)
        self.zHeight.setValue(bottom)

    def handleSnapGrid16(self):
        """
        Snaps the current zone to a 16x16 grid
        """
        left = self.zPosX.value()
        top = self.zPosY.value()
        right = left + self.zWidth.value()
        bottom = top + self.zHeight.value()

        if left % 16 < 8:
            left -= (left % 16)
        else:
            left += 16 - (left % 16)

        if top % 16 < 8:
            top -= (top % 16)
        else:
            top += 16 - (top % 16)

        if right % 16 < 8:
            right -= (right % 16)
        else:
            right += 16 - (right % 16)

        if bottom % 16 < 8:
            bottom -= (bottom % 16)
        else:
            bottom += 16 - (bottom % 16)

        if right <= left: right += 16
        if bottom <= top: bottom += 16

        right -= left
        bottom -= top

        # Keep zone size within reasonable bounds
        left = common.clamp(left, 16, 65520)
        top = common.clamp(top, 16, 65520)
        right = common.clamp(right, 304, 65520)
        bottom = common.clamp(bottom, 208, 65520)

        self.zPosX.setValue(left)
        self.zPosY.setValue(top)
        self.zWidth.setValue(right)
        self.zHeight.setValue(bottom)

    def createRendering(self, zone: ZoneItem):
        """
        Creates the "Rendering" section of the tab
        """
        self.rendering = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 84))

        comboboxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed)

        themeValues = globals_.ZoneThemeValues
        terrainLightValues = globals_.trans.stringList('ZonesDlg', 2)

        self.theme = QtWidgets.QComboBox()
        self.theme.addItems(themeValues)
        self.theme.setToolTip(globals_.trans.string('ZonesDlg', 21))
        self.theme.setSizePolicy(comboboxSizePolicy)

        zone.modeldark = common.clamp(zone.modeldark, 0, len(themeValues))
        self.theme.setCurrentIndex(zone.modeldark)

        self.terrainLight = QtWidgets.QComboBox()
        self.terrainLight.addItems(terrainLightValues)
        self.terrainLight.setToolTip(globals_.trans.string('ZonesDlg', 23))
        self.terrainLight.setSizePolicy(comboboxSizePolicy)

        if terrainLightValues is not None:
            zone.terraindark = common.clamp(zone.terraindark, 0, len(terrainLightValues))
        self.terrainLight.setCurrentIndex(zone.terraindark)

        self.spotlight = QtWidgets.QCheckBox(globals_.trans.string('ZonesDlg', 26))
        self.spotlight.setToolTip(globals_.trans.string('ZonesDlg', 27))

        self.fullDark = QtWidgets.QCheckBox(globals_.trans.string('ZonesDlg', 28))
        self.fullDark.setToolTip(globals_.trans.string('ZonesDlg', 29))

        self.visibility = QtWidgets.QComboBox()

        self.vis = zone.visibility

        self.spotlight.setChecked(self.vis & 0x10)
        self.fullDark.setChecked(self.vis & 0x20)

        self.handleVisibilityList()
        self.spotlight.clicked.connect(self.handleVisibilityList)
        self.fullDark.clicked.connect(self.handleVisibilityList)

        renderLyt = QtWidgets.QFormLayout()
        renderLyt.addRow(globals_.trans.string('ZonesDlg', 20), self.theme)
        renderLyt.addRow(globals_.trans.string('ZonesDlg', 22), self.terrainLight)

        visibilityLyt = QtWidgets.QHBoxLayout()
        visibilityLyt.addWidget(self.spotlight)
        visibilityLyt.addWidget(self.fullDark)

        innerLyt = QtWidgets.QVBoxLayout()
        innerLyt.addLayout(renderLyt)
        innerLyt.addLayout(visibilityLyt)
        innerLyt.addWidget(self.visibility)
        self.rendering.setLayout(innerLyt)

    def createCamera(self, zone: ZoneItem):
        """
        Creates the "Camera" section of the tab
        """
        self.camera = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 19))

        comboboxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed)

        self.camModeZoom = CameraModeZoomSettingsLayout(True)
        self.camModeZoom.setValues(zone.cammode, zone.camzoom)

        dirs = globals_.trans.stringList('ZonesDlg', 38)
        self.direction = QtWidgets.QComboBox()
        self.direction.addItems(dirs)
        self.direction.setToolTip(globals_.trans.string('ZonesDlg', 40))
        self.direction.setSizePolicy(comboboxSizePolicy)

        if dirs is not None:
            zone.camtrack = common.clamp(zone.camtrack, 0, len(dirs) - 1)
        self.direction.setCurrentIndex(zone.camtrack)

        self.restrictY = QtWidgets.QCheckBox()
        self.restrictY.setToolTip(globals_.trans.string('ZonesDlg', 78))
        self.restrictY.setChecked(zone.mpcamzoomadjust != 15)
        self.restrictY.stateChanged.connect(self.handleMPZoomAdjust)

        self.mpZoomAdjust = QtWidgets.QSpinBox()
        self.mpZoomAdjust.setRange(0, 14)
        self.mpZoomAdjust.setToolTip(globals_.trans.string('ZonesDlg', 79))

        self.handleMPZoomAdjust()
        if zone.mpcamzoomadjust < 15:
            self.mpZoomAdjust.setValue(zone.mpcamzoomadjust)

        # Layouts
        camLyt = QtWidgets.QFormLayout()
        camLyt.addRow(self.camModeZoom)
        camLyt.addRow(globals_.trans.string('ZonesDlg', 39), self.direction)
        camLyt.addRow(globals_.trans.string('ZonesDlg', 80), self.restrictY)
        camLyt.addRow(globals_.trans.string('ZonesDlg', 81), self.mpZoomAdjust)

        self.camera.setLayout(camLyt)

    def handleVisibilityList(self):
        """
        Handles changing the visibility type list
        """
        addIdx = 0

        # Figure out which set of options to show
        if self.fullDark.isChecked():
            if self.spotlight.isChecked():
                addIdx = 82
            else:
                addIdx = 45
        else:
            if self.spotlight.isChecked():
                addIdx = 43
            else:
                addIdx = 41

        addList = globals_.trans.stringList('ZonesDlg', addIdx)

        self.visibility.clear()
        self.visibility.addItems(addList)
        self.visibility.setToolTip(globals_.trans.string('ZonesDlg', addIdx + 1))

        if addList is not None:
            choice = min(self.vis & 0xF, len(addList) - 1)
            self.visibility.setCurrentIndex(choice)

    def handleMPZoomAdjust(self):
        """
        Handles toggling the multiplayer zoom adjust
        """
        self.mpZoomAdjust.setEnabled(self.restrictY.isChecked())
        self.mpZoomAdjust.setValue(0)

    def createBounds(self, zone: ZoneItem):
        """
        Creates the "Bounds" section of the tab
        """
        self.bounds = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 47))

        self.boundUp = QtWidgets.QSpinBox()
        self.boundUp.setRange(-32768, 32767)
        self.boundUp.setToolTip(globals_.trans.string('ZonesDlg', 49))
        self.boundUp.setSpecialValueText('32')
        self.boundUp.setValue(zone.yupperbound)

        self.boundDown = QtWidgets.QSpinBox()
        self.boundDown.setRange(-32768, 32767)
        self.boundDown.setToolTip(globals_.trans.string('ZonesDlg', 51))
        self.boundDown.setValue(zone.ylowerbound)

        self.lakituBoundUp = QtWidgets.QSpinBox()
        self.lakituBoundUp.setRange(-32768, 32767)
        self.lakituBoundUp.setToolTip(globals_.trans.string('ZonesDlg', 71))
        self.lakituBoundUp.setValue(zone.yupperbound2)

        self.lakituBoundDown = QtWidgets.QSpinBox()
        self.lakituBoundDown.setRange(-32768, 32767)
        self.lakituBoundDown.setToolTip(globals_.trans.string('ZonesDlg', 73))
        self.lakituBoundDown.setValue(zone.ylowerbound2)

        self.mpBoundUp = QtWidgets.QSpinBox()
        self.mpBoundUp.setRange(-32768, 32767)
        self.mpBoundUp.setToolTip(globals_.trans.string('ZonesDlg', 104))
        self.mpBoundUp.setSpecialValueText('32')
        self.mpBoundUp.setValue(zone.yupperbound3)

        self.mpBoundDown = QtWidgets.QSpinBox()
        self.mpBoundDown.setRange(-32768, 32767)
        self.mpBoundDown.setToolTip(globals_.trans.string('ZonesDlg', 106))
        self.mpBoundDown.setValue(zone.ylowerbound3)

        LA = QtWidgets.QFormLayout()
        LA.addRow(globals_.trans.string('ZonesDlg', 48), self.boundUp)
        LA.addRow(globals_.trans.string('ZonesDlg', 50), self.boundDown)

        LB = QtWidgets.QFormLayout()
        LB.addRow(globals_.trans.string('ZonesDlg', 70), self.lakituBoundUp)
        LB.addRow(globals_.trans.string('ZonesDlg', 72), self.lakituBoundDown)

        LC = QtWidgets.QHBoxLayout()
        LC.addLayout(LA)
        LC.addLayout(LB)

        LD = QtWidgets.QFormLayout()
        LD.addRow(LC)
        LD.addRow(globals_.trans.string('ZonesDlg', 103), self.mpBoundUp)
        LD.addRow(globals_.trans.string('ZonesDlg', 105), self.mpBoundDown)

        self.bounds.setLayout(LD)

    def createAudio(self, zone: ZoneItem):
        """
        Creates the "Audio" section of the tab
        """
        self.audio = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 52))
        self.autoEditMusic = False

        self.musicList = QtWidgets.QComboBox()
        self.musicList.setToolTip(globals_.trans.string('ZonesDlg', 54))

        for songID, text in globals_.MusicInfo:
            self.musicList.addItem(text, songID)

        self.musicList.setCurrentIndex(self.musicList.findData(zone.music))
        self.musicList.currentIndexChanged.connect(self.handleMusicListSelect)

        # Show 'Undefined Track XX' if there's no list item to show
        if self.musicList.findData(zone.music) == -1:
            self.musicList.setPlaceholderText(globals_.trans.string('ZonesDlg', 108, '[id]', str(zone.music)))

        self.musicID = QtWidgets.QSpinBox()
        self.musicID.setToolTip(globals_.trans.string('ZonesDlg', 69))
        self.musicID.setMaximum(255)
        self.musicID.setValue(zone.music)
        self.musicID.valueChanged.connect(self.handleMusicIDChange)

        self.modulation = QtWidgets.QComboBox()
        self.modulation.setToolTip(globals_.trans.string('ZonesDlg', 56))

        modulationList = globals_.trans.stringList('ZonesDlg', 57)
        self.modulation.addItems(modulationList)
        self.modulation.setCurrentIndex(zone.sfxmod // 16)

        self.bossFlag = QtWidgets.QCheckBox()
        self.bossFlag.setToolTip(globals_.trans.string('ZonesDlg', 59))
        self.bossFlag.setChecked(zone.sfxmod % 16)

        audioLyt = QtWidgets.QFormLayout()
        audioLyt.addRow(globals_.trans.string('ZonesDlg', 53), self.musicList)
        audioLyt.addRow(globals_.trans.string('ZonesDlg', 68), self.musicID)
        audioLyt.addRow(globals_.trans.string('ZonesDlg', 55), self.modulation)
        audioLyt.addRow(globals_.trans.string('ZonesDlg', 58), self.bossFlag)

        self.audio.setLayout(audioLyt)

    def handleMusicListSelect(self):
        """
        Handles the user selecting an entry from the music list
        """
        if self.autoEditMusic:
            return

        id = self.musicList.itemData(self.musicList.currentIndex())
        id = int(str(id)) # ID starts out as QString

        self.autoEditMusic = True
        self.musicID.setValue(id)
        self.autoEditMusic = False

    def handleMusicIDChange(self):
        """
        Handles the user selecting a custom music ID
        """
        if self.autoEditMusic:
            return
        id = self.musicID.value()

        # BUG: The music entries are out of order
        # (What does this mean?)

        self.autoEditMusic = True
        self.musicList.setCurrentIndex(self.musicList.findData(id))

        # Show 'Undefined Track XX' if there's no list item to show
        if self.musicList.findData(id) == -1:
            self.musicList.setPlaceholderText(globals_.trans.string('ZonesDlg', 108, '[id]', str(id)))

        self.autoEditMusic = False

    def handlePresetSelected(self, info=None):
        """
        Handles a zone size preset being selected
        """
        if self.autoChangeSize:
            return

        # Check if preset text is currently "(none)"
        if self.presetChooser.currentText() == globals_.trans.string('ZonesDlg', 60):
            return

        w, h = self.presetChooser.currentText().split('x')

        self.autoChangeSize = True
        self.zWidth.setValue(int(w))
        self.zHeight.setValue(int(h))
        self.autoChangeSize = False

        # Since a preset is now chosen, remove the None option from the list
        if self.presetChooser.itemText(0) == globals_.trans.string('ZonesDlg', 60):
            self.presetChooser.removeItem(0)

    def handlePresetChanged(self, info=None):
        """
        Handles the zone height or width boxes being changed
        """
        if self.autoChangeSize:
            return

        self.autoChangeSize = True
        w = self.zWidth.value()
        h = self.zHeight.value()
        check = str(w) + 'x' + str(h)

        sizeName = globals_.trans.string('ZonesDlg', 60)

        try:
            idx = self.sizePresets.index(check)
        except ValueError:
            idx = -1

        if idx == -1:
            if self.presetChooser.itemText(0) != sizeName:
                self.presetChooser.insertItem(0, sizeName)

            idx = 0

        elif self.presetChooser.itemText(0) == sizeName:
            self.presetChooser.removeItem(0)

        self.presetChooser.setCurrentIndex(idx)
        self.autoChangeSize = False

    def copyZoneData(self, z, currID):
        """
        Copies data from one zone into another
        """
        z.objx = common.clamp(16, 24560, self.zPosX.value())
        z.objy = common.clamp(16, 12272, self.zPosY.value())
        z.width = min(24560 - z.objx, self.zWidth.value())
        z.height = min(12272 - z.objy, self.zHeight.value())

        z.prepareGeometryChange()
        z.UpdateRects()
        z.setPos(z.objx * 1.5, z.objy * 1.5)

        z.modeldark = self.theme.currentIndex()
        z.terraindark = self.terrainLight.currentIndex()
        z.cammode = self.camModeZoom.modeButtonGroup.checkedId()
        z.camzoom = self.camModeZoom.screenSizes.currentIndex()
        z.camtrack = self.direction.currentIndex()

        if self.restrictY.isChecked():
            z.mpcamzoomadjust = self.mpZoomAdjust.value()
        else:
            z.mpcamzoomadjust = 15

        z.visibility = 0

        if self.spotlight.isChecked():
            z.visibility |= 1 << 4
        if self.fullDark.isChecked():
            z.visibility |= 1 << 5

        z.visibility |= self.visibility.currentIndex()

        z.yupperbound = self.boundUp.value()
        z.ylowerbound = self.boundDown.value()
        z.yupperbound2 = self.lakituBoundUp.value()
        z.ylowerbound2 = self.lakituBoundDown.value()
        z.yupperbound3 = self.mpBoundUp.value()
        z.ylowerbound3 = self.mpBoundDown.value()

        z.music = self.musicID.value()
        z.sfxmod = self.modulation.currentIndex() << 4
        if self.bossFlag.isChecked():
            z.sfxmod |= 1

        # For convenience, let's copy the background data too
        curZone = globals_.Area.zones[0]

        # Since the BG dialog isn't open, we must copy data directly from the selected zone
        for zone in globals_.Area.zones:
            if (zone.id == currID):
                curZone = zone

        # Copy the bgA first
        z.XscrollA = curZone.XscrollA
        z.YscrollA = curZone.YscrollA
        z.YpositionA = curZone.YpositionA
        z.XpositionA = curZone.XpositionA
        z.bg1A = curZone.bg1A
        z.bg2A = curZone.bg2A
        z.bg3A = curZone.bg3A
        z.ZoomA = curZone.ZoomA

        # And the bgB
        z.XscrollB = curZone.XscrollB
        z.YscrollB = curZone.YscrollB
        z.YpositionB = curZone.YpositionB
        z.XpositionB = curZone.XpositionB
        z.bg1B = curZone.bg1B
        z.bg2B = curZone.bg2B
        z.bg3B = curZone.bg3B
        z.ZoomB = curZone.ZoomB


class CameraModeZoomSettingsLayout(QtWidgets.QFormLayout):
    """
    A layout that shows the camera mode / zoom settings for editing.
    Separate from Zone Options so it can be reused for Camera Profiles
    """
    edited = QtCore.pyqtSignal()
    updating = False

    def __init__(self, showCamMode5: bool):
        super().__init__()
        self.updating = True

        comboboxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.zoomMode = -1

        self.modeButtonGroup = QtWidgets.QButtonGroup()
        modeButtons = []
        for i, name, tooltip in [
                    (0, globals_.trans.string('ZonesDlg', 85), globals_.trans.string('ZonesDlg', 86)),  # Normal
                    (3, globals_.trans.string('ZonesDlg', 87), globals_.trans.string('ZonesDlg', 88)),  # Static
                    (4, globals_.trans.string('ZonesDlg', 89), globals_.trans.string('ZonesDlg', 90)),  # Static, Y Track
                    (5, globals_.trans.string('ZonesDlg', 91), globals_.trans.string('ZonesDlg', 92)),  # Static, Event
                    (6, globals_.trans.string('ZonesDlg', 93), globals_.trans.string('ZonesDlg', 94)),  # X Track
                    (7, globals_.trans.string('ZonesDlg', 95), globals_.trans.string('ZonesDlg', 96)),  # X Expand
                    (1, globals_.trans.string('ZonesDlg', 97), globals_.trans.string('ZonesDlg', 98)),  # Y Track
                    (2, globals_.trans.string('ZonesDlg', 99), globals_.trans.string('ZonesDlg', 100)), # Y Expand
                ]:
            rb = QtWidgets.QRadioButton(name)
            rb.setToolTip(f'<b>{name}:</b><br>{tooltip}')
            self.modeButtonGroup.addButton(rb, i)
            modeButtons.append(rb)

            # Hides "Static Zoom, Event Controlled"
            if i == 5 and not showCamMode5:
                rb.setVisible(False)

            rb.clicked.connect(self.changeCamModeList)
            rb.clicked.connect(self.handleModeChanged)

        self.screenSizes = QtWidgets.QComboBox()
        self.screenSizes.setToolTip(globals_.trans.string('ZonesDlg', 102))
        self.screenSizes.setSizePolicy(comboboxSizePolicy)

        self.screenSizes.currentIndexChanged.connect(self.handleScreenSizesChanged)

        modesLyt = QtWidgets.QGridLayout()
        for i, btn in enumerate(modeButtons):
            modesLyt.addWidget(btn, i % 4, i // 4)

        self.addRow(modesLyt)
        self.addRow(globals_.trans.string('ZonesDlg', 101), self.screenSizes)

        self.updating = False

    def changeCamModeList(self):
        """
        Handles changing the available Screen Heights items
        """
        mode = self.modeButtonGroup.checkedId()
        oldListChoice = [1, 1, 2, 3, 3, 3, 1, 1][self.zoomMode]
        newListChoice = [1, 1, 2, 3, 3, 3, 1, 1][mode]

        if self.zoomMode != -1 and oldListChoice == newListChoice:
            return

        if newListChoice == 1:
            sizes = [
                ([14, 19], ''),
                ([14, 19, 24], ''),
                ([14, 19, 28], ''),
                ([20, 24], ''),
                ([19, 24, 28], ''),
                ([17, 24], ''),
                ([17, 24, 28], ''),
                ([17, 20], ''),
                ([7, 11, 28], '**'),
                ([17, 20.5, 24], ''),
                ([17, 20, 28], ''),
            ]
        elif newListChoice == 2:
            sizes = [
                ([14, 19], ''),
                ([14, 19, 24], ''),
                ([14, 19, 28], ''),
                ([19, 19, 24], ''),
                ([19, 24, 28], ''),
                ([19, 24, 28], ''),
                ([17, 24, 28], ''),
                ([17, 20.5, 24], ''),
            ]
        else:
            sizes = [
                ([14], ''),
                ([19], ''),
                ([24], ''),
                ([28], ''),
                ([17], ''),
                ([20], ''),
                ([16], ''),
                ([28], ''),
                ([7], '*'),
                ([10.5], '*'),
            ]

        items = []
        for i, (options, asterisk) in enumerate(sizes):
            items.append(', '.join(str(o) for o in options) + asterisk)

        self.screenSizes.clear()
        self.screenSizes.addItems(items)
        self.screenSizes.setCurrentIndex(0)
        self.zoomMode = mode

    def setValues(self, camMode, camZoom):
        self.updating = True
        camMode = common.clamp(camMode, 0, 7)

        button = self.modeButtonGroup.button(camMode)
        if button is not None:
            button.setChecked(True)
        self.changeCamModeList()

        camZoom = common.clamp(camZoom, 0, self.screenSizes.count())

        self.screenSizes.setCurrentIndex(camZoom)
        self.updating = False

    def handleModeChanged(self):
        """
        Handles the camera mode being changed
        """
        if self.updating:
            return
        self.changeCamModeList()
        self.edited.emit()

    def handleScreenSizesChanged(self):
        """
        Handles the screen size being changed
        """
        if self.updating:
            return
        self.edited.emit()
