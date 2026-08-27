from collections import OrderedDict
from typing import Literal

from PyQt6 import QtCore, QtGui, QtWidgets

from src.data.common.gamedef import ReggieGameDefinition
from reggie import ReggieWindow
from src.data.level.abstract_level import AbstractLevel
from src.data.level.area import Area as AreaType
from src.data.level.sprite_definition import SpriteDefinition
from src.data.common.keybind import Keybind
from src.data.common.menu_action import MenuAction
from src.data.tileset.tile.rand_tile_selection import RandTileSelection
from src.data.sprite.sprite_category import SpriteCategory
from src.data.tileset.tileset_category import TilesetCategory
from src.data.tileset.object.object_def import ObjectDef
from src.data.tileset.tile.tileset_tile import TilesetTile
from src.data.common.reggie_translation import ReggieTranslation
from src.ui.theme.reggie_theme import ReggieTheme

# Reggie / UI
AutoDiagEnabled = True
AutoDiagFrequency = 1
AutoSaveData = b''
AutoSaveDirty = False
AutoSavePath = ''
BgANames: list[list[str]] = []
BgBNames: list[list[str]] = []
CursorMode = 0
DarkMode = False
EntranceTypeNames: OrderedDict[int, str] = OrderedDict()
ErrMsg = ''
FirstStageFilename: str | None = None
Initializing = False
LevelNames: tuple[str, ...] = ()
MusicInfo: dict[str, str] = {}
NumberFont: QtGui.QFont | None = None
ObjDesc: dict[int, str] = {}
ReggieID = 'Reggie! Next Level Editor by Treeki, Tempus and RoadrunnerWMC'
ReggieVersionFloat = 4.11
ReggieVersionShort = 'v4.11.0'
RestoredFromAutoSave = False
TilesetTabPos = 0
UseFullFilepath = False
UseRecentFileKeys = True

# Menu
EditActions: tuple[MenuAction, ...] = ()
FileActions: tuple[MenuAction, ...] = ()
HelpActions: tuple[MenuAction, ...] = ()
SettingsActions: tuple[MenuAction, ...] = ()
ViewActions: tuple[MenuAction, ...] = ()

# Keybinds
FileKeybinds: list[Keybind]
EditKeybinds: list[Keybind]
ViewKeybinds: list[Keybind]
SettingsKeybinds: list[Keybind]
HelpKeybinds: list[Keybind]

# Canvas / Editor
BoundsDrawn = False
CollisionsShown = False
CommentsFrozen = False
CommentsShown = True
CurrentLayer = 1
CurrentObject = -1
CurrentPaintType = 0
CurrentSprite = -1
DrawEntIndicators = False
EntrancesFrozen = False
EntrancesShown = True
GridType: Literal['grid', 'checker'] | None = None
InsertPathNode = False
Layer0Shown = True
Layer1Shown = True
Layer2Shown = True
LocationsFrozen = False
LocationsShown = True
ObjectsFrozen = False
PathsFrozen = False
PathsShown = True
PlaceObjectsAtFullSize = True
RealViewEnabled = False
SpriteImagesShown = True
SpritesFrozen = False
SpritesShown = True
TilesetsAnimating = False
UseRoundedRectangles = True

# Level
Area: AreaType = AreaType.DummyArea()
Dirty = False
DirtyOverride = 0
EnablePadding = False
FileExtentions = ('.arc', '.arc.LH', '.arc.LZ')
Level: AbstractLevel # Uninitialized on purpose. It's never accessed before being written to. Reduces redudant "is None" checks.
PaddingLength = 0
ZoneThemeValues: list[str] = []

# Tilesets
ObjectDefinitions: list[list[ObjectDef | None]] = [] # 4 tilesets
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
OverrideSnapping = False
Overrides: list[TilesetTile | None] = [] # 320 tiles, this is put into Tiles usually
Overrides_safe: list[TilesetTile | None] = []
OVERRIDE_UNKNOWN = 0
Tiles: list[TilesetTile | None] = [] # 0x200 tiles per tileset, plus 64 for each type of override
TilesetAnimTimer: QtCore.QTimer | None = None
TilesetFilesLoaded: list[str | None] = [None for _ in range(4)] # should always have exactly 4 entries
TilesetInfo: dict[str, dict[int, RandTileSelection]] = {}
TilesetNames: list[TilesetCategory] = [TilesetCategory() for _ in range(4)] # should always have exactly 4 entries

# Sprites
NumSprites = 0
ResetDataWhenHiding = False
SpriteCategories: list[SpriteCategory] = []
Sprites: list[SpriteDefinition] = []

# Game patch config settings
DispConnectedPipeDir = False
SpecialEventSpriteID = 0
AllowSizeHacks = False

app: QtWidgets.QApplication | None = None
firstLoad = True
trans: ReggieTranslation = ReggieTranslation(None)
gamedef: ReggieGameDefinition = ReggieGameDefinition()
mainWindow: ReggieWindow | None = None
# uninitialized
settings: QtCore.QSettings
theme: ReggieTheme
