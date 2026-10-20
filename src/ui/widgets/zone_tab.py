from PyQt6 import QtWidgets

from data import globals_
from data.common.utils import clamp
from data.level.items.zone import ZoneItem
from ui.layouts.camera_settings import CameraSettingsLayout

class ZoneTab(QtWidgets.QWidget):
    """
    Represents an individial zone within the Zones Dialog
    """

    def __init__(self, zone: ZoneItem) -> None:
        super().__init__()

        self.zone_obj = zone
        self.auto_change_size = False

        # Create the different sections of the tab
        self.create_dimensions(zone)
        self.create_rendering(zone)
        self.create_audio(zone)

        self.create_camera(zone)
        self.create_bounds(zone)

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(self.dimensions)
        left_layout.addWidget(self.rendering)
        left_layout.addWidget(self.audio)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self.camera)
        right_layout.addWidget(self.bounds)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def create_dimensions(self, zone: ZoneItem) -> None:
        """
        Creates the "Dimensions" section of the tab
        """
        self.dimensions = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 8))

        self.pos_x = QtWidgets.QSpinBox()
        self.pos_x.setRange(16, 65535)
        self.pos_x.setToolTip(globals_.trans.string('ZonesDlg', 10))
        self.pos_x.setValue(zone.objx)

        self.pos_y = QtWidgets.QSpinBox()
        self.pos_y.setRange(16, 65535)
        self.pos_y.setToolTip(globals_.trans.string('ZonesDlg', 12))
        self.pos_y.setValue(zone.objy)

        self.snap_half_grid_btn = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 76))
        self.snap_half_grid_btn.clicked.connect(lambda: self.snap_to_grid(True))

        self.snap_grid_btn = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 77))
        self.snap_grid_btn.clicked.connect(lambda: self.snap_to_grid(False))

        self.zone_width = QtWidgets.QSpinBox()
        self.zone_width.setRange(204, 65535)
        self.zone_width.setToolTip(globals_.trans.string('ZonesDlg', 14))
        self.zone_width.setValue(zone.width)
        self.zone_width.valueChanged.connect(self.preset_changed)

        self.zone_height = QtWidgets.QSpinBox()
        self.zone_height.setRange(112, 65535)
        self.zone_height.setToolTip(globals_.trans.string('ZonesDlg', 16))
        self.zone_height.setValue(zone.height)
        self.zone_height.valueChanged.connect(self.preset_changed)

        # Common retail zone presets:
        # 416 x 224 (used with minigames)
        # 448 x 224 (used with boss battles)
        # 512 x 272 (used in many, many places)
        # 560 x 304
        # 608 x 320 (actually 609x320; rounded it down myself)
        # 784 x 320 (not added to list because it's just an expansion of 608x320)
        # 704 x 384 (used multiple times; therefore it's important)
        # 944 x 448 (used in 9-3 zone 3)
        self.size_presets = (
            '204x112', '308x168', '408x224', '468x256',
            '496x272', '556x304', '584x320', '700x384', '816x448'
        )

        self.preset_chooser = QtWidgets.QComboBox()
        self.preset_chooser.addItems(self.size_presets)
        self.preset_chooser.setToolTip(globals_.trans.string('ZonesDlg', 18))
        self.preset_chooser.currentIndexChanged.connect(self.select_preset)

        # Initialize self.preset_chooser
        self.preset_changed()

        pos_layout = QtWidgets.QFormLayout()
        pos_layout.addRow(globals_.trans.string('ZonesDlg', 9), self.pos_x)
        pos_layout.addRow(globals_.trans.string('ZonesDlg', 11), self.pos_y)

        size_layout = QtWidgets.QFormLayout()
        size_layout.addRow(globals_.trans.string('ZonesDlg', 13), self.zone_width)
        size_layout.addRow(globals_.trans.string('ZonesDlg', 15), self.zone_height)
        size_layout.addRow(globals_.trans.string('ZonesDlg', 17), self.preset_chooser)

        snap_layout = QtWidgets.QHBoxLayout()
        snap_layout.addWidget(self.snap_half_grid_btn)
        snap_layout.addWidget(self.snap_grid_btn)

        pos_size_layout = QtWidgets.QHBoxLayout()
        pos_size_layout.addLayout(pos_layout)
        pos_size_layout.addLayout(size_layout)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(pos_size_layout)
        main_layout.addLayout(snap_layout)

        self.dimensions.setLayout(main_layout)

    def create_rendering(self, zone: ZoneItem) -> None:
        """
        Creates the "Rendering" section of the tab
        """
        self.rendering = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 84))

        combobox_size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed)

        terrain_light_values = globals_.trans.stringList('ZonesDlg', 2)

        self.theme = QtWidgets.QComboBox()
        self.theme.setSizePolicy(combobox_size_policy)
        self.theme.currentIndexChanged.connect(self.set_zone_theme)

        for theme in globals_.ZoneThemes:
            self.theme.addItem(theme.name, theme.idx)

        zone.modeldark = clamp(zone.modeldark, 0, len(globals_.ZoneThemes))
        self.theme.setCurrentIndex(zone.modeldark)

        self.terrain_light = QtWidgets.QComboBox()
        self.terrain_light.addItems(terrain_light_values)
        self.terrain_light.setToolTip(globals_.trans.string('ZonesDlg', 23))
        self.terrain_light.setSizePolicy(combobox_size_policy)

        if terrain_light_values is not None:
            zone.terraindark = clamp(zone.terraindark, 0, len(terrain_light_values))
        self.terrain_light.setCurrentIndex(zone.terraindark)

        self.spotlight = QtWidgets.QCheckBox(globals_.trans.string('ZonesDlg', 26))
        self.spotlight.setToolTip(globals_.trans.string('ZonesDlg', 27))

        self.full_dark = QtWidgets.QCheckBox(globals_.trans.string('ZonesDlg', 28))
        self.full_dark.setToolTip(globals_.trans.string('ZonesDlg', 29))

        self.visibility = QtWidgets.QComboBox()

        self.vis = zone.visibility

        self.spotlight.setChecked(bool(self.vis & 0x10))
        self.full_dark.setChecked(bool(self.vis & 0x20))

        self.set_visibility_list()
        self.spotlight.clicked.connect(self.set_visibility_list)
        self.full_dark.clicked.connect(self.set_visibility_list)

        render_layout = QtWidgets.QFormLayout()
        render_layout.addRow(globals_.trans.string('ZonesDlg', 20), self.theme)
        render_layout.addRow(globals_.trans.string('ZonesDlg', 22), self.terrain_light)

        visibility_layout = QtWidgets.QHBoxLayout()
        visibility_layout.addWidget(self.spotlight)
        visibility_layout.addWidget(self.full_dark)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(render_layout)
        main_layout.addLayout(visibility_layout)
        main_layout.addWidget(self.visibility)
        self.rendering.setLayout(main_layout)

    def create_audio(self, zone: ZoneItem) -> None:
        """
        Creates the "Audio" section of the tab
        """
        self.audio = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 52))
        self.auto_edit_music = False

        self.music_list = QtWidgets.QComboBox()
        self.music_list.setToolTip(globals_.trans.string('ZonesDlg', 54))

        for song_id, text in globals_.MusicInfo:
            if int(song_id) > 255:
                continue

            self.music_list.addItem(text, song_id)

        self.music_list.setCurrentIndex(self.music_list.findData(zone.music))
        self.music_list.currentIndexChanged.connect(self.set_music_list)

        # Show 'Undefined Track XX' if there's no list item to show
        if self.music_list.findData(zone.music) == -1:
            self.music_list.setPlaceholderText(globals_.trans.string('ZonesDlg', 108, '[id]', str(zone.music)))

        self.music_id = QtWidgets.QSpinBox()
        self.music_id.setToolTip(globals_.trans.string('ZonesDlg', 69))
        self.music_id.setMaximum(255)
        self.music_id.setValue(zone.music)
        self.music_id.valueChanged.connect(self.set_music_id)

        self.modulation = QtWidgets.QComboBox()
        self.modulation.setToolTip(globals_.trans.string('ZonesDlg', 56))

        modulation_list = globals_.trans.stringList('ZonesDlg', 57)
        self.modulation.addItems(modulation_list)
        self.modulation.setCurrentIndex(zone.sfxmod // 16)

        self.boss_flag = QtWidgets.QCheckBox()
        self.boss_flag.setToolTip(globals_.trans.string('ZonesDlg', 59))
        self.boss_flag.setChecked(bool(zone.sfxmod % 16))

        main_layout = QtWidgets.QFormLayout()
        main_layout.addRow(globals_.trans.string('ZonesDlg', 53), self.music_list)
        main_layout.addRow(globals_.trans.string('ZonesDlg', 68), self.music_id)
        main_layout.addRow(globals_.trans.string('ZonesDlg', 55), self.modulation)
        main_layout.addRow(globals_.trans.string('ZonesDlg', 58), self.boss_flag)
        self.audio.setLayout(main_layout)

    def create_camera(self, zone: ZoneItem) -> None:
        """
        Creates the "Camera" section of the tab
        """
        self.camera = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 19))

        combobox_size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed)

        self.cam_settings = CameraSettingsLayout(True)
        self.cam_settings.set_values(zone.cammode, zone.camzoom)

        dirs = globals_.trans.stringList('ZonesDlg', 38)
        self.direction = QtWidgets.QComboBox()
        self.direction.addItems(dirs)
        self.direction.setToolTip(globals_.trans.string('ZonesDlg', 40))
        self.direction.setSizePolicy(combobox_size_policy)

        if dirs is not None:
            zone.camtrack = clamp(zone.camtrack, 0, len(dirs) - 1)
        self.direction.setCurrentIndex(zone.camtrack)

        self.restrict_y = QtWidgets.QCheckBox()
        self.restrict_y.setToolTip(globals_.trans.string('ZonesDlg', 78))
        self.restrict_y.setChecked(zone.mpcamzoomadjust != 15)
        self.restrict_y.stateChanged.connect(self.set_mp_zoom_adjust)

        self.mp_zoom_adjust = QtWidgets.QSpinBox()
        self.mp_zoom_adjust.setRange(0, 14)
        self.mp_zoom_adjust.setToolTip(globals_.trans.string('ZonesDlg', 79))

        self.set_mp_zoom_adjust()
        if zone.mpcamzoomadjust < 15:
            self.mp_zoom_adjust.setValue(zone.mpcamzoomadjust)

        main_layout = QtWidgets.QFormLayout()
        main_layout.addRow(self.cam_settings)
        main_layout.addRow(globals_.trans.string('ZonesDlg', 39), self.direction)
        main_layout.addRow(globals_.trans.string('ZonesDlg', 80), self.restrict_y)
        main_layout.addRow(globals_.trans.string('ZonesDlg', 81), self.mp_zoom_adjust)
        self.camera.setLayout(main_layout)

    def create_bounds(self, zone: ZoneItem) -> None:
        """
        Creates the "Bounds" section of the tab
        """
        self.bounds = QtWidgets.QGroupBox(globals_.trans.string('ZonesDlg', 47))

        self.bound_up = QtWidgets.QSpinBox()
        self.bound_up.setRange(-32768, 32767)
        self.bound_up.setToolTip(globals_.trans.string('ZonesDlg', 49))
        self.bound_up.setSpecialValueText('32')
        self.bound_up.setValue(zone.yupperbound)

        self.bound_down = QtWidgets.QSpinBox()
        self.bound_down.setRange(-32768, 32767)
        self.bound_down.setToolTip(globals_.trans.string('ZonesDlg', 51))
        self.bound_down.setValue(zone.ylowerbound)

        self.lakitu_bound_up = QtWidgets.QSpinBox()
        self.lakitu_bound_up.setRange(-32768, 32767)
        self.lakitu_bound_up.setToolTip(globals_.trans.string('ZonesDlg', 71))
        self.lakitu_bound_up.setValue(zone.yupperbound2)

        self.lakitu_bound_down = QtWidgets.QSpinBox()
        self.lakitu_bound_down.setRange(-32768, 32767)
        self.lakitu_bound_down.setToolTip(globals_.trans.string('ZonesDlg', 73))
        self.lakitu_bound_down.setValue(zone.ylowerbound2)

        self.mp_bound_up = QtWidgets.QSpinBox()
        self.mp_bound_up.setRange(-32768, 32767)
        self.mp_bound_up.setToolTip(globals_.trans.string('ZonesDlg', 104))
        self.mp_bound_up.setSpecialValueText('32')
        self.mp_bound_up.setValue(zone.yupperbound3)

        self.mp_bound_down = QtWidgets.QSpinBox()
        self.mp_bound_down.setRange(-32768, 32767)
        self.mp_bound_down.setToolTip(globals_.trans.string('ZonesDlg', 106))
        self.mp_bound_down.setValue(zone.ylowerbound3)

        bound_layout = QtWidgets.QFormLayout()
        bound_layout.addRow(globals_.trans.string('ZonesDlg', 48), self.bound_up)
        bound_layout.addRow(globals_.trans.string('ZonesDlg', 50), self.bound_down)

        lakitu_bound_layout = QtWidgets.QFormLayout()
        lakitu_bound_layout.addRow(globals_.trans.string('ZonesDlg', 70), self.lakitu_bound_up)
        lakitu_bound_layout.addRow(globals_.trans.string('ZonesDlg', 72), self.lakitu_bound_down)

        bound_combined_layout = QtWidgets.QHBoxLayout()
        bound_combined_layout.addLayout(bound_layout)
        bound_combined_layout.addLayout(lakitu_bound_layout)

        main_layout = QtWidgets.QFormLayout()
        main_layout.addRow(bound_combined_layout)
        main_layout.addRow(globals_.trans.string('ZonesDlg', 103), self.mp_bound_up)
        main_layout.addRow(globals_.trans.string('ZonesDlg', 105), self.mp_bound_down)
        self.bounds.setLayout(main_layout)

    def snap_to_grid(self, is_half_grid: bool) -> None:
        """
        Snaps the current zone to an 8x8 or 16x16 grid
        """
        # Snapping code is the same besides these values being different
        if is_half_grid:
            unit = 8
            round_check = 4
            clamp_max = 65528
            bottom_min = 200
        else:
            unit = 16
            round_check = 8
            clamp_max = 65520
            bottom_min = 208

        left = self.pos_x.value()
        top = self.pos_y.value()
        right = left + self.zone_width.value()
        bottom = top + self.zone_height.value()

        if left % unit < round_check:
            left -= (left % unit)
        else:
            left += unit - (left % unit)

        if top % unit < round_check:
            top -= (top % unit)
        else:
            top += unit - (top % unit)

        if right % unit < round_check:
            right -= (right % unit)
        else:
            right += unit - (right % unit)

        if bottom % unit < round_check:
            bottom -= (bottom % unit)
        else:
            bottom += unit - (bottom % unit)

        if right <= left:
            right += unit
        if bottom <= top:
            bottom += unit

        right -= left
        bottom -= top

        # Keep zone size within reasonable bounds
        left = clamp(left, 16, clamp_max)
        top = clamp(top, 16, clamp_max)
        right = clamp(right, 304, clamp_max)
        bottom = clamp(bottom, bottom_min, clamp_max)

        self.pos_x.setValue(left)
        self.pos_y.setValue(top)
        self.zone_width.setValue(right)
        self.zone_height.setValue(bottom)

    def set_zone_theme(self) -> None:
        """
        Handles changing the current Zone theme
        """
        tooltip = globals_.trans.string('ZonesDlg', 21)
        theme_comment = ''

        curr_theme = globals_.ZoneThemes[self.theme.currentIndex()]
        if curr_theme.desc is not None:
            theme_comment = globals_.trans.string('ZonesDlg', 109, '[info]', curr_theme.desc)

        self.theme.setToolTip(f'{tooltip}{theme_comment}')

    def set_visibility_list(self) -> None:
        """
        Handles changing the visibility type list
        """
        add_idx = 0

        # Figure out which set of options to show
        if self.full_dark.isChecked():
            if self.spotlight.isChecked():
                add_idx = 82
            else:
                add_idx = 45
        else:
            if self.spotlight.isChecked():
                add_idx = 43
            else:
                add_idx = 41

        add_list = globals_.trans.stringList('ZonesDlg', add_idx)

        self.visibility.clear()
        self.visibility.addItems(add_list)
        self.visibility.setToolTip(globals_.trans.string('ZonesDlg', add_idx + 1))

        if add_list is not None:
            choice = min(self.vis & 0xF, len(add_list) - 1)
            self.visibility.setCurrentIndex(choice)

    def set_mp_zoom_adjust(self) -> None:
        """
        Handles toggling the multiplayer zoom adjust
        """
        self.mp_zoom_adjust.setEnabled(self.restrict_y.isChecked())
        self.mp_zoom_adjust.setValue(0)

    def set_music_list(self) -> None:
        """
        Handles the user selecting an entry from the music list
        """
        if self.auto_edit_music:
            return

        id = self.music_list.itemData(self.music_list.currentIndex())
        id = int(str(id)) # ID starts out as QString

        self.auto_edit_music = True
        self.music_id.setValue(id)
        self.auto_edit_music = False

    def set_music_id(self) -> None:
        """
        Handles the user selecting a custom music ID
        """
        if self.auto_edit_music:
            return
        id = self.music_id.value()

        self.auto_edit_music = True
        self.music_list.setCurrentIndex(self.music_list.findData(id))

        # Show 'Undefined Track XX' if there's no list item to show
        if self.music_list.findData(id) == -1:
            self.music_list.setPlaceholderText(globals_.trans.string('ZonesDlg', 108, '[id]', str(id)))

        self.auto_edit_music = False

    def select_preset(self, _i: int | None = None) -> None:
        """
        Handles a zone size preset being selected
        """
        if self.auto_change_size:
            return

        # Check if preset text is currently "(none)"
        if self.preset_chooser.currentText() == globals_.trans.string('ZonesDlg', 60):
            return

        w, h = self.preset_chooser.currentText().split('x')

        self.auto_change_size = True
        self.zone_width.setValue(int(w))
        self.zone_height.setValue(int(h))
        self.auto_change_size = False

        # Since a preset is now chosen, remove the None option from the list
        if self.preset_chooser.itemText(0) == globals_.trans.string('ZonesDlg', 60):
            self.preset_chooser.removeItem(0)

    def preset_changed(self, _i: int | None = None) -> None:
        """
        Handles the zone height or width boxes being changed
        """
        if self.auto_change_size:
            return

        self.auto_change_size = True
        w = self.zone_width.value()
        h = self.zone_height.value()
        check = str(w) + 'x' + str(h)

        sizeName = globals_.trans.string('ZonesDlg', 60)

        try:
            idx = self.size_presets.index(check)
        except ValueError:
            idx = -1

        if idx == -1:
            if self.preset_chooser.itemText(0) != sizeName:
                self.preset_chooser.insertItem(0, sizeName)

            idx = 0

        elif self.preset_chooser.itemText(0) == sizeName:
            self.preset_chooser.removeItem(0)

        self.preset_chooser.setCurrentIndex(idx)
        self.auto_change_size = False

    def copy_zone_data(self, z: ZoneItem, curr_id: int) -> None:
        """
        Copies data from one zone into another
        """
        z.objx = clamp(16, 24560, self.pos_x.value())
        z.objy = clamp(16, 12272, self.pos_y.value())
        z.width = min(24560 - z.objx, self.zone_width.value())
        z.height = min(12272 - z.objy, self.zone_height.value())

        z.prepareGeometryChange()
        z.UpdateRects()
        z.setPos(z.objx * 1.5, z.objy * 1.5)

        z.modeldark = self.theme.currentIndex()
        z.terraindark = self.terrain_light.currentIndex()
        z.cammode = self.cam_settings.mode_button_group.checkedId()
        z.camzoom = self.cam_settings.screen_sizes.currentIndex()
        z.camtrack = self.direction.currentIndex()

        if self.restrict_y.isChecked():
            z.mpcamzoomadjust = self.mp_zoom_adjust.value()
        else:
            z.mpcamzoomadjust = 15

        z.visibility = 0

        if self.spotlight.isChecked():
            z.visibility |= 1 << 4
        if self.full_dark.isChecked():
            z.visibility |= 1 << 5

        z.visibility |= self.visibility.currentIndex()

        z.yupperbound = self.bound_up.value()
        z.ylowerbound = self.bound_down.value()
        z.yupperbound2 = self.lakitu_bound_up.value()
        z.ylowerbound2 = self.lakitu_bound_down.value()
        z.yupperbound3 = self.mp_bound_up.value()
        z.ylowerbound3 = self.mp_bound_down.value()

        z.music = self.music_id.value()
        z.sfxmod = self.modulation.currentIndex() << 4
        if self.boss_flag.isChecked():
            z.sfxmod |= 1

        # For convenience, let's copy the background data too
        curr_zone = globals_.Area.zones[0]

        # Since the Background dialog isn't open, we must
        # copy data directly from the selected zone
        for zone in globals_.Area.zones:
            if (zone.id == curr_id):
                curr_zone = zone

        # Copy the bgA first
        z.XscrollA = curr_zone.XscrollA
        z.YscrollA = curr_zone.YscrollA
        z.YpositionA = curr_zone.YpositionA
        z.XpositionA = curr_zone.XpositionA
        z.bg1A = curr_zone.bg1A
        z.bg2A = curr_zone.bg2A
        z.bg3A = curr_zone.bg3A
        z.ZoomA = curr_zone.ZoomA

        # And the bgB
        z.XscrollB = curr_zone.XscrollB
        z.YscrollB = curr_zone.YscrollB
        z.YpositionB = curr_zone.YpositionB
        z.XpositionB = curr_zone.XpositionB
        z.bg1B = curr_zone.bg1B
        z.bg2B = curr_zone.bg2B
        z.bg3B = curr_zone.bg3B
        z.ZoomB = curr_zone.ZoomB
