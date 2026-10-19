from collections import OrderedDict
from typing import Literal

from PyQt6 import QtCore, QtGui, QtWidgets

from data.common.gamedef import ReggieGameDefinition
from data.common.keybind import Keybind
from data.common.menu_action import MenuAction
from data.common.reggie_translation import ReggieTranslation
from data.common.toolbar_action import ToolbarAction
from data.level.abstract_level import AbstractLevel
from data.level.area import Area as AreaType
from data.level.sprite_definition import SpriteDefinition
from data.sprite.sprite_category import SpriteCategory
from data.tileset.object.object_def import ObjectDef
from data.tileset.tile.rand_tile_selection import RandTileSelection
from data.tileset.tile.tileset_tile import TilesetTile
from data.tileset.tileset_category import TilesetCategory
from reggie import ReggieWindow
from ui.theme.reggie_theme import ReggieTheme

# Reggie / UI
AutoDiagEnabled: bool = True
AutoDiagFrequency: int = 1
AutoSaveData: bytes = b''
AutoSaveDirty: bool = False
AutoSavePath: str = ''
BgANames: list[list[str]] = []
BgBNames: list[list[str]] = []
CursorMode: int = 0
DarkMode: bool = False
EntranceTypeNames: OrderedDict[int, str] = OrderedDict()
ErrMsg: str = ''
FirstStageFilename: str | None = None
IgnoreWinScale: bool = False
Initializing: bool = False
LevelNames: tuple[str, ...] = ()
MusicInfo: dict[str, str] = {}
NumberFont: QtGui.QFont | None = None
ObjDesc: dict[int, str] = {}
ReggieID: str = 'Reggie! Next Level Editor by Treeki, Tempus and RoadrunnerWMC'
ReggieVersionFloat: float = 5.0
ReggieVersionShort: str = 'v5.0.0'
RestoredFromAutoSave: bool = False
TilesetTabPos: int = 0
UseFullFilepath: bool = False
UseRecentFileKeys: bool = True

# Menu
EditActions: tuple[ToolbarAction, ...] = ()
FileActions: tuple[ToolbarAction, ...] = ()
HelpActions: tuple[ToolbarAction, ...] = ()
SettingsActions: tuple[ToolbarAction, ...] = ()
ViewActions: tuple[ToolbarAction, ...] = ()

MenuActions: tuple[MenuAction, ...] = ()

# Keybinds
FileKeybinds: list[Keybind]
EditKeybinds: list[Keybind]
ViewKeybinds: list[Keybind]
SettingsKeybinds: list[Keybind]
HelpKeybinds: list[Keybind]

# Canvas / Editor
BoundsDrawn: bool = False
CollisionsShown: bool = False
CommentsFrozen: bool = False
CommentsShown: bool = True
CurrentLayer: int = 1
CurrentObject: int = -1
CurrentPaintType: int = 0
CurrentSprite: int = -1
DrawEntIndicators: bool = False
EntrancesFrozen: bool = False
EntrancesShown: bool = True
GridType: Literal['grid', 'checker'] | None = None
InsertPathNode: bool = False
Layer0Shown: bool = True
Layer1Shown: bool = True
Layer2Shown: bool = True
LocationsFrozen: bool = False
LocationsShown: bool = True
MoveItemsWithArrowKeys: bool = True
ObjectsFrozen: bool = False
PathsFrozen: bool = False
PathsShown: bool = True
PlaceObjectsAtFullSize: bool = True
RealViewEnabled: bool = False
SpriteImagesShown: bool = True
SpritesFrozen: bool = False
SpritesShown: bool = True
TilesetsAnimating: bool = False
UseRoundedRectangles: bool = True

# Level
Area: AreaType = AreaType.DummyArea()
Dirty: bool = False
DirtyOverride: int = 0
EnablePadding: bool = False
FileExtentions: tuple[str, ...] = ('.arc', '.arc.LH', '.arc.LZ')
Level: AbstractLevel  # Uninitialized on purpose. It's never accessed before being written to. Reduces redudant "is None" checks.
PaddingLength: int = 0
ZoneThemeValues: list[str] = []

# Tilesets
ObjectDefinitions: list[list[ObjectDef | None]] = []  # 4 tilesets
OverriddenTilesets: dict[str, set[str]] = {
    "Pa0": set(),
    "no-Pa0": set(),
    "Flowers": set(),
    "Forest Flowers": set(),
    "Lines": set(),
    "Minigame Lines": set(),
    "Full Lines": set(),
    "Conveyors": set()
}
OverrideSnapping: bool = False
Overrides: list[TilesetTile | None] = []  # 320 tiles, this is put into Tiles usually
Overrides_safe: list[TilesetTile | None] = []
OVERRIDE_UNKNOWN: int = 0
ShowTilesetPreview: bool = False
Tiles: list[TilesetTile | None] = []  # 0x200 tiles per tileset, plus 64 for each type of override
TilesetAnimTimer: QtCore.QTimer | None = None
TilesetFilesLoaded: list[str | None] = [None for _ in range(4)]  # should always have exactly 4 entries
TilesetInfo: dict[str, dict[int, RandTileSelection]] = {}
TilesetNames: list[TilesetCategory] = [TilesetCategory() for _ in range(4)]  # should always have exactly 4 entries

# Sprites
NumSprites: int = 0
ResetDataWhenHiding: bool = False
ShowUnknownSpriteWarning: bool = True
SpriteCategories: list[SpriteCategory] = []
Sprites: list[SpriteDefinition] = []

# Game patch config settings
DispConnectedPipeDir: bool = False
SpecialEventSpriteID: int = 0
AllowSizeHacks: bool = False

app: QtWidgets.QApplication | None = None
firstLoad: bool = True
trans: ReggieTranslation = ReggieTranslation(None)
gamedef: ReggieGameDefinition = ReggieGameDefinition()
mainWindow: ReggieWindow | None = None
# uninitialized
settings: QtCore.QSettings
theme: ReggieTheme
