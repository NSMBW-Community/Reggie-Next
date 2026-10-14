from typing import cast

from PyQt6 import QtWidgets

from data import globals_
from data.level.dirty import SetDirty
from data.level.items.zone import ZoneItem
from ui.theme.reggie_theme import GetIcon

from ui.widgets.zone_tab import ZoneTab
from data.common.utils import clamp

class ZonesDialog(QtWidgets.QDialog):
    """
    Dialog which lets you modify zones
    """

    def __init__(self) -> None:
        """
        Creates and initializes the tab dialog
        """
        super().__init__()
        self.setWindowTitle(globals_.trans.string('ZonesDlg', 0))
        self.setWindowIcon(GetIcon('zone'))

        self.tab_widget = QtWidgets.QTabWidget()
        self.zone_tabs: list[ZoneTab] = []

        # Make tabs
        for zone in globals_.Area.zones:
            name = globals_.trans.string('ZonesDlg', 3, '[num]', zone.id + 1)

            tab = ZoneTab(zone)
            self.zone_tabs.append(tab)
            self.tab_widget.addTab(tab, name)

        self.new_button = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 4))
        self.copy_button = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 107))
        self.delete_button = QtWidgets.QPushButton(globals_.trans.string('ZonesDlg', 5))

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.addButton(self.new_button, button_box.ButtonRole.ActionRole)
        button_box.addButton(self.copy_button, button_box.ButtonRole.ActionRole)
        button_box.addButton(self.delete_button, button_box.ButtonRole.ActionRole)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.new_button.clicked.connect(self.create_zone)
        self.copy_button.clicked.connect(self.copy_zone)
        self.delete_button.clicked.connect(self.delete_zone)

        self.set_button_state()

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def save(self) -> None:
        """
        Saves the Zone settings
        """
        if globals_.mainWindow is None:
            return

        SetDirty()

        # Resync the zones
        items = globals_.mainWindow.scene.items()
        func_ii = isinstance
        type_zone = ZoneItem

        for item in items:
            if func_ii(item, type_zone):
                globals_.mainWindow.scene.removeItem(item)

        globals_.Area.zones = []

        for i, tab in enumerate(self.zone_tabs):
            z = tab.zone_obj
            z.id = i
            z.UpdateTitle()
            globals_.Area.zones.append(z)
            globals_.mainWindow.scene.addItem(z)

            z.objx = clamp(16, 24560, tab.pos_x.value())
            z.objy = clamp(16, 12272, tab.pos_y.value())
            z.width = min(24560 - z.objx, tab.zone_width.value())
            z.height = min(12272 - z.objy, tab.zone_height.value())

            z.prepareGeometryChange()
            z.UpdateRects()
            z.setPos(z.objx * 1.5, z.objy * 1.5)

            z.modeldark = tab.theme.currentIndex()
            z.terraindark = tab.terrain_light.currentIndex()
            z.cammode = tab.cam_settings.mode_button_group.checkedId()
            z.camzoom = tab.cam_settings.screen_sizes.currentIndex()
            z.camtrack = tab.direction.currentIndex()

            if tab.restrict_y.isChecked():
                z.mpcamzoomadjust = tab.mp_zoom_adjust.value()
            else:
                z.mpcamzoomadjust = 15

            z.visibility = 0

            if tab.spotlight.isChecked():
                z.visibility |= 1 << 4
            if tab.full_dark.isChecked():
                z.visibility |= 1 << 5

            z.visibility |= tab.visibility.currentIndex()

            z.yupperbound = tab.bound_up.value()
            z.ylowerbound = tab.bound_down.value()
            z.yupperbound2 = tab.lakitu_bound_up.value()
            z.ylowerbound2 = tab.lakitu_bound_down.value()
            z.yupperbound3 = tab.mp_bound_up.value()
            z.ylowerbound3 = tab.mp_bound_down.value()

            z.music = tab.music_id.value()
            z.sfxmod = tab.modulation.currentIndex() << 4
            if tab.boss_flag.isChecked():
                z.sfxmod |= 1

        for spr in globals_.Area.actors:
            spr.ImageObj.positionChanged()

        globals_.mainWindow.action_list['backgrounds'].setEnabled(len(globals_.Area.zones) > 0)
        globals_.mainWindow.level_overview.update()

    def create_zone(self) -> None:
        """
        Handles creating a new zone
        """
        # Show warning about the zone limit
        if len(self.zone_tabs) >= 6:
            result = QtWidgets.QMessageBox.warning(self, globals_.trans.string('ZonesDlg', 6), globals_.trans.string('ZonesDlg', 7),
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if result == QtWidgets.QMessageBox.StandardButton.No:
                return

        if globals_.mainWindow is None:
            return

        zone = ZoneItem.CreateZone(256, 256)
        name = globals_.trans.string('ZonesDlg', 3, '[num]', zone.id + 1)

        tab = ZoneTab(zone)
        self.zone_tabs.append(tab)
        self.tab_widget.addTab(tab, name)

        tab_count = self.tab_widget.count()
        self.tab_widget.setCurrentIndex(tab_count - 1)
        self.set_button_state()

    def copy_zone(self) -> None:
        """
        Handles copying the current zone data to a new one
        """
        if len(self.zone_tabs) >= 6:
            result = QtWidgets.QMessageBox.warning(self, globals_.trans.string('ZonesDlg', 6), globals_.trans.string('ZonesDlg', 7),
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if result == QtWidgets.QMessageBox.StandardButton.No:
                return

        if globals_.mainWindow is None:
            return

        zone = ZoneItem.CreateZone(256, 256)
        widget = cast(ZoneTab, self.tab_widget.widget(self.tab_widget.currentIndex()))
        widget.copy_zone_data(zone, self.tab_widget.currentIndex())

        name = globals_.trans.string('ZonesDlg', 3, '[num]', zone.id + 1)

        tab = ZoneTab(zone)
        self.zone_tabs.append(tab)
        self.tab_widget.addTab(tab, name)

        tab_count = self.tab_widget.count()
        self.tab_widget.setCurrentIndex(tab_count - 1)
        self.set_button_state()

    def delete_zone(self) -> None:
        """
        Handles deleting the current zone
        """
        tab_count = self.tab_widget.count()
        if tab_count == 0:
            return

        index = self.tab_widget.currentIndex()
        self.tab_widget.removeTab(index)
        self.zone_tabs.pop(index)
        self.set_button_state()

    def set_button_state(self) -> None:
        """
        Toggles the Copy and Delete buttons
        """
        tab_count = self.tab_widget.count()
        self.copy_button.setEnabled(tab_count != 0)
        self.delete_button.setEnabled(tab_count != 0)
