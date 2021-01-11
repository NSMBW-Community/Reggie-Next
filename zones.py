from PyQt5 import QtWidgets

import globals_
from ui import GetIcon
from levelitems import ZoneItem

# Sets up the Zones Menu
class ZonesDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose among various from tabs
    """

    def __init__(self):
        """
        Creates and initializes the tab dialog
        """
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle(globals_.trans.string('ZonesDlg', 0))
        self.setWindowIcon(GetIcon('zones'))

        self.tabWidget = QtWidgets.QTabWidget()

        i = 0
        self.zoneTabs = []
        for z in globals_.Area.zones:
            i = i + 1
            ZoneTabName = globals_.trans.string('ZonesDlg', 3, '[num]', i)
            tab = ZoneTab(z)
            self.zoneTabs.append(tab)
            self.tabWidget.addTab(tab, ZoneTabName)

        if self.tabWidget.count() > 5:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, str(tab + 1))

        self.NewButton = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 4))
        self.DeleteButton = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 5))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.addButton(self.NewButton, buttonBox.ActionRole)
        buttonBox.addButton(self.DeleteButton, buttonBox.ActionRole)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        # self.NewButton.setEnabled(len(self.zoneTabs) < 8)
        self.NewButton.clicked.connect(self.NewZone)
        self.DeleteButton.clicked.connect(self.DeleteZone)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def NewZone(self):
        if len(self.zoneTabs) >= 8:
            result = QtWidgets.QMessageBox.warning(self, globals_.trans.string('ZonesDlg', 6), globals_.trans.string('ZonesDlg', 7),
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No:
                return

        a = [0, 0, 0, 0, 0, 0]
        b = [[0, 0, 0, 0, 0, 10, 10, 10, 0]]
        id = len(self.zoneTabs)
        z = ZoneItem(256, 256, 448, 224, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, a, b, b, id)
        ZoneTabName = globals_.trans.string('ZonesDlg', 3, '[num]', id + 1)
        tab = ZoneTab(z)
        self.zoneTabs.append(tab)
        self.tabWidget.addTab(tab, ZoneTabName)
        if self.tabWidget.count() > 5:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, str(tab + 1))

                # self.NewButton.setEnabled(len(self.zoneTabs) < 8)

    def DeleteZone(self):
        curindex = self.tabWidget.currentIndex()
        tabamount = self.tabWidget.count()
        if tabamount == 0: return
        self.tabWidget.removeTab(curindex)

        for tab in range(curindex, tabamount):
            if self.tabWidget.count() < 6:
                self.tabWidget.setTabText(tab, globals_.trans.string('ZonesDlg', 3, '[num]', tab + 1))
            if self.tabWidget.count() > 5:
                self.tabWidget.setTabText(tab, str(tab + 1))

        self.zoneTabs.pop(curindex)
        if self.tabWidget.count() < 6:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, globals_.trans.string('ZonesDlg', 3, '[num]', tab + 1))

                # self.NewButton.setEnabled(len(self.zoneTabs) < 8)


class ZoneTab(QtWidgets.QWidget):
    def __init__(self, z):
        QtWidgets.QWidget.__init__(self)

        self.zoneObj = z
        self.AutoChangingSize = False

        self.createDimensions(z)
        self.createVisibility(z)
        self.createBounds(z)
        self.createAudio(z)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.Dimensions)
        mainLayout.addWidget(self.Visibility)
        mainLayout.addWidget(self.Bounds)
        mainLayout.addWidget(self.Audio)
        self.setLayout(mainLayout)

    def createDimensions(self, z):
        self.Dimensions = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 8))

        self.Zone_xpos = QtWidgets.QSpinBox()
        self.Zone_xpos.setRange(16, 65535)
        self.Zone_xpos.setToolTip(globals_.trans.string('ZonesDlg', 10))
        self.Zone_xpos.setValue(z.objx)

        self.Zone_ypos = QtWidgets.QSpinBox()
        self.Zone_ypos.setRange(16, 65535)
        self.Zone_ypos.setToolTip(globals_.trans.string('ZonesDlg', 12))
        self.Zone_ypos.setValue(z.objy)

        self.snapButton8 = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 76))
        self.snapButton8.clicked.connect(lambda: self.HandleSnapTo8x8Grid(z))

        self.snapButton16 = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 77))
        self.snapButton16.clicked.connect(lambda: self.HandleSnapTo16x16Grid(z))

        self.Zone_width = QtWidgets.QSpinBox()
        self.Zone_width.setRange(300, 65535)
        self.Zone_width.setToolTip(globals_.trans.string('ZonesDlg', 14))
        self.Zone_width.setValue(z.width)
        self.Zone_width.valueChanged.connect(self.PresetDeselected)

        self.Zone_height = QtWidgets.QSpinBox()
        self.Zone_height.setRange(200, 65535)
        self.Zone_height.setToolTip(globals_.trans.string('ZonesDlg', 16))
        self.Zone_height.setValue(z.height)
        self.Zone_height.valueChanged.connect(self.PresetDeselected)

        # Common retail zone presets
        # 416 x 224; Zoom Level 0 (used with minigames)
        # 448 x 224; Zoom Level 0 (used with boss battles)
        # 512 x 272; Zoom Level 0 (used in many, many places)
        # 560 x 304; Zoom Level 2
        # 608 x 320; Zoom Level 2 (actually 609x320; rounded it down myself)
        # 784 x 320; Zoom Level 2 (not added to list because it's just an expansion of 608x320)
        # 704 x 384; Zoom Level 3 (used multiple times; therefore it's important)
        # 944 x 448; Zoom Level 4 (used in 9-3 zone 3)
        self.Zone_presets_values = (
        '0: 416x224', '0: 448x224', '0: 512x272', '2: 560x304', '2: 608x320', '3: 704x384', '4: 944x448')

        self.Zone_presets = QtWidgets.QComboBox()
        self.Zone_presets.addItems(self.Zone_presets_values)
        self.Zone_presets.setToolTip(globals_.trans.string('ZonesDlg', 18))
        self.Zone_presets.currentIndexChanged.connect(self.PresetSelected)
        self.PresetDeselected()  # can serve as an initializer for self.Zone_presets

        ZonePositionLayout = QtWidgets.QFormLayout()
        ZonePositionLayout.addRow(globals_.trans.string('ZonesDlg', 9), self.Zone_xpos)
        ZonePositionLayout.addRow(globals_.trans.string('ZonesDlg', 11), self.Zone_ypos)

        ZoneSizeLayout = QtWidgets.QFormLayout()
        ZoneSizeLayout.addRow(globals_.trans.string('ZonesDlg', 13), self.Zone_width)
        ZoneSizeLayout.addRow(globals_.trans.string('ZonesDlg', 15), self.Zone_height)
        ZoneSizeLayout.addRow(globals_.trans.string('ZonesDlg', 17), self.Zone_presets)

        snapLayout = QtWidgets.QHBoxLayout()

        snapLayout.addWidget(self.snapButton8)
        snapLayout.addWidget(self.snapButton16)

        innerLayout = QtWidgets.QHBoxLayout()

        innerLayout.addLayout(ZonePositionLayout)
        innerLayout.addLayout(ZoneSizeLayout)

        verticalLayout = QtWidgets.QVBoxLayout()

        verticalLayout.addLayout(innerLayout)
        verticalLayout.addLayout(snapLayout)

        self.Dimensions.setLayout(verticalLayout)

    def HandleSnapTo8x8Grid(self, z):
        """
        Snaps the current zone to an 8x8 grid
        """
        left = self.Zone_xpos.value()
        top = self.Zone_ypos.value()
        right = left + self.Zone_width.value()
        bottom = top + self.Zone_height.value()

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

        if right <= left: right += 8
        if bottom <= top: bottom += 8

        right -= left
        bottom -= top

        if left < 16: left = 16
        if top < 16: top = 16
        if right < 304: right = 304
        if bottom < 200: bottom = 200

        if left > 65528: left = 65528
        if top > 65528: top = 65528
        if right > 65528: right = 65528
        if bottom > 65528: bottom = 65528

        self.Zone_xpos.setValue(left)
        self.Zone_ypos.setValue(top)
        self.Zone_width.setValue(right)
        self.Zone_height.setValue(bottom)

    def HandleSnapTo16x16Grid(self, z):
        """
        Snaps the current zone to a 16x16 grid
        """
        left = self.Zone_xpos.value()
        top = self.Zone_ypos.value()
        right = left + self.Zone_width.value()
        bottom = top + self.Zone_height.value()

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

        if left < 16: left = 16
        if top < 16: top = 16
        if right < 304: right = 304
        if bottom < 208: bottom = 208

        if left > 65520: left = 65520
        if top > 65520: top = 65520
        if right > 65520: right = 65520
        if bottom > 65520: bottom = 65520

        self.Zone_xpos.setValue(left)
        self.Zone_ypos.setValue(top)
        self.Zone_width.setValue(right)
        self.Zone_height.setValue(bottom)

    def createVisibility(self, z):
        self.Visibility = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 19))

        comboboxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        self.Zone_modeldark = QtWidgets.QComboBox()
        self.Zone_modeldark.addItems(globals_.ZoneThemeValues)
        self.Zone_modeldark.setToolTip(globals_.trans.string('ZonesDlg', 21))
        self.Zone_modeldark.setSizePolicy(comboboxSizePolicy)
        if z.modeldark < 0: z.modeldark = 0
        if z.modeldark >= len(globals_.ZoneThemeValues): z.modeldark = len(globals_.ZoneThemeValues) - 1
        self.Zone_modeldark.setCurrentIndex(z.modeldark)

        self.Zone_terraindark = QtWidgets.QComboBox()
        self.Zone_terraindark.addItems(globals_.ZoneTerrainThemeValues)
        self.Zone_terraindark.setToolTip(globals_.trans.string('ZonesDlg', 23))
        self.Zone_terraindark.setSizePolicy(comboboxSizePolicy)
        if z.terraindark < 0: z.terraindark = 0
        if z.terraindark >= len(globals_.ZoneTerrainThemeValues): z.terraindark = len(globals_.ZoneTerrainThemeValues) - 1
        self.Zone_terraindark.setCurrentIndex(z.terraindark)

        self.Zone_vnormal = QtWidgets.QRadioButton(globals_.trans.string('ZonesDlg', 24))
        self.Zone_vnormal.setToolTip(globals_.trans.string('ZonesDlg', 25))

        self.Zone_vspotlight = QtWidgets.QRadioButton(globals_.trans.string('ZonesDlg', 26))
        self.Zone_vspotlight.setToolTip(globals_.trans.string('ZonesDlg', 27))

        self.Zone_vfulldark = QtWidgets.QRadioButton(globals_.trans.string('ZonesDlg', 28))
        self.Zone_vfulldark.setToolTip(globals_.trans.string('ZonesDlg', 29))

        self.Zone_visibility = QtWidgets.QComboBox()

        self.zv = z.visibility
        VRadioDiv = self.zv // 16

        if VRadioDiv == 0:
            self.Zone_vnormal.setChecked(True)
        elif VRadioDiv == 1:
            self.Zone_vspotlight.setChecked(True)
        elif VRadioDiv == 2:
            self.Zone_vfulldark.setChecked(True)
        elif VRadioDiv == 3:
            self.Zone_vfulldark.setChecked(True)

        self.ChangeVisibilityList()
        self.Zone_vnormal.clicked.connect(self.ChangeVisibilityList)
        self.Zone_vspotlight.clicked.connect(self.ChangeVisibilityList)
        self.Zone_vfulldark.clicked.connect(self.ChangeVisibilityList)

        self.zm = -1

        self.Zone_cammodebuttongroup = QtWidgets.QButtonGroup()
        cammodebuttons = []
        for i, name, tooltip in [
                    (0, 'Normal', 'The standard camera mode, appropriate for most situations.'),
                    (3, 'Static Zoom', 'In this mode, the camera will not zoom out during multiplayer.'),
                    (4, 'Static Zoom, Y Tracking Only', 'In this mode, the camera will not zoom out during multiplayer, and will be centered horizontally in the zone.'),
                    (5, 'Static Zoom, Event-Controlled', 'In this mode, the camera will not zoom out during multiplayer, and will use event-controlled camera settings (which currently cannot be edited).'),
                    (6, 'X Tracking Only', 'In this mode, the camera will only move horizontally. It will be aligned to the bottom edge of the zone.'),
                    (7, 'X Expanding Only', 'In this mode, the camera will only zoom out during multiplayer if the players are far apart horizontally.'),
                    (1, 'Y Tracking Only', 'In this mode, the camera will only move vertically. It will be centered horizontally in the zone.'),
                    (2, 'Y Expanding Only', 'In this mode, the camera will zoom out during multiplayer if the players are far apart vertically.'),
                ]:

            rb = QtWidgets.QRadioButton('%d: %s' % (i, name))
            rb.setToolTip('<b>' + name + ':</b><br>' + tooltip)
            self.Zone_cammodebuttongroup.addButton(rb, i)
            cammodebuttons.append(rb)

            if i == z.cammode:
                rb.setChecked(True)

            rb.clicked.connect(self.ChangeCamModeList)

        self.Zone_screenheights = QtWidgets.QComboBox()
        self.Zone_screenheights.setToolTip("<b>Screen Heights:</b><br>Selects screen heights (in blocks) the camera can use during multiplayer. The camera will zoom out if the players are too far apart, and zoom back in when they get closer together. Values represent screen heights, measured in tiles.<br><br>In single-player, only the smallest height will be used.<br><br>Options marked with * or ** are glitchy if zone bounds are set to 0; see the Upper/Lower Bounds tooltips for more info.<br>Options marked with ** are also unplayably glitchy in multiplayer.")
        self.Zone_screenheights.setSizePolicy(comboboxSizePolicy)

        self.ChangeCamModeList()
        self.Zone_screenheights.setCurrentIndex(z.camzoom)

        directionmodeValues = globals_.trans.stringList('ZonesDlg', 38)
        self.Zone_directionmode = QtWidgets.QComboBox()
        self.Zone_directionmode.addItems(directionmodeValues)
        self.Zone_directionmode.setToolTip(globals_.trans.string('ZonesDlg', 40))
        self.Zone_directionmode.setSizePolicy(comboboxSizePolicy)
        if z.camtrack < 0: z.camtrack = 0
        if z.camtrack >= 6: z.camtrack = 6
        idx = z.camtrack / 2
        if z.camtrack == 1: idx = 1
        self.Zone_directionmode.setCurrentIndex(idx)

        # Layouts
        ZoneCameraModesLayout = QtWidgets.QGridLayout()
        for i, b in enumerate(cammodebuttons):
            ZoneCameraModesLayout.addWidget(b, i % 4, i // 4)
        ZoneCameraLayout = QtWidgets.QFormLayout()
        ZoneCameraLayout.addRow('Camera Mode:', ZoneCameraModesLayout)
        ZoneCameraLayout.addRow('Screen Heights:', self.Zone_screenheights)
        ZoneCameraLayout.addRow(globals_.trans.string('ZonesDlg', 20), self.Zone_modeldark)
        ZoneCameraLayout.addRow(globals_.trans.string('ZonesDlg', 22), self.Zone_terraindark)

        ZoneVisibilityLayout = QtWidgets.QHBoxLayout()
        ZoneVisibilityLayout.addWidget(self.Zone_vnormal)
        ZoneVisibilityLayout.addWidget(self.Zone_vspotlight)
        ZoneVisibilityLayout.addWidget(self.Zone_vfulldark)

        ZoneDirectionLayout = QtWidgets.QFormLayout()
        ZoneDirectionLayout.addRow(globals_.trans.string('ZonesDlg', 39), self.Zone_directionmode)

        InnerLayout = QtWidgets.QVBoxLayout()
        InnerLayout.addLayout(ZoneCameraLayout)
        InnerLayout.addLayout(ZoneVisibilityLayout)
        InnerLayout.addWidget(self.Zone_visibility)
        InnerLayout.addLayout(ZoneDirectionLayout)
        self.Visibility.setLayout(InnerLayout)

    def ChangeVisibilityList(self):
        VRadioMod = self.zv % 16

        if self.Zone_vnormal.isChecked():
            self.Zone_visibility.clear()
            addList = globals_.trans.stringList('ZonesDlg', 41)
            self.Zone_visibility.addItems(addList)
            self.Zone_visibility.setToolTip(globals_.trans.string('ZonesDlg', 42))
        elif self.Zone_vspotlight.isChecked():
            self.Zone_visibility.clear()
            addList = globals_.trans.stringList('ZonesDlg', 43)
            self.Zone_visibility.addItems(addList)
            self.Zone_visibility.setToolTip(globals_.trans.string('ZonesDlg', 44))
        elif self.Zone_vfulldark.isChecked():
            self.Zone_visibility.clear()
            addList = globals_.trans.stringList('ZonesDlg', 45)
            self.Zone_visibility.addItems(addList)
            self.Zone_visibility.setToolTip(globals_.trans.string('ZonesDlg', 46))

        # Make sure the selected index exists in the list
        if VRadioMod >= len(addList):
            self.Zone_visibility.setCurrentIndex(0)
            self.zv &= 0xF0 # clear the bottom 4 bits
        else:
            self.Zone_visibility.setCurrentIndex(VRadioMod)

    def ChangeCamModeList(self):
        mode = self.Zone_cammodebuttongroup.checkedId()

        oldListChoice = [1, 1, 2, 3, 3, 3, 1, 1][self.zm]
        newListChoice = [1, 1, 2, 3, 3, 3, 1, 1][mode]

        if self.zm == -1 or oldListChoice != newListChoice:

            if newListChoice == 1:
                heights = [
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
                heights = [
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
                heights = [
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
            for i, (options, asterisk) in enumerate(heights):
                items.append(', '.join(('%04.1f blocks' % o) for o in options) + asterisk)

            self.Zone_screenheights.clear()
            self.Zone_screenheights.addItems(items)
            self.Zone_screenheights.setCurrentIndex(0)
            self.zm = mode

    def createBounds(self, z):
        self.Bounds = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 47))

        self.Zone_yboundup = QtWidgets.QSpinBox()
        self.Zone_yboundup.setRange(-32766, 32767)
        self.Zone_yboundup.setToolTip(globals_.trans.string('ZonesDlg', 49))
        self.Zone_yboundup.setSpecialValueText('32')
        self.Zone_yboundup.setValue(z.yupperbound)

        self.Zone_ybounddown = QtWidgets.QSpinBox()
        self.Zone_ybounddown.setRange(-32766, 32767)
        self.Zone_ybounddown.setToolTip(globals_.trans.string('ZonesDlg', 51))
        self.Zone_ybounddown.setValue(z.ylowerbound)

        self.Zone_yboundup2 = QtWidgets.QSpinBox()
        self.Zone_yboundup2.setRange(-32766, 32767)
        self.Zone_yboundup2.setToolTip(globals_.trans.string('ZonesDlg', 71))
        self.Zone_yboundup2.setValue(z.yupperbound2)

        self.Zone_ybounddown2 = QtWidgets.QSpinBox()
        self.Zone_ybounddown2.setRange(-32766, 32767)
        self.Zone_ybounddown2.setToolTip(globals_.trans.string('ZonesDlg', 73))
        self.Zone_ybounddown2.setValue(z.ylowerbound2)

        self.Zone_boundflg = QtWidgets.QCheckBox()
        self.Zone_boundflg.setToolTip(globals_.trans.string('ZonesDlg', 75))
        self.Zone_boundflg.setChecked(z.unknownbnf == 0xF)

        LA = QtWidgets.QFormLayout()
        LA.addRow(globals_.trans.string('ZonesDlg', 48), self.Zone_yboundup)
        LA.addRow(globals_.trans.string('ZonesDlg', 50), self.Zone_ybounddown)
        LA.addRow(globals_.trans.string('ZonesDlg', 74), self.Zone_boundflg)
        LB = QtWidgets.QFormLayout()
        LB.addRow(globals_.trans.string('ZonesDlg', 70), self.Zone_yboundup2)
        LB.addRow(globals_.trans.string('ZonesDlg', 72), self.Zone_ybounddown2)
        LC = QtWidgets.QGridLayout()
        LC.addLayout(LA, 0, 0)
        LC.addLayout(LB, 0, 1)

        self.Bounds.setLayout(LC)

    def createAudio(self, z):
        self.Audio = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 52))
        self.AutoEditMusic = False

        self.Zone_music = QtWidgets.QComboBox()
        self.Zone_music.setToolTip(globals_.trans.string('ZonesDlg', 54))
        newItems = getMusic()
        for a, b in newItems:
            self.Zone_music.addItem(b, a)  # text, songid
        self.Zone_music.setCurrentIndex(self.Zone_music.findData(z.music))
        self.Zone_music.currentIndexChanged.connect(self.handleMusicListSelect)

        self.Zone_musicid = QtWidgets.QSpinBox()
        self.Zone_musicid.setToolTip(globals_.trans.string('ZonesDlg', 69))
        self.Zone_musicid.setMaximum(255)
        self.Zone_musicid.setValue(z.music)
        self.Zone_musicid.valueChanged.connect(self.handleMusicIDChange)

        self.Zone_sfx = QtWidgets.QComboBox()
        self.Zone_sfx.setToolTip(globals_.trans.string('ZonesDlg', 56))
        newItems3 = globals_.trans.stringList('ZonesDlg', 57)
        self.Zone_sfx.addItems(newItems3)
        self.Zone_sfx.setCurrentIndex(z.sfxmod / 16)

        self.Zone_boss = QtWidgets.QCheckBox()
        self.Zone_boss.setToolTip(globals_.trans.string('ZonesDlg', 59))
        self.Zone_boss.setChecked(z.sfxmod % 16)

        ZoneAudioLayout = QtWidgets.QFormLayout()
        ZoneAudioLayout.addRow(globals_.trans.string('ZonesDlg', 53), self.Zone_music)
        ZoneAudioLayout.addRow(globals_.trans.string('ZonesDlg', 68), self.Zone_musicid)
        ZoneAudioLayout.addRow(globals_.trans.string('ZonesDlg', 55), self.Zone_sfx)
        ZoneAudioLayout.addRow(globals_.trans.string('ZonesDlg', 58), self.Zone_boss)

        self.Audio.setLayout(ZoneAudioLayout)

    def handleMusicListSelect(self):
        """
        Handles the user selecting an entry from the music list
        """
        if self.AutoEditMusic: return
        id = self.Zone_music.itemData(self.Zone_music.currentIndex())
        id = int(str(id))  # id starts out as a QString

        self.AutoEditMusic = True
        self.Zone_musicid.setValue(id)
        self.AutoEditMusic = False

    def handleMusicIDChange(self):
        """
        Handles the user selecting a custom music ID
        """
        if self.AutoEditMusic: return
        id = self.Zone_musicid.value()

        # BUG: The music entries are out of order

        self.AutoEditMusic = True
        self.Zone_music.setCurrentIndex(self.Zone_music.findData(id))
        self.AutoEditMusic = False

    def PresetSelected(self, info=None):
        """
        Handles a zone size preset being selected
        """
        if self.AutoChangingSize: return

        if self.Zone_presets.currentText() == globals_.trans.string('ZonesDlg', 60): return
        w, h = self.Zone_presets.currentText()[3:].split('x')

        self.AutoChangingSize = True
        self.Zone_width.setValue(int(w))
        self.Zone_height.setValue(int(h))
        self.AutoChangingSize = False

        if self.Zone_presets.itemText(0) == globals_.trans.string('ZonesDlg', 60): self.Zone_presets.removeItem(0)

    def PresetDeselected(self, info=None):
        """
        Handles the zone height or width boxes being changed
        """
        if self.AutoChangingSize: return

        self.AutoChangingSize = True
        w = self.Zone_width.value()
        h = self.Zone_height.value()
        check = str(w) + 'x' + str(h)

        found = None
        for preset in self.Zone_presets_values:
            if check == preset[3:]: found = preset

        if found is not None:
            self.Zone_presets.setCurrentIndex(self.Zone_presets.findText(found))
            if self.Zone_presets.itemText(0) == globals_.trans.string('ZonesDlg', 60): self.Zone_presets.removeItem(0)
        else:
            if self.Zone_presets.itemText(0) != globals_.trans.string('ZonesDlg', 60): self.Zone_presets.insertItem(0,
                                                                                                           globals_.trans.string(
                                                                                                               'ZonesDlg',
                                                                                                               60))
            self.Zone_presets.setCurrentIndex(0)
        self.AutoChangingSize = False


def getMusic():
    """
    Uses the current gamedef + translation to get the music data, and returns it as a list of tuples
    """

    transsong = globals_.trans.files['music']
    gamedefsongs, isPatch = globals_.gamedef.recursiveFiles('music', True)
    if isPatch:
        paths = [transsong]
        for path in gamedefsongs: paths.append(path)
    else:
        paths = gamedefsongs

    songs = []
    for path in paths:
        musicfile = open(path)
        data = musicfile.read()
        musicfile.close()
        del musicfile

        # Split the data
        data = data.split('\n')
        while '' in data: data.remove('')
        for i, line in enumerate(data): data[i] = line.split(':')

        # Apply it
        for songid, name in data:
            found = False
            for song in songs:
                if song[0] == songid:
                    song[1] = name
                    found = True
            if not found:
                songs.append([songid, name])

    return sorted(songs, key=lambda song: int(song[0]))

