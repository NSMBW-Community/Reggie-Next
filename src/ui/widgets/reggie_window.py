import os.path
import struct
import sys

from typing import cast

from PyQt6 import QtCore, QtGui, QtWidgets
Qt = QtCore.Qt

from data import globals_

from data.common import archive
import spritelib as SLib

from libs import lh, lib_versions, lz77
from ui.theme.reggie_theme import GetIcon, SetColorScheme
from data.common.loaders import LoadMenuActions, LoadLevelNames, LoadZoneThemes, GetKeybind, SetKeybind
from data.common.utils import clamp, SetGamePaths, get_reggiedata_folder
from data.common.validators import IsNSMBLevel, areValidGamePaths
from ui.widgets.level_scene import LevelScene
from ui.widgets.level_view import LevelViewWidget
from data.level.dirty import SetDirty, CheckDirty
from data.common.settings import setting, setSetting
from data.level.items.basic import LevelEditorItem
from data.level.items.comment import CommentItem
from data.level.items.entrance import EntranceItem
from data.level.items.location import LocationItem
from data.level.items.object import ObjectItem
from data.level.items.path import PathItem
from data.level.items.path_editor_line import PathEditorLineItem
from data.level.items.sprite import SpriteItem
from data.level.items.zone import ZoneItem
from data.level.path import Path
from data.common.loaders import UnloadTileset, LoadTileset
from data.level.nsmbw_level import NSMBWLevel
from ui.widgets.spriteeditor.sprite_editor import SpriteEditorWidget
from ui.actions.undo.undo_stack import UndoStack

from ui.dialogs.area import AreaOptionsDialog
from ui.dialogs.area_import import AreaImportDialog
from ui.dialogs.background import BackgroundDialog
from ui.dialogs.camera_profile import CameraProfilesDialog
from ui.dialogs.choose_level_name import ChooseLevelNameDialog
from ui.dialogs.item_shift import ItemShiftDialog
from ui.dialogs.meta_info import MetaInfoDialog
from ui.dialogs.obj_tileset_swap import ObjectTilesetSwapDialog
from ui.dialogs.preference import PreferencesDialog
from ui.dialogs.screenshot import ScreenshotDialog
from ui.dialogs.sprite_switch import SpriteSwitchDialog
from ui.dialogs.zone import ZonesDialog

from ui.menus.game_def_menu import GameDefMenu
from ui.menus.recent_files_menu import RecentFilesMenu

from ui.widgets.preferences.widgets.toolbar_check_box import ToolbarCheckBox
from ui.widgets.preferences.widgets.keybind_line_edit import KeybindLineEdit
from ui.widgets.preferences.widgets.keybind_editor_tab import KeybindEditorTab

from ui.widgets.zoom import ZoomWidget
from ui.widgets.zoom_status import ZoomStatusWidget
from ui.widgets.diagnostic import DiagnosticWidget
from ui.widgets.level_overview import LevelOverviewWidget

from ui.widgets.editors.entrance import EntranceEditorWidget
from ui.widgets.editors.location import LocationEditorWidget
from ui.widgets.editors.path_node import PathNodeEditorWidget

from ui.widgets.palette_dock import PaletteDock
from data.common.reggie_clip import ReggieClip

################################################################################
################################################################################
################################################################################

class ReggieWindow(QtWidgets.QMainWindow):
    """
    Reggie main level editor window
    """
    action_list: dict[str, QtGui.QAction] = {}

    def CreateDockWidget(self, title, obj_name, widget, features, area, allowed_areas, visible, floating, is_palette = False):
        """
        Helper function to create docks
        """
        if is_palette:
            dock = PaletteDock(title, self)
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

    def __init__(self):
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
        self.setWindowIcon(QtGui.QIcon(os.path.join(get_reggiedata_folder(), 'icon.png')))
        self.setIconSize(QtCore.QSize(16, 16))
        self.setUnifiedTitleAndToolBarOnMac(True)

        # Create the level view
        self.scene = LevelScene(0, 0, 1024 * 24, 512 * 24, self)
        self.scene.setItemIndexMethod(QtWidgets.QGraphicsScene.ItemIndexMethod.NoIndex)
        self.scene.selectionChanged.connect(self.ChangeSelectionHandler)

        self.view = LevelViewWidget(self.scene, self)
        self.view.centerOn(0, 0) # This scrolls to the top left
        self.view.PositionHover.connect(self.PositionHovered)
        self.view.XScrollBar.valueChanged.connect(self.XScrollChange)
        self.view.YScrollBar.valueChanged.connect(self.YScrollChange)
        self.view.FrameSize.connect(self.HandleWindowSizeChange)

        # Done creating the window!
        self.setCentralWidget(self.view)

        # Set up the clipboard stuff
        self.clipboard = None
        self.systemClipboard = QtWidgets.QApplication.clipboard()
        if self.systemClipboard is not None:
            self.systemClipboard.dataChanged.connect(self.TrackClipboardUpdates)

    def __init2__(self):
        """
        Finishes initialization. (fixes bugs with some widgets calling globals_.mainWindow.something before it's init'ed)
        """
        self.auto_save_timer = QtCore.QTimer()
        self.auto_save_timer.timeout.connect(self.Autosave)
        self.auto_save_timer.start(20000) # 20 seconds

        # Set up actions and menus
        self.RecentMenu = RecentFilesMenu()
        self.GameDefMenu = GameDefMenu()
        self.setup_menu_bar()

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
            act.setIcon(GetIcon('diagnostics'))
            if self.vmenu is not None:
                self.vmenu.addAction(act)

            self.action_list['toolbar'] = act

        # Now get stuff ready
        loaded = False
        self.fileSavePath = None

        if len(sys.argv) > 1 and IsNSMBLevel(sys.argv[1]):
            # There's a level in the args, load that
            loaded = self.LoadLevel(sys.argv[1], True, 1)
        else:
            # Try the last level loaded with this game patch
            last_level = globals_.gamedef.GetLastLevel()
            if last_level is not None:
                loaded = self.LoadLevel(last_level, True, 1)

        # Fall back to the first level in the current patch's Stage folder
        if not loaded:
            self.LoadLevel(globals_.FirstStageFilename, True, 1)

        # Call toggle-button handlers to set each feature correctly upon startup
        toggle_handlers = {
            self.HandleSpritesVisibility: globals_.SpritesShown,
            self.HandleSpriteImages: globals_.SpriteImagesShown,
            self.HandleEntrancesVisibility: globals_.EntrancesShown,
            self.HandleLocationsVisibility: globals_.LocationsShown,
            self.HandleCommentsVisibility: globals_.CommentsShown,
            self.HandlePathsVisibility: globals_.PathsShown,
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

        # Restore zoom level
        zoom = setting('ZoomLevel', 100.0)
        self.ZoomTo(zoom, towardsCursor=False)

        # Set initial state for diagnostic widget
        # Calling this while the auto-diag is initing
        # will cause the 'no zones' check to always fail
        if globals_.AutoDiagEnabled:
            self.diagnostic.update_status()

        globals_.Initializing = False

    def setup_status_bar(self):
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

    def setup_menu_bar(self):
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
        self.area_combo_box.activated.connect(self.HandleSwitchArea)

        self.setup_toolbar()

    def setup_help_menu(self, menu=None):
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

    def setup_toolbar(self):
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

    def setup_docks(self):
        """
        Sets up the dock widgets and panels
        """
        # Level Overview
        self.level_overview = LevelOverviewWidget()
        self.level_overview.moved.connect(self.HandleOverviewClick)
        features = QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable   | \
                   QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable | \
                   QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable

        overview_dock = self.CreateDockWidget(globals_.trans.string('MenuItems', 94), 'leveloverview', self.level_overview,
                                              features, Qt.DockWidgetArea.RightDockWidgetArea, None, True, False)
        self.level_overview_dock = overview_dock

        # These apply to all editor docks
        features = QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
        allowed_areas = Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea

        # Sprite Editor
        self.spriteDataEditor = SpriteEditorWidget()
        self.spriteDataEditor.DataUpdate.connect(self.SpriteDataUpdated)
        sprite_dock = self.CreateDockWidget(globals_.trans.string('SpriteDataEditor', 0), 'spriteeditor', self.spriteDataEditor,
                                            features, Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True)
        self.spriteEditorDock = sprite_dock

        # Default Sprite Editor
        self.defaultDataEditor = SpriteEditorWidget(True)
        self.defaultDataEditor.setVisible(False)
        def_sprite_dock = self.CreateDockWidget(globals_.trans.string('Palette', 7), 'defaultprops', self.defaultDataEditor,
                                                features | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable,
                                                Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True)
        self.defaultPropDock = def_sprite_dock

        # Entrance Editor
        self.entrance_editor = EntranceEditorWidget()
        entrance_dock = self.CreateDockWidget(globals_.trans.string('EntranceDataEditor', 24), 'entranceeditor', self.entrance_editor,
                                              features, Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True)
        self.entrance_editor_dock = entrance_dock

        # Location Editor
        self.location_editor = LocationEditorWidget()
        location_dock = self.CreateDockWidget(globals_.trans.string('LocationDataEditor', 12), 'locationeditor', self.location_editor,
                                              features, Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True)
        self.location_editor_dock = location_dock

        # Path (Node) Editor
        self.path_editor = PathNodeEditorWidget()
        path_dock = self.CreateDockWidget(globals_.trans.string('PathDataEditor', 10), 'pathnodeeditor', self.path_editor,
                                            features, Qt.DockWidgetArea.RightDockWidgetArea, allowed_areas, False, True)
        self.path_editor_dock = path_dock

        # Palette
        features = QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable   | \
                   QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable | \
                   QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable

        palette_dock = self.CreateDockWidget(globals_.trans.string('MenuItems', 96), 'palette', None, features,
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
            act.setIcon(GetIcon('overview'))
            act.setStatusTip(globals_.trans.string('MenuItems', 95))
            if self.vmenu is not None:
                self.vmenu.addAction(act)

            self.action_list['leveloverview'] = act

    def Autosave(self):
        """
        Auto saves the level
        """
        if not globals_.AutoSaveDirty:
            return

        data = globals_.Level.save()
        setSetting('AutoSaveFilePath', self.fileSavePath)
        setSetting('AutoSaveFileData', QtCore.QByteArray(data))
        globals_.AutoSaveDirty = False

    def TrackClipboardUpdates(self):
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

    def XScrollChange(self, pos):
        """
        Moves the Overview current position box based on X scroll bar value
        """
        self.level_overview.pos_x_locator = pos
        self.level_overview.update()

    def YScrollChange(self, pos):
        """
        Moves the Overview current position box based on Y scroll bar value
        """
        self.level_overview.pos_y_locator = pos
        self.level_overview.update()

    def HandleWindowSizeChange(self, w, h):
        self.level_overview.height_locator = h
        self.level_overview.width_locator = w
        self.level_overview.update()

    def UpdateTitle(self):
        """
        Sets the window title accordingly
        """
        dirty_text = ''
        if globals_.Dirty:
            dirty_text = f' {globals_.trans.string('MainWindow', 0)}' # '[unsaved]'

        # ' - Reggie Next' is added automatically by Qt (see QApplication.setApplicationDisplayName())
        self.setWindowTitle(f'{self.fileTitle}{dirty_text}')

    def HandleInfo(self):
        """
        Records the Level Meta Information
        """
        if globals_.Area.areanum == 1:
            dlg = MetaInfoDialog()
            if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                globals_.Area.Metadata.setStrData('Creator', f'Reggie! Next {globals_.ReggieVersionShort}')
                globals_.Area.Metadata.setStrData('Title', dlg.name_field.text())
                globals_.Area.Metadata.setStrData('Author', dlg.author_field.text())
                globals_.Area.Metadata.setStrData('Group', dlg.group_field.text())
                globals_.Area.Metadata.setStrData('Website', dlg.website_field.text())

                SetDirty()
        else:
            dlg = QtWidgets.QMessageBox()
            dlg.setText(globals_.trans.string('InfoDlg', 14))
            dlg.exec()

    def HelpBox(self):
        """
        Shows the help box
        """
        file_path = os.path.join(get_reggiedata_folder(), 'help', 'index.html')

        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(file_path))

    def TipBox(self):
        """
        Reggie Next Tips and Commands
        """
        file_path = os.path.join(get_reggiedata_folder(), 'help', 'tips.html')

        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(file_path))

    def SelectAll(self):
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

    def Deselect(self):
        """
        Deselect all currently selected items
        """
        items = self.scene.selectedItems()
        for obj in items:
            obj.setSelected(False)

    def CopyOrCut(self, cutAction):
        """
        Copies or cuts the selected items
        """
        selitems = self.scene.selectedItems()
        if cutAction:
            self.SelectionUpdateFlag = True
            self.scene.clearSelection()

        if selitems is not None:
            # Enable pasting and encode the ReggieClip
            self.action_list['paste'].setEnabled(True)
            self.clipboard = ReggieClip.get_reggie_clip(selitems)
            if self.systemClipboard is not None:
                self.systemClipboard.setText(self.clipboard)

            if cutAction:
                # Delete everything
                for obj in selitems:
                    obj.delete()
                    obj.setSelected(False)
                    self.scene.removeItem(obj)

                SetDirty()
                self.action_list['cut'].setEnabled(False)

        if cutAction:
            self.level_overview.update()
            self.SelectionUpdateFlag = False
            self.ChangeSelectionHandler()

    def Cut(self):
        """
        Cuts the selected items
        """
        self.CopyOrCut(True)

    def Copy(self):
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
        self.CopyOrCut(False)

    def Paste(self):
        """
        Paste the selected items
        """
        if self.clipboard is not None:
            ReggieClip.paste_reggie_clip(self.clipboard)

    def ShiftItems(self):
        """
        Shifts the selected object(s)
        """
        items = self.scene.selectedItems()
        if not items:
            return

        dlg = ItemShiftDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        offs_x = dlg.offset_x.value()
        offs_y = dlg.offset_y.value()

        # Do we need to do anything?
        if offs_x == 0 and offs_y == 0:
            return

        if ((offs_x % 16) != 0) or ((offs_y % 16) != 0):
            # Warn if any objects exist
            objectsExist = False
            type_obj = ObjectItem

            for obj in items:
                if isinstance(obj, type_obj):
                    objectsExist = True
                    break

            if objectsExist:
                # Objects are selected and the offset is not a multiple of 16.
                # We should warn the user that we will round the offset to the
                # nearest multiple of 16, because objects can only be placed on
                # the grid.
                result = QtWidgets.QMessageBox.information(None, globals_.trans.string('ShftItmDlg', 5),
                                                            globals_.trans.string('ShftItmDlg', 6), QtWidgets.QMessageBox.StandardButton.Yes,
                                                            QtWidgets.QMessageBox.StandardButton.No)

                if result == QtWidgets.QMessageBox.StandardButton.No:
                    return

                # Round the offset to the nearest multiple of 16
                offs_x = 16 * round(offs_x / 16)
                offs_y = 16 * round(offs_y / 16)

        pos_offs_x = offs_x * 1.5
        pos_offs_y = offs_y * 1.5

        globals_.OverrideSnapping = True

        for obj in items:
            obj.setPos(obj.x() + pos_offs_x, obj.y() + pos_offs_y)

        globals_.OverrideSnapping = False

        SetDirty()

    def SwapObjectsTilesets(self):
        """
        Swaps objects' tilesets
        """
        dlg = ObjectTilesetSwapDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        from_tileset = dlg.curr_tileset.currentIndex()
        to_tileset = dlg.new_tileset.currentIndex()
        do_exchange = dlg.exchange_tiles.isChecked()

        if from_tileset == to_tileset:
            return

        for layer in globals_.Area.layers:
            for nsmbobj in layer:
                if nsmbobj.tileset == from_tileset:
                    nsmbobj.SetType(to_tileset, nsmbobj.object_num)
                    SetDirty()
                elif do_exchange and nsmbobj.tileset == to_tileset:
                    nsmbobj.SetType(from_tileset, nsmbobj.object_num)
                    SetDirty()

    def SwitchSprites(self):
        """
        Switches sprites of one ID to another
        """
        initial_id = 0

        items = self.scene.selectedItems()
        if items:
            id_list = []

            # Get all the sprite IDs
            for item in items:
                if isinstance(item, SpriteItem):
                    id_list.append(item.sprite_num)

            # If we only have one unique item, pass that as an ID
            if len(set(id_list)) <= 1:
                initial_id = id_list[0]

        SpriteSwitchDialog(initial_id).exec()

    def HandleAddNewArea(self):
        """
        Adds a new area to the level
        """
        if len(globals_.Level.areas) >= 4:
            QtWidgets.QMessageBox.warning(self, globals_.trans.string('Menu Items', 78), globals_.trans.string('AreaImportDlg', 2))
            return

        # This is an unsaved new level if self.fileSavePath is None
        if CheckDirty() or self.fileSavePath is None:
            # Level is still dirty
            return

        newID = len(globals_.Level.areas) + 1
        globals_.Level.appendArea(None, None, None, None)

        if not self.HandleSave():
            globals_.Level.deleteArea(newID)
            return

        self.LoadLevel(self.fileSavePath, True, newID)

        # Force the new area to be saved to the archive
        # This fixes issues when switching back and forth without saving first,
        # as the area tries load from data that doesn't exist in the archive
        globals_.Level.areas[newID - 1].save()

    def HandleImportArea(self):
        """
        Imports an area from another level
        """
        if len(globals_.Level.areas) >= 4:
            QtWidgets.QMessageBox.warning(self, globals_.trans.string('AreaImportDlg', 0), globals_.trans.string('AreaImportDlg', 2))
            return

        if CheckDirty():
            return

        filetypes = ''
        filetypes += globals_.trans.string('FileDlgs', 1) + ' (*' + '.arc' + ');;'  # *.arc
        filetypes += globals_.trans.string('FileDlgs', 5) + ' (*' + '.arc' + '.LH);;'  # *.arc.LH
        filetypes += globals_.trans.string('FileDlgs', 10) + ' (*' + '.arc' + '.LZ);;'  # *.arc.LZ
        filetypes += globals_.trans.string('FileDlgs', 2) + ' (*)'  # *

        fn = QtWidgets.QFileDialog.getOpenFileName(self, globals_.trans.string('FileDlgs', 0), '', filetypes)[0]
        if fn == '':
            return

        with open(str(fn), 'rb') as fileobj:
            arcdata = fileobj.read()

        if (arcdata[0] & 0xF0) == 0x40:  # If LH-compressed
            try:
                arcdata = lh.UncompressLH(arcdata)
            except IndexError:
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Decompress', 0),
                                              globals_.trans.string('Err_Decompress', 1, '[file]', str(fn)))
                return
        elif not arcdata.startswith(b"U\xAA8-"):  # If LZ-compressed
            try:
                arcdata = lz77.UncompressLZ77(arcdata)
            except IndexError:
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Decompress', 0),
                                                globals_.trans.string('Err_Decompress', 2, '[file]', str(fn)))
                return

        arc = archive.U8.load(arcdata)

        # get the area count
        areacount = 0

        for item, val in arc.files:
            if val is not None:
                # it's a file
                fname = item[item.rfind('/') + 1:]
                if fname.startswith('course'):
                    maxarea = int(fname[6])
                    if maxarea > areacount: areacount = maxarea

        # Choose the area
        dlg = AreaImportDialog(areacount)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Rejected:
            return

        area = dlg.area_combo.currentIndex() + 1

        # get the required files
        reqcourse = 'course%d.bin' % area
        reqL0 = 'course%d_bgdatL0.bin' % area
        reqL1 = 'course%d_bgdatL1.bin' % area
        reqL2 = 'course%d_bgdatL2.bin' % area

        course = None
        L0 = None
        L1 = None
        L2 = None

        for item, val in arc.files:
            if val is not None:
                fname = item.split('/')[-1]
                if fname == reqcourse:
                    course = val
                elif fname == reqL0:
                    L0 = val
                elif fname == reqL1:
                    L1 = val
                elif fname == reqL2:
                    L2 = val

        # add them to our level
        globals_.Level.appendArea(course, L0, L1, L2)
        new_id = globals_.Level.areas[-1].areanum

        if not self.HandleSave():
            globals_.Level.deleteArea(new_id)
            return

        self.LoadLevel(self.fileSavePath, True, new_id)

    def HandleDeleteArea(self):
        """
        Deletes the current area
        """
        result = QtWidgets.QMessageBox.warning(self, globals_.trans.string('DeleteArea', 1), globals_.trans.string('DeleteArea', 0),
                                               QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return

        # Save the current area in case something goes wrong.
        if not self.HandleSave():
            return

        area_to_delete = globals_.Area.areanum
        new_area_one = 1 if area_to_delete != 1 else 2

        # Load the new area 1 before deleting the old area to avoid glitches
        # when the old area was area 1.
        self.LoadLevel(self.fileSavePath, True, new_area_one)

        # Actually delete the area
        globals_.Level.deleteArea(area_to_delete)

        self.action_list['deletearea'].setEnabled(len(globals_.Level.areas) > 1)

        # Update the area selection combobox
        self.area_combo_box.clear()

        for area in globals_.Level.areas:
            self.area_combo_box.addItem(globals_.trans.string('AreaCombobox', 0, '[num]', area.areanum))

        self.area_combo_box.setCurrentIndex(0)

        # Save the level without the area as promised
        self.HandleSave()

    def HandleChangeGamePath(self, auto=False):
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
            ok = self.LoadLevel(globals_.FirstStageFilename, True, 1)
            if not ok:
                self.LoadLevel(None, False, 1)

        return True

    def HandlePreferences(self):
        """
        Edit Reggie Next preferences
        """
        # Show the dialog
        dlg = PreferencesDialog()
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Rejected:
            return

        # Check if we need to show the restart warning
        show_restart_warning = False

        # Get the translation's folder name
        name = dlg.general_tab.translations[dlg.general_tab.trans_combo.currentIndex()][0]
        if setting('Translation') != name:
            show_restart_warning = True
        setSetting('Translation', name)

        # Get the Zone Entrance Indicators setting
        globals_.DrawEntIndicators = dlg.general_tab.zone_entrance_line.isChecked()
        setSetting('ZoneEntIndicators', globals_.DrawEntIndicators)

        # Get the Zone Bounds Indicators setting
        globals_.BoundsDrawn = dlg.general_tab.zone_bound_indicators.isChecked()
        setSetting('ZoneBoundIndicators', globals_.BoundsDrawn)

        # Get the reset data when hiding setting
        globals_.ResetDataWhenHiding = dlg.general_tab.reset_data_hide.isChecked()
        setSetting('ResetDataWhenHiding', globals_.ResetDataWhenHiding)

        # Padding settings
        globals_.EnablePadding = dlg.general_tab.enable_padding.isChecked()
        setSetting('EnablePadding', globals_.EnablePadding)

        globals_.PaddingLength = dlg.general_tab.padding_value.value()
        setSetting('PaddingLength', globals_.PaddingLength)

        # Full object size setting
        globals_.PlaceObjectsAtFullSize = dlg.general_tab.full_object_size.isChecked()
        setSetting('PlaceObjectsAtFullSize', globals_.PlaceObjectsAtFullSize)

        globals_.AutoDiagEnabled = dlg.general_tab.auto_diag.isChecked()
        setSetting('AutoDiagEnabled', globals_.AutoDiagEnabled)

        globals_.AutoDiagFrequency = dlg.general_tab.diag_freq.currentIndex()
        setSetting('AutoDiagFrequency', globals_.AutoDiagFrequency)

        globals_.ShowUnknownSpriteWarning = dlg.general_tab.show_unk_sprite_msg.isChecked()
        setSetting('ShowUnknownSpriteWarning', globals_.ShowUnknownSpriteWarning)

        # Update diagnostic widget
        self.diagnostic.set_timer()
        if globals_.AutoDiagEnabled:
            # Need to remake the entire bar, or else
            # auto-diag will appear after the zoom stuff
            self.setup_status_bar()

            self.diagnostic.update_status()
        else:
            status_bar = self.statusBar()
            if status_bar is not None:
                status_bar.removeWidget(self.diagnostic)

        # Get the Toolbar tab settings
        boxes = (
            dlg.toolbar_tab.file_boxes,
            dlg.toolbar_tab.edit_boxes,
            dlg.toolbar_tab.view_boxes,
            dlg.toolbar_tab.settings_boxes,
            dlg.toolbar_tab.help_boxes
        )

        toolbar_actions = {}
        box: ToolbarCheckBox

        for box_list in boxes:
            for box in box_list:
                toolbar_actions[box.internal_name] = box.isChecked()
        setSetting('ToolbarActs', toolbar_actions)

        # Update the toolbar
        self.setup_toolbar()

        # Get keybinds and save them
        tab: KeybindEditorTab
        key_edit: KeybindLineEdit

        for tab in dlg.keybind_tab.tabs:
            for key_edit in tab.key_edits:
                SetKeybind(key_edit.name, key_edit.keySequence())

        # Toggles keybinds for first 10 items in Recent Files menu
        globals_.UseRecentFileKeys = dlg.keybind_tab.recent_file_keybind.isChecked()
        setSetting('UseRecentFileKeys', globals_.UseRecentFileKeys)

        globals_.MoveItemsWithArrowKeys = dlg.keybind_tab.arrow_move_items.isChecked()
        setSetting('MoveItemsWithArrowKeys', globals_.MoveItemsWithArrowKeys)

        for i, act in enumerate(self.RecentMenu.actions()):
            if not globals_.UseRecentFileKeys:
                act.setShortcut(QtGui.QKeySequence())
            else:
                if i <= 9:
                    act.setShortcut(QtGui.QKeySequence(f'Ctrl+Alt+{i}'))

        # Get the theme settings
        theme = dlg.appearance_tab.themes[dlg.appearance_tab.theme_combo.currentIndex()][0]
        style = dlg.appearance_tab.window_style.currentText()

        if setting('Theme') != theme:
            show_restart_warning = True
        if setting('uiStyle') != style:
            show_restart_warning = True

        setSetting('Theme', theme)
        setSetting('uiStyle', style)

        globals_.UseRoundedRectangles = dlg.appearance_tab.rounded_rects.isChecked()
        globals_.DarkMode = dlg.appearance_tab.dark_mode.isChecked()
        globals_.TilesetTabPos = dlg.appearance_tab.tileset_tab_pos.currentIndex()
        globals_.UseFullFilepath = dlg.appearance_tab.full_file_path.isChecked()
        globals_.CursorMode = dlg.appearance_tab.cursor_mode.currentIndex()

        setSetting('UseRoundedRectangles', globals_.UseRoundedRectangles)
        setSetting('DarkMode', globals_.DarkMode)
        setSetting('TilesetTabPos', globals_.TilesetTabPos)
        setSetting('UseFullFilepath', globals_.UseFullFilepath)
        setSetting('CursorMode', globals_.CursorMode)

        # Update window title
        if self.fileSavePath:
            if globals_.UseFullFilepath:
                self.fileTitle = self.fileSavePath
            else:
                self.fileTitle = os.path.basename(self.fileSavePath)
        self.UpdateTitle()

        # Toggle hover events for scene items
        for item in self.scene.items():
            if not isinstance(item, ZoneItem):
                item.setAcceptHoverEvents(globals_.CursorMode != 0)

        # Update mode
        SetColorScheme()

        # We have to restart since this must be applied before the QApplication
        # is created... no way to do that while the editor is running
        globals_.IgnoreWinScale = dlg.appearance_tab.ignore_win_scale.isChecked()
        if setting('IgnoreWinScale') != globals_.IgnoreWinScale:
            show_restart_warning = True

        setSetting('IgnoreWinScale', globals_.IgnoreWinScale)

        # Warn the user that they may need to restart
        if show_restart_warning:
            QtWidgets.QMessageBox.warning(None, globals_.trans.string('PrefsDlg', 0), globals_.trans.string('PrefsDlg', 30))

    def HandleNewLevel(self):
        """
        Create a new level
        """
        if CheckDirty():
            return

        self.LoadLevel(None, False, 1)

    def HandleOpenFromName(self):
        """
        Open a level using the level picker
        """
        if CheckDirty():
            return

        LoadLevelNames()
        dlg = ChooseLevelNameDialog()
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.LoadLevel(dlg.current_level, False, 1)

    def HandleOpenFromFile(self):
        """
        Open a level using the filename
        """
        if CheckDirty():
            return

        filetypes = ''
        filetypes += globals_.trans.string('FileDlgs', 9) + ' (*.arc *.arc.LH *.arc.LZ);;'   # *.arc, *arc.LH, *.arc.LZ
        filetypes += globals_.trans.string('FileDlgs', 1) + ' (*.arc);;'            # *.arc
        filetypes += globals_.trans.string('FileDlgs', 5) + ' (*.arc.LH);;'         # *.arc.LH
        filetypes += globals_.trans.string('FileDlgs', 10) + ' (*.arc.LZ);;'         # *.arc.LZ
        filetypes += globals_.trans.string('FileDlgs', 2) + ' (*)'                  # *
        fn = QtWidgets.QFileDialog.getOpenFileName(self, globals_.trans.string('FileDlgs', 0), '', filetypes)[0]
        if fn == '':
            return

        self.LoadLevel(str(fn), True, 1)

    def HandleSave(self):
        """
        Save a level back to the archive. Returns whether saving was successful.
        """
        if not self.fileSavePath or self.fileSavePath.endswith('.arc.LH'):
            # Delegate save to HandleSaveAs function
            return self.HandleSaveAs()

        data = globals_.Level.save()

        # maybe need to compress the data
        if self.fileSavePath.endswith(".arc.LZ"):
            compressed = lz77.CompressLZ77(data)

            if compressed is None:
                # Error during compression
                QtWidgets.QMessageBox.warning(None,
                    globals_.trans.string('Err_Save', 0),
                    globals_.trans.string('Err_Save', 3, '[file-size]', len(data))
                )

                # Delegate to HandleSaveAs
                return self.HandleSaveAs()

            data = compressed

        # maybe pad with null bytes
        if globals_.EnablePadding:
            pad_length = globals_.PaddingLength - len(data)

            if pad_length < 0:
                # err: orig data is longer than padding data
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Save', 0), globals_.trans.string('Err_Save', 2, '[orig-len]', len(data), '[pad-len]', globals_.PaddingLength))
                return False

            data += bytes(pad_length)

        try:
            with open(self.fileSavePath, 'wb') as f:
                f.write(data)
        except IOError as e:
            QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Save', 0),
                                          globals_.trans.string('Err_Save', 1, '[err1]', e.args[0], '[err2]', e.args[1]))
            return False

        globals_.Dirty = False
        globals_.AutoSaveDirty = False
        self.UpdateTitle()

        setSetting('AutoSaveFilePath', self.fileSavePath)
        setSetting('AutoSaveFileData', 'x')
        return True

    def HandleSaveAs(self, copy = False):
        """
        Save a level back to the archive, with a new filename. Returns whether
        saving was successful.
        """
        fn = QtWidgets.QFileDialog.getSaveFileName(self,
            globals_.trans.string('FileDlgs', 8 if copy else 3),
            '',
            globals_.trans.string('FileDlgs', 1) + ' (*' + '.arc' + ');;' +
            globals_.trans.string('FileDlgs', 10) + ' (*' + '.arc.LZ'+ ');;' +
            globals_.trans.string('FileDlgs', 2) + ' (*)'
        )[0]

        if fn == '':  # No filename given - abort
            return False

        if not copy:
            globals_.AutoSaveDirty = False
            globals_.Dirty = False

            self.fileSavePath = fn
            if globals_.UseFullFilepath:
                self.fileTitle = fn
            else:
                self.fileTitle = os.path.basename(fn)

        data = globals_.Level.save()

        # maybe need to compress the data
        if fn.endswith(".arc.LZ"):
            compressed = lz77.CompressLZ77(data)

            if compressed is None:
                # Error during compression
                QtWidgets.QMessageBox.warning(None,
                    globals_.trans.string('Err_Save', 0),
                    globals_.trans.string('Err_Save', 3, '[file-size]', len(data))
                )

                return False

            data = compressed

        # maybe pad with null bytes
        if globals_.EnablePadding:
            pad_length = globals_.PaddingLength - len(data)

            if pad_length < 0:
                # err: orig data is longer than padding data
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Save', 0), globals_.trans.string('Err_Save', 2, '[orig-len]', len(data), '[pad-len]', globals_.PaddingLength))
                return False

            data += bytes(pad_length)

        with open(fn, 'wb') as f:
            f.write(data)

        if not copy:
            setSetting('AutoSaveFilePath', fn)
            setSetting('AutoSaveFileData', 'x')

            self.UpdateTitle()
            self.RecentMenu.add_to_list(self.fileSavePath)

        return True

    def HandleSwitchArea(self, idx):
        """
        Handle activated signals for area_combo_box
        """
        old_idx = globals_.Area.areanum - 1
        if idx == old_idx:
            return

        if CheckDirty():
            self.area_combo_box.setCurrentIndex(old_idx)
            return

        ok = self.LoadLevel(self.fileSavePath, True, idx + 1)

        if not ok:
            # loading the new area failed, so reset the combobox
            self.area_combo_box.setCurrentIndex(old_idx)

    def HandleUpdateLayer0(self, checked):
        """
        Handle toggling of layer 0 being shown
        """
        globals_.Layer0Shown = checked

        if globals_.Area.areanum == -1:
            return

        for obj in globals_.Area.layers[0]:
            obj.setVisible(checked)

        self.scene.update()

    def HandleUpdateLayer1(self, checked):
        """
        Handle toggling of layer 1 being shown
        """
        globals_.Layer1Shown = checked

        if globals_.Area.areanum == -1:
            return

        for obj in globals_.Area.layers[1]:
            obj.setVisible(checked)

        self.scene.update()

    def HandleUpdateLayer2(self, checked):
        """
        Handle toggling of layer 2 being shown
        """
        globals_.Layer2Shown = checked

        if globals_.Area.areanum == -1:
            return

        for obj in globals_.Area.layers[2]:
            obj.setVisible(checked)

        self.scene.update()

    def HandleTilesetAnimToggle(self, checked):
        """
        Handle toggling of tileset animations
        """
        globals_.TilesetsAnimating = checked

        for tile in globals_.Tiles:
            if tile is not None:
                tile.resetAnimation()

        self.scene.update()

    def HandleCollisionsToggle(self, checked):
        """
        Handle toggling of tileset collisions viewing
        """
        globals_.CollisionsShown = checked

        setSetting('ShowCollisions', globals_.CollisionsShown)
        self.scene.update()

    def HandleRealViewToggle(self, checked):
        """
        Handle toggling of Real View
        """
        globals_.RealViewEnabled = checked
        SLib.RealViewEnabled = globals_.RealViewEnabled

        setSetting('RealViewEnabled', globals_.RealViewEnabled)
        self.scene.update()

    def HandleSpritesVisibility(self, checked):
        """
        Handle toggling of sprite visibility
        """
        globals_.SpritesShown = checked
        setSetting('ShowSprites', globals_.SpritesShown)

        if globals_.Area.areanum == -1:
            return

        for spr in globals_.Area.sprites:
            spr.setVisible(checked)

    def HandleSpriteImages(self, checked):
        """
        Handle toggling of sprite images
        """
        globals_.SpriteImagesShown = checked

        setSetting('ShowSpriteImages', globals_.SpriteImagesShown)

        if globals_.Area.areanum == -1:
            return

        globals_.DirtyOverride += 1
        for spr in globals_.Area.sprites:
            spr.UpdateRects()

            if globals_.Initializing:
                continue

            # Prevents snapping the sprite to the grid
            spr.ChangingPos = True

            if checked:
                spr.setPos(
                    (spr.objx + spr.ImageObj.xOffset) * 1.5,
                    (spr.objy + spr.ImageObj.yOffset) * 1.5,
                )
            else:
                spr.setPos(
                    spr.objx * 1.5,
                    spr.objy * 1.5,
                )

            spr.ChangingPos = False
            spr.update()

        globals_.DirtyOverride -= 1

        self.level_overview.update()

    def HandleEntrancesVisibility(self, checked):
        """
        Handle toggling of entrance visibility
        """
        globals_.EntrancesShown = checked
        setSetting('ShowEntrances', globals_.EntrancesShown)

        if globals_.Area.areanum == -1:
            return

        for ent in globals_.Area.entrances:
            ent.setVisible(checked)

    def HandleLocationsVisibility(self, checked):
        """
        Handle toggling of location visibility
        """
        globals_.LocationsShown = checked
        setSetting('ShowLocations', globals_.LocationsShown)

        if globals_.Area.areanum == -1:
            return

        for loc in globals_.Area.locations:
            loc.setVisible(checked)

    def HandleCommentsVisibility(self, checked):
        """
        Handle toggling of comment visibility
        """
        globals_.CommentsShown = checked
        setSetting('ShowComments', globals_.CommentsShown)

        if globals_.Area.areanum == -1:
            return

        for com in globals_.Area.comments:
            com.setVisible(checked)

    def HandlePathsVisibility(self, checked):
        """
        Handle toggling of path visibility
        """
        globals_.PathsShown = checked
        setSetting('ShowPaths', globals_.PathsShown)

        if globals_.Area.areanum == -1:
            return

        for path in globals_.Area.paths:
            path.setVisible(checked)

    def HandleObjectsFreeze(self, checked):
        """
        Handle toggling of objects being frozen
        """
        globals_.ObjectsFrozen = checked
        setSetting('FreezeObjects', globals_.ObjectsFrozen)

        if globals_.Area.areanum == -1:
            return

        flag1 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        unfrozen = not checked

        for layer in globals_.Area.layers:
            for obj in layer:
                obj.setFlag(flag1, unfrozen)
                obj.setFlag(flag2, unfrozen)

    def HandleSpritesFreeze(self, checked):
        """
        Handle toggling of sprites being frozen
        """
        globals_.SpritesFrozen = checked
        setSetting('FreezeSprites', globals_.SpritesFrozen)

        if globals_.Area.areanum == -1:
            return

        flag1 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        unfrozen = not checked

        for spr in globals_.Area.sprites:
            spr.setFlag(flag1, unfrozen)
            spr.setFlag(flag2, unfrozen)

    def HandleEntrancesFreeze(self, checked):
        """
        Handle toggling of entrances being frozen
        """
        globals_.EntrancesFrozen = checked
        setSetting('FreezeEntrances', globals_.EntrancesFrozen)

        if globals_.Area.areanum == -1:
            return

        flag1 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        unfrozen = not checked

        for ent in globals_.Area.entrances:
            ent.setFlag(flag1, unfrozen)
            ent.setFlag(flag2, unfrozen)

    def HandleLocationsFreeze(self, checked):
        """
        Handle toggling of locations being frozen
        """
        globals_.LocationsFrozen = checked
        setSetting('FreezeLocations', globals_.LocationsFrozen)

        if globals_.Area.areanum == -1:
            return

        flag1 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        unfrozen = not checked

        for loc in globals_.Area.locations:
            loc.setFlag(flag1, unfrozen)
            loc.setFlag(flag2, unfrozen)

    def HandlePathsFreeze(self, checked):
        """
        Handle toggling of path nodes being frozen
        """
        globals_.PathsFrozen = checked
        setSetting('FreezePaths', globals_.PathsFrozen)

        if globals_.Area.areanum == -1:
            return

        for path in globals_.Area.paths:
            path.set_freeze(checked)

    def HandleCommentsFreeze(self, checked):
        """
        Handle toggling of comments being frozen
        """
        globals_.CommentsFrozen = checked
        setSetting('FreezeComments', globals_.CommentsFrozen)

        if globals_.Area.areanum == -1:
            return

        flag1 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        unfrozen = not checked

        for com in globals_.Area.comments:
            com.setFlag(flag1, unfrozen)
            com.setFlag(flag2, unfrozen)

    def HandleSwitchGrid(self):
        """
        Handle switching of the grid view
        """
        if globals_.GridType is None:
            globals_.GridType = 'grid'
        elif globals_.GridType == 'grid':
            globals_.GridType = 'checker'
        else:
            globals_.GridType = None

        setSetting('GridType', globals_.GridType)
        self.scene.update()

    def HandleZoomIn(self, *, towardsCursor=False):
        """
        Handle zooming in
        """
        z = self.ZoomLevel
        zi = self.ZoomLevels.index(z) + 1
        if zi < len(self.ZoomLevels):
            self.ZoomTo(self.ZoomLevels[zi], towardsCursor=towardsCursor)

    def HandleZoomOut(self, *, towardsCursor=False):
        """
        Handle zooming out
        """
        z = self.ZoomLevel
        zi = self.ZoomLevels.index(z) - 1
        if zi >= 0:
            self.ZoomTo(self.ZoomLevels[zi], towardsCursor=towardsCursor)

    def HandleZoomActual(self):
        """
        Handle zooming to the actual size
        """
        self.ZoomTo(100.0)

    def HandleZoomMin(self):
        """
        Handle zooming to the minimum size
        """
        self.ZoomTo(self.ZoomLevels[0])

    def HandleZoomMax(self):
        """
        Handle zooming to the maximum size
        """
        self.ZoomTo(self.ZoomLevels[-1])

    def ZoomTo(self, z, *, towardsCursor=False):
        """
        Zoom to a specific level
        """
        if towardsCursor:
            self.view.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        tr = QtGui.QTransform()
        tr.scale(z / 100.0, z / 100.0)
        self.ZoomLevel = z
        self.view.setTransform(tr)
        self.level_overview.main_window_scale = z / 100.0

        if towardsCursor:
            # (reset back to original transformation anchor)
            self.view.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)

        zi = self.ZoomLevels.index(z)
        self.action_list['zoommax'].setEnabled(zi < len(self.ZoomLevels) - 1)
        self.action_list['zoomin'].setEnabled(zi < len(self.ZoomLevels) - 1)
        self.action_list['zoomactual'].setEnabled(z != 100.0)
        self.action_list['zoomout'].setEnabled(zi > 0)
        self.action_list['zoommin'].setEnabled(zi > 0)

        self.ZoomWidget.set_zoom_level(z)
        self.ZoomStatusWidget.set_zoom_level(z)

        # Update the zone grabber rects, to resize for the new zoom level
        for z in globals_.Area.zones:
            z.UpdateRects()

        self.scene.update()

    def HandleOverviewClick(self, x, y):
        """
        Handle position changes from the level overview
        """
        self.view.centerOn(x, y)
        self.level_overview.update()

    def SaveComments(self):
        """
        Saves the comments data back to self.Metadata
        """
        b = b""
        for com in globals_.Area.comments:
            text_data = com.text.encode("utf-8")
            # A previous version of this format used the third integer to store
            # the length (number of characters) of the comment string. This
            # makes reading comments back very hard, as a single character can
            # consist of multiple points.
            # So, to indicate we're using the new version, we set a length of
            # 2 ** 32 - 1, and we add an extra int to store the number of bytes
            # in the utf-8 encoding of the comment text.
            b += struct.pack(">4I", com.objx, com.objy, 0xFFFF_FFFF, len(text_data))
            b += text_data

        globals_.Area.Metadata.setBinData('InLevelComments_A%d' % globals_.Area.areanum, b)

    def closeEvent(self, a0):
        """
        Handler for the main window close event
        """
        if a0 is None:
            return

        if CheckDirty():
            a0.ignore()
            return

        # Save our state
        self.spriteEditorDock.setVisible(False)
        self.entrance_editor_dock.setVisible(False)
        self.path_editor_dock.setVisible(False)
        self.location_editor_dock.setVisible(False)
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

    def LoadLevel(self, name, isFullPath, areaNum):
        """
        Load a level from NSMBW into the editor.
        """
        new = name is None
        same = False

        if not new:
            checknames = []
            if isFullPath:
                checknames = [name]
            else:
                for ext in globals_.FileExtentions:
                    checknames.append(os.path.join(globals_.gamedef.GetStageGamePath(), name + ext))

            for checkname in checknames:
                if os.path.isfile(checkname):
                    break
            else:
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_CantFindLevel', 1),
                                              globals_.trans.string('Err_CantFindLevel', 0, '[name]', checkname),
                                              QtWidgets.QMessageBox.StandardButton.Ok)
                return False

            if not IsNSMBLevel(checkname):
                QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_InvalidLevel', 1), globals_.trans.string('Err_InvalidLevel', 0),
                                              QtWidgets.QMessageBox.StandardButton.Ok)
                return False

            name = checkname
            same = name == self.fileSavePath  # Just an area change

        # Get the file path, if possible
        if new:
            # Set the filepath variables
            self.fileSavePath = None
            self.fileTitle = 'untitled'

        elif not same:

            # Get the data
            if not globals_.RestoredFromAutoSave:

                # Set the filepath variables
                self.fileSavePath = name
                if self.fileSavePath is None:
                    return

                if globals_.UseFullFilepath:
                    self.fileTitle = self.fileSavePath
                else:
                    self.fileTitle = os.path.basename(self.fileSavePath)

                # Open the file
                with open(self.fileSavePath, 'rb') as fileobj:
                    levelData = fileobj.read()

                # Decompress, if needed
                if (levelData[0] & 0xF0) == 0x40:  # If LH-compressed
                    try:
                        levelData = lh.UncompressLH(levelData)
                    except IndexError:
                        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Decompress', 0),
                                                      globals_.trans.string('Err_Decompress', 1, '[file]', name))
                        return False
                elif not levelData.startswith(b"U\xAA8-"):  # If LZ-compressed
                    try:
                        levelData = lz77.UncompressLZ77(levelData)
                    except IndexError:
                        QtWidgets.QMessageBox.warning(None, globals_.trans.string('Err_Decompress', 0),
                                                      globals_.trans.string('Err_Decompress', 2, '[file]', name))
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
                levelData = globals_.AutoSaveData
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
        globals_.LocationsShown = True
        globals_.EntrancesShown = True
        globals_.PathsShown = True
        globals_.CommentsShown = True

        # Prevent things from snapping when they're created
        globals_.OverrideSnapping = True

        # Load the actual level
        if new:
            self.newLevel()
        elif not same:
            self.LoadNSMBWLevel(levelData, areaNum)
        else:
            # We have already loaded this area's data - it's stored as
            # AbstractAreas in the Level. This means we do not have to open and
            # optionally decompress the level file. Hence, we can just relay
            # this to the level.
            globals_.Level.changeArea(areaNum)
            self.reset_area()

        # Fill up the area list
        self.area_combo_box.clear()

        for area in globals_.Level.areas:
            self.area_combo_box.addItem(globals_.trans.string('AreaCombobox', 0, '[num]', area.areanum))

        self.area_combo_box.setCurrentIndex(areaNum - 1)

        # Refresh object layouts
        for layer in globals_.Area.layers:
            for obj in layer:
                obj.updateObjCache()

        for sprite in globals_.Area.sprites:
            sprite.UpdateDynamicSizing()
            sprite.ImageObj.positionChanged()

        # Scroll to the initial entrance
        startEntID = globals_.Area.startEntrance
        startEnt = None
        for ent in globals_.Area.entrances:
            if ent.entid == startEntID:
                self.view.centerOn(ent)
                break
        else:
            self.view.centerOn(0, 0)

        self.ZoomTo(100.0)

        # Reset some editor things
        self.action_list['showlay0'].setChecked(True)
        self.action_list['showlay1'].setChecked(True)
        self.action_list['showlay2'].setChecked(True)
        self.action_list['showsprites'].setChecked(True)
        self.action_list['showentrances'].setChecked(True)
        self.action_list['showlocations'].setChecked(True)
        self.action_list['showpaths'].setChecked(True)
        self.action_list['showcomments'].setChecked(True)
        self.action_list['addarea'].setEnabled(len(globals_.Level.areas) < 4)
        self.action_list['importarea'].setEnabled(len(globals_.Level.areas) < 4)
        self.action_list['deletearea'].setEnabled(len(globals_.Level.areas) > 1)
        self.action_list['backgrounds'].setEnabled(len(globals_.Area.zones) > 0)

        # Turn snapping back on
        globals_.OverrideSnapping = False

        # Turn the dirty flag off
        globals_.DirtyOverride -= 1
        self.UpdateTitle()

        # Update UI things
        self.scene.update()

        self.level_overview.reset()
        self.level_overview.update()

        if new:
            SetDirty()

        elif not same:
            # Add the path to Recent Files
            self.RecentMenu.add_to_list(self.fileSavePath)

        # If we got this far, everything worked! Return True.
        return True

    def newLevel(self):
        # Create the new level object
        globals_.Level = NSMBWLevel()

        # Load it
        globals_.Level.new()

        self.palette_dock.object_tab.reset(True)

        self.action_list['swapobjectstypes'].setEnabled(True)
        self.action_list['swapobjectstilesets'].setEnabled(True)

    def LoadNSMBWLevel(self, levelData, areaNum):
        """
        Performs all level-loading tasks specific to New Super Mario Bros. Wii levels.
        Do not call this directly - use LoadLevel instead!
        """
        # Create the new level object
        globals_.Level = NSMBWLevel()

        # Load it
        if not globals_.Level.load(levelData, areaNum):
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

        self.reset_area()

    def reset_area(self):
        """
        Resets the palette and initialises the scene from the currently loaded
        Area.
        """
        # Reset the palette
        self.palette_dock.reset()

        pos_change = ObjectItem.position_changed
        for layer in reversed(globals_.Area.layers):
            for obj in layer:
                obj.positionChanged = pos_change
                self.scene.addItem(obj)

        for zone in globals_.Area.zones:
            self.scene.addItem(zone)

        for path in globals_.Area.paths:
            path.add_to_scene()

    def ChangeSelectionHandler(self):
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
        showSpritePanel = False
        showEntrancePanel = False
        showLocationPanel = False
        showPathPanel = False
        updateModeInfo = False

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
                showSpritePanel = True
                updateModeInfo = True
                allowStamp = True
            elif func_ii(item, type_ent):
                self.palette_dock.set_tab(2)
                self.UpdateFlag = True
                self.palette_dock.entrance_tab.entrance_list.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                showEntrancePanel = True
                updateModeInfo = True
                allowStamp = False
            elif func_ii(item, type_loc):
                self.palette_dock.set_tab(3)
                self.UpdateFlag = True
                self.palette_dock.location_tab.location_list.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                showLocationPanel = True
                updateModeInfo = True
                allowStamp = False
            elif func_ii(item, type_path):
                self.palette_dock.set_tab(4)
                self.UpdateFlag = True
                self.palette_dock.path_tab.path_list.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                showPathPanel = True
                updateModeInfo = True
                allowStamp = False
            elif func_ii(item, type_com):
                self.palette_dock.set_tab(7)
                self.UpdateFlag = True
                self.palette_dock.comment_tab.comment_list.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                updateModeInfo = True
                allowStamp = False

        else:
            updateModeInfo = True

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

        self.spriteEditorDock.setVisible(showSpritePanel)
        self.entrance_editor_dock.setVisible(showEntrancePanel)
        self.location_editor_dock.setVisible(showLocationPanel)
        self.path_editor_dock.setVisible(showPathPanel)

        self.action_list['deselect'].setEnabled(bool(selitems))

        if updateModeInfo:
            globals_.DirtyOverride += 1
            self.UpdateModeInfo()
            globals_.DirtyOverride -= 1

    def SpriteDataUpdated(self, data):
        """
        Handle the current sprite's data being updated
        """
        if self.spriteEditorDock.isVisible():
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

        if isinstance(self.selObj, SpriteItem) and self.spriteEditorDock.isVisible():
            obj = self.selObj
            self.spriteDataEditor.setSprite(obj.sprite_num, initial_data=obj.spritedata)
        elif isinstance(self.selObj, EntranceItem) and self.entrance_editor_dock.isVisible():
            self.entrance_editor.set_entrance(self.selObj)
        elif isinstance(self.selObj, PathItem) and self.path_editor_dock.isVisible():
            self.path_editor.setPath(self.selObj)
        elif isinstance(self.selObj, LocationItem) and self.location_editor_dock.isVisible():
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

        SetDirty()

        # Sprites
        # Extracting the sprite id from the sprite name is hacky, but it works.
        globals_.Area.loaded_sprites = set(int(desc.split(']')[0][1:]) for desc in dlg.loadedSpritesTab.autoModel.stringList())
        globals_.Area.force_loaded_sprites = set(int(desc.split(']')[0][1:]) for desc in dlg.loadedSpritesTab.customModel.stringList())

        # Settings
        globals_.Area.timeLimit = dlg.settingsTab.timer.value() - 200
        globals_.Area.startEntrance = dlg.settingsTab.entrance.value()
        globals_.Area.toadHouseType = dlg.settingsTab.toadHouseType.currentIndex()
        globals_.Area.wrapFlag = dlg.settingsTab.wrap.isChecked()
        globals_.Area.creditsFlag = dlg.settingsTab.credits.isChecked()
        globals_.Area.faceLeftFlag = dlg.settingsTab.faceLeft.isChecked()
        globals_.Area.unkFlag1 = dlg.settingsTab.unk1.isChecked()
        globals_.Area.unkFlag2 = dlg.settingsTab.unk2.isChecked()
        globals_.Area.unkVal1 = dlg.settingsTab.unk3.value()
        globals_.Area.unkVal2 = dlg.settingsTab.unk4.value()

        # Tilesets
        tilesetNum = 0
        for idx, fname in enumerate(dlg.tilesetsTab.values()):

            if fname in ('', None):
                fname = ''
            elif fname.startswith(globals_.trans.string('AreaDlg', 16)):
                fname = fname[len(globals_.trans.string('AreaDlg', 17, '[name]', '')):]

            globals_.Area.tilesets[idx] = fname

            if fname != '':
                tilesetNum += 1
                LoadTileset(idx, fname)
            else:
                UnloadTileset(idx)

        self.palette_dock.object_tab.reset(False, False)

        for layer in globals_.Area.layers:
            for obj in layer:
                obj.updateObjCache()

        self.action_list['swapobjectstypes'].setEnabled(tilesetNum != 0)
        self.action_list['swapobjectstilesets'].setEnabled(tilesetNum != 0)

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

        SetDirty()

        # resync the zones
        items = self.scene.items()
        func_ii = isinstance
        type_zone = ZoneItem

        for item in items:
            if func_ii(item, type_zone):
                self.scene.removeItem(item)

        globals_.Area.zones = []

        for i, tab in enumerate(dlg.zoneTabs):
            z = tab.zoneObj
            z.id = i
            z.UpdateTitle()
            globals_.Area.zones.append(z)
            self.scene.addItem(z)

            z.objx = clamp(16, 24560, tab.zPosX.value())
            z.objy = clamp(16, 12272, tab.zPosY.value())
            z.width = min(24560 - z.objx, tab.zWidth.value())
            z.height = min(12272 - z.objy, tab.zHeight.value())

            z.prepareGeometryChange()
            z.UpdateRects()
            z.setPos(z.objx * 1.5, z.objy * 1.5)

            z.modeldark = tab.theme.currentIndex()
            z.terraindark = tab.terrainLight.currentIndex()
            z.cammode = tab.camModeZoom.modeButtonGroup.checkedId()
            z.camzoom = tab.camModeZoom.screenSizes.currentIndex()
            z.camtrack = tab.direction.currentIndex()

            if tab.restrictY.isChecked():
                z.mpcamzoomadjust = tab.mpZoomAdjust.value()
            else:
                z.mpcamzoomadjust = 15

            z.visibility = 0

            if tab.spotlight.isChecked():
                z.visibility |= 1 << 4
            if tab.fullDark.isChecked():
                z.visibility |= 1 << 5

            z.visibility |= tab.visibility.currentIndex()

            z.yupperbound = tab.boundUp.value()
            z.ylowerbound = tab.boundDown.value()
            z.yupperbound2 = tab.lakituBoundUp.value()
            z.ylowerbound2 = tab.lakituBoundDown.value()
            z.yupperbound3 = tab.mpBoundUp.value()
            z.ylowerbound3 = tab.mpBoundDown.value()

            z.music = tab.musicID.value()
            z.sfxmod = tab.modulation.currentIndex() << 4
            if tab.bossFlag.isChecked():
                z.sfxmod |= 1

        for spr in globals_.Area.sprites:
            spr.ImageObj.positionChanged()

        self.action_list['backgrounds'].setEnabled(len(globals_.Area.zones) > 0)
        self.level_overview.update()

    def HandleBG(self):
        """
        Pops up the Background settings Dialog
        """
        dlg = BackgroundDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        SetDirty()
        for tab, z in zip(dlg.bgTabs, globals_.Area.zones):
            # First index: BGA/BGB
            # Second index: X/Y
            z.XpositionA = tab.posBoxes[0][0].value()
            z.YpositionA = -tab.posBoxes[0][1].value()
            z.XpositionB = tab.posBoxes[1][0].value()
            z.YpositionB = -tab.posBoxes[1][1].value()

            z.XscrollA = tab.scrollBoxes[0][0].currentIndex()
            z.YscrollA = tab.scrollBoxes[0][1].currentIndex()
            z.XscrollB = tab.scrollBoxes[1][0].currentIndex()
            z.YscrollB = tab.scrollBoxes[1][1].currentIndex()

            z.ZoomA = tab.zoomBoxes[0].currentIndex()
            z.ZoomB = tab.zoomBoxes[1].currentIndex()

            z.bg1A = tab.hexBoxes[0][0].value()
            z.bg2A = tab.hexBoxes[0][1].value()
            z.bg3A = tab.hexBoxes[0][2].value()

            z.bg1B = tab.hexBoxes[1][0].value()
            z.bg2B = tab.hexBoxes[1][1].value()
            z.bg3B = tab.hexBoxes[1][2].value()

    def HandleScreenshot(self):
        """
        Takes a screenshot of the entire level and saves it
        """
        dlg = ScreenshotDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        target = dlg.target_combo.currentIndex()
        grid_type = dlg.grid_type.currentIndex()
        hide_background = dlg.hide_background.isChecked()
        save_to_file = dlg.save_img.isChecked()

        # Update the canvas grid while we take the screenshot
        grid_type_list = [None, 'grid', 'checker']
        current_grid_type = globals_.GridType
        globals_.GridType = grid_type_list[grid_type]
        self.scene.update()

        file_name = ''
        if save_to_file:
            filt = f'{globals_.trans.string('FileDlgs', 4)} (*.png)'

            file_name = QtWidgets.QFileDialog.getSaveFileName(self, globals_.trans.string('FileDlgs', 3), None, filt)[0]
            if file_name == '':
                return

        # Current view
        if target == 0:
            screenshot_rect = QtCore.QRect(QtCore.QPoint(), self.view.size())
            renderer = self.view
            ss_img = QtGui.QImage(screenshot_rect.size(), QtGui.QImage.Format.Format_ARGB32)
        else:
            # All zones together
            if target == 1:
                screenshot_rect = QtCore.QRectF()

                for z in globals_.Area.zones:
                    screenshot_rect |= z.ZoneRect

            # Specific zone
            else:
                screenshot_rect = globals_.Area.zones[target - 2].ZoneRect

            # Map the zone rects to the scene coordinate system
            screenshot_rect = (QtGui.QTransform() * 1.5).mapRect(screenshot_rect)
            # Add 40 pixels of padding on all sides
            screenshot_rect += QtCore.QMarginsF(40, 40, 40, 40)
            # Make sure the rectangle doesn't go out of bounds
            screenshot_rect &= QtCore.QRectF(0, 0, 1024 * 24, 512 * 24)

            renderer = self.scene
            renderer.is_screenshot = True
            ss_img = QtGui.QImage(screenshot_rect.size().toSize(), QtGui.QImage.Format.Format_ARGB32)

        ss_img.fill(Qt.GlobalColor.transparent)
        ss_painter = QtGui.QPainter(ss_img)

        # Remove the background
        if hide_background:
            brush = self.scene.backgroundBrush()
            style = brush.style()
            brush.setStyle(Qt.BrushStyle.NoBrush)
            self.scene.setBackgroundBrush(brush)

            # Render
            renderer.render(ss_painter, source=screenshot_rect)

            # Restore the background
            brush.setStyle(style)
            self.scene.setBackgroundBrush(brush)
        else:
            renderer.render(ss_painter, source=screenshot_rect)

        ss_painter.end()

        if save_to_file:
            ss_img.save(file_name, 'PNG', 50)
        else:
            if globals_.app is not None:
                clip = globals_.app.clipboard()
                if clip is not None:
                    clip.setImage(ss_img)

        if target != 0:
            self.scene.is_screenshot = False

        # Restore grid
        globals_.GridType = current_grid_type
        self.scene.update()

    def HandleCameraProfiles(self):
        """
        Pops up the options for camera profiles
        """
        dlg = CameraProfilesDialog()
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        cam_profiles = []
        for row in range(dlg.list.count()):
            item = dlg.list.item(row)
            if item is not None:
                cam_profiles.append(item.data(QtCore.Qt.ItemDataRole.UserRole))

        globals_.Area.camprofiles = cam_profiles
        SetDirty()
