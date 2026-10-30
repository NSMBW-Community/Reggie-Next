import os.path
import struct
import sys

from typing import cast

from PyQt6 import QtCore, QtGui, QtWidgets
Qt = QtCore.Qt

from data import globals_

import spritelib as SLib

from libs import lh, lib_versions, lz77
from ui.theme.reggie_theme import GetIcon, GetAppIcon
from data.common.loaders import LoadMenuActions, LoadLevelNames, LoadZoneThemes, GetKeybind, DecompressLevel
from data.common.utils import SetGamePaths, get_reggiedata_folder
from data.common.validators import IsValidLevel, areValidGamePaths
from ui.widgets.level_scene import LevelScene
from ui.widgets.level_view import LevelViewWidget
from data.level.dirty import SetDirty, CheckDirty
from data.common.settings import setting, setSetting
from data.level.items.comment import CommentItem
from data.level.items.entrance import EntranceItem
from data.level.items.location import LocationItem
from data.level.items.object import ObjectItem
from data.level.items.path import PathItem
from data.level.items.path_editor_line import PathEditorLineItem
from data.level.items.sprite import SpriteItem
from data.level.items.zone import ZoneItem
from data.level.nsmbw_level import NSMBWLevel
from ui.widgets.spriteeditor.sprite_editor import SpriteEditorWidget
from ui.actions.undo.undo_stack import UndoStack

from ui.dialogs.area import AreaOptionsDialog
from ui.dialogs.area_delete import AreaDeleteDialog
from ui.dialogs.area_import import AreaImportDialog
from ui.dialogs.background import BackgroundDialog
from ui.dialogs.camera_profile import CameraProfilesDialog
from ui.dialogs.choose_level_name import ChooseLevelNameDialog
from ui.dialogs.item_shift import ItemShiftDialog
from ui.dialogs.meta_info import MetaInfoDialog
from ui.dialogs.tileset_swap import TilesetSwapDialog
from ui.dialogs.preference import PreferencesDialog
from ui.dialogs.screenshot import ScreenshotDialog
from ui.dialogs.zone import ZonesDialog

from ui.menus.game_def_menu import GameDefMenu
from ui.menus.recent_files_menu import RecentFilesMenu

from ui.widgets.zoom import ZoomWidget
from ui.widgets.zoom_status import ZoomStatusWidget
from ui.widgets.diagnostic import DiagnosticWidget
from ui.widgets.level_overview import LevelOverviewWidget

from ui.widgets.editors.entrance import EntranceEditorWidget
from ui.widgets.editors.location import LocationEditorWidget
from ui.widgets.editors.path_node import PathNodeEditorWidget

from ui.widgets.palette_dock import PaletteDock
from data.common.reggie_clip import ReggieClip
from ui.widgets.item_editor_dock import ItemEditorDockWidget

################################################################################
################################################################################
################################################################################

class ReggieWindow(QtWidgets.QMainWindow):
    """
    Reggie main level editor window
    """
    action_list: dict[str, QtGui.QAction] = {}

    def create_dock_widget(self, title: str | None, obj_name: str, widget: QtWidgets.QWidget, features: QtWidgets.QDockWidget.DockWidgetFeature,
                           area: QtCore.Qt.DockWidgetArea, allowed_areas: QtCore.Qt.DockWidgetArea | None, visible: bool, floating: bool,
                           is_palette: bool = False, is_editor: bool = False) -> PaletteDock | ItemEditorDockWidget | QtWidgets.QDockWidget:
        """
        Helper function to create docks
        """
        if is_palette:
            dock = PaletteDock(title, self)
        elif is_editor:
            dock = ItemEditorDockWidget(title, self)
        else:
            dock = QtWidgets.QDockWidget(title, self)

        dock.setFeatures(features)
        if allowed_areas is not None:
            dock.setAllowedAreas(allowed_areas)

        # Allows for state saving/restoring
        dock.setObjectName(obj_name)

        dock.setWidget(widget)
        dock.setVisible(visible)
        dock.setFloating(floating)

        # Offset from top-left corner
        if floating:
            dock.move(100, 100)

        self.addDockWidget(area, dock)
        return dock

    def __init__(self) -> None:
        """
        Editor window constructor
        """
        globals_.Initializing = True

        self.ZoomLevels = [7.5, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0,
                           85.0, 90.0, 95.0, 100.0, 125.0, 150.0, 175.0, 200.0, 250.0, 300.0, 350.0, 400.0]

        # Add the undo stack object
        self.undoStack = UndoStack()

        # Required variables
        self.UpdateFlag = False
        self.SelectionUpdateFlag = False
        self.selObj = None
        self.CurrentSelection = []

        # Set up the window
        QtWidgets.QMainWindow.__init__(self, None)
        self.setWindowTitle(f'Reggie! Next {globals_.ReggieVersionShort}')
        self.setWindowIcon(GetAppIcon())
        self.setIconSize(QtCore.QSize(16, 16))
        self.setUnifiedTitleAndToolBarOnMac(True)

        # Create the level view
        self.scene = LevelScene(0, 0, 1024 * 24, 512 * 24, self)
        self.scene.setItemIndexMethod(QtWidgets.QGraphicsScene.ItemIndexMethod.NoIndex)
        self.scene.selectionChanged.connect(self.ChangeSelectionHandler)

        self.view = LevelViewWidget(self.scene, self)
        self.view.centerOn(0, 0) # This scrolls to the top left
        self.view.PositionHover.connect(self.PositionHovered)

        # Done creating the window!
        self.setCentralWidget(self.view)

        # Set up the clipboard stuff
        self.clipboard = None
        self.systemClipboard = QtWidgets.QApplication.clipboard()
        if self.systemClipboard is not None:
            self.systemClipboard.dataChanged.connect(self.track_clipboard_updates)

    def __init2__(self) -> None:
        """
        Finishes initialization. (fixes bugs with some widgets calling globals_.mainWindow.something before it's init'ed)
        """
        self.auto_save_timer = QtCore.QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_level)
        self.auto_save_timer.start(20000) # 20 seconds

        # Set up actions and menus
        self.RecentMenu = RecentFilesMenu()
        self.GameDefMenu = GameDefMenu()
        self.setup_menu_bar()

        # Get the zoom level
        self.ZoomLevel = setting('ZoomLevel', 100.0)

        # Set up the status bar
        self.setup_status_bar()

        # Create the various panels
        self.setup_docks()

        # Add a menu action for the toolbar
        # That way it can be easily toggled if hidden by accident
        if self.toolbar is not None:
            act = self.toolbar.toggleViewAction()
            if act is None:
                return

            act.setShortcut(GetKeybind('toolbar'))
            act.setIcon(GetIcon('toolbox'))
            if self.vmenu is not None:
                self.vmenu.addAction(act)

            self.action_list['toolbar'] = act

        # Now get stuff ready
        loaded = False
        self.fileSavePath = None

        if len(sys.argv) > 1 and IsValidLevel(sys.argv[1]):
            # There's a level in the args, load that
            loaded = self.load_level(sys.argv[1], True, 1)
        else:
            # Try the last level loaded with this game patch
            last_level = globals_.gamedef.GetLastLevel()
            if last_level is not None:
                loaded = self.load_level(last_level, True, 1)

        # Fall back to the first level in the current patch's Stage folder
        if not loaded:
            self.load_level(globals_.FirstStageFilename, True, 1)

        # Call toggle-button handlers to set each feature correctly upon startup
        toggle_handlers = {
            globals_.Area.show_sprites: globals_.SpritesShown,
            globals_.Area.show_sprite_images: globals_.SpriteImagesShown,
            globals_.Area.show_entrances: globals_.EntrancesShown,
            globals_.Area.show_locations: globals_.LocationsShown,
            globals_.Area.show_comments: globals_.CommentsShown,
            globals_.Area.show_path_nodes: globals_.PathsShown,
        }

        for handler in toggle_handlers:
            handler(toggle_handlers[handler])

        # Let's restore the state and geometry
        # Geometry determines the main window position
        # State determines positions of docks
        if globals_.settings.contains('MainWindowGeometry'):
            geo = setting('MainWindowGeometry')
            if geo is not None:
                self.restoreGeometry(geo)

        if globals_.settings.contains('MainWindowState'):
            state = setting('MainWindowState')
            if state is not None:
                self.restoreState(state, 0)

        # Restore zoom level now that everything is setup
        self.set_zoom(self.ZoomLevel)

        # Set initial state for diagnostic widget
        # Calling this while the auto-diag is initing
        # will cause the 'no zones' check to always fail
        if globals_.AutoDiagEnabled:
            self.diagnostic.update_status()

        globals_.Initializing = False

    def setup_status_bar(self) -> None:
        """
        Sets up the status bar
        """
        self.posLabel = QtWidgets.QLabel()
        self.selectionLabel = QtWidgets.QLabel()
        self.hoverLabel = QtWidgets.QLabel()

        status_bar = self.statusBar()
        if status_bar is None:
            return

        # Clear all widgets, this is so we can refresh the status bar
        # while Reggie is running
        for widget in status_bar.findChildren(QtWidgets.QWidget):
            status_bar.removeWidget(widget)

        status_bar.addWidget(self.posLabel)
        status_bar.addWidget(self.selectionLabel)
        status_bar.addWidget(self.hoverLabel)

        self.diagnostic = DiagnosticWidget()
        if globals_.AutoDiagEnabled:
            self.diagnostic.set_timer()
            status_bar.addPermanentWidget(self.diagnostic)

        self.ZoomWidget = ZoomWidget()
        self.ZoomStatusWidget = ZoomStatusWidget()

        status_bar.addPermanentWidget(self.ZoomWidget)
        status_bar.addPermanentWidget(self.ZoomStatusWidget)

    def setup_menu_bar(self) -> None:
        """
        Sets up actions, a menubar and a toolbar
        """
        LoadMenuActions(self)

        # Set all of the actions
        for action in globals_.MenuActions:
            act = action.create_action(self)
            self.action_list[action.shortname] = act

        self.action_list['openrecent'].setMenu(self.RecentMenu)
        self.action_list['changegamedef'].setMenu(self.GameDefMenu)

        # Set default states
        self.action_list['collisions'].setChecked(globals_.CollisionsShown)
        self.action_list['realview'].setChecked(globals_.RealViewEnabled)

        self.action_list['showsprites'].setChecked(globals_.SpritesShown)
        self.action_list['showspriteimages'].setChecked(globals_.SpriteImagesShown)
        self.action_list['showentrances'].setChecked(globals_.EntrancesShown)
        self.action_list['showlocations'].setChecked(globals_.LocationsShown)
        self.action_list['showcomments'].setChecked(globals_.CommentsShown)
        self.action_list['showpaths'].setChecked(globals_.PathsShown)

        self.action_list['freezeobjects'].setChecked(globals_.ObjectsFrozen)
        self.action_list['freezesprites'].setChecked(globals_.SpritesFrozen)
        self.action_list['freezeentrances'].setChecked(globals_.EntrancesFrozen)
        self.action_list['freezelocations'].setChecked(globals_.LocationsFrozen)
        self.action_list['freezepaths'].setChecked(globals_.PathsFrozen)
        self.action_list['freezecomments'].setChecked(globals_.CommentsFrozen)

        self.action_list['undo'].setEnabled(False)
        self.action_list['redo'].setEnabled(False)
        self.action_list['cut'].setEnabled(False)
        self.action_list['copy'].setEnabled(False)
        self.action_list['paste'].setEnabled(False)
        self.action_list['shiftitems'].setEnabled(False)
        self.action_list['mergelocations'].setEnabled(False)
        self.action_list['deselect'].setEnabled(False)

        # Prepare the menu bar
        menubar = QtWidgets.QMenuBar()
        self.setMenuBar(menubar)

        fmenu = menubar.addMenu(globals_.trans.string('Menubar', 0))
        if fmenu is not None:
            fmenu.addAction(self.action_list['newlevel'])
            fmenu.addAction(self.action_list['openfromname'])
            fmenu.addAction(self.action_list['openfromfile'])
            fmenu.addAction(self.action_list['openrecent'])
            fmenu.addSeparator()
            fmenu.addAction(self.action_list['save'])
            fmenu.addAction(self.action_list['saveas'])
            fmenu.addAction(self.action_list['savecopyas'])
            fmenu.addAction(self.action_list['metainfo'])
            fmenu.addSeparator()
            fmenu.addAction(self.action_list['changegamedef'])
            fmenu.addAction(self.action_list['screenshot'])
            fmenu.addAction(self.action_list['changegamepath'])
            fmenu.addAction(self.action_list['preferences'])
            fmenu.addSeparator()
            fmenu.addAction(self.action_list['exit'])

        emenu = menubar.addMenu(globals_.trans.string('Menubar', 1))
        if emenu is not None:
            emenu.addAction(self.action_list['selectall'])
            emenu.addAction(self.action_list['deselect'])
            emenu.addSeparator()
            emenu.addAction(self.action_list['undo'])
            emenu.addAction(self.action_list['redo'])
            emenu.addSeparator()
            emenu.addAction(self.action_list['cut'])
            emenu.addAction(self.action_list['copy'])
            emenu.addAction(self.action_list['paste'])
            emenu.addSeparator()
            emenu.addAction(self.action_list['shiftitems'])
            emenu.addAction(self.action_list['mergelocations'])
            emenu.addAction(self.action_list['swapobjectstilesets'])
            emenu.addAction(self.action_list['swapobjectstypes'])
            emenu.addAction(self.action_list['switchsprites'])
            emenu.addSeparator()
            emenu.addAction(self.action_list['diagnostic'])
            emenu.addSeparator()
            emenu.addAction(self.action_list['freezeobjects'])
            emenu.addAction(self.action_list['freezesprites'])
            emenu.addAction(self.action_list['freezeentrances'])
            emenu.addAction(self.action_list['freezelocations'])
            emenu.addAction(self.action_list['freezepaths'])
            emenu.addAction(self.action_list['freezecomments'])

        vmenu = menubar.addMenu(globals_.trans.string('Menubar', 2))
        if vmenu is not None:
            vmenu.addAction(self.action_list['showlay0'])
            vmenu.addAction(self.action_list['showlay1'])
            vmenu.addAction(self.action_list['showlay2'])
            vmenu.addAction(self.action_list['tileanim'])
            vmenu.addAction(self.action_list['collisions'])
            vmenu.addAction(self.action_list['realview'])
            vmenu.addSeparator()
            vmenu.addAction(self.action_list['showsprites'])
            vmenu.addAction(self.action_list['showspriteimages'])
            vmenu.addAction(self.action_list['showentrances'])
            vmenu.addAction(self.action_list['showlocations'])
            vmenu.addAction(self.action_list['showpaths'])
            vmenu.addAction(self.action_list['showcomments'])
            vmenu.addSeparator()
            vmenu.addAction(self.action_list['grid'])
            vmenu.addSeparator()
            vmenu.addAction(self.action_list['zoommax'])
            vmenu.addAction(self.action_list['zoomin'])
            vmenu.addAction(self.action_list['zoomactual'])
            vmenu.addAction(self.action_list['zoomout'])
            vmenu.addAction(self.action_list['zoommin'])
            vmenu.addSeparator()

        # Several items are assigned to this later, so we need to keep track of it
        self.vmenu = vmenu

        lmenu = menubar.addMenu(globals_.trans.string('Menubar', 3))
        if lmenu is not None:
            lmenu.addAction(self.action_list['areaoptions'])
            lmenu.addAction(self.action_list['camprofiles'])
            lmenu.addAction(self.action_list['zones'])
            lmenu.addAction(self.action_list['backgrounds'])
            lmenu.addSeparator()
            lmenu.addAction(self.action_list['addarea'])
            lmenu.addAction(self.action_list['importarea'])
            lmenu.addAction(self.action_list['deletearea'])
            lmenu.addSeparator()
            lmenu.addAction(self.action_list['reloadgfx'])
            lmenu.addAction(self.action_list['reloaddata'])

        hmenu = menubar.addMenu(globals_.trans.string('Menubar', 4))
        self.setup_help_menu(hmenu)

        # Create a toolbar
        self.area_combo_box = QtWidgets.QComboBox()
        self.area_combo_box.activated.connect(self.switch_area)

        self.setup_toolbar()

    def setup_help_menu(self, menu: QtWidgets.QMenu | None = None) -> QtWidgets.QMenu:
        """
        Creates the help menu
        """
        if menu is None:
            menu = QtWidgets.QMenu(globals_.trans.string('Menubar', 4))

        menu.addAction(self.action_list['infobox'])
        menu.addAction(self.action_list['helpbox'])
        menu.addAction(self.action_list['tipbox'])
        menu.addSeparator()
        menu.addAction(self.action_list['genstrxml'])
        menu.addSeparator()
        menu.addAction(self.action_list['aboutqt'])
        menu.addSeparator()

        # Add version info actions
        if lib_versions["nsmblib-updated"] is not None:
            value = str(lib_versions["nsmblib-updated"])
            version = int(value[:4]), int(value[4:6]), int(value[6:8]), int(value[8:10])
            nsmblib_info_text = "Using NSMBLib Updated %d.%d.%d.%d" % version
        elif lib_versions["nsmblib"] is not None:
            nsmblib_info_text = "Using NSMBLib %d" % lib_versions["nsmblib"]
        else:
            nsmblib_info_text = "Not using NSMBLib"

        info_labels = [
            "Using Python %d.%d.%d" % sys.version_info[:3],
            "Using PyQt %s" % QtCore.PYQT_VERSION_STR,
            "Using Qt %s" % QtCore.QT_VERSION_STR,
            nsmblib_info_text
        ]

        for label in info_labels:
            act = menu.addAction(label)
            if act is not None:
                act.setEnabled(False)

        return menu

    def setup_toolbar(self) -> None:
        """
        Reads from the Preferences file and adds the appropriate options to the toolbar
        """
        # First, define groups. Each group is isolated by separators.
        toolbar_groups = (
            (
                'newlevel',
                'openfromname',
                'openfromfile',
                'openrecent',
                'save',
                'saveas',
                'savecopyas',
                'metainfo',
                'changegamedef',
                'screenshot',
                'changegamepath',
                'preferences',
                'exit',
            ), (
                'selectall',
                'deselect',
            ), (
                'cut',
                'copy',
                'paste',
            ), (
                'shiftitems',
                'mergelocations',
                'swapobjectstilesets',
                'swapobjectstypes',
                'switchsprites',
            ), (
                'freezeobjects',
                'freezesprites',
                'freezeentrances',
                'freezelocations',
                'freezepaths',
            ), (
                'diagnostic',
            ), (
                'zoommax',
                'zoomin',
                'zoomactual',
                'zoomout',
                'zoommin',
            ), (
                'grid',
            ), (
                'showlay0',
                'showlay1',
                'showlay2',
                'tileanim',
                'collisions',
                'realview',
            ), (
                'showsprites',
                'showspriteimages',
                'showentrances',
                'showlocations',
                'showpaths',
            ), (
                'areaoptions',
                'camprofiles',
                'zones',
                'backgrounds',
            ), (
                'addarea',
                'importarea',
                'deletearea',
            ), (
                'reloadgfx',
                'reloaddata',
            ), (
                'infobox',
                'helpbox',
                'tipbox',
                'aboutqt',
            ),
        )

        # Determine which keys are activated
        if setting('ToolbarActs') in (None, 'None', 'none', '', 0):
            # Get the default settings
            toggled = {}
            for act_list in (globals_.FileActions, globals_.EditActions, globals_.ViewActions, globals_.SettingsActions, globals_.HelpActions):
                for action in act_list:
                    toggled[action.id] = action.active
        else:
            # Get the settings from the .ini
            toggled = setting('ToolbarActs')
            if toggled is None:
                return

            new_toggled = {}  # Replacing QStrings with Python strings
            for key in toggled:
                new_toggled[str(key)] = toggled[key]
            toggled = new_toggled

        if not hasattr(self, 'toolbar'):
            self.toolbar = self.addToolBar(globals_.trans.string('Menubar', 5))
        else:
            if self.toolbar is not None:
                self.toolbar.clear()

        if self.toolbar is None:
            return

        self.toolbar.setObjectName('MainToolbar')

        # Add each to the toolbar if toggled[key]
        for group in toolbar_groups:
            added_buttons = False
            for key in group:
                if key in toggled and toggled[key]:
                    act = self.action_list[key]
                    self.toolbar.addAction(act)
                    added_buttons = True
            if added_buttons:
                self.toolbar.addSeparator()

        # Add the area combo box
        if self.toolbar is not None:
            # The widget cannot be added back onto the toolbar unless we do this
            if hasattr(self, 'area_combo_action'):
                self.toolbar.addAction(self.area_combo_action)
                return

            self.area_combo_action = self.toolbar.addWidget(self.area_combo_box)

    def setup_docks(self) -> None:
        """
        Sets up the dock widgets and panels
        """
        # Level Overview
        self.level_overview = LevelOverviewWidget()
        features = QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable   | \
                   QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable | \
                   QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable

        overview_dock = self.create_dock_widget(globals_.trans.string('MenuItems', 94), 'leveloverview', self.level_overview,
                                              features, Qt.DockWidgetArea.RightDockWidgetArea, None, True, False)
        self.level_overview_dock = overview_dock

        # These apply to all editor docks
        features = QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        allowed_areas = Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea

        # Sprite Editor
        self.spriteDataEditor = SpriteEditorWidget()
        self.spriteDataEditor.DataUpdate.connect(self.SpriteDataUpdated)
        sprite_dock = self.create_dock_widget(globals_.trans.string('SpriteDataEditor', 0), 'spriteeditor', self.spriteDataEditor,
                                            features, Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True, is_editor=True)
        self.spriteEditorDock = cast(ItemEditorDockWidget, sprite_dock)

        # Default Sprite Editor
        self.defaultDataEditor = SpriteEditorWidget(True)
        self.defaultDataEditor.setVisible(False)
        def_sprite_dock = self.create_dock_widget(globals_.trans.string('Palette', 7), 'defaultprops', self.defaultDataEditor,
                                                features | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable,
                                                Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True)
        self.defaultPropDock = def_sprite_dock

        # Entrance Editor
        self.entrance_editor = EntranceEditorWidget()
        entrance_dock = self.create_dock_widget(globals_.trans.string('EntranceDataEditor', 24), 'entranceeditor', self.entrance_editor,
                                              features, Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True, is_editor=True)
        self.entrance_editor_dock = cast(ItemEditorDockWidget, entrance_dock)

        # Location Editor
        self.location_editor = LocationEditorWidget()
        location_dock = self.create_dock_widget(globals_.trans.string('LocationDataEditor', 12), 'locationeditor', self.location_editor,
                                              features, Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True, is_editor=True)
        self.location_editor_dock = cast(ItemEditorDockWidget, location_dock)

        # Path (Node) Editor
        self.path_editor = PathNodeEditorWidget()
        path_dock = self.create_dock_widget(globals_.trans.string('PathDataEditor', 10), 'pathnodeeditor', self.path_editor,
                                            features, Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True, is_editor=True)
        self.path_editor_dock = cast(ItemEditorDockWidget, path_dock)

        # Palette
        features = QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable   | \
                   QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable | \
                   QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable

        palette_dock = self.create_dock_widget(globals_.trans.string('MenuItems', 96), 'palette', None, features,
                                             Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, True, False, True)
        self.palette_dock = cast(PaletteDock, palette_dock)

        # Create palette contents
        self.palette_dock.setup()
        self.palette_dock.current_tab_changed(0) # Default to the Objects tab

        # Palette toggle option
        act = self.palette_dock.toggleViewAction()
        if act is not None:
            act.setShortcut(GetKeybind('palette'))
            act.setIcon(GetIcon('palette'))
            act.setStatusTip(globals_.trans.string('MenuItems', 97))
            if self.vmenu is not None:
                self.vmenu.addAction(act)

            self.action_list['palette'] = act

        # Overview toggle action
        act = overview_dock.toggleViewAction()
        if act is not None:
            act.setShortcut(GetKeybind('leveloverview'))
            act.setIcon(GetIcon('globe-model'))
            act.setStatusTip(globals_.trans.string('MenuItems', 95))
            if self.vmenu is not None:
                self.vmenu.addAction(act)

            self.action_list['leveloverview'] = act

    def auto_save_level(self) -> None:
        """
        Auto saves the level
        """
        if not globals_.AutoSaveDirty:
            return

        data = globals_.Level.save()
        setSetting('AutoSaveFilePath', self.fileSavePath)
        setSetting('AutoSaveFileData', QtCore.QByteArray(data))
        globals_.AutoSaveDirty = False

    def track_clipboard_updates(self) -> None:
        """
        Catches systemwide clipboard updates
        """
        if globals_.Initializing:
            return

        clipboard = self.systemClipboard
        if clipboard is None:
            return

        clip = clipboard.text()
        if clip is not None and clip != '':
            clip = str(clip).strip()

            if clip.startswith('ReggieClip|') and clip.endswith('|%'):
                self.clipboard = clip.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

                self.action_list['paste'].setEnabled(True)
            else:
                self.clipboard = None
                self.action_list['paste'].setEnabled(False)

    def set_window_title(self) -> None:
        """
        Sets the window title accordingly
        """
        if self.fileSavePath:
            if globals_.UseFullFilepath:
                self.fileTitle = self.fileSavePath
            else:
                self.fileTitle = os.path.basename(self.fileSavePath)

        dirty_text = ''
        if globals_.Dirty:
            dirty_text = f' {globals_.trans.string('WindowTitle', 1)}' # '[unsaved]'

        # ' - Reggie Next' is added automatically by Qt (see QApplication.setApplicationDisplayName())
        self.setWindowTitle(f'{self.fileTitle}{dirty_text}')

    def exec_meta_info(self) -> None:
        """
        Records the Level Meta Information
        """
        dlg = MetaInfoDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dlg.save_info()

    def open_help_contents(self) -> None:
        """
        Shows the help contents webpage
        """
        file_path = os.path.join(get_reggiedata_folder(), 'help', 'index.html')
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(file_path))

    def open_tips(self):
        """
        Shows the tips and tricks page (redirect)
        """
        file_path = os.path.join(get_reggiedata_folder(), 'help', 'tips.html')
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(file_path))

    def select_all(self) -> None:
        """
        Select all objects in the current area, or selects all text in the focused widget
        """
        if globals_.app is None:
            return

        if globals_.app.activeWindow() is not globals_.mainWindow:
            focus = globals_.app.focusWidget()
            if focus is None:
                return

            if isinstance(focus, (QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit, QtWidgets.QLineEdit)):
                focus.selectAll()
            return

        paintRect = QtGui.QPainterPath()
        paintRect.addRect(0, 0, 1024 * 24, 512 * 24)
        self.scene.setSelectionArea(paintRect)

    def deselect(self):
        """
        Deselect all currently selected items
        """
        items = self.scene.selectedItems()
        for obj in items:
            obj.setSelected(False)

    def copy_(self, is_cut_action: bool) -> None:
        """
        Copies or cuts the selected items
        """
        selitems = self.scene.selectedItems()
        if is_cut_action:
            self.SelectionUpdateFlag = True
            self.scene.clearSelection()

        if selitems is not None:
            # Enable pasting and encode the ReggieClip
            self.action_list['paste'].setEnabled(True)
            self.clipboard = ReggieClip.get_reggie_clip(selitems)
            if self.systemClipboard is not None:
                self.systemClipboard.setText(self.clipboard)

            if is_cut_action:
                # Delete everything
                for obj in selitems:
                    obj.delete()
                    obj.setSelected(False)
                    self.scene.removeItem(obj)

                SetDirty()
                self.action_list['cut'].setEnabled(False)

        if is_cut_action:
            self.level_overview.update()
            self.SelectionUpdateFlag = False
            self.ChangeSelectionHandler()

    def cut(self) -> None:
        """
        Cuts the selected items
        """
        self.copy_(True)

    def copy(self) -> None:
        """
        Copies the selected items or text
        """
        if globals_.app is None:
            return

        # Check if we should copy selected text from a separate window
        if globals_.app.activeWindow() is not globals_.mainWindow:
            focus = globals_.app.focusWidget()
            if focus is not None:
                if isinstance(focus, (QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit)):
                    text = focus.textCursor().selectedText()
                elif isinstance(focus, QtWidgets.QLineEdit):
                    text = focus.selectedText()
                else:
                    return

                if self.systemClipboard is not None:
                    self.systemClipboard.setText(text)
            return

        # Main window is focused, copy selected items
        self.copy_(False)

    def paste(self) -> None:
        """
        Paste the selected items
        """
        if self.clipboard is not None:
            ReggieClip.paste_reggie_clip(self.clipboard)

    def exec_item_shift(self) -> None:
        """
        Shifts the selected level item(s)
        """
        dlg = ItemShiftDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dlg.shift_items()

    def exec_tileset_swap(self) -> None:
        """
        Swaps tilesets
        """
        dlg = TilesetSwapDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dlg.swap_tilesets()

    def add_new_area(self) -> None:
        """
        Adds a new area to the level
        """
        if len(globals_.Level.areas) >= 4:
            QtWidgets.QMessageBox.warning(self, globals_.trans.string('MenuItems', 78), globals_.trans.string('AreaImportDlg', 2))
            return

        # This is an unsaved new level if self.fileSavePath is None
        if CheckDirty() or self.fileSavePath is None:
            # Level is still dirty
            return

        newID = len(globals_.Level.areas) + 1
        globals_.Level.appendArea(None, None, None, None, None)

        self.load_level(self.fileSavePath, True, newID)

    def exec_area_import(self) -> None:
        """
        Imports an area from another level
        """
        if len(globals_.Level.areas) >= 4:
            QtWidgets.QMessageBox.warning(self, globals_.trans.string('AreaImportDlg', 0), globals_.trans.string('AreaImportDlg', 2))
            return

        if CheckDirty():
            return

        # Choose the area
        dlg = AreaImportDialog()
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Rejected:
            return

        dlg.import_area()

    def exec_area_delete(self) -> None:
        """
        Deletes the current area
        """
        dlg = AreaDeleteDialog()
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Rejected:
            return

        dlg.delete_area()

    def change_game_path(self, auto: bool = False) -> None:
        """
        Change the game path used by the current game definition
        """
        if CheckDirty():
            return

        while True:
            stage_path = QtWidgets.QFileDialog.getExistingDirectory(
                None,
                globals_.trans.string('ChangeGamePath', 0, '[game]', globals_.gamedef.name)
            )

            if stage_path == '':
                return False

            stage_path = str(stage_path)
            texture_path = os.path.join(stage_path, "Texture")

            while not os.path.isdir(texture_path):
                texture_path = QtWidgets.QFileDialog.getExistingDirectory(
                    None,
                    globals_.trans.string('ChangeGamePath', 4, '[game]', globals_.gamedef.name)
                )

                if texture_path == "":
                    return False

            if (not areValidGamePaths(stage_path, texture_path)) and (not globals_.gamedef.custom):  # custom gamedefs can use incomplete folders
                QtWidgets.QMessageBox.information(
                    None, globals_.trans.string('ChangeGamePath', 1),
                    globals_.trans.string('ChangeGamePath', 2)
                )
            else:
                SetGamePaths(stage_path, texture_path)
                break

        if not auto:
            # Try loading the first detected file in our Stage folder. If that fails, load up an empty canvas.
            ok = self.load_level(globals_.FirstStageFilename, True, 1)
            if not ok:
                self.load_level(None, False, 1)

        return True

    def exec_preferences(self) -> None:
        """
        Edit Reggie Next preferences
        """
        # Show the dialog
        dlg = PreferencesDialog()
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Rejected:
            return

        dlg.save_preferences()

    def new_level(self) -> None:
        """
        Create a new level
        """
        if CheckDirty():
            return

        self.load_level(None, False, 1)

    def open_from_name(self) -> None:
        """
        Open a level using the level picker
        """
        if CheckDirty():
            return

        LoadLevelNames()
        dlg = ChooseLevelNameDialog()
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.load_level(dlg.current_level, False, 1)

    def open_from_file(self) -> None:
        """
        Open a level using the filename
        """
        if CheckDirty():
            return

        # Use the currently open level's directory, if applicable
        if self.fileSavePath is not None:
            open_dir = os.path.dirname(self.fileSavePath)
        else:
            open_dir = ''

        filter = (
            f'{globals_.trans.string('FileDlgs', 9)} (*.arc *.arc.LH *.arc.LZ);;'
            f'{globals_.trans.string('FileDlgs', 1)} (*.arc);;'
            f'{globals_.trans.string('FileDlgs', 5)} (*.arc.LH);;'
            f'{globals_.trans.string('FileDlgs', 10)} (*.arc.LZ);;'
            f'{globals_.trans.string('FileDlgs', 2)} (*)'
        )
        fn = QtWidgets.QFileDialog.getOpenFileName(self, globals_.trans.string('FileDlgs', 0), open_dir, filter)[0]
        if fn == '':
            return

        self.load_level(str(fn), True, 1)

    def save_(self, name: str) -> bytearray | bytes | None:
        """
        Save a level back to the archive. Returns whether saving was successful.
        """
        data = globals_.Level.save()
        is_lz_compression = False

        # maybe need to compress the data
        if name.endswith(".arc.LZ"):
            compressed = lz77.CompressLZ77(data)
            if compressed is None:
                # Error during compression
                QtWidgets.QMessageBox.warning(None,
                    globals_.trans.string('Err_Save', 0),
                    globals_.trans.string('Err_Save', 3, '[file-size]', len(data))
                )

                return None

            is_lz_compression = True
            data = compressed

        # Pad file if needed
        # NOTE: We don't pad LZ-compressed files as
        # the game crashes trying to decompress them.
        if globals_.EnablePadding and not is_lz_compression:
            pad_length = globals_.PaddingLength - len(data)

            if pad_length < 0:
                # Original data is longer than padding data
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Save', 0),
                                                globals_.trans.string('Err_Save', 2, '[orig-len]', len(data), '[pad-len]', globals_.PaddingLength))
                return None

            data += bytes(pad_length)

        return data

    def save(self) -> bool:
        """
        Save a level back to the archive. Returns whether saving was successful.
        """
        if not self.fileSavePath or self.fileSavePath.endswith('.arc.LH'):
            # Delegate to save_as()
            return self.save_as()

        data = self.save_(self.fileSavePath)
        if data is None:
            return False

        try:
            with open(self.fileSavePath, 'wb') as f:
                f.write(data)
        except IOError as e:
            QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Save', 0),
                                            globals_.trans.string('Err_Save', 1, '[err1]', e.args[0], '[err2]', e.args[1]))
            return False

        globals_.Dirty = False
        globals_.AutoSaveDirty = False
        self.set_window_title()

        setSetting('AutoSaveFilePath', self.fileSavePath)
        setSetting('AutoSaveFileData', 'x')
        return True

    def save_as(self, is_copy: bool = False) -> bool:
        """
        Save a level back to the archive, with a new filename. Returns whether
        saving was successful.
        """
        caption = globals_.trans.string('FileDlgs', 8 if is_copy else 3)

        # Use the currently open level's directory, if applicable
        if self.fileSavePath is not None:
            save_dir = os.path.dirname(self.fileSavePath)
        else:
            save_dir = ''

        filter = (
            f'{globals_.trans.string('FileDlgs', 1)} (*.arc);;'
            f'{globals_.trans.string('FileDlgs', 10)} (*.arc.LZ);;'
            f'{globals_.trans.string('FileDlgs', 2)} (*)'
        )

        fn = QtWidgets.QFileDialog.getSaveFileName(self, caption, save_dir, filter)[0]
        if fn == '':  # No filename given - abort
            return False

        if not is_copy:
            globals_.AutoSaveDirty = False
            globals_.Dirty = False

            self.fileSavePath = fn
            if globals_.UseFullFilepath:
                self.fileTitle = fn
            else:
                self.fileTitle = os.path.basename(fn)

        data = self.save_(fn)
        if data is None:
            return False

        with open(fn, 'wb') as f:
            f.write(data)

        if not is_copy:
            setSetting('AutoSaveFilePath', fn)
            setSetting('AutoSaveFileData', 'x')

            self.set_window_title()
            self.RecentMenu.add_to_list(self.fileSavePath)

        return True

    def switch_area(self, idx: int) -> None:
        """
        Handle activated signals for area_combo_box
        """
        old_idx = globals_.Area.areanum - 1
        if idx == old_idx:
            return

        if CheckDirty():
            self.area_combo_box.setCurrentIndex(old_idx)
            return

        ok = self.load_level(self.fileSavePath, True, idx + 1)
        if not ok:
            # Loading the new area failed, so reset the combobox
            self.area_combo_box.setCurrentIndex(old_idx)

    def zoom_in(self, towards_cursor: bool = False) -> None:
        """
        Handle zooming in
        """
        z = self.ZoomLevel
        zi = self.ZoomLevels.index(z) + 1
        if zi < len(self.ZoomLevels):
            self.set_zoom(self.ZoomLevels[zi], towards_cursor)

    def zoom_out(self, towards_cursor: bool = False) -> None:
        """
        Handle zooming out
        """
        z = self.ZoomLevel
        zi = self.ZoomLevels.index(z) - 1
        if zi >= 0:
            self.set_zoom(self.ZoomLevels[zi], towards_cursor)

    def zoom_default(self) -> None:
        """
        Handle zooming to the default size
        """
        self.set_zoom(100.0)

    def zoom_min(self) -> None:
        """
        Handle zooming to the minimum size
        """
        self.set_zoom(self.ZoomLevels[0])

    def zoom_max(self) -> None:
        """
        Handle zooming to the maximum size
        """
        self.set_zoom(self.ZoomLevels[-1])

    def set_zoom(self, value: float | None, towards_cursor: bool = False) -> None:
        """
        Zoom to a specific level
        """
        if value is None:
            return

        if towards_cursor:
            self.view.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        tr = QtGui.QTransform()
        tr.scale(value / 100.0, value / 100.0)
        self.ZoomLevel = value
        self.view.setTransform(tr)
        self.level_overview.main_window_scale = value / 100.0

        if towards_cursor:
            # Reset back to original transformation anchor
            self.view.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)

        zi = self.ZoomLevels.index(value)
        self.action_list['zoommax'].setEnabled(zi < len(self.ZoomLevels) - 1)
        self.action_list['zoomin'].setEnabled(zi < len(self.ZoomLevels) - 1)
        self.action_list['zoomactual'].setEnabled(value != 100.0)
        self.action_list['zoomout'].setEnabled(zi > 0)
        self.action_list['zoommin'].setEnabled(zi > 0)

        self.ZoomWidget.set_zoom_level(value)
        self.ZoomStatusWidget.set_zoom_level(value)

        # Update the zone grabber rects, to resize for the new zoom level
        for z in globals_.Area.zones:
            z.UpdateRects()

        self.scene.update()

    def closeEvent(self, a0: QtGui.QCloseEvent | None) -> None:
        """
        Handler for the main window close event
        """
        if a0 is None:
            return

        if CheckDirty():
            a0.ignore()
            return

        # Save our state
        self.spriteEditorDock.set_active(False)
        self.entrance_editor_dock.set_active(False)
        self.path_editor_dock.set_active(False)
        self.location_editor_dock.set_active(False)
        self.defaultPropDock.setVisible(False)

        # State: determines positions of docks
        # Geometry: determines the main window position
        setSetting('MainWindowState', self.saveState(0))
        setSetting('MainWindowGeometry', self.saveGeometry())

        globals_.gamedef.SetLastLevel(str(self.fileSavePath))

        # Save some other settings not handled by Preferences
        setSetting('ZoomLevel', self.ZoomLevel)
        setSetting('InsertPathNode', globals_.InsertPathNode)
        setSetting('AutoSaveFilePath', None)
        setSetting('AutoSaveFileData', 'x')

        a0.accept()

    def load_level(self, name: str | None, is_full_path: bool, area_num: int) -> bool:
        """
        Load a level from NSMBW into the editor.
        """
        new = name is None
        same = False

        level_data = bytes()

        if not new:
            check_names = []
            if is_full_path:
                check_names = [name]
            else:
                # Get this name with all possible archive extensions
                for ext in globals_.FileExtentions:
                    check_names.append(os.path.join(str(globals_.gamedef.GetStageGamePath()), name + ext))

            for check_name in check_names:
                if os.path.isfile(check_name):
                    break
            else:
                base_name = f'{os.path.splitext(check_names[0])[0]}.arc'
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_CantFindLevel', 1),
                                              globals_.trans.string('Err_CantFindLevel', 0, '[name]', base_name),
                                              QtWidgets.QMessageBox.StandardButton.Ok)
                return False

            if not IsValidLevel(check_name):
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_InvalidLevel', 1), globals_.trans.string('Err_InvalidLevel', 0),
                                              QtWidgets.QMessageBox.StandardButton.Ok)
                return False

            name = check_name
            same = name == self.fileSavePath  # Just an area change

        # Get the file path, if possible
        if new:
            # Set the filepath variables
            self.fileSavePath = None
            self.fileTitle = str(globals_.trans.string('WindowTitle', 0))

        elif not same:
            # Get the data
            if not globals_.RestoredFromAutoSave:
                # Set the filepath variables
                self.fileSavePath = name
                if self.fileSavePath is None:
                    return False

                if globals_.UseFullFilepath:
                    self.fileTitle = self.fileSavePath
                else:
                    self.fileTitle = os.path.basename(self.fileSavePath)

                # Open the file
                with open(self.fileSavePath, 'rb') as fileobj:
                    level_data = fileobj.read()

                # Do we need to decompress it?
                level_data = DecompressLevel(level_data, str(name))
                if level_data is None:
                    return False
            else:
                # Auto-saved level. Check if there's a path associated with it:
                if globals_.AutoSavePath == 'None':
                    self.fileSavePath = None
                    self.fileTitle = globals_.trans.string('WindowTitle', 0)
                else:
                    self.fileSavePath = globals_.AutoSavePath
                    if globals_.UseFullFilepath:
                        self.fileTitle = self.fileSavePath
                    else:
                        name = globals_.AutoSavePath
                        self.fileTitle = os.path.basename(name)

                # Get the level data
                level_data = globals_.AutoSaveData
                SetDirty(noautosave=True)

                # Turn off the autosave flag
                globals_.RestoredFromAutoSave = False

        # Turn the dirty flag off, and keep it that way
        globals_.Dirty = False
        globals_.DirtyOverride += 1

        # First, clear out the existing level.
        self.scene.clearSelection()
        self.CurrentSelection = []
        self.scene.clear()

        # Clear out all level-thing lists
        for item_list in (
            self.palette_dock.sprite_tab.sprite_list,
            self.palette_dock.sprite_tab.sprite_order_list,
            self.palette_dock.entrance_tab.entrance_list,
            self.palette_dock.location_tab.location_list,
            self.palette_dock.path_tab.path_list,
            self.palette_dock.comment_tab.comment_list
        ):
            item_list.clear()
            sel_model = item_list.selectionModel()
            if sel_model is not None:
                sel_model.setCurrentIndex(QtCore.QModelIndex(), QtCore.QItemSelectionModel.SelectionFlag.Clear)

        # Reset these here, because if they are set after
        # creating the objects, they use the old values.
        globals_.CurrentLayer = 1
        globals_.Layer0Shown = True
        globals_.Layer1Shown = True
        globals_.Layer2Shown = True

        # Also enable things that use 'True' by default
        globals_.SpritesShown = True
        globals_.SpriteImagesShown = True
        globals_.LocationsShown = True
        globals_.EntrancesShown = True
        globals_.PathsShown = True
        globals_.CommentsShown = True

        # Prevent things from snapping when they're created
        globals_.OverrideSnapping = True

        # Load the actual level
        if new:
            self.create_level_()
        elif not same:
            self.load_level_(level_data, area_num)
        else:
            # We have already loaded this area's data - it's stored as
            # AbstractAreas in the Level. This means we do not have to open and
            # optionally decompress the level file. Hence, we can just relay
            # this to the level.
            globals_.Level.changeArea(area_num)
            globals_.Area.reset()

        # Fill up the area list
        self.area_combo_box.clear()

        for area in globals_.Level.areas:
            self.area_combo_box.addItem(globals_.trans.string('AreaCombobox', 0, '[num]', area.areanum))

        self.area_combo_box.setCurrentIndex(area_num - 1)

        # Refresh object layouts
        for layer in globals_.Area.layers:
            for obj in layer:
                obj.updateObjCache()

        for sprite in globals_.Area.sprites:
            sprite.UpdateDynamicSizing()
            sprite.ImageObj.positionChanged()

        # Scroll to the initial entrance
        center_pos = QtCore.QPointF(0, 0)
        found_ent = False
        start_ent_id = globals_.Area.start_entrance

        for ent in globals_.Area.entrances:
            if area_num == 1 and ent.entid == start_ent_id:
                center_pos = ent.pos()
                found_ent = True
                break
        else:
            # Try to center on the first entrance in the list
            if globals_.Area.entrances:
                center_pos = globals_.Area.entrances[0].pos()
                found_ent = True

        # For some reason, there's a noticeable offset when launching
        # Reggie, so we need to manually adjust the position here
        if found_ent and globals_.Initializing:
            offset_fix = QtCore.QPointF(492, 179)
            center_pos -= offset_fix

        self.view.centerOn(center_pos)

        # Reset some editor things
        self.action_list['showlay0'].setChecked(True)
        self.action_list['showlay1'].setChecked(True)
        self.action_list['showlay2'].setChecked(True)
        self.action_list['showsprites'].setChecked(True)
        self.action_list['showspriteimages'].setChecked(True)
        self.action_list['showentrances'].setChecked(True)
        self.action_list['showlocations'].setChecked(True)
        self.action_list['showpaths'].setChecked(True)
        self.action_list['showcomments'].setChecked(True)
        self.action_list['addarea'].setEnabled(len(globals_.Level.areas) < 4)
        self.action_list['importarea'].setEnabled(len(globals_.Level.areas) < 4)
        self.action_list['deletearea'].setEnabled(len(globals_.Level.areas) > 1)
        self.action_list['backgrounds'].setEnabled(len(globals_.Area.zones) > 0)

        if not globals_.Initializing:
            self.set_zoom(100.0)

        # Turn snapping back on
        globals_.OverrideSnapping = False

        # Turn the dirty flag off
        globals_.DirtyOverride -= 1
        self.set_window_title()

        # Update UI things
        self.scene.update()

        self.level_overview.reset()
        self.level_overview.update()

        if new:
            SetDirty()
        elif not same:
            # Add the path to Recent Files
            self.RecentMenu.add_to_list(self.fileSavePath)

        return True

    def create_level_(self) -> None:
        """
        Creates a new level, do not call this directly
        """
        globals_.Level = NSMBWLevel()
        globals_.Level.new()

        self.palette_dock.object_tab.reset(True)

        self.action_list['swapobjectstypes'].setEnabled(True)
        self.action_list['swapobjectstilesets'].setEnabled(True)

    def load_level_(self, level_data: bytes, area_num: int) -> None:
        """
        Performs all level-loading tasks specific to New Super Mario Bros. Wii levels.
        Do not call this directly - use load_level instead!
        """
        # Create the new level object
        globals_.Level = NSMBWLevel()

        # Load it
        if not globals_.Level.load(level_data, area_num):
            raise Exception

        # https://github.com/Zement/Reggie/blob/master/reggie.py#L3630-L3637
        # Check for unknown sprite IDs and show warning message
        if globals_.ShowUnknownSpriteWarning:
            if hasattr(globals_.Area, 'unknown_sprite_ids') and globals_.Area.unknown_sprite_ids is not None:
                sprite_ids = sorted(globals_.Area.unknown_sprite_ids)

                if len(sprite_ids) == 1:
                    msg = globals_.trans.string('Err_UnknownSprite', 1, '[id]', str(sprite_ids[0]))
                else:
                    msg = globals_.trans.string('Err_UnknownSprite', 2, '[ids]', ', '.join(map(str, sprite_ids)))

                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_UnknownSprite', 0), msg)

        globals_.Area.reset()

    def ChangeSelectionHandler(self) -> None:
        """
        Update the visible panels whenever the selection changes
        """
        if self.SelectionUpdateFlag:
            return

        try:
            selitems = self.scene.selectedItems()
        except RuntimeError:
            # must catch this error: if you close the app while something is selected,
            # you get a RuntimeError about the 'underlying C++ object being deleted'
            return

        # do this to avoid flicker
        show_sprite_dock = False
        show_entrance_dock = False
        show_location_dock = False
        show_path_dock = False
        update_mode_info = False

        # clear our variables
        self.selObj = None
        self.selObjs = None

        self.palette_dock.entrance_tab.entrance_list.setCurrentItem(None)
        self.palette_dock.location_tab.location_list.setCurrentItem(None)
        self.palette_dock.path_tab.path_list.setCurrentItem(None)
        self.palette_dock.comment_tab.comment_list.setCurrentItem(None)

        # possibly a small optimization
        func_ii = isinstance
        type_obj = ObjectItem
        type_spr = SpriteItem
        type_ent = EntranceItem
        type_loc = LocationItem
        type_path = PathItem
        type_com = CommentItem

        allowStamp = True

        if not selitems:
            # nothing is selected
            self.action_list['cut'].setEnabled(False)
            self.action_list['copy'].setEnabled(False)
            self.action_list['shiftitems'].setEnabled(False)
            self.action_list['mergelocations'].setEnabled(False)

        elif len(selitems) == 1:
            # only one item, check the type
            self.action_list['cut'].setEnabled(True)
            self.action_list['copy'].setEnabled(True)
            self.action_list['shiftitems'].setEnabled(True)
            self.action_list['mergelocations'].setEnabled(False)

            item = selitems[0]
            self.selObj = item
            if func_ii(item, type_obj):
                allowStamp = True
            elif func_ii(item, type_spr):
                show_sprite_dock = True
                update_mode_info = True
                allowStamp = True
            elif func_ii(item, type_ent):
                self.palette_dock.set_tab(2)
                self.UpdateFlag = True
                self.palette_dock.entrance_tab.entrance_list.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                show_location_dock = True
                update_mode_info = True
                allowStamp = False
            elif func_ii(item, type_loc):
                self.palette_dock.set_tab(3)
                self.UpdateFlag = True
                self.palette_dock.location_tab.location_list.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                show_location_dock = True
                update_mode_info = True
                allowStamp = False
            elif func_ii(item, type_path):
                self.palette_dock.set_tab(4)
                self.UpdateFlag = True
                self.palette_dock.path_tab.path_list.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                show_path_dock = True
                update_mode_info = True
                allowStamp = False
            elif func_ii(item, type_com):
                self.palette_dock.set_tab(7)
                self.UpdateFlag = True
                self.palette_dock.comment_tab.comment_list.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                update_mode_info = True
                allowStamp = False

        else:
            update_mode_info = True

            for item in selitems:
                if not func_ii(item, (type_obj, type_spr)):
                    allowStamp = False

            # more than one item
            self.action_list['cut'].setEnabled(True)
            self.action_list['copy'].setEnabled(True)
            self.action_list['shiftitems'].setEnabled(True)

        # turn on the Stamp Add btn if applicable
        self.palette_dock.stamp_tab.add_button.setEnabled(bool(selitems) and allowStamp)

        # count the # of each type, for the statusbar label
        spr = 0
        ent = 0
        obj = 0
        loc = 0
        path = 0
        com = 0
        for item in selitems:
            if func_ii(item, type_spr): spr += 1
            if func_ii(item, type_ent): ent += 1
            if func_ii(item, type_obj): obj += 1
            if func_ii(item, type_loc): loc += 1
            if func_ii(item, type_path): path += 1
            if func_ii(item, type_com): com += 1

        self.action_list['mergelocations'].setEnabled(loc >= 2)
        self.palette_dock.object_tab.layer_change_button.setEnabled(obj != 0)

        # write the statusbar label text
        text = ''
        if selitems:
            singleitem = len(selitems) == 1
            if singleitem:
                if obj:
                    text = globals_.trans.string('Statusbar', 0)  # 1 object selected
                elif spr:
                    text = globals_.trans.string('Statusbar', 1)  # 1 sprite selected
                elif ent:
                    text = globals_.trans.string('Statusbar', 2)  # 1 entrance selected
                elif loc:
                    text = globals_.trans.string('Statusbar', 3)  # 1 location selected
                elif path:
                    text = globals_.trans.string('Statusbar', 4)  # 1 path node selected
                else:
                    text = globals_.trans.string('Statusbar', 29)  # 1 comment selected
            else:  # multiple things selected; see if they're all the same type
                if not any((spr, ent, loc, path, com)):
                    text = globals_.trans.string('Statusbar', 5, '[x]', obj)  # x objects selected
                elif not any((obj, ent, loc, path, com)):
                    text = globals_.trans.string('Statusbar', 6, '[x]', spr)  # x sprites selected
                elif not any((obj, spr, loc, path, com)):
                    text = globals_.trans.string('Statusbar', 7, '[x]', ent)  # x entrances selected
                elif not any((obj, spr, ent, path, com)):
                    text = globals_.trans.string('Statusbar', 8, '[x]', loc)  # x locations selected
                elif not any((obj, spr, ent, loc, com)):
                    text = globals_.trans.string('Statusbar', 9, '[x]', path)  # x path nodes selected
                elif not any((obj, spr, ent, path, loc)):
                    text = globals_.trans.string('Statusbar', 30, '[x]', com)  # x comments selected
                else:  # different types
                    text = globals_.trans.string('Statusbar', 10, '[x]', len(selitems))  # x items selected
                    types = (
                        (obj, 12, 13),  # variable, translation string ID if var == 1, translation string ID if var > 1
                        (spr, 14, 15),
                        (ent, 16, 17),
                        (loc, 18, 19),
                        (path, 20, 21),
                        (com, 31, 32),
                    )
                    first = True
                    for var, singleCode, multiCode in types:
                        if var > 0:
                            if not first: text += globals_.trans.string('Statusbar', 11)
                            first = False
                            text += globals_.trans.string('Statusbar', (singleCode if var == 1 else multiCode), '[x]', var)
                            # above: '[x]', var) can't hurt if var == 1

                    text += globals_.trans.string('Statusbar', 22)  # ')'

        self.selectionLabel.setText(text)

        self.CurrentSelection = selitems

        for thing in selitems:
            # This helps sync non-objects with objects while dragging
            if not isinstance(thing, ObjectItem):
                thing.dragoffsetx = (((thing.objx // 16) * 16) - thing.objx) * 1.5
                thing.dragoffsety = (((thing.objy // 16) * 16) - thing.objy) * 1.5

        self.spriteEditorDock.set_active(show_sprite_dock)
        self.entrance_editor_dock.set_active(show_entrance_dock)
        self.location_editor_dock.set_active(show_location_dock)
        self.path_editor_dock.set_active(show_path_dock)

        self.action_list['deselect'].setEnabled(bool(selitems))

        if update_mode_info:
            globals_.DirtyOverride += 1
            self.UpdateModeInfo()
            globals_.DirtyOverride -= 1

    def SpriteDataUpdated(self, data):
        """
        Handle the current sprite's data being updated
        """
        if self.spriteEditorDock.is_active():
            obj = self.selObj
            if isinstance(obj, SpriteItem):
                obj.spritedata = data
                obj.UpdateListItem()
                SetDirty()

                obj.UpdateDynamicSizing()
                self.palette_dock.sprite_tab.sprite_list.updateSprite(obj)

    def UpdateModeInfo(self):
        """
        Change the info in the currently visible panel
        """
        self.UpdateFlag = True

        if isinstance(self.selObj, SpriteItem) and self.spriteEditorDock.is_active():
            obj = self.selObj
            self.spriteDataEditor.setSprite(obj.sprite_num, initial_data=obj.spritedata)
        elif isinstance(self.selObj, EntranceItem) and self.entrance_editor_dock.is_active():
            self.entrance_editor.set_entrance(self.selObj)
        elif isinstance(self.selObj, PathItem) and self.path_editor_dock.is_active():
            self.path_editor.setPath(self.selObj)
        elif isinstance(self.selObj, LocationItem) and self.location_editor_dock.is_active():
            self.location_editor.set_location(self.selObj)

        self.UpdateFlag = False

    def PositionHovered(self, x, y):
        """
        Handle a position being hovered in the view
        """
        info = ''
        hovereditems = self.scene.items(QtCore.QPointF(x, y))
        hovered = None
        type_zone = ZoneItem
        type_peline = PathEditorLineItem
        for item in hovereditems:
            hover = item.hover if hasattr(item, 'hover') else True
            if (not isinstance(item, (type_zone, type_peline))) and hover:
                hovered = item
                break

        if hovered is not None:
            if isinstance(hovered, ObjectItem):  # Object
                info = globals_.trans.string('Statusbar', 23, '[width]', hovered.width, '[height]', hovered.height, '[xpos]',
                                    hovered.objx, '[ypos]', hovered.objy, '[layer]', hovered.layer, '[type]',
                                    hovered.object_num, '[tileset]', hovered.tileset + 1)
            elif isinstance(hovered, SpriteItem):  # Sprite
                info = globals_.trans.string('Statusbar', 24, '[name]', hovered.name, '[xpos]', hovered.objx, '[ypos]',
                                    hovered.objy)
            elif isinstance(hovered, SLib.AuxiliaryItem):  # Sprite (auxiliary thing) (treat it like the actual sprite)
                info = globals_.trans.string('Statusbar', 24, '[name]', hovered.parentItem().name, '[xpos]',
                                    hovered.parentItem().objx, '[ypos]', hovered.parentItem().objy)
            elif isinstance(hovered, EntranceItem):  # Entrance
                info = globals_.trans.string('Statusbar', 25, '[name]', hovered.name, '[xpos]', hovered.objx, '[ypos]',
                                    hovered.objy, '[dest]', hovered.destination)
            elif isinstance(hovered, LocationItem):  # Location
                info = globals_.trans.string('Statusbar', 26, '[id]', int(hovered.id), '[xpos]', int(hovered.objx), '[ypos]',
                                    int(hovered.objy), '[width]', int(hovered.width), '[height]', int(hovered.height))
            elif isinstance(hovered, PathItem):  # Path
                info = globals_.trans.string('Statusbar', 27, '[path]', hovered.pathid, '[node]', hovered.nodeid, '[xpos]',
                                    hovered.objx, '[ypos]', hovered.objy)
            elif isinstance(hovered, CommentItem):  # Comment
                info = globals_.trans.string('Statusbar', 33, '[xpos]', hovered.objx, '[ypos]', hovered.objy, '[text]',
                                    hovered.OneLineText())

        self.posLabel.setText(
            globals_.trans.string('Statusbar', 28, '[objx]', int(x / 24), '[objy]', int(y / 24), '[sprx]', int(x / 1.5),
                         '[spry]', int(y / 1.5)))
        self.hoverLabel.setText(info)

    def keyPressEvent(self, a0):
        """
        Handles key press events for the main window if needed
        """
        if a0 is None:
            return

        if a0.key() == Qt.Key.Key_Delete or a0.key() == Qt.Key.Key_Backspace:
            sel = self.scene.selectedItems()
            if sel:
                self.SelectionUpdateFlag = True

                for obj in sel:
                    obj.delete()
                    obj.setSelected(False)
                    self.scene.removeItem(obj)

                SetDirty()
                a0.accept()
                self.level_overview.update()
                self.SelectionUpdateFlag = False
                self.ChangeSelectionHandler()
                return

        self.level_overview.update()

        QtWidgets.QMainWindow.keyPressEvent(self, a0)

    def HandleAreaOptions(self):
        """
        Pops up the options for Area Dialogue
        """
        dlg = AreaOptionsDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dlg.save()
        self.scene.update()

    def HandleZones(self):
        """
        Pops up the options for Zone dialog
        """
        LoadZoneThemes()

        dlg = ZonesDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            self.level_overview.update()
            return

        dlg.save()

    def HandleBG(self):
        """
        Pops up the Background settings Dialog
        """
        dlg = BackgroundDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dlg.save()

    def HandleScreenshot(self):
        """
        Takes a screenshot of the entire level and saves it
        """
        dlg = ScreenshotDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dlg.create_screenshot()

    def HandleCameraProfiles(self):
        """
        Pops up the options for camera profiles
        """
        dlg = CameraProfilesDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dlg.save()
