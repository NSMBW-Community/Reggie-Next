from PyQt6 import QtCore, QtWidgets, QtGui

from data import globals_
from ui.widgets.icon_only_tab_bar import IconsOnlyTabBar
from ui.theme.reggie_theme import GetIcon

from ui.widgets.palette.object import ObjectTab
from ui.widgets.palette.sprite import SpriteTab
from ui.widgets.palette.entrance import EntranceTab
from ui.widgets.palette.location import LocationTab
from ui.widgets.palette.path import PathTab
from ui.widgets.palette.event import EventTab
from ui.widgets.palette.stamp import StampTab
from ui.widgets.palette.comment import CommentTab

from data.level.items.sprite import ActorItem
from data.level.items.entrance import EntranceItem
from data.level.items.location import LocationItem
from data.level.items.comment import CommentItem

from ui.widgets.item_sorts_by_other import ListWidgetItem_SortsByOther

class PaletteDock(QtWidgets.QDockWidget):
    """
    Represents the Palette widget
    """
    def setup(self):
        """
        Sets up the various palette tabs
        """
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabBar(IconsOnlyTabBar())
        self.tabs.setIconSize(QtCore.QSize(16, 16))
        self.tabs.currentChanged.connect(self.current_tab_changed)

        # Objects
        self.object_tab = ObjectTab()
        self.tabs.addTab(self.object_tab, GetIcon('block'), '')
        self.tabs.setTabToolTip(0, globals_.trans.string('Palette', 13))

        # Sprites
        self.sprite_tab = SpriteTab()
        self.tabs.addTab(self.sprite_tab, GetIcon('rocket'), '')
        self.tabs.setTabToolTip(1, globals_.trans.string('Palette', 14))

        # Entrances
        self.entrance_tab = EntranceTab()
        self.tabs.addTab(self.entrance_tab, GetIcon('door'), '')
        self.tabs.setTabToolTip(2, globals_.trans.string('Palette', 15))

        # Locations
        self.location_tab = LocationTab()
        self.tabs.addTab(self.location_tab, GetIcon('layer-shape-purple'), '')
        self.tabs.setTabToolTip(3, globals_.trans.string('Palette', 16))

        # Paths
        self.path_tab = PathTab()
        self.tabs.addTab(self.path_tab, GetIcon('node'), '')
        self.tabs.setTabToolTip(4, globals_.trans.string('Palette', 17))

        # Events
        self.event_tab = EventTab()
        self.tabs.addTab(self.event_tab, GetIcon('flag'), '')
        self.tabs.setTabToolTip(5, globals_.trans.string('Palette', 18))

        # Stamps
        self.stamp_tab = StampTab()
        self.tabs.addTab(self.stamp_tab, GetIcon('stamp'), '')
        self.tabs.setTabToolTip(6, globals_.trans.string('Palette', 19))

        # Comments
        self.comment_tab = CommentTab()
        self.tabs.addTab(self.comment_tab, GetIcon('balloon'), '')
        self.tabs.setTabToolTip(7, globals_.trans.string('Palette', 33))

        self.setWidget(self.tabs)

    def reset(self):
        """
        Resets data for all child tabs
        """
        if globals_.mainWindow is None:
            return

        self.object_tab.reset(False)
        if all(tileset == '' for tileset in globals_.Area.tilesets):
            globals_.mainWindow.action_list['swapobjectstypes'].setEnabled(False)
            globals_.mainWindow.action_list['swapobjectstilesets'].setEnabled(False)

        # Add all the level items

        # Sprites
        self.sprite_tab.prepare_batch_add()

        pos_change = ActorItem.position_changed
        for spr in globals_.Area.sprites:
            spr.positionChanged = pos_change
            self.sprite_tab.add_sprite(spr)
            globals_.mainWindow.scene.addItem(spr)
            spr.UpdateListItem()

        self.sprite_tab.end_batch_add()

        # Entrances
        pos_change = EntranceItem.position_changed
        for ent in globals_.Area.entrances:
            ent.positionChanged = pos_change
            ent.listitem = ListWidgetItem_SortsByOther(ent)
            ent.listitem.entid = ent.entid
            self.entrance_tab.entrance_list.addItem(ent.listitem)
            globals_.mainWindow.scene.addItem(ent)
            ent.UpdateListItem()

        # Locations
        pos_change = LocationItem.position_changed
        size_change = LocationItem.size_changed
        for location in globals_.Area.locations:
            location.positionChanged = pos_change
            location.sizeChanged = size_change
            location.listitem = ListWidgetItem_SortsByOther(location)
            self.location_tab.location_list.addItem(location.listitem)
            globals_.mainWindow.scene.addItem(location)
            location.UpdateListItem()

        # Load events
        self.event_tab.load_event_data()

        # Comments
        pos_change = CommentItem.position_changed
        text_change = CommentItem.text_changed
        for com in globals_.Area.comments:
            com.positionChanged = pos_change
            com.textChanged = text_change
            com.listitem = QtWidgets.QListWidgetItem()
            self.comment_tab.comment_list.addItem(com.listitem)
            globals_.mainWindow.scene.addItem(com)
            com.UpdateListItem()

    def set_tab(self, index):
        """
        Updates the current palette tab
        """
        self.tabs.setCurrentIndex(index)

    def current_tab_changed(self, new_tab):
        """
        Handles the selected palette tab changing
        """
        paint_type = -1

        if new_tab == 0: # Objects
            paint_type = self.object_tab.currentIndex()
        elif new_tab == 1: # Sprites
            # Ensure the user can't paint sprites when the
            # 'current sprites' tab is opened.
            if self.sprite_tab.currentIndex() != 1:
                paint_type = 4
        elif new_tab == 2: # Entrances
            paint_type = 5
        elif new_tab == 3: # Locations
            paint_type = 7
        elif new_tab == 4: # Paths
            paint_type = 6
        elif new_tab == 6: # Stamps
            paint_type = 8
        elif new_tab == 7: # Comments
            paint_type = 9

        globals_.CurrentPaintType = paint_type
