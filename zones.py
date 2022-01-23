from PyQt5 import QtWidgets, QtCore

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
        self.zoneTabs = []

        num_zones = len(globals_.Area.zones)

        for i, z in enumerate(globals_.Area.zones):
            if num_zones <= 5:
                zone_tab_name = globals_.trans.string('ZonesDlg', 3, '[num]', z.id + 1)
            else:
                zone_tab_name = str(z.id + 1)

            tab = ZoneTab(z)
            self.zoneTabs.append(tab)
            self.tabWidget.addTab(tab, zone_tab_name)

        self.NewButton = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 4))
        self.DeleteButton = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 5))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.addButton(self.NewButton, buttonBox.ActionRole)
        buttonBox.addButton(self.DeleteButton, buttonBox.ActionRole)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.NewButton.clicked.connect(self.NewZone)
        self.DeleteButton.clicked.connect(self.DeleteZone)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def NewZone(self):
        if len(self.zoneTabs) >= 6:
            result = QtWidgets.QMessageBox.warning(self, globals_.trans.string('ZonesDlg', 6), globals_.trans.string('ZonesDlg', 7),
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No:
                return

        z = globals_.mainWindow.CreateZone(256, 256)

        if len(self.zoneTabs) + 1 <= 5:
            zone_tab_name = globals_.trans.string('ZonesDlg', 3, '[num]', z.id + 1)
        else:
            zone_tab_name = str(z.id + 1)

        tab = ZoneTab(z)
        self.zoneTabs.append(tab)
        self.tabWidget.addTab(tab, zone_tab_name)

        tab_amount = self.tabWidget.count()
        self.tabWidget.setCurrentIndex(tab_amount - 1)

        # Re-label zone tabs. This is only needed if the number of zones grows
        # above 5, as the long names need to be replaced by short names. Since
        # this function always adds a zone, it can never happen that the short
        # name needs to be lengthened.
        if tab_amount != 6:
            return

        # No need to do the last one, since that's the one we just added, and
        # we already set that correctly.
        for tab in range(tab_amount - 1):
            widget = self.tabWidget.widget(tab)

            if widget is None:
                break

            zone_id = widget.zoneObj.id
            self.tabWidget.setTabText(tab, str(zone_id + 1))

    def DeleteZone(self):
        index = self.tabWidget.currentIndex()
        tab_amount = self.tabWidget.count()
        if tab_amount == 0:
            return

        self.tabWidget.removeTab(index)
        self.zoneTabs.pop(index)

        new_tab_amount = tab_amount - 1

        # Re-label zone tabs. This is only needed if the number of zones drops
        # below 5, as the short names need to be replaced by long names. Since
        # this function always removes zones, it can never happen that the long
        # name needs to be shortened.
        if new_tab_amount != 5:
            return

        for tab in range(new_tab_amount):
            widget = self.tabWidget.widget(tab)

            if widget is None:
                break

            zone_id = widget.zoneObj.id
            self.tabWidget.setTabText(tab, globals_.trans.string('ZonesDlg', 3, '[num]', zone_id + 1))

class ZoneTab(QtWidgets.QWidget):
    def __init__(self, z):
        QtWidgets.QWidget.__init__(self)

        self.zoneObj = z
        self.AutoChangingSize = False

        self.createDimensions(z)
        self.createRendering(z)
        self.createAudio(z)

        self.createCamera(z)
        self.createBounds(z)

        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.addWidget(self.Dimensions)
        leftLayout.addWidget(self.Rendering)
        leftLayout.addWidget(self.Audio)

        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(self.Camera)
        rightLayout.addWidget(self.Bounds)

        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.addLayout(leftLayout)
        mainLayout.addLayout(rightLayout)
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
        # 416 x 224 (used with minigames)
        # 448 x 224 (used with boss battles)
        # 512 x 272 (used in many, many places)
        # 560 x 304
        # 608 x 320 (actually 609x320; rounded it down myself)
        # 784 x 320 (not added to list because it's just an expansion of 608x320)
        # 704 x 384 (used multiple times; therefore it's important)
        # 944 x 448 (used in 9-3 zone 3)
        self.Zone_presets_values = (
            '416x224', '448x224', '512x272', '560x304', '608x320', '704x384', '944x448'
        )

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

    def createRendering(self, z):
        self.Rendering = QtWidgets.QGroupBox('Rendering')

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

        self.Zone_vspotlight = QtWidgets.QCheckBox(globals_.trans.string('ZonesDlg', 26))
        self.Zone_vspotlight.setToolTip(globals_.trans.string('ZonesDlg', 27))

        self.Zone_vfulldark = QtWidgets.QCheckBox(globals_.trans.string('ZonesDlg', 28))
        self.Zone_vfulldark.setToolTip(globals_.trans.string('ZonesDlg', 29))

        self.Zone_visibility = QtWidgets.QComboBox()

        self.zv = z.visibility

        self.Zone_vspotlight.setChecked(self.zv & 0x10)
        self.Zone_vfulldark.setChecked(self.zv & 0x20)

        self.ChangeVisibilityList()
        self.Zone_vspotlight.clicked.connect(self.ChangeVisibilityList)
        self.Zone_vfulldark.clicked.connect(self.ChangeVisibilityList)

        ZoneRenderingLayout = QtWidgets.QFormLayout()
        ZoneRenderingLayout.addRow(globals_.trans.string('ZonesDlg', 20), self.Zone_modeldark)
        ZoneRenderingLayout.addRow(globals_.trans.string('ZonesDlg', 22), self.Zone_terraindark)

        ZoneVisibilityLayout = QtWidgets.QHBoxLayout()
        ZoneVisibilityLayout.addWidget(self.Zone_vspotlight)
        ZoneVisibilityLayout.addWidget(self.Zone_vfulldark)

        InnerLayout = QtWidgets.QVBoxLayout()
        InnerLayout.addLayout(ZoneRenderingLayout)
        InnerLayout.addLayout(ZoneVisibilityLayout)
        InnerLayout.addWidget(self.Zone_visibility)
        self.Rendering.setLayout(InnerLayout)

    def createCamera(self, z):
        self.Camera = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 19))

        comboboxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        self.Zone_cammodezoom = CameraModeZoomSettingsLayout(True)
        self.Zone_cammodezoom.setValues(z.cammode, z.camzoom)

        dirs = globals_.trans.stringList('ZonesDlg', 38)
        self.Zone_direction = QtWidgets.QComboBox()
        self.Zone_direction.addItems(dirs)
        self.Zone_direction.setToolTip(globals_.trans.string('ZonesDlg', 40))
        self.Zone_direction.setSizePolicy(comboboxSizePolicy)
        if z.camtrack < 0: z.camtrack = 0
        if z.camtrack >= len(dirs): z.camtrack = len(dirs) - 1
        self.Zone_direction.setCurrentIndex(z.camtrack)

        self.Zone_yrestrict = QtWidgets.QCheckBox()
        self.Zone_yrestrict.setToolTip(globals_.trans.string('ZonesDlg', 78))
        self.Zone_yrestrict.setChecked(z.mpcamzoomadjust != 15)
        self.Zone_yrestrict.stateChanged.connect(self.ChangeMPZoomAdjust)

        self.Zone_mpzoomadjust = QtWidgets.QSpinBox()
        self.Zone_mpzoomadjust.setRange(0, 14)
        self.Zone_mpzoomadjust.setToolTip(globals_.trans.string('ZonesDlg', 79))

        self.ChangeMPZoomAdjust()
        if z.mpcamzoomadjust < 15:
            self.Zone_mpzoomadjust.setValue(z.mpcamzoomadjust)

        # Layouts
        ZoneCameraLayout = QtWidgets.QFormLayout()
        ZoneCameraLayout.addRow(self.Zone_cammodezoom)
        ZoneCameraLayout.addRow(globals_.trans.string('ZonesDlg', 39), self.Zone_direction)
        ZoneCameraLayout.addRow(globals_.trans.string('ZonesDlg', 80), self.Zone_yrestrict)
        ZoneCameraLayout.addRow(globals_.trans.string('ZonesDlg', 81), self.Zone_mpzoomadjust)

        self.Camera.setLayout(ZoneCameraLayout)

    def ChangeVisibilityList(self):
        add_idx = 0

        if self.Zone_vfulldark.isChecked():
            if self.Zone_vspotlight.isChecked():
                add_idx = 82
            else:
                add_idx = 45
        else:
            if self.Zone_vspotlight.isChecked():
                add_idx = 43
            else:
                add_idx = 41

        add_list = globals_.trans.stringList('ZonesDlg', add_idx)

        self.Zone_visibility.clear()
        self.Zone_visibility.addItems(add_list)
        self.Zone_visibility.setToolTip(globals_.trans.string('ZonesDlg', add_idx + 1))

        choice = min(self.zv & 0xF, len(add_list) - 1)
        self.Zone_visibility.setCurrentIndex(choice)

    def ChangeMPZoomAdjust(self):
        self.Zone_mpzoomadjust.setEnabled(self.Zone_yrestrict.isChecked())
        self.Zone_mpzoomadjust.setValue(0)

    def createBounds(self, z):
        self.Bounds = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 47))

        self.Zone_yboundup = QtWidgets.QSpinBox()
        self.Zone_yboundup.setRange(-32768, 32767)
        self.Zone_yboundup.setToolTip(globals_.trans.string('ZonesDlg', 49))
        self.Zone_yboundup.setSpecialValueText('32')
        self.Zone_yboundup.setValue(z.yupperbound)

        self.Zone_ybounddown = QtWidgets.QSpinBox()
        self.Zone_ybounddown.setRange(-32768, 32767)
        self.Zone_ybounddown.setToolTip(globals_.trans.string('ZonesDlg', 51))
        self.Zone_ybounddown.setValue(z.ylowerbound)

        self.Zone_yboundup2 = QtWidgets.QSpinBox()
        self.Zone_yboundup2.setRange(-32768, 32767)
        self.Zone_yboundup2.setToolTip(globals_.trans.string('ZonesDlg', 71))
        self.Zone_yboundup2.setValue(z.yupperbound2)

        self.Zone_ybounddown2 = QtWidgets.QSpinBox()
        self.Zone_ybounddown2.setRange(-32768, 32767)
        self.Zone_ybounddown2.setToolTip(globals_.trans.string('ZonesDlg', 73))
        self.Zone_ybounddown2.setValue(z.ylowerbound2)

        self.Zone_yboundup3 = QtWidgets.QSpinBox()
        self.Zone_yboundup3.setRange(-32768, 32767)
        self.Zone_yboundup3.setToolTip('<b>Multiplayer Upper Bounds Adjust:</b><br>Added to the upper bounds value (regular or Lakitu) during multiplayer mode, and during the transition back to normal camera behavior after an Auto-Scrolling Controller reaches the end of its path.')
        self.Zone_yboundup3.setSpecialValueText('32')
        self.Zone_yboundup3.setValue(z.yupperbound3)

        self.Zone_ybounddown3 = QtWidgets.QSpinBox()
        self.Zone_ybounddown3.setRange(-32768, 32767)
        self.Zone_ybounddown3.setToolTip('<b>Multiplayer Lower Bounds Adjust:</b><br>Added to the lower bounds value (regular or Lakitu) during multiplayer mode, and during the transition back to normal camera behavior after an Auto-Scrolling Controller reaches the end of its path.')
        self.Zone_ybounddown3.setValue(z.ylowerbound3)

        LA = QtWidgets.QFormLayout()
        LA.addRow(globals_.trans.string('ZonesDlg', 48), self.Zone_yboundup)
        LA.addRow(globals_.trans.string('ZonesDlg', 50), self.Zone_ybounddown)

        LB = QtWidgets.QFormLayout()
        LB.addRow(globals_.trans.string('ZonesDlg', 70), self.Zone_yboundup2)
        LB.addRow(globals_.trans.string('ZonesDlg', 72), self.Zone_ybounddown2)

        LC = QtWidgets.QHBoxLayout()
        LC.addLayout(LA)
        LC.addLayout(LB)

        LD = QtWidgets.QFormLayout()
        LD.addRow(LC)
        LD.addRow('Multiplayer Upper Bounds Adjust:', self.Zone_yboundup3)
        LD.addRow('Multiplayer Lower Bounds Adjust:', self.Zone_ybounddown3)

        self.Bounds.setLayout(LD)

    def createAudio(self, z):
        self.Audio = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 52))
        self.AutoEditMusic = False

        self.Zone_music = QtWidgets.QComboBox()
        self.Zone_music.setToolTip(globals_.trans.string('ZonesDlg', 54))
        for songid, text in getMusic():
            self.Zone_music.addItem(text, songid)
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
        self.Zone_sfx.setCurrentIndex(z.sfxmod // 16)

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
        w, h = self.Zone_presets.currentText().split('x')

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

        custom_size_name = globals_.trans.string('ZonesDlg', 60)

        try:
            idx = self.Zone_presets_values.index(check)
        except ValueError:
            idx = -1

        if idx == -1:
            if self.Zone_presets.itemText(0) != custom_size_name:
                self.Zone_presets.insertItem(0, custom_size_name)

            idx = 0

        elif self.Zone_presets.itemText(0) == custom_size_name:
            self.Zone_presets.removeItem(0)

        self.Zone_presets.setCurrentIndex(idx)
        self.AutoChangingSize = False


class CameraModeZoomSettingsLayout(QtWidgets.QFormLayout):
    """
    A layout that shows the camera mode / zoom settings for editing.
    """
    edited = QtCore.pyqtSignal()
    updating = False

    def __init__(self, show_mode_5):
        super().__init__()
        self.updating = True

        comboboxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        self.zm = -1

        self.modeButtonGroup = QtWidgets.QButtonGroup()
        modebuttons = []
        for i, name, tooltip in [
                    (0, 'Normal', 'The standard camera mode, appropriate for most situations.'),
                    (3, 'Static Zoom', 'In this mode, the camera will not zoom out during multiplayer.'),
                    (4, 'Static Zoom, Y Tracking Only', 'In this mode, the camera will not zoom out during multiplayer, and will be centered horizontally in the zone.'),
                    (5, 'Static Zoom, Event-Controlled', 'In this mode, the camera will not zoom out during multiplayer, and will use event-controlled camera settings from the Camera Profiles dialog.'),
                    (6, 'X Tracking Only', 'In this mode, the camera will only move horizontally. It will be aligned to the bottom edge of the zone.'),
                    (7, 'X Expanding Only', 'In this mode, the camera will only zoom out during multiplayer if the players are far apart horizontally.'),
                    (1, 'Y Tracking Only', 'In this mode, the camera will only move vertically. It will be centered horizontally in the zone.'),
                    (2, 'Y Expanding Only', 'In this mode, the camera will zoom out during multiplayer if the players are far apart vertically. The largest screen size will only be used if a player is flying with a Propeller Suit or Block.'),
                ]:
            rb = QtWidgets.QRadioButton(name)
            rb.setToolTip('<b>' + name + ':</b><br>' + tooltip)
            self.modeButtonGroup.addButton(rb, i)
            modebuttons.append(rb)

            if i == 5 and not show_mode_5:
                rb.setVisible(False)

            rb.clicked.connect(self.ChangeCamModeList)
            rb.clicked.connect(self.handleModeChanged)

        self.screenSizes = QtWidgets.QComboBox()
        self.screenSizes.setToolTip("<b>Screen Heights:</b><br>Selects screen heights (in blocks) the camera can use during multiplayer. The camera will zoom out if the players are too far apart, and zoom back in when they get closer together. Values represent screen heights, measured in tiles.<br><br>In single-player, only the smallest height will be used.<br><br>Options marked with * or ** are glitchy if zone bounds are set to 0; see the Upper/Lower Bounds tooltips for more info.<br>Options marked with ** are also unplayably glitchy in multiplayer.")
        self.screenSizes.setSizePolicy(comboboxSizePolicy)

        self.screenSizes.currentIndexChanged.connect(self.handleScreenSizesChanged)

        ModesLayout = QtWidgets.QGridLayout()
        for i, b in enumerate(modebuttons):
            ModesLayout.addWidget(b, i % 4, i // 4)

        self.addRow(ModesLayout)
        self.addRow('Screen Heights:', self.screenSizes)

        self.updating = False

    def ChangeCamModeList(self):
        mode = self.modeButtonGroup.checkedId()
        oldListChoice = [1, 1, 2, 3, 3, 3, 1, 1][self.zm]
        newListChoice = [1, 1, 2, 3, 3, 3, 1, 1][mode]

        if self.zm != -1 and oldListChoice == newListChoice:
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
        self.zm = mode

    def setValues(self, cammode, camzoom):
        self.updating = True

        if cammode < 0: cammode = 0
        if cammode >= 8: cammode = 7

        self.modeButtonGroup.button(cammode).setChecked(True)
        self.ChangeCamModeList()

        if camzoom < 0: camzoom = 0
        if camzoom >= self.screenSizes.count(): camzoom = self.screenSizes.count() - 1

        self.screenSizes.setCurrentIndex(camzoom)

        self.updating = False

    def handleModeChanged(self):
        if self.updating: return
        self.ChangeCamModeList()
        self.edited.emit()

    def handleScreenSizesChanged(self):
        if self.updating: return
        self.edited.emit()


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

