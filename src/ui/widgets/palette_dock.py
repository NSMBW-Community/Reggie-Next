from PyQt6 import QtCore, QtWidgets, QtGui

from src.data import globals_
from src.ui.widgets.icon_only_tab_bar import IconsOnlyTabBar
from src.ui.theme.reggie_theme import GetIcon

from src.ui.widgets.palette.object import ObjectTab
from src.ui.widgets.palette.sprite import SpriteTab
from src.ui.widgets.palette.entrance import EntranceTab
from src.ui.widgets.palette.location import LocationTab
from src.ui.widgets.palette.path import PathTab
from src.ui.widgets.palette.event import EventTab
from src.ui.widgets.palette.stamp import StampTab
from src.ui.widgets.palette.comment import CommentTab

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
        self.tabs.addTab(self.object_tab, GetIcon('objects'), '')
        self.tabs.setTabToolTip(0, globals_.trans.string('Palette', 13))

        # Sprites
        self.sprite_tab = SpriteTab()
        self.tabs.addTab(self.sprite_tab, GetIcon('sprites'), '')
        self.tabs.setTabToolTip(1, globals_.trans.string('Palette', 14))

        # Entrances
        self.entrance_tab = EntranceTab()
        self.tabs.addTab(self.entrance_tab, GetIcon('entrances'), '')
        self.tabs.setTabToolTip(2, globals_.trans.string('Palette', 15))

        # Locations
        self.location_tab = LocationTab()
        self.tabs.addTab(self.location_tab, GetIcon('locations'), '')
        self.tabs.setTabToolTip(3, globals_.trans.string('Palette', 16))

        # Paths
        self.path_tab = PathTab()
        self.tabs.addTab(self.path_tab, GetIcon('paths'), '')
        self.tabs.setTabToolTip(4, globals_.trans.string('Palette', 17))

        # Events
        self.event_tab = EventTab()
        self.tabs.addTab(self.event_tab, GetIcon('events'), '')
        self.tabs.setTabToolTip(5, globals_.trans.string('Palette', 18))

        # Stamps
        self.stamp_tab = StampTab()
        self.tabs.addTab(self.stamp_tab, GetIcon('stamp'), '')
        self.tabs.setTabToolTip(6, globals_.trans.string('Palette', 19))

        # Comments
        self.comment_tab = CommentTab()
        self.tabs.addTab(self.comment_tab, GetIcon('comments'), '')
        self.tabs.setTabToolTip(7, globals_.trans.string('Palette', 33))

        self.setWidget(self.tabs)

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
